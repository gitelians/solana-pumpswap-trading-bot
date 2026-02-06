"""
THIS CODE MANAGE DATA COLLECTING TRHOUGH COINGECKO TERMINAL API WITH A 
DUAL LIQUIDITY FILTER AND A THRESHOLD ON THE PERCENTAGE OF LOCKED LIQUIDITY
"""

import requests
import csv
import time
import os

# API Endpoint configuration 
NEW_POOLS_API = "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1"
POOL_DATA_API = "https://api.geckoterminal.com/api/v2/networks/solana/pools/{}" 
TOKEN_INFO_API = "https://api.geckoterminal.com/api/v2/networks/solana/tokens/{}/info"
CSV_FILE = "pools_data.csv"
LIQUIDITY_THRESHOLD = 9999
LOCKED_LIQUIDITY_THRESHOLD = 89
# Price intervals
CHECK_INTERVAL_1 = 600    #10 minutes - price_10m
CHECK_INTERVAL_2 = 900    #15 minutes - price_15m
CHECK_INTERVAL_3 = 1200   #20 minutes - price_20m
CHECK_INTERVAL_4 = 1500   #25 minutes - price_25m
CHECK_INTERVAL_5 = 1800   #30 minutes - price_30m
CHECK_INTERVAL_6 = 2100   #35 minutes - price_35m
CHECK_INTERVAL_7 = 2400   #40 minutes - price_40m
CHECK_INTERVAL_8 = 2700   #45 minutes - price_45m
CHECK_INTERVAL_9 = 3000   #50 minutes - price_50m
CHECK_INTERVAL_10 = 3300  #55 minutes - price_55m
CHECK_INTERVAL_11 = 3600  #60 minutes - price_60m
CHECK_INTERVAL_2h  = 7200    # 2h
CHECK_INTERVAL_3h  = 10800   # 3h
CHECK_INTERVAL_4h  = 14400   # 4h
CHECK_INTERVAL_5h  = 18000   # 5h
CHECK_INTERVAL_6h  = 21600   # 6h
CHECK_INTERVAL_7h  = 25200   # 7h
CHECK_INTERVAL_8h  = 28800   # 8h
CHECK_INTERVAL_9h  = 32400   # 9h
CHECK_INTERVAL_10h = 36000   # 10h
CHECK_INTERVAL_11h = 39600   # 11h
CHECK_INTERVAL_12h = 43200   # 12h

# Cache for pools already processed
processed_pools = set()

# Fetch new pools data
def fetch_new_pools():
    response = requests.get(NEW_POOLS_API)
    if response.status_code == 200:
        return response.json().get("data", [])
    print(f"Errore nella richiesta API 'Fetch New Pools': {response.status_code}")
    return []

# Token INFO
def fetch_token_info(token_address):
    response = requests.get(TOKEN_INFO_API.format(token_address))
    if response.status_code == 200:
        return response.json().get("data", {})
    print(f"Errore nella richiesta API 'Fetch Token Info': {response.status_code}")
    return {}

# Get current token price
def fetch_pool_data(address):
    response = requests.get(POOL_DATA_API.format(address))
    if response.status_code == 200:
        return response.json().get("data", {})
    print(f"Errore nella richiesta API 'Fetch Pool Data': {response.status_code}")
    return {}

# Read pools already collected
def load_existing_pools():
    existing_pools = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row["timestamp"] = float(row.get("timestamp", time.time()))
                row["price_10m"] = float(row.get("price_10m", 0)) if row.get("price_10m") not in [None, ""] else ""
                row["price_15m"] = float(row.get("price_15m", 0)) if row.get("price_15m") not in [None, ""] else ""
                row["price_20m"] = float(row.get("price_20m", 0)) if row.get("price_20m") not in [None, ""] else ""
                row["price_25m"] = float(row.get("price_25m", 0)) if row.get("price_25m") not in [None, ""] else ""
                row["price_30m"] = float(row.get("price_30m", 0)) if row.get("price_30m") not in [None, ""] else ""
                row["price_35m"] = float(row.get("price_35m", 0)) if row.get("price_35m") not in [None, ""] else ""
                row["price_40m"] = float(row.get("price_40m", 0)) if row.get("price_40m") not in [None, ""] else ""
                row["price_45m"] = float(row.get("price_45m", 0)) if row.get("price_45m") not in [None, ""] else ""
                row["price_50m"] = float(row.get("price_50m", 0)) if row.get("price_50m") not in [None, ""] else ""
                row["price_55m"] = float(row.get("price_55m", 0)) if row.get("price_55m") not in [None, ""] else ""
                row["price_60m"] = float(row.get("price_60m", 0)) if row.get("price_60m") not in [None, ""] else ""
                row["price_2h"]  = float(row.get("price_2h", 0))  if row.get("price_2h")  not in [None, ""] else ""
                row["price_3h"]  = float(row.get("price_3h", 0))  if row.get("price_3h")  not in [None, ""] else ""
                row["price_4h"]  = float(row.get("price_4h", 0))  if row.get("price_4h")  not in [None, ""] else ""
                row["price_5h"]  = float(row.get("price_5h", 0))  if row.get("price_5h")  not in [None, ""] else ""
                row["price_6h"]  = float(row.get("price_6h", 0))  if row.get("price_6h")  not in [None, ""] else ""
                row["price_7h"]  = float(row.get("price_7h", 0))  if row.get("price_7h")  not in [None, ""] else ""
                row["price_8h"]  = float(row.get("price_8h", 0))  if row.get("price_8h")  not in [None, ""] else ""
                row["price_9h"]  = float(row.get("price_9h", 0))  if row.get("price_9h")  not in [None, ""] else ""
                row["price_10h"] = float(row.get("price_10h", 0)) if row.get("price_10h") not in [None, ""] else ""
                row["price_11h"] = float(row.get("price_11h", 0)) if row.get("price_11h") not in [None, ""] else ""
                row["price_12h"] = float(row.get("price_12h", 0)) if row.get("price_12h") not in [None, ""] else ""
                existing_pools[row["address"]] = row
    return existing_pools

# Save new pools into csv file
def save_all_pools(existing_pools):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["name", "address", "liquidity", "volume", "market_cap", 
                         "holders", "top_10", "twitter", "b/s", "v/mc", 
                         "price0", "price_10m", "price_15m", "price_20m", "price_25m", "price_30m",
                         "price_35m", "price_40m", "price_45m", "price_50m", "price_55m", "price_60m",
                         "price_2h", "price_3h", "price_4h", "price_5h", "price_6h", "price_7h", "price_8h", "price_9h", 
                         "price_10h", "price_11h", "price_12h", "timestamp"])
        
        for pool in existing_pools.values():
            writer.writerow([
                pool['name'], pool['address'], pool['liquidity'], pool['volume'], pool['market_cap'], 
                pool['holders'], pool['top_10'], pool['twitter'], pool['b/s'], pool['v/mc'],  
                pool['price0'], pool.get('price_10m', ''), pool.get('price_15m', ''), pool.get('price_20m', ''),
                pool.get('price_25m', ''), pool.get('price_30m', ''), pool.get('price_35m', ''), pool.get('price_40m', ''),
                pool.get('price_45m', ''), pool.get('price_50m', ''), pool.get('price_55m', ''), pool.get('price_60m', ''),
                pool.get('price_2h', ''), pool.get('price_3h', ''), pool.get('price_4h', ''), pool.get('price_5h', ''), 
                pool.get('price_6h', ''), pool.get('price_7h', ''), pool.get('price_8h', ''), pool.get('price_9h', ''), 
                pool.get('price_10h', ''), pool.get('price_11h', ''), pool.get('price_12h', ''), pool['timestamp']
            ])

# Update prices
def update_prices(existing_pools):
    updated_pools = False

    steps = [
        ("price_10m", CHECK_INTERVAL_1),
        ("price_15m", CHECK_INTERVAL_2),
        ("price_20m", CHECK_INTERVAL_3),
        ("price_25m", CHECK_INTERVAL_4),
        ("price_30m", CHECK_INTERVAL_5),
        ("price_35m", CHECK_INTERVAL_6),
        ("price_40m", CHECK_INTERVAL_7),
        ("price_45m", CHECK_INTERVAL_8),
        ("price_50m", CHECK_INTERVAL_9),
        ("price_55m", CHECK_INTERVAL_10),
        ("price_60m", CHECK_INTERVAL_11),
        ("price_2h", CHECK_INTERVAL_2h),
        ("price_3h", CHECK_INTERVAL_3h),
        ("price_4h", CHECK_INTERVAL_4h),
        ("price_5h", CHECK_INTERVAL_5h),
        ("price_6h", CHECK_INTERVAL_6h),
        ("price_7h", CHECK_INTERVAL_7h),
        ("price_8h", CHECK_INTERVAL_8h),
        ("price_9h", CHECK_INTERVAL_9h),
        ("price_10h", CHECK_INTERVAL_10h),
        ("price_11h", CHECK_INTERVAL_11h),
        ("price_12h", CHECK_INTERVAL_12h)
    ]

    for address, data in sorted(existing_pools.items(), key=lambda x: x[1]["timestamp"], reverse=True):
        elapsed_time = time.time() - data["timestamp"]

        for key, interval in steps:
            if data.get(key, "") == "" and elapsed_time >= interval:
                # Set delays to not overload API calls
                if "h" in key:
                    time.sleep(5)
                elif key.endswith("60m"):
                    time.sleep(2)

                pool_data = fetch_pool_data(address)
                data[key] = float(pool_data["attributes"]["base_token_price_usd"])
                updated_pools = True
                print(f"✅ {data['name']} - ({address}): {key}={data[key]}")

    if updated_pools:
        save_all_pools(existing_pools)
  

# --- MAIN LOOP --- #
def main():
    global processed_pools
    existing_pools = load_existing_pools()
    processed_pools.update(existing_pools.keys())
    print("Welcome back! I start looking for new tokens 👀")

    while True:
        pools = fetch_new_pools()
        new_pools = []
        
        for pool in pools: 
            # New pools data
            address = pool['attributes']['address']
            name = pool['attributes']['name']
            dex = pool['relationships']['dex']['data']['id'].lower()

            try: 
                liquidity = float(pool['attributes']['reserve_in_usd'])   
            except (TypeError, ValueError):
                print(f"Errore nel parsing di liquidity")
                liquidity = float('nan')
            
            # --- CONDITION 1 --- #
            if liquidity > LIQUIDITY_THRESHOLD and address not in processed_pools and dex in ('pumpswap'):
                processed_pools.add(address)
                time.sleep(12)
                # Get pool data
                try:    
                    pool_data = fetch_pool_data(address)
                    pool_attributes = pool_data.get('attributes', {})
                    raw_lock = pool_attributes.get('locked_liquidity_percentage')
                    lock = float(raw_lock) if raw_lock is not None else 0.0  
                    liquidity_2 = float(pool_attributes.get('reserve_in_usd')) 
                except Exception as e:
                    print(f"Errore in 'Fetch Pool Data': {e}")
                    lock = float('nan')
                    liquidity_2 = float('nan')

                # --- CONDITION 2 --- #
                if liquidity_2 > LIQUIDITY_THRESHOLD and lock > LOCKED_LIQUIDITY_THRESHOLD:
                    try:
                        volume = float(pool_attributes['volume_usd'].get('h24'))
                        fdv = float(pool_attributes.get('fdv_usd'))
                    except Exception as e:
                        print(f"Errore nel parsing di volume e/o fdv: {e}")
                        volume, fdv = float('nan'), float('nan')

                    price0 = float(pool_attributes['base_token_price_usd'])
                    buys = pool_attributes['transactions']['h24'].get('buys') or 0
                    sells = pool_attributes['transactions']['h24'].get('sells') or 0
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
                        twitter = 1 if attributes.get('twitter_handle') else 0 # dummy for excisting X account

                    except Exception as e:
                        print(f"Errore in 'Fetch Token Info': {e}")
                        holders = float('nan')
                        top_10_dist = float('nan')
                        twitter = float('nan')

                    timestamp = time.time() # get timestamp
                
                    # Append new pool data          
                    new_pools.append({
                        "name": name,
                        "address": address,
                        "liquidity": liquidity_2,
                        "volume": volume,
                        "market_cap": fdv,
                        "holders": holders,
                        "top_10": top_10_dist,
                        "twitter": twitter,
                        "b/s": (buys/(buys+sells)) if buys > 0 else float('nan'),
                        "v/mc":(volume/fdv) if volume > 0 and fdv > 0 else float('nan'),
                        "price0": price0,
                        "price_10m": '',
                        "price_15m": '',
                        "price_20m": '',
                        "price_25m": '',
                        "price_30m": '',
                        "price_35m": '',
                        "price_40m": '',
                        "price_45m": '',
                        "price_50m": '',
                        "price_55m": '',
                        "price_60m": '',
                        "price_2h": '',
                        "price_3h": '',
                        "price_4h": '',
                        "price_5h": '',
                        "price_6h": '',
                        "price_7h": '',
                        "price_8h": '',
                        "price_9h": '',
                        "price_10h": '',
                        "price_11h": '',
                        "price_12h": '',
                        "timestamp": timestamp,
                    })                  
            

        # Update price(n)
        time.sleep(2)
        update_prices(existing_pools)
        
        # Save new pools into dataset
        if new_pools:
            existing_pools.update({pool["address"]: pool for pool in new_pools})
            save_all_pools(existing_pools)
       
        print("Waiting for new pools... 🤤")       

if __name__ == "__main__":
    main()



