import yfinance as yf
import csv
import os
from datetime import datetime, timedelta

# Define the CSV file directory relative to the script's location
CSV_DIR = os.path.join(os.path.dirname(__file__), "crypto_data")
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

def get_crypto_symbols():
    """Define list of crypto symbols to fetch"""
    return [
        "BTC-USD",  # Bitcoin
        "ETH-USD",  # Ethereum
        "USDT-USD", # Tether
        "BNB-USD",  # Binance Coin
        "XRP-USD",  # Ripple
        "SOL-USD",  # Solana
        "DOGE-USD", # Dogecoin
        "ADA-USD",  # Cardano
        "LINK-USD", # Chainlink
        "DOT-USD"   # Polkadot
    ]

def fetch_historical_data(symbol, start_time, end_time):
    """Fetch historical hourly data for a given crypto symbol"""
    try:
        # Create a Ticker object
        ticker = yf.Ticker(symbol)
        
        # Get historical data with hourly intervals
        df = ticker.history(start=start_time, end=end_time, interval='1h')
        
        if df.empty:
            print(f"No data returned for {symbol}")
            return []
            
        # Convert the data to the format we want
        data = [(t.strftime("%Y-%m-%d %H:%M:%S"), price) 
                for t, price in zip(df.index, df['Close'])]
        return data
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return []

def save_to_csv(symbol, data):
    """Save the crypto data to a CSV file"""
    try:
        # Create filename - convert BTC-USD to btc_usd_hourly_data.csv
        filename = f"{symbol.lower().replace('-', '_')}_hourly_data.csv"
        csv_file = os.path.join(CSV_DIR, filename)
        
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "price_usd"])  # Header
            writer.writerows(data)
        print(f"Successfully saved data for {symbol}")
    except Exception as e:
        print(f"Error saving data for {symbol}: {e}")

def update_data():
    """Main function to update all crypto data"""
    print(f"Starting crypto data update at {datetime.now()}")
    
    # Get list of cryptocurrencies
    cryptos = get_crypto_symbols()
    
    # Calculate time range - last 30 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    # Fetch and save data for each crypto
    for symbol in cryptos:
        print(f"Fetching data for {symbol}")
        historical_data = fetch_historical_data(symbol, start_time, end_time)
        if historical_data:
            save_to_csv(symbol, historical_data)
        else:
            print(f"No data to save for {symbol}")

if __name__ == "__main__":
    update_data()
