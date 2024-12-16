import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os

def read_crypto_list():
    """Read crypto list from CSV"""
    try:
        df = pd.read_csv('top_crypto_list.csv')
        return dict(zip(df['symbol'], df['name']))
    except Exception as e:
        print(f"Error reading crypto list: {e}")
        return {}

def fetch_data(symbol: str, period: str = "2mo", interval: str = "1h"):
    """Fetch data using yfinance with basic validation"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"No data returned for {symbol}")
            return None
            
        # Basic volume filter
        recent_volume = df['Volume'].iloc[-24:].mean() * df['Close'].iloc[-1]  # Last 24h avg volume in USD
        if recent_volume < 50000:  # $50k minimum recent volume
            print(f"Insufficient volume for {symbol}: ${recent_volume:,.0f}")
            return None
            
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def get_coin_logo(symbol: str) -> str:
    """Get coin logo URL from CoinGecko"""
    try:
        clean_symbol = symbol.split('-')[0]  # Remove -USD
        response = requests.get(f"https://api.coingecko.com/api/v3/search?query={clean_symbol}")
        data = response.json()
        if data['coins']:
            return data['coins'][0]['large']
    except:
        pass
    return "https://cdn.discordapp.com/embed/avatars/0.png"

def analyze_timeframes(trading_pairs):
    timeframe_messages = []
    
    timeframes = {
        '6h': 6,
        '1d': 24,
        '1w': 168,   # 7 * 24
        '2w': 336,   # 14 * 24
        '1mo': 720,  # 30 * 24
        '2mo': 1440  # 60 * 24
    }
    
    all_data = []
    for symbol, name in trading_pairs.items():
        print(f"Analyzing {symbol}...")
        
        df = fetch_data(symbol, period="3mo", interval="1h")
        
        if df is not None and not df.empty:
            current_price = df['Close'].iloc[-1]
            volume_24h = df['Volume'].iloc[-24:].mean() * current_price  # 24h average volume in USD
            
            # Calculate returns for each timeframe
            returns = {}
            for timeframe, hours in timeframes.items():
                if len(df) >= hours:  # Make sure we have enough data
                    past_price = df['Close'].iloc[-hours]
                    ret = ((current_price - past_price) / past_price) * 100
                    returns[timeframe] = ret
                else:
                    print(f"Insufficient data for {symbol} {timeframe} ({len(df)} < {hours} hours)")
                    returns[timeframe] = 0
            
            print(f"Debug - {symbol}: Price {current_price:.8f}, Volume ${volume_24h:,.0f}")
            for tf, ret in returns.items():
                print(f"{tf}: {ret:.2f}%")
            
            all_data.append({
                'symbol': symbol,
                'name': name,
                'price': current_price,
                'volume': volume_24h,
                'logo': get_coin_logo(symbol),
                **returns
            })
    
    # Create Discord embeds for each timeframe
    for timeframe in timeframes.keys():
        # Sort by return for this timeframe
        top_10 = sorted(all_data, key=lambda x: x[timeframe], reverse=True)[:10]
        
        embed = {
            "title": f"🏆 Top 10 Performers - {timeframe}",
            "color": 3066993,
            "fields": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for coin in top_10:
            embed["fields"].append({
                "name": f"{coin['name']} ({coin['symbol']})",
                "value": f"Return: {coin[timeframe]:.2f}%\nPrice: ${coin['price']:.8f}\nVolume: ${coin['volume']:,.0f}",
                "inline": True
            })
        
        timeframe_messages.append({"embeds": [embed]})
    
    return timeframe_messages

if __name__ == "__main__":
    print("\nReading crypto list from CSV...")
    trading_pairs = read_crypto_list()
    
    WEBHOOK_URL = os.getenv("DISCORD_CRYPTO_MOVERS_WEBHOOK")
    
    if trading_pairs and WEBHOOK_URL:
        print("Analyzing timeframe returns...")
        messages = analyze_timeframes(trading_pairs)
        
        print("Sending messages to Discord...")
        for message in messages:
            requests.post(WEBHOOK_URL, json=message)
            time.sleep(1)  # Rate limiting
        
        print("Analysis complete")
    else:
        print("Error: Missing trading pairs or webhook URL")
