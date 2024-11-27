import pandas as pd
from datetime import datetime, timedelta
import backtrader as bt
import yfinance as yf
import matplotlib.pyplot as plt
import logging

# Set up logging configuration
log_filename = f'crypto_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define crypto pairs to fetch 
crypto_pairs = ["BTC-USD", "ETH-USD", "ADA-USD", "XRP-USD", "LTC-USD"]
start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")

# Define function to fetch crypto data
def fetch_crypto_data(symbol, start_date, end_date):
    logging.info(f"Fetching data for symbol: {symbol}")  
    try:
        # Fetch data from Yahoo Finance
        df = yf.download(symbol, 
                        start=start_date, 
                        end=end_date, 
                        interval='1h')
        
        if not df.empty:
            df.index = pd.to_datetime(df.index)
            return df
        else:
            logging.info(f"No data returned for {symbol}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Failed to fetch data for {symbol}: {str(e)}")
        return pd.DataFrame()

# Fetch data for all pairs
crypto_data = {pair: fetch_crypto_data(pair, start_date, end_date) for pair in crypto_pairs}
logging.info(crypto_data)  

def analyze_price_movements(crypto_data):
    logging.info("Starting price movement analysis")
    
    for pair, df in crypto_data.items():
        if not df.empty:
            # Get the Close price column 
            close_prices = df['Close'][pair]
            
            # Calculate percentage change between consecutive closes
            df['pct_change'] = close_prices.pct_change() * 100
            
            # Find instances where price change exceeded threshold
            threshold = 2.0  # 2%
            large_moves = df[abs(df['pct_change']) >= threshold]
            
            if not large_moves.empty:
                # Create a more detailed analysis DataFrame
                analysis_df = pd.DataFrame({
                    'Current_Close': close_prices,
                    'Previous_Close': close_prices.shift(1),
                    'Pct_Change': df['pct_change']
                })
                
                # Filter for large moves and sort
                large_moves_detailed = analysis_df[abs(analysis_df['Pct_Change']) >= threshold]
                largest_moves = large_moves_detailed.nlargest(5, 'Pct_Change')
                
                # Log detailed information
                for idx, row in largest_moves.iterrows():
                    logging.info(f"""
                    Date: {idx}
                    Change: {row['Pct_Change']:.2f}%
                    Current Price: {row['Current_Close']:.2f}
                    Previous Price: {row['Previous_Close']:.2f}
                    """)
                
                # Log distribution of moves
                logging.info("\nDistribution of large moves:")
                move_ranges = [(5,10), (10,15), (15,20), (20,float('inf'))]
                for low, high in move_ranges:
                    count = len(df[abs(df['pct_change']).between(low, high)])
                    logging.info(f"{low}% to {high}%: {count} instances")
                
            else:
                logging.info(f"\nNo moves >= {threshold}% found for {pair}")
                
            # Log general statistics instead of printing
            logging.info(f"\nGeneral statistics for {pair}:")
            logging.info(f"Mean absolute change: {abs(df['pct_change']).mean():.2f}%")
            logging.info(f"Max absolute change: {abs(df['pct_change']).max():.2f}%")
            logging.info(f"Number of >1% moves: {len(df[abs(df['pct_change']) > 1])}")
            logging.info(f"Number of >2% moves: {len(df[abs(df['pct_change']) > 2])}")
            logging.info(f"Number of >3% moves: {len(df[abs(df['pct_change']) > 3])}")
            logging.info(f"Number of >4% moves: {len(df[abs(df['pct_change']) > 4])}")
            logging.info(f"Number of >5% moves: {len(df[abs(df['pct_change']) > 5])}")
            
            # Add some summary statistics
            logging.info("\nDistribution of moves:")
            move_ranges = [(1,2), (2,3), (3,4), (4,5), (5,float('inf'))]
            for low, high in move_ranges:
                count = len(df[abs(df['pct_change']).between(low, high)])
                total = len(df)
                percentage = (count/total)*100 if total > 0 else 0
                logging.info(f"{low}% to {high}%: {count} instances ({percentage:.1f}% of total)")
            
            logging.info("\n" + "="*50 + "\n")  # Add separator between coins

# logging summary statistics 
def log_summary(crypto_data):
    logging.info("\nANALYSIS SUMMARY")
    logging.info("=" * 30)
    for pair, df in crypto_data.items():
        if not df.empty:
            avg_change = abs(df['pct_change']).mean()
            max_change = abs(df['pct_change']).max()
            total_moves = len(df[abs(df['pct_change']) > 5])
            logging.info(f"{pair}:")
            logging.info(f"  Average Move: {avg_change:.2f}%")
            logging.info(f"  Max Move: {max_change:.2f}%")
            logging.info(f"  Total >5% Moves: {total_moves}")
    logging.info("=" * 30)

# Add this debugging section to check the actual gap calculations
def debug_strategy_conditions(crypto_data):
    logging.info("\nDebugging Strategy Entry Conditions:")
    for pair, df in crypto_data.items():
        if not df.empty:
            # Calculate the same gap as in the strategy
            df['gap'] = (df['Close'][pair] - df['Close'][pair].shift(1)) / df['Close'][pair].shift(1)
            # Example:
            # Current Close: 50000
            # Previous Close (shift(1)): 48000
            # Gap = (50000 - 48000) / 48000 = 0.0416 (4.16%)
            
            # Find potential entry points
            entries = df[df['gap'] >= 0.02]  # 2% threshold
            
            logging.info(f"\n{pair} potential entry points: {len(entries)}")
            if len(entries) > 0:
                logging.info("\nTop 5 potential entries:")
                for idx, row in entries.nlargest(5, 'gap').iterrows():
                    # Get previous index using iloc
                    prev_idx = df.index[df.index.get_loc(idx) - 1]
                    logging.info(f"""
                    Time: {idx}
                    Gap: {row['gap'].iloc[0]*100:.2f}%
                    Current Price: {row['Close'][pair]:.2f}
                    Previous Price: {df['Close'][pair].loc[prev_idx]:.2f}
                    """)

# Run both analyses
logging.info("\nAnalyzing price movements...")
analyze_price_movements(crypto_data)
log_summary(crypto_data)

logging.info("\nDebugging strategy entry conditions...")
debug_strategy_conditions(crypto_data)


class GapATRStrategy(bt.Strategy):
    params = (
        ("gap_threshold", 0.02),     # 2% price jump
        ("atr_period", 14),          # ATR lookback period
        ("atr_multiplier", 3),       # Multiplier for stop-loss
        ("max_allocation", 0.15)     # Maximum 15% allocation per coin
    )

    def __init__(self):
        # Create ATR and tracking dictionaries for each data feed
        self.atrs = {} # ATR for each coin
        self.entry_prices = {} # Entry price for each coin
        self.stop_losses = {} # Stop loss for each coin
        self.active_trades = {} # Active trade status for each coin
        self.allocations = {}  # Track allocation for each coin
        
        # Store initial portfolio value for allocation calculations
        self.initial_portfolio = self.broker.getvalue()
        
        # Initialize indicators and tracking for each data feed
        for i, d in enumerate(self.datas):
            self.atrs[d._name] = bt.indicators.AverageTrueRange(d, period=self.params.atr_period)
            self.entry_prices[d._name] = None # Entry price for each coin
            self.stop_losses[d._name] = None # Stop loss for each coin
            self.active_trades[d._name] = False # Active trade status for each coin
            self.allocations[d._name] = 0.0  # Track allocation percentage
            logging.info(f'Initialized strategy for {d._name}')

    def next(self):
        current_portfolio = self.broker.getvalue()
        logging.info(f"\nCurrent datetime: {self.datas[0].datetime.datetime(0)}")
        logging.info(f"Portfolio value: ${current_portfolio:.2f}")
        logging.info(f"Available cash: ${self.broker.getcash():.2f}")
        
        # Iterate through each data feed independently
        for i, d in enumerate(self.datas):
            pos = self.getposition(d)
            current_allocation = (pos.size * d.close[0] / current_portfolio) if pos else 0
            self.allocations[d._name] = current_allocation
            
            # Log current price and position info
            logging.info(f"\n{d._name}:")
            logging.info(f"Current price: ${d.close[0]:.2f}")
            logging.info(f"Position size: {pos.size if pos else 0}")
            logging.info(f"Current allocation: {current_allocation*100:.2f}%")
            
            # Check for entry conditions if no position
            if not pos:
                if len(d) > 1:  # Make sure we have at least 2 bars
                    gap = (d.close[0] - d.close[-1]) / d.close[-1]
                    logging.info(f"Gap: {gap*100:.2f}%")
                    
                    if gap >= self.params.gap_threshold:
                        # Calculate position size based on maximum allocation
                        max_investment = current_portfolio * self.params.max_allocation # Maximum investment per coin
                        available_cash = self.broker.getcash() # Available cash in portfolio
                        target_value = min(max_investment, available_cash) # Target value for investment
                        size = target_value / d.close[0] # Position size
                        
                        self.entry_prices[d._name] = d.close[0] # Entry price
                        self.stop_losses[d._name] = d.close[0] - (self.atrs[d._name][0] * self.params.atr_multiplier) # Stop loss
                        
                        # Place the order
                        self.buy(data=d, size=size)
                        self.active_trades[d._name] = True
                        
                        logging.info(f'''
                        BUY EXECUTED for {d._name}:
                        Price: {d.close[0]:.2f}
                        Size: {size:.6f} units
                        Amount: ${target_value:.2f}
                        Allocation: {(target_value/current_portfolio)*100:.2f}%
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
                
                logging.info(f"Current stop loss: ${self.stop_losses[d._name]:.2f}")
                
                # Check if stop loss is hit
                if d.close[0] < self.stop_losses[d._name]:
                    self.close(data=d)
                    self.active_trades[d._name] = False
                    self.allocations[d._name] = 0.0
                    logging.info(f'''
                    SELL EXECUTED for {d._name}:
                    Price: {d.close[0]:.2f}
                    Stop Loss: {self.stop_losses[d._name]:.2f}
                    ''')

# Convert Yfinance data to BackTrader feed
def convert_to_bt_feed(dataframe):
    # Add openinterest column (required by BackTrader)
    dataframe['OpenInterest'] = 0
    
    # Reset the multi-index structure and select the required columns
    # First, get the symbol from the columns multi-index
    symbol = dataframe.columns.get_level_values(1)[0]
    
    # Create a new DataFrame with flattened columns
    bt_data = pd.DataFrame({
        'Open': dataframe['Open'][symbol],
        'High': dataframe['High'][symbol],
        'Low': dataframe['Low'][symbol],
        'Close': dataframe['Close'][symbol],
        'Volume': dataframe['Volume'][symbol],
        'OpenInterest': dataframe['OpenInterest']
    })
    
    # Convert to BackTrader feed
    return bt.feeds.PandasData(
        dataname=bt_data,
        open='Open',
        high='High',
        low='Low',
        close='Close',
        volume='Volume',
        openinterest='OpenInterest'
    )

# Initialize Cerebro with some basic settings
cerebro = bt.Cerebro()
cerebro.broker.setcash(10000000.0)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

# Function to run backtest and plot for a single pair
def run_and_plot_single(pair, data):
    cerebro_single = bt.Cerebro()
    cerebro_single.broker.setcash(10000000.0)
    cerebro_single.broker.setcommission(commission=0.001)
    
    bt_feed = convert_to_bt_feed(data)
    cerebro_single.adddata(bt_feed, name=pair)
    cerebro_single.addstrategy(GapATRStrategy)
    
    cerebro_single.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro_single.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    results = cerebro_single.run()
    
    # Plot single pair
    fig = cerebro_single.plot(style='candlestick', volume=True, title=f"{pair} Analysis")[0][0]
    fig.savefig(f"{pair}_plot.png")
    plt.close(fig)
    
    return results[0]

# Run individual backtests and generate plots
individual_results = {}
for pair, data in crypto_data.items():
    if not data.empty:
        logging.info(f"Running backtest for {pair}")
        individual_results[pair] = run_and_plot_single(pair, data)
        logging.info(f"Plot saved as {pair}_plot.png")

# Add data feeds to main Cerebro instance
for pair, data in crypto_data.items():
    if not data.empty:
        logging.info(f"Adding data for {pair} to main Cerebro instance")
        bt_feed = convert_to_bt_feed(data)
        cerebro.adddata(bt_feed, name=pair)

# Add strategy to main Cerebro instance
cerebro.addstrategy(GapATRStrategy)

# Add analyzers to main Cerebro instance
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

# Print starting portfolio value
logging.info(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

# Run main backtest
results = cerebro.run()

# Print final results for main backtest
strat = results[0]
logging.info(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
logging.info(f'Max Drawdown: {strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
logging.info(f'Total Return: {strat.analyzers.returns.get_analysis()["rtot"]:.2f}%')

# Print individual results
for pair, result in individual_results.items():
    logging.info(f"\nResults for {pair}:")
    logging.info(f'Max Drawdown: {result.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
    logging.info(f'Total Return: {result.analyzers.returns.get_analysis()["rtot"]:.2f}%')

# Plot combined results
cerebro.plot(style='candlestick', volume=True, title="Combined Analysis")


