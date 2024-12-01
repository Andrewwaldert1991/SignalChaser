import requests
import csv
from datetime import datetime

# API endpoint for real-time BTC price (CoinGecko)
API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# CSV file path
CSV_FILE = "btc_prices.csv"

def fetch_btc_price():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data["bitcoin"]["usd"]
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        return None

def update_csv(price):
    try:
        # Get current timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        # Open or create the CSV file and append the new row
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, price])
        print(f"Updated CSV: {timestamp}, {price}")
    except Exception as e:
        print(f"Error updating CSV: {e}")

def main():
    price = fetch_btc_price()
    if price is not None:
        update_csv(price)

if __name__ == "__main__":
    main()
