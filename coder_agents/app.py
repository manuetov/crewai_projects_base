import gradio as gr
from crypto_portfolio import CryptoPortfolio

# Create an instance of the CryptoPortfolio class
portfolio_tracker = CryptoPortfolio()

# Define the coins to fetch prices for
coins = ["bitcoin", "ethereum", "solana", "cardano", "ripple"]

# Create a function to update prices and demonstrate portfolio features
def update_portfolio(holdings):
    # Convert holdings from list of lists to dictionary
    holdings_dict = {coin.lower(): float(amount) for coin, amount in holdings}
    
    # Set holdings in the portfolio
    portfolio_tracker.set_holdings(holdings_dict)
    
    # Fetch the latest prices
    portfolio_tracker.fetch_prices(coins)
    
    # Get portfolio value in USD
    total_value_usd, breakdown_usd = portfolio_tracker.get_portfolio_value(currency="usd")
    total_value_eur, _ = portfolio_tracker.get_portfolio_value(currency="eur")

    # Get risk summary
    risk_summary = portfolio_tracker.get_risk_summary()

    # Get top and worst performer
    top_performer = portfolio_tracker.get_top_performer()
    worst_performer = portfolio_tracker.get_worst_performer()

    # Prepare breakdown table
    breakdown_table = [[coin, holdings_dict.get(coin, 0), info['price_usd'], info['value_usd'], info['24h_change']] 
                       for coin, info in breakdown_usd.items()]

    # Return data for display
    return total_value_usd, total_value_eur, top_performer, worst_performer, breakdown_table, risk_summary

# Define Gradio interface
def main():
    holdings_input = gr.inputs.Dataframe(headers=["Coin", "Amount"],
                                         datatype=["str", "number"],
                                         row_count=(5, "dynamic"))
    
    total_value_usd_display = gr.outputs.Textbox(label="Total Portfolio Value in USD")
    total_value_eur_display = gr.outputs.Textbox(label="Total Portfolio Value in EUR")

    top_performer_display = gr.outputs.Textbox(label="Top Performer (24h)")
    worst_performer_display = gr.outputs.Textbox(label="Worst Performer (24h)")

    breakdown_display = gr.outputs.Dataframe(headers=["Coin", "Amount", "Price USD", "Value USD", "24h Change %"])
    risk_summary_display = gr.outputs.Textbox(label="Risk Summary")

    interface = gr.Interface(
        fn=update_portfolio,
        inputs=[holdings_input],
        outputs=[total_value_usd_display, total_value_eur_display, top_performer_display,
                 worst_performer_display, breakdown_display, risk_summary_display],
        title="Crypto Portfolio Tracker",
        description="Monitor and manage your cryptocurrency portfolio in real time."
    )

    interface.launch()

if __name__ == "__main__":
    main()
