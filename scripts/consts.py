from keys import AVKEY

TRADINGDAYS = 252
FEDFUNDS = 0.0408
FVURL = "https://finviz.com/quote.ashx?t="
CMCURL = "https://coinmarketcap.com/currencies/"
FXURL1 = "https://finance.yahoo.com/quote/"
FXURL2 = "=X/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://finviz.com/"
}
AVURL1 = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol="
AVURL2 = f"&apikey={AVKEY}"
AVURL3 = "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol="
AVURL4 = "&market=USD"
AVURL5 = "https://www.alphavantage.co/query?function=FX_DAILY&from_symbol="
AVURL6 = "&to_symbol="
BONDURL = "https://www.bloomberg.com/markets/rates-bonds/government-bonds/us"
OPTIONSURL1 = "https://optioncharts.io/options/"
OPTIONSURL2 = "/option-chain"
OPTIONSURL3 = "https://optioncharts.io/options/SPY/option-chain?option_type=all&expiration_dates="
OPTIONSURL4 = ":w&view=straddle&strike_range=all"