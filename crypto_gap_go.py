import requests
import pandas as pd
from datetime import datetime, timedelta
import backtrader as bt


# Tiingo API configuration
TIINGO_API_KEY = "ABC"
BASE_URL = "https://api.tiingo.com/tiingo/crypto"

# Define crypto pairs to fetch
crypto_pairs = ["btcusd", "ethusd", "adausd", "xrpusd", "ltcusd"]  # Add more as needed
start_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

# Function to fetch data
def fetch_crypto_data(pair, start_date, end_date):
    params = {
        "tickers": pair,
        "startDate": start_date,
        "endDate": end_date,
        "resampleFreq": "1hour",  # Adjust as needed (e.g., "5min", "1day")
        "token": TIINGO_API_KEY,
    }
    response = requests.get(f"{BASE_URL}/prices", params=params)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            # Extract the price data from the response
            df = pd.DataFrame(data[0]['priceData'])
            # Rename columns to match backtrader requirements
            df.rename(columns={
                "date": "datetime",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume"
            }, inplace=True)
            # Convert datetime and set as index
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            return df
    else:
        print(f"Failed to fetch data for {pair}: {response.text}")
        return pd.DataFrame()

# Fetch data for all pairs
crypto_data = {pair: fetch_crypto_data(pair, start_date, end_date) for pair in crypto_pairs}
print(crypto_data)  

def analyze_price_movements(crypto_data):
    for pair, df in crypto_data.items():
        if not df.empty:
            # Calculate percentage change between consecutive closes
            df['pct_change'] = df['close'].pct_change() * 100
            
            # Find instances where price change exceeded threshold
            threshold = 5.0  # 5%
            large_moves = df[abs(df['pct_change']) >= threshold]
            
            if not large_moves.empty:
                print(f"\nAnalysis for {pair}:")
                print(f"Total number of {threshold}% or larger moves: {len(large_moves)}")
                print("\nLargest price movements:")
                
                # Create a more detailed analysis DataFrame
                analysis_df = pd.DataFrame({
                    'Current_Close': df['close'],
                    'Previous_Close': df['close'].shift(1),
                    'Pct_Change': df['pct_change']
                })
                
                # Filter for large moves and sort
                large_moves_detailed = analysis_df[abs(analysis_df['Pct_Change']) >= threshold]
                largest_moves = large_moves_detailed.nlargest(5, 'Pct_Change')
                
                # Print detailed information
                for idx, row in largest_moves.iterrows():
                    print(f"""
                    Date: {idx}
                    Change: {row['Pct_Change']:.2f}%
                    Current Price: {row['Current_Close']:.2f}
                    Previous Price: {row['Previous_Close']:.2f}
                    """)
                
                # Print distribution of moves
                print("\nDistribution of large moves:")
                move_ranges = [(5,10), (10,15), (15,20), (20,float('inf'))]
                for low, high in move_ranges:
                    count = len(df[abs(df['pct_change']).between(low, high)])
                    print(f"{low}% to {high}%: {count} instances")
                
            else:
                print(f"\nNo moves >= {threshold}% found for {pair}")
                
            # Print some general statistics
            print(f"\nGeneral statistics for {pair}:")
            print(f"Mean absolute change: {abs(df['pct_change']).mean():.2f}%")
            print(f"Max absolute change: {abs(df['pct_change']).max():.2f}%")
            print(f"Number of >1% moves: {len(df[abs(df['pct_change']) > 1])}")
            print(f"Number of >2% moves: {len(df[abs(df['pct_change']) > 2])}")
            print(f"Number of >3% moves: {len(df[abs(df['pct_change']) > 3])}")
            print(f"Number of >4% moves: {len(df[abs(df['pct_change']) > 4])}")
            print(f"Number of >5% moves: {len(df[abs(df['pct_change']) > 5])}")

# Add this debugging section to check the actual gap calculations
def debug_strategy_conditions(crypto_data):
    print("\nDebugging Strategy Entry Conditions:")
    for pair, df in crypto_data.items():
        if not df.empty:
            # Calculate the same gap as in the strategy
            df['gap'] = (df['close'] - df['close'].shift(1)) / df['close'].shift(1)
            
            # Find potential entry points
            entries = df[df['gap'] >= 0.05]  # 5% threshold
            
            print(f"\n{pair} potential entry points: {len(entries)}")
            if len(entries) > 0:
                print("\nTop 5 potential entries:")
                for idx, row in entries.nlargest(5, 'gap').iterrows():
                    print(f"""
                    Time: {idx}
                    Gap: {row['gap']*100:.2f}%
                    Current Price: {row['close']:.2f}
                    Previous Price: {df['close'][df.index.get_loc(idx)-1]:.2f}
                    """)

# Run both analyses
print("\nAnalyzing price movements...")
analyze_price_movements(crypto_data)

print("\nDebugging strategy entry conditions...")
debug_strategy_conditions(crypto_data)


class GapATRStrategy(bt.Strategy):
    params = (
        ("gap_threshold", 0.05),  # 5% price jump
        ("atr_period", 14),      # ATR lookback period
        ("atr_multiplier", 3),   # Multiplier for stop-loss
        ("risk_percentage", 0.8)  # Percentage of available cash to invest
    )

    def __init__(self):
        # Create ATR and tracking dictionaries for each data feed
        self.atrs = {}
        self.entry_prices = {}
        self.stop_losses = {}
        self.active_trades = {}  # Changed from self.positions
        
        # Initialize indicators for each data feed
        for i, d in enumerate(self.datas):
            self.atrs[d._name] = bt.indicators.AverageTrueRange(d, period=self.params.atr_period)
            self.entry_prices[d._name] = None
            self.stop_losses[d._name] = None
            self.active_trades[d._name] = False  # Track if we have an active trade
            print(f'Initialized strategy for {d._name}')

    def next(self):
        # Debug information
        print(f"\nCurrent datetime: {self.datas[0].datetime.datetime(0)}")
        print(f"Available cash: ${self.broker.getcash():.2f}")
        
        # Iterate through each data feed
        for i, d in enumerate(self.datas):
            pos = self.getposition(d)
            
            # Print current price and position info
            print(f"\n{d._name}:")
            print(f"Current price: ${d.close[0]:.2f}")
            print(f"Position size: {pos.size if pos else 0}")
            
            # Check for entry conditions if no position
            if not pos:
                if len(d) > 1:  # Make sure we have at least 2 bars
                    gap = (d.close[0] - d.close[-1]) / d.close[-1]
                    print(f"Gap: {gap*100:.2f}%")
                    
                    if gap >= self.params.gap_threshold:
                        # Calculate position size based on available cash
                        available_cash = self.broker.getcash()
                        target_value = available_cash * self.params.risk_percentage
                        size = target_value / d.close[0]
                        
                        self.entry_prices[d._name] = d.close[0]
                        self.stop_losses[d._name] = d.close[0] - (self.atrs[d._name][0] * self.params.atr_multiplier)
                        
                        # Place the order
                        self.buy(data=d, size=size)
                        self.active_trades[d._name] = True
                        
                        print(f'''
                        BUY EXECUTED for {d._name}:
                        Price: {d.close[0]:.2f}
                        Size: {size:.6f} units
                        Amount: ${target_value:.2f}
                        Gap: {gap*100:.2f}%
                        Stop Loss: {self.stop_losses[d._name]:.2f}
                        ''')
            
            # Update stop loss for existing position
            elif pos:
                # Update trailing stop
                self.stop_losses[d._name] = max(
                    self.stop_losses[d._name],
                    d.close[0] - (self.atrs[d._name][0] * self.params.atr_multiplier)
                )
                
                print(f"Current stop loss: ${self.stop_losses[d._name]:.2f}")
                
                # Check if stop loss is hit
                if d.close[0] < self.stop_losses[d._name]:
                    self.close(data=d)
                    self.active_trades[d._name] = False
                    print(f'''
                    SELL EXECUTED for {d._name}:
                    Price: {d.close[0]:.2f}
                    Stop Loss: {self.stop_losses[d._name]:.2f}
                    ''')

# Convert Tiingo data to BackTrader feed
def convert_to_bt_feed(dataframe):
    # Add openinterest column (required by BackTrader)
    dataframe['openinterest'] = 0
    
    # Select only the columns needed by BackTrader
    bt_data = dataframe[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    
    return bt.feeds.PandasData(dataname=bt_data)

# Initialize Cerebro with some basic settings
cerebro = bt.Cerebro()
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

# Add data feeds
for pair, data in crypto_data.items():
    if not data.empty:
        print(f"Adding data for {pair}")
        bt_feed = convert_to_bt_feed(data)
        cerebro.adddata(bt_feed, name=pair)

# Add strategy
cerebro.addstrategy(GapATRStrategy)

# Add analyzers

cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

# Print starting portfolio value
print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

# Run backtest
results = cerebro.run()

# Print final results
strat = results[0]
print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
print(f'Max Drawdown: {strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
print(f'Total Return: {strat.analyzers.returns.get_analysis()["rtot"]:.2f}%')

# Plot results
cerebro.plot(style='candlestick', volume=True)


