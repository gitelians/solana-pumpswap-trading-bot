# Import libraries
import requests
import json
import time
import os
import pickle
import pandas as pd
import base64
import csv
from solana.rpc.api import Client
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from solana.rpc.types import TokenAccountOpts
from datetime import datetime, timezone
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders import message
from solana.rpc.commitment import Processed
from dotenv import load_dotenv
from ai_agent import get_boosts

# === CONFIG ===
load_dotenv(dotenv_path="auth.env")
PRIVATE_KEY_B64 = os.getenv("PRIVATE_KEY_B64") # Wallet private key in base64
# Solana API
RPC_URL = "https://api.mainnet-beta.solana.com"
NEW_POOLS_API = "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1"
POOL_DATA_API = "https://api.geckoterminal.com/api/v2/networks/solana/pools/{}"
TOKEN_INFO_API = "https://api.geckoterminal.com/api/v2/networks/solana/tokens/{}/info"
# Telegram login
TELEGRAM_BOT_TOKEN = "yourbottoken"
TELEGRAM_CHANNEL = "@yourchannelname"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
# General variable
LIQUIDITY_THRESHOLD = 9999
LOCKED_LIQUIDITY_THRESHOLD = 89
INVESTMENT_AMOUNT_SOL = 0.01
POSITIONS_FILE = "active_positions.json"
MODEL_PATH = "./training/patricio.pkl"
LOG_FILE = 'positions_logs.csv'

# Initialize Client
client = Client(RPC_URL)

# --- FUNCTIONS --- #
# Load my Phantom Wallet
def load_wallet():
    if not PRIVATE_KEY_B64:
        raise ValueError("❌ PRIVATE_KEY_B64 missing")
    secret_key = base64.b64decode(PRIVATE_KEY_B64)
    return Keypair.from_bytes(secret_key)
wallet = load_wallet()

# Load RF model
def load_model():
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)
model = load_model()

# SOL Balance
def get_sol_balance():
    sol_balance = client.get_balance(wallet.pubkey())
    return sol_balance.value / 1e9

# --- API CALLS --- #
# Get New Pools
def fetch_new_pools():
    response = requests.get(NEW_POOLS_API)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Get Pools Data
def fetch_pool_data(address):
    response = requests.get(POOL_DATA_API.format(address))
    if response.status_code == 200:
        return response.json().get("data", {})
    print(f"Error in API request 'Fetch Pool Data': {response.status_code}")
    return {}

# Get token price
def fetch_pool_price(address):
    response = requests.get(POOL_DATA_API.format(address))
    if response.status_code == 200:
        price = float(response.json().get("data", {}).get('attributes', {})["base_token_price_usd"])
        return price
    print(f"Error in API request 'Fetch Pool Price': {response.status_code}")
    return 0.0

# Get Token INFO
def fetch_token_info(token_address):
    response = requests.get(TOKEN_INFO_API.format(token_address))
    if response.status_code == 200:
        return response.json().get("data", {})
    print(f"Error in API request 'Fetch Token Info': {response.status_code}")
    return {}
     
# Send messages on Telegram
def send_telegram_message(address, boost):
    message = f"{int(boost)}⚡: {address}"
    payload = {"chat_id": TELEGRAM_CHANNEL, "text": message}
    response = requests.post(TELEGRAM_API_URL, json=payload)
    if response.status_code != 200:
        print(f"Error sending Telegram message: {response.text}")    

# === MANAGE SWAP & TRADES === #
# Get swap tx on Jupiter
def get_jupiter_swap_tx(input_mint, output_mint, amount):
    try:
        # 1. Get quotes from the new Quote API
        quote_url = "https://lite-api.jup.ag/swap/v1/quote"
        quote_params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 50,
            "swapMode": "ExactIn",
            "restrictIntermediateTokens": "true"
        }
        quote_response = requests.get(quote_url, params=quote_params)
        if quote_response.status_code != 200:
            print(f"❌ Error in Jupiter quote: {quote_response.status_code}")
            print(quote_response.text)
            return None
        # Data structure for tx parameters
        quote_data = quote_response.json() 
        # Extract SOL in output
        sol_out = float(quote_data["outAmount"]) / 1e9  # from lamport to SOL

        # 2. Build transaction using the quote just obtained
        swap_url = "https://lite-api.jup.ag/swap/v1/swap"
        payload = {
            "userPublicKey": str(wallet.pubkey()),
            "quoteResponse": quote_data,
            "prioritizationFeeLamports": {
                "priorityLevelWithMaxLamports": {
                    "maxLamports": 10000000,
                    "priorityLevel": "veryHigh"
                }
            },
            "dynamicComputeUnitLimit": True,
            "dynamicSlippage": True
        }

        headers = {
            "Content-Type": "application/json",
            'Accept': 'application/json'
        }
        swap_response = requests.post(swap_url, json=payload, headers=headers)

        if swap_response.status_code == 200:
            result = swap_response.json()
            if 'swapTransaction' in result:
                return result, sol_out
            else:
                print("⚠️ No 'swapTransaction' present:", result)
        else:
            print(f"❌ Errore HTTP Jupiter /swap: {swap_response.status_code}")
            print(swap_response.text)
    except Exception as e:
        print(f"❌ Error during Jupiter swap request: {e}")

    return None

# Build full tx on Solana
def execute_swap(transaction):
    try:
        # 1. Convert from Serialized base64 → Serialized Uint8array (binary buffer) format
        tx_bytes = base64.b64decode(transaction['swapTransaction'])

        # 2. Deserialize the versioned transaction
        tx_des = VersionedTransaction.from_bytes(tx_bytes)
 
        # 3. Sign the transaction
        signature = wallet.sign_message(message.to_bytes_versioned(tx_des.message)) 
        signed_tx = VersionedTransaction.populate(tx_des.message,[signature]) 

        # 4. Serialize for sending (Uint8Array → bytes)
        serialized_tx = bytes(signed_tx)    

        # 5. Send transaction to the network
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = client.send_raw_transaction(txn=serialized_tx, opts=opts)

        # Store transaction id
        tx_id = json.loads(result.to_json())['result']
        print(f"✅ Transaction Sent: https://solscan.io/tx/{tx_id}")
        return tx_id

    except Exception as e:
        print(f"❌ Transaction Error: {e}")
        return None

# Get token balance
def get_token_balance(token_mint):
    try: 
        mint = Pubkey.from_string(token_mint)
        owner = Pubkey.from_string("58LReYgZ56SYpaMLrEEob2fMHxecYguZ6FRHkYN73PSR")
        token_accounts = client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint=mint))
        token_account_pubkey = token_accounts.value[0].pubkey

        # Return 0 if no tokens present
        if not token_account_pubkey:
            return 0.0
        
        # Get token balance amount
        balance = client.get_token_account_balance(token_account_pubkey)
        return balance.value.ui_amount
    
    except Exception as e:
        print(f"❌ Error retrieving balance for {token_mint}: {e}")
        return 0.0

# Buy tokens
def buy_token(pool_address, input_mint, output_mint, price0):
    sol_balance = get_sol_balance()
    if sol_balance >= INVESTMENT_AMOUNT_SOL:
        amount = int(INVESTMENT_AMOUNT_SOL * 1e9)
        print(f"🪙  SOL → {output_mint} - Pool: {pool_address}")
        swap_tx, sol_out = get_jupiter_swap_tx(input_mint, output_mint, amount)
        if swap_tx:
            tx_id = execute_swap(swap_tx)
            positions = load_positions()
            positions[pool_address] = {
                "output_mint": output_mint,
                "entry_price": price0,
                "tx_id": tx_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            save_positions(positions)
        else:
            print(f"❌ Error retrieving swap transaction for {pool_address}.")
    else:
        print("❌ You don't have enough SOL")

# Sell tokens
def sell_token(pool_address, token_mint):
    amount = get_token_balance(token_mint)
    amount = int(amount) * 1000000
    print(f"🪙  {token_mint} → SOL - Pool: {pool_address}")
    if amount > 0:
        swap_tx, sol_out = get_jupiter_swap_tx(token_mint, "So11111111111111111111111111111111111111112", amount)
        if swap_tx:
            # Execute swap
            tx_id = execute_swap(swap_tx)
            # Position log
            log_investment(pool_address, token_mint, tx_id, sol_out=sol_out)
        else:
            print("❌ Error during token sale")
    else:
        print(f"⚠️ No tokens to sell found for {token_mint}.")

# Manage open positions
def check_investments():
    positions = load_positions()
    updated_positions = {}

    for pool_address, data in positions.items():
        entry_price = data['entry_price']     
        time.sleep(1)   
        current_price = fetch_pool_price(pool_address)

        if current_price >= 2 * entry_price:
            print(f"🚀 You did a 2x! 😎 ")
            sell_token(pool_address, data['output_mint'])
            print(f'current price = {current_price}')
        elif current_price <= 0.49 * entry_price:
            print(f"👎 Ooh no! -51% on bet 😪")
            sell_token(pool_address, data['output_mint'])
            print(f'current price = {current_price}')
        else:
            updated_positions[pool_address] = data
    save_positions(updated_positions)

# === LOG SETUP === #
# Load open positions in json file
def load_positions():
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save open positions in json file
def save_positions(data):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize csv file for order logs
FIELDNAMES = ["pool", "token", "timestamp", "tx", "sol_out"]
def initialize_log_file():
    try:
        with open(LOG_FILE, "x", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
    except FileExistsError:
        pass

# Upload logs into csv file
def log_investment(address, output_mint, tx_id, sol_out=None):
    initialize_log_file()
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "pool": address,
            "token": output_mint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tx": f"https://solscan.io/tx/{tx_id}",
            "sol_out": sol_out if sol_out is not None else ""
        })

# --- MAIN --- #
def main():
    print("🤖 Running the trading bot on Solana...")
    processed_pools = set()

    while True:
        new_pools = fetch_new_pools()
        for pool in new_pools:
            # New pools data
            address = pool['attributes']['address']
            dex = pool['relationships']['dex']['data']['id'].lower()
            # Handle None values
            try: 
                liquidity = float(pool['attributes']['reserve_in_usd'])   
            except (TypeError, ValueError):
                print(f"Error in liquidity parsing")
                liquidity = float('nan')
            
            # --- CONDITION 1 --- #
            if liquidity > LIQUIDITY_THRESHOLD and address not in processed_pools and dex in ('pumpswap'):                
                check_investments()
                processed_pools.add(address)
                time.sleep(12) # API timeout error handling
                # Get pool data
                try:    
                    pool_data = fetch_pool_data(address)
                    pool_attributes = pool_data.get('attributes', {})
                    raw_lock = pool_attributes.get('locked_liquidity_percentage')
                    lock = float(raw_lock) if raw_lock is not None else 0.0  
                    liquidity_2 = float(pool_attributes.get('reserve_in_usd')) 
                except Exception as e:
                    print(f"Error in 'Fetch Pool Data': {e}")
                    lock = float('nan')
                    liquidity_2 = float('nan')

                # --- CONDITION 2 --- #
                if liquidity_2 > LIQUIDITY_THRESHOLD and lock > LOCKED_LIQUIDITY_THRESHOLD:                    
                    try:
                        volume = float(pool_attributes['volume_usd'].get('h24'))
                        fdv = float(pool_attributes.get('fdv_usd'))
                    except Exception as e:
                        print(f"Error in parsing volume and/or fdv: {e}")
                        volume, fdv = float('nan'), float('nan')

                    price0 = float(pool_attributes['base_token_price_usd'])
                    buys = pool_attributes['transactions']['h24'].get('buys') or 0
                    sells = pool_attributes['transactions']['h24'].get('sells') or 0
                    b_s = (buys/(buys+sells)) if buys > 0 else float('nan')
                    v_mc = (volume/fdv) if volume > 0 and fdv > 0 else float('nan')
                    token_address = pool['relationships']['base_token']['data']['id'].replace('solana_', '')
                    time.sleep(1) 
                    # try-except block to handle fetch_token_info 404 API error
                    try:
                        token_info = fetch_token_info(token_address)
                        attributes = token_info.get('attributes', {})
                        holders_data = attributes.get('holders', {})
                        holders = holders_data.get('count') or 0 # get number of token holders
                        top_10_dist = 0 # get top 10 dist percentage
                        if holders_data.get('distribution_percentage') and holders_data['distribution_percentage'].get('top_10') is not None:
                            top_10_dist = float(holders_data['distribution_percentage']['top_10'])
                        twitter = 1 if attributes.get('twitter_handle') else 0 # dummy for existing X profile

                    except Exception as e:
                        print(f"Errore in 'Fetch Token Info': {e}")
                        holders = float('nan')
                        top_10_dist = float('nan')
                        twitter = float('nan')               
                
                    data = {
                        'liquidity': [liquidity_2],
                        'volume': [volume],
                        'market_cap': [fdv],
                        'holders': [holders],
                        'top_10': [top_10_dist],
                        'twitter': [twitter],
                        'b/s': [b_s],
                        'v/mc': [v_mc], 
                        'price0':  [price0]                          
                    }
                    
                    features = pd.DataFrame(data) # Extract features

                    # Model prediction 
                    if features is not None: # Error Handling if None values are present in features   
                        y = model.predict(features)
                        print(y[0])            
                        if y[0] == 1:
                            input_mint = "So11111111111111111111111111111111111111112" # wSOL address
                            output_mint = pool.get("relationships", {}).get("base_token", {}).get("data", {}).get("id", "").replace("solana_", "")
                            buy_token(address, input_mint, output_mint, price0)
                            print(f'entry price = {price0}')                
                            # AI Agent checking for boosts ⚡
                            # boost = get_boosts(address)
                            # if int(boost) > 0:                       
                            #     send_telegram_message(address, boost)
                    else:
                        print('features are None')   

                    time.sleep(1)
                    check_investments() 

        time.sleep(2)
        check_investments()


# --- RUN BOT --- #
if __name__ == '__main__':
    main()



