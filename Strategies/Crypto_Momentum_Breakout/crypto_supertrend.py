import backtrader as bt
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

class Supertrend(bt.Indicator):
    """
    Supertrend Indicator Implementation
    
    Technical Details:
    - Inherits from bt.Indicator for automatic data synchronization and calculation
    - Uses ATR (Average True Range) for volatility measurement
    - Generates dynamic support/resistance levels
    """
    # Define the lines (time series) that this indicator will generate
    lines = ('supertrend', 'direction')  # direction: 1=bullish, -1=bearish
    
    # Configurable parameters with default values
    params = (
        ('length', 7),       # Period for ATR calculation
        ('multiplier', 3),   # Multiplier for band width
    )

    def __init__(self):
        # Initialize parent class (required for proper line handling)
        super(Supertrend, self).__init__()
        
        # Tell Backtrader we need at least 'length' periods of data
        self.addminperiod(self.params.length)
        
        # Core indicator components
        self.atr = bt.indicators.ATR(self.data, period=self.params.length)  # Volatility measure
        
        # Calculate median price and bands
        self.hl2 = (self.data.high + self.data.low) / 2  # Median price
        # Upper and lower bands based on ATR
        self.basic_ub = self.hl2 + (self.params.multiplier * self.atr)
        self.basic_lb = self.hl2 - (self.params.multiplier * self.atr)

    def next(self):
        """
        Called for each new bar. Implements the Supertrend calculation logic.
        Index reference guide:
            [0] = current bar
            [-1] = previous bar
        """
        # Initialize for the first 'length' bars
        if len(self) <= self.params.length:
            self.lines.supertrend[0] = self.basic_ub[0]
            self.lines.direction[0] = 1
            return

        # Supertrend logic: Compare previous close with previous supertrend
        if self.data.close[-1] > self.lines.supertrend[-1]:
            # Uptrend: Use the higher of basic lower band or previous supertrend
            self.lines.supertrend[0] = max(self.basic_lb[0], self.lines.supertrend[-1])
        else:
            # Downtrend: Use the lower of basic upper band or previous supertrend
            self.lines.supertrend[0] = min(self.basic_ub[0], self.lines.supertrend[-1])

        # Determine trend direction based on close price vs supertrend
        self.lines.direction[0] = 1 if self.data.close[0] > self.lines.supertrend[0] else -1

class SupertrendStrategy(bt.Strategy):
    """
    Trading strategy that combines three technical indicators:
    1. Supertrend for trend direction
    2. EMA (Exponential Moving Average) for trend confirmation
    3. ADX (Average Directional Index) for trend strength
    """
    params = (
        ('length', 7),           # Supertrend period
        ('multiplier', 3),       # Supertrend multiplier
        ('ema_period', 50),      # EMA lookback period
        ('adx_period', 14),      # ADX lookback period
        ('adx_threshold', 20),   # Minimum ADX value for trade signals
    )

    def __init__(self):
        # Initialize technical indicators
        self.supertrend = Supertrend(
            self.data,  # Feed price data to indicator
            length=self.params.length,
            multiplier=self.params.multiplier
        )
        self.ema = bt.indicators.EMA(self.data.close, period=self.params.ema_period)
        self.adx = bt.indicators.ADX(period=self.params.adx_period)
        
        # Trade management
        self.trade_list = []     # Historical trade log
        self.trade_count = 0     # Number of trades taken
        self.current_trade = None  # Current active trade reference

    def next(self):
        """
        Main strategy logic executed on each bar
        Entry Conditions:
        - ADX above threshold (strong trend)
        - Supertrend direction aligned with EMA crossover
        """
        # Long Entry Logic
        if not self.position and self.adx[0] > self.params.adx_threshold:
            if (self.supertrend.direction[0] == 1 and  # Bullish Supertrend
                self.data.close[-1] < self.ema[-1] and  # Price was below EMA
                self.data.close[0] > self.ema[0]):      # Price crossed above EMA
                self.buy()
                self.trade_count += 1
                print(f"BUY SIGNAL at {self.data.datetime.date()} - Price: {self.data.close[0]:.2f}")
        
        # Exit Logic
        elif self.position and self.adx[0] > self.params.adx_threshold:
            if (self.supertrend.direction[0] == -1 and  # Bearish Supertrend
                self.data.close[-1] > self.ema[-1] and  # Price was above EMA
                self.data.close[0] < self.ema[0]):      # Price crossed below EMA
                self.close()
                print(f"SELL SIGNAL at {self.data.datetime.date()} - Price: {self.data.close[0]:.2f}")

    def notify_trade(self, trade):
        """Keep track of completed trades"""
        if trade.isclosed:
            self.trade_list.append({
                'entry_date': bt.num2date(trade.dtopen),
                'exit_date': bt.num2date(trade.dtclose),
                'entry_price': trade.price,
                'exit_price': trade.pnl,
                'profit_loss': trade.pnl
            })

def plot_supertrend(cerebro):
    """
    Custom visualization function that creates two plots:
    1. Default Backtrader plot with candlesticks
    2. Custom matplotlib plot with color-coded Supertrend lines
    
    Args:
        cerebro: Backtrader cerebro instance containing the executed strategy
    """
    # Generate default Backtrader plot
    cerebro.plot(style='candlestick', volume=False)
    
    # Access the executed strategy instance
    strategy = cerebro.runstrategy[0]
    
    # Initialize matplotlib figure
    plt.figure(figsize=(15, 7))  # Width: 15 inches, Height: 7 inches
    
    # Extract data from Backtrader's internal lines
    # .get(size=...) converts line objects to numpy arrays
    close_prices = strategy.data.close.get(size=len(strategy.data))
    supertrend = strategy.supertrend.supertrend.get(size=len(strategy.data))
    direction = strategy.supertrend.direction.get(size=len(strategy.data))
    
    # Convert Backtrader's numeric dates to datetime objects
    dates = strategy.data.datetime.array
    dates = [bt.num2date(d) for d in dates]  # Convert numeric dates to datetime
    
    # Plot price action
    plt.plot(dates, close_prices, label='Close Price', color='blue', alpha=0.75)
    
    # Plot Supertrend line with dynamic coloring
    # Iterate through data points to change color based on trend direction
    for i in range(1, len(dates)):
        if direction[i] == 1:  # Bullish trend
            plt.plot(dates[i-1:i+1], supertrend[i-1:i+1], color='green', linewidth=2)
        else:  # Bearish trend
            plt.plot(dates[i-1:i+1], supertrend[i-1:i+1], color='red', linewidth=2)
    
    # Configure plot aesthetics
    plt.title('Supertrend Indicator')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.xticks(rotation=45)  # Rotate date labels for better readability
    plt.grid(True)          # Add grid for easier reading
    plt.tight_layout()      # Adjust layout to prevent label clipping
    plt.show()

def main():
    """
    Main execution function that:
    1. Downloads historical data
    2. Configures and runs the backtest
    3. Displays results and plots
    
    The backtest uses:
    - DOGE-USD hourly data for the last 30 days
    - 100,000 initial capital
    - 80% position sizing
    - 0.1% commission per trade
    """
    # Data acquisition
    start_date = datetime.now() - timedelta(days=60)
    end_date = datetime.now()
    # Download hourly DOGEereum data from Yahoo Finance
    data = yf.download('DOGE-USD', start=start_date, end=end_date, interval='1h')
    
    # Initialize Backtrader's brain (cerebro)
    cerebro = bt.Cerebro()
    
    # Add strategy with optimized parameters
    cerebro.addstrategy(SupertrendStrategy,
        length=11,           # Supertrend period (longer for less noise)
        multiplier=4,        # Supertrend multiplier (higher for wider bands)
        ema_period=40,       # EMA period for trend confirmation
        adx_period=14,       # Standard ADX period
        adx_threshold=20     # Minimum trend strength requirement
    )
    
    # Prepare and add data feed
    feed = bt.feeds.PandasData(dataname=data)  # Convert pandas DataFrame to Backtrader feed
    cerebro.adddata(feed)
    
    # Configure backtest parameters
    cerebro.broker.setcash(100000.0)  # Initial capital
    # Use position sizing (80% of portfolio per trade)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=80)
    # Set realistic commission rate
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Execute and report
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()  # Execute backtest
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Store results and generate plots
    cerebro.runstrategy = results
    plot_supertrend(cerebro)

# Standard Python idiom for script execution
if __name__ == '__main__':
    main()






    
