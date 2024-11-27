import yfinance as yf
import backtrader as bt

# Step 1: Define the Strategy
class EMACrossStrategy(bt.Strategy):
    # Define the parameters for the EMAs
    params = (
        ('fast_ema_period', 9),
        ('slow_ema_period', 21),
    )

    def __init__(self):
        # Initialize the two EMAs
        self.fast_ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.fast_ema_period)
        self.slow_ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.slow_ema_period)
        
        # We track the crossover condition
        self.crossover = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)
    
    def next(self):
        if self.crossover > 0:  # Fast EMA crosses above Slow EMA (Buy signal)
            if not self.position:  # Check if we don't already have a position
                self.buy()
        elif self.crossover < 0:  # Fast EMA crosses below Slow EMA (Sell signal)
            if self.position:  # Check if we have a position to sell
                self.sell()

# Step 2: Set up the Backtest Environment
def run_backtest():
    # Create a Backtrader Cerebro engine
    cerebro = bt.Cerebro()

    # Step 3: Download AAPL data using yfinance
    aapl_data = yf.download('AAPL', 
                           start='2020-01-01', 
                           end='2024-01-01',
                           auto_adjust=True)
    
    # Clean up the MultiIndex structure - keep the price type, drop the ticker
    aapl_data.columns = aapl_data.columns.get_level_values(0)  # Keep the first level (Price type)
    aapl_data.columns = [col.lower() for col in aapl_data.columns]  # Convert to lowercase
    
    print("Final columns:", aapl_data.columns)  # Debug print
    
    # Create a Pandas data feed
    data = bt.feeds.PandasData(
        dataname=aapl_data,
        datetime=None,    # Use index as datetime
        open='open',      # Column name for Open
        high='high',      # Column name for High
        low='low',        # Column name for Low
        close='close',    # Column name for Close
        volume='volume',  # Column name for Volume
        openinterest=-1   # Column position for Open Interest (not available)
    )

    # Step 4: Add data to the engine
    cerebro.adddata(data)

    # Step 5: Add the strategy
    cerebro.addstrategy(EMACrossStrategy)

    # Step 6: Set the initial cash amount
    cerebro.broker.set_cash(100000)

    # Step 7: Set the commission (e.g., 0.1%)
    cerebro.broker.setcommission(commission=0.001)

    # Step 8: Set the position size to 90% of available cash
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

    # Step 9: Add analyzers for performance evaluation
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')

    # Step 10: Run the backtest and print results nicely
    print('\n====== Backtest Results ======')
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}')
    
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    # Calculate strategy returns
    strategy_returns = (final_value - 100000) / 100000 * 100
    
    # Get strategy drawdown info
    drawdown = results[0].analyzers.drawdown.get_analysis()
    
    # Calculate buy & hold returns and drawdown
    start_price = aapl_data['close'].iloc[0]  # Using iloc instead of []
    end_price = aapl_data['close'].iloc[-1]   # Using iloc instead of []
    buy_hold_returns = (end_price - start_price) / start_price * 100
    
    # Calculate buy & hold drawdown
    rolling_max = aapl_data['close'].expanding().max()
    drawdowns = (aapl_data['close'] - rolling_max) / rolling_max * 100
    max_buy_hold_drawdown = abs(drawdowns.min())
    
    print(f'\nFinal Portfolio Value: ${final_value:,.2f}')
    print(f'\nReturns Comparison:')
    print(f'  Strategy Return: {strategy_returns:.2f}%')
    print(f'  Buy & Hold Return: {buy_hold_returns:.2f}%')
    print(f'  Strategy vs Buy & Hold: {strategy_returns - buy_hold_returns:.2f}%')
    
    print(f'\nDrawdown Comparison:')
    print(f'  Strategy Max Drawdown: {drawdown.max.drawdown:.2f}%')
    print(f'  Buy & Hold Max Drawdown: {max_buy_hold_drawdown:.2f}%')
    print(f'  Drawdown Difference: {drawdown.max.drawdown - max_buy_hold_drawdown:.2f}%')
    
    # Print Sharpe Ratio
    sharpe = results[0].analyzers.sharpe.get_analysis()['sharperatio']
    print(f'\nSharpe Ratio: {sharpe:.3f}')
    
    # Print Drawdown Info
    drawdown = results[0].analyzers.drawdown.get_analysis()
    print(f'\nDrawdown:')
    print(f'  Max Drawdown: {drawdown.max.drawdown:.2f}%')
    print(f'  Longest Drawdown: {drawdown.max.len} days')
    
    # Print Trade Analysis
    trade_analysis = results[0].analyzers.trade_analysis.get_analysis()
    
    print(f'\nTrade Analysis:')
    print(f'  Total Trades: {trade_analysis.total.total}')
    print(f'  Winning Trades: {trade_analysis.won.total}')
    print(f'  Losing Trades: {trade_analysis.lost.total}')
    print(f'  Win Rate: {(trade_analysis.won.total/trade_analysis.total.total)*100:.2f}%')
    print(f'  Average Profit per Trade: ${trade_analysis.pnl.net.average:.2f}')
    print(f'  Largest Win: ${trade_analysis.won.pnl.max:.2f}')
    print(f'  Largest Loss: ${trade_analysis.lost.pnl.max:.2f}')
    print('\n============================')

    # Step 11: Plot the results
    cerebro.plot()

# Run the backtest
if __name__ == '__main__':
    run_backtest()
