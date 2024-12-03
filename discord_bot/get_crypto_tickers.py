import requests
import csv
import os
from datetime import datetime

# API endpoint for CoinGecko
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Define the CSV file directory relative to the script's location
CSV_DIR = os.path.join(os.path.dirname(__file__), "crypto_data")
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

def get_top_1000_cryptos():
    try:
        all_cryptos = []
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,  # Max allowed per request
            'sparkline': False
        }
        
        # Paginate through the top 1000 cryptos (250 per page, 4 pages)
        for page in range(1, 5):
            params['page'] = page
            response = requests.get(COINGECKO_API_URL, params=params)
            response.raise_for_status()
            cryptos = response.json()
            all_cryptos.extend(cryptos)
        
        return all_cryptos
    except Exception as e:
        print(f"Error fetching top 1000 cryptos: {e}")
        return []

def save_crypto_list():
    cryptos = get_top_1000_cryptos()
    if not cryptos:
        return
    
    # Save to CSV
    csv_file = os.path.join(CSV_DIR, "top_crypto_list.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:  # Use UTF-8 encoding
        writer = csv.writer(file)
        writer.writerow(['symbol', 'name', 'market_cap_rank'])  # Header
        
        for crypto in cryptos:
            # Convert symbol to Yahoo Finance format
            yahoo_symbol = f"{crypto['symbol'].upper()}-USD"
            writer.writerow([
                yahoo_symbol,
                crypto['name'],
                crypto['market_cap_rank']
            ])
    
    print(f"Saved {len(cryptos)} cryptocurrencies to {csv_file}")

if __name__ == "__main__":
    save_crypto_list()
