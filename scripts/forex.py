from consts import FXURL1, FXURL2, HEADERS, AVURL2, AVURL5, AVURL6
import os
import re
import csv
import sys
import requests
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

if __name__ == "__main__":
    if len(sys.argv) == 2:
        fromcurrency = sys.argv[1][0:3].lower()
        tocurrency = sys.argv[1][3:].lower()

        print(f"scripts/forex.py :: {fromcurrency}/{tocurrency} query starting...")

        fxurl = FXURL1+fromcurrency+tocurrency+FXURL2
        print(f"scripts/forex.py :: Requesting finance.yahoo.com for {fromcurrency}/{tocurrency}'s HTML content...")

        response = requests.get(fxurl, headers=HEADERS)

        soup = BeautifulSoup(response.text, "html.parser")
        
        price_span = soup.find("span", class_="yf-ipw1h0 base")
        price = price_span.text if price_span else "--"

        dollar_span = soup.find("span", attrs={"data-testid": "qsp-price-change"})
        dollarchange = dollar_span.text if dollar_span else "--"

        percentchange = "--"
        if dollar_span:
            sibling = dollar_span.find_next("span")
            if sibling:
                percentchange = sibling.text

        percentchange = re.sub(r"[()]", "", percentchange)  

        pairs = [
            ["Symbol", f"{fromcurrency}{tocurrency}"], ["Price", price],
            ["Change", percentchange], ["$ Change", dollarchange]
        ]

        csv_path = os.path.join("data", f"{fromcurrency}{tocurrency}.csv")

        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Label", "Value"])
            writer.writerows(pairs)

        print(f"scripts/forex.py :: {fromcurrency}{tocurrency} data successfully written to {csv_path}")
        response.close()

        avurl = f"{AVURL5}{fromcurrency}{AVURL6}{tocurrency}{AVURL2}"

        response = requests.get(avurl)
        data = response.json()
        time_series = data.get("Time Series FX (Daily)", {})

        if not time_series:
            print(f"scripts/forex.py :: No {fromcurrency}{tocurrency} time series data found in AlphaVantage response.\n")
            sys.exit(1)

        print(f"scripts/forex.py :: Successfully fetched time series data for {fromcurrency}{tocurrency}.")
        df = pd.DataFrame.from_dict(time_series, orient="index", dtype=float)

        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df["4. close"], label="Close Price")
        plt.title(f"{fromcurrency}/{tocurrency} Daily Close Price")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.legend()
        plt.grid(True)

        png_path = os.path.join("img", f"{fromcurrency}{tocurrency}.png")
        plt.savefig(png_path, dpi=150, bbox_inches="tight")
        plt.close()

        bmp_path = os.path.join("img", f"{fromcurrency}{tocurrency}.bmp")
        with Image.open(png_path) as png:
            png = png.resize((400, 300), Image.LANCZOS)
            png.convert("RGB").save(bmp_path, "BMP")

        if os.path.exists(png_path):
            os.remove(png_path)

        print(f"scripts/forex.py :: Saved {fromcurrency}/{tocurrency} close price chart to {bmp_path}\n")
    else:
        print(f"scripts/forex.py :: No exchange rate cross argument provided.\n")