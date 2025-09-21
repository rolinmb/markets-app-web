from consts import FVURL, HEADERS, AVURL1, AVURL2
import os
import re
import csv
import sys
import requests
from PIL import Image
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    if len(sys.argv) == 2:
        ticker = sys.argv[1].upper()
        print(f"scripts/equities.py :: Ticker {ticker} query starting...")

        fvurl = f"{FVURL}{ticker}"
        print(f"scripts/equities.py :: Requesting Finviz.com for {ticker}'s HTML content...")
        
        response = requests.get(fvurl, headers=HEADERS)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        pairs = []

        table = soup.find("table", class_="js-snapshot-table snapshot-table2 screener_snapshot-table-body")

        if table:
            for row in table.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                # cells come in [label, value, label, value, ...]
                for i in range(0, len(cells), 2):
                    label = cells[i]
                    value = cells[i+1] if i+1 < len(cells) else ""
                    pairs.append([label, value])

        spans = soup.find_all("span", class_=[
            "table-row", "w-full", "items-baseline",
            "justify-end", "whitespace-nowrap",
            "text-negative", "text-muted-2"
        ])

        if not spans:
            print(f"scripts/equities.py :: Ticker {ticker} is invalid.\n")
            sys.exit()

        dollar_change = spans[0].get_text(strip=True)
        dollar_change_clean = re.search(r"[-+]?[\d.,]+", dollar_change) # Keep only numbers, sign, decimal, and percent
        dollar_change = dollar_change_clean.group(0) if dollar_change_clean else dollar_change
        pairs.append(["$ Change", dollar_change])

        csv_path = os.path.join("data", f"{ticker}.csv")

        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Label", "Value"])
            writer.writerows(pairs)

        print(f"scripts/equities.py :: {ticker} data successfully written to {csv_path}")
        response.close()

        avurl = f"{AVURL1}{ticker}{AVURL2}"

        response = requests.get(avurl)
        data = response.json()
        time_series = data.get("Time Series (Daily)", {})

        if not time_series:
            print(f"scripts/equities.py :: No {ticker} time series data found in AlphaVantage response.\n")
            sys.exit(1)

        print(f"scripts/equities.py :: Successfully fetched time series data for {ticker}.")
        df = pd.DataFrame.from_dict(time_series, orient="index", dtype=float)

        # Columns are "1. open", "2. high", "3. low", "4. close", "5. volume"
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df["4. close"], label="Close Price")
        plt.title(f"{ticker} Daily Close Prices")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.legend()
        plt.grid(True)

        png_path = os.path.join("img", f"{ticker}.png")
        plt.savefig(png_path, dpi=150, bbox_inches="tight")
        plt.close()

        bmp_path = os.path.join("img", f"{ticker}.bmp")
        with Image.open(png_path) as png:
            png = png.resize((400, 300), Image.LANCZOS)
            png.convert("RGB").save(bmp_path, "BMP")

        if os.path.exists(png_path):
            os.remove(png_path)

        print(f"scripts/equities.py :: Saved {ticker} close price chart to {bmp_path}\n")
    else:
        print("scripts/equities.py :: No equity ticker argument provided.\n")
