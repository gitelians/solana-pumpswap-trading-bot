# solana-pumpswap-trading-bot
A python codebase to create a personalized dataset, train a Random Forest model, and use it to build an autonomous trading bot on memecoin just listed on PumpSwap (those who have just graduated from pump.fun).

1. COLLECTING DATA
Collect data in a tailor-made dataset running 'get_pools_data.py'. You can run it locally or deploy the code into an external server (like Hetzner) to let it run 24/7. Collect at least 5,000 observations for a consistent training. 

2. TRAINING & TESTING A RANDOM FOREST MODEL
Once your dataset is ready, it is time to clean it and prepare it for training: remove eventual duplicates, check for rows with missing data, build label and features for model training. You may want to remove those tokens who have abnormal (fake outliers) 'holders' and 'top_10' values by removing those rows that have 'top_10' = 0. Otherwise you can convert those values in np.nan, which could be useful for Random Forest training (it depends on your training strategy).

3. TRADING
Run 'trading_bot.py' calling the .pkl file of the trained model.
