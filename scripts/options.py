from util import *
from consts import TRADINGDAYS, OPTIONSURL1, OPTIONSURL2, OPTIONSURL3, OPTIONSURL4
import os
import sys
import csv
import time
import requests
import numpy as np
from PIL import Image
from datetime import datetime
from selenium import webdriver
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("scripts/options.py :: Usage: python scripts/options.py <TICKER>")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    url = f"{OPTIONSURL1}{ticker}{OPTIONSURL2}"
    driver.get(url)
    print(f"scripts/options.py :: Successfully fetched html data from {url}")
    driver.implicitly_wait(5)

    try:
        button = driver.find_element(By.ID, "expiration-dates-form-button-1")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        wait = WebDriverWait(driver, 1)
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "label.tw-ml-3.tw-min-w-0.tw-flex-1.tw-text-gray-600")
            )
        )
    except Exception as e:
        print(f"scripts/options.py :: Error clicking expiration button or waiting for labels: {e}")
        driver.quit()
        sys.exit(1)

    spans = driver.find_elements(By.CSS_SELECTOR, ".tw-text-3xl.tw-font-semibold")
    price_string = spans[1].text.strip()
    print(f"scripts/options.py :: Scraped Underlying Price: {price_string}")
    
    labels = driver.find_elements(
        By.CSS_SELECTOR, "label.tw-ml-3.tw-min-w-0.tw-flex-1.tw-text-gray-600"
    )
    expirations_text = [lbl.text for lbl in labels if lbl.text.strip()]
    formatted_expiration_dates = []
    exp_in_years = []
    for text in expirations_text:
        date_str = text.split("(")[0].strip()
        exp_dt = datetime.strptime(date_str, "%b %d, %Y")
        final_dt = exp_dt.strftime("%Y-%m-%d")
        formatted_expiration_dates.append(final_dt)

        days_part = text.split("(")[1].split()[0]
        days = int(days_part)
        years = days / TRADINGDAYS
        exp_in_years.append(years)
        if len(formatted_expiration_dates) != len(exp_in_years):
            print(f"scripts/options.py :: len(formatted_expiration_dates) != len(exp_in_years)")
            sys.exit(1)
    
    print(f"scripts/options.py :: Successfully parsed expiration dates and calculated yte for each expiry/contract")
    time.sleep(1.0)
    expiries = []
    for i in range(0, len(exp_in_years)):
        url = f"{OPTIONSURL3}{formatted_expiration_dates[i]}{OPTIONSURL4}"
        driver.get(url)
        time.sleep(1.0)
        calls = []
        puts = []
        table = driver.find_element(By.CSS_SELECTOR, "table.table.table-sm.table-hover")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
        for row in rows:
            cbid = cask = cvol = c_oi = strike = 0
            pbid = pask = pvol = p_oi = 0
            cols = [c.text.strip() for c in row.find_elements(By.TAG_NAME, "td")]
            if len(cols) != 11:
                continue
            clast = cols[0] if cols[0] != "-" else "0.00"
            cbid = cols[1]
            cask = cols[2]
            cvol = cols[3]
            c_oi = cols[4]
            strike = cols[5]
            plast = cols[6] if cols[6] != "-" else "0.00"
            pbid = cols[7]
            pask = cols[8]
            pvol = cols[9]
            p_oi = cols[10]
            c = OptionContract(ticker, strike, price_string, exp_in_years[i], clast, cbid, cask, cvol, c_oi, True)
            p = OptionContract(ticker, strike, price_string, exp_in_years[i], plast, pbid, pask, pvol, p_oi, False)
            calls.append(c)
            puts.append(p)
        print(f"scripts/options.py :: Processed Calls and Puts for expiration {formatted_expiration_dates[i]}")
        expiries.append(OptionExpiry(ticker, formatted_expiration_dates[i], exp_in_years[i], calls, puts))
    
    option_chain = OptionChain(ticker, expiries)
    csv_filename = f"data/{ticker}chain.csv"
    with open(csv_filename, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "expiry", "underlying", "underlying_price", "strike", "call_or_put",
            "last", "bid", "ask", "volume", "open_interest", "yte"
        ])

        for expiry in option_chain.expiries:
            for c in expiry.calls:
                writer.writerow([
                    expiry.date, c.underlying, c.underlying_price, c.strike, "Call",
                    c.midprice, c.bidprice, c.askprice, c.volume, c.openinterest, f"{c.yte:.2f}"
                ])
            for p in expiry.puts:
                writer.writerow([
                    expiry.date, p.underlying, p.underlying_price, p.strike, "Put",
                    p.midprice, p.bidprice, p.askprice, p.volume, p.openinterest, f"{p.yte:.2f}"
                ])

    print(f"scripts/options.py :: Saved {ticker} Option Chain to {csv_filename}")
    #TODO: Plot iv surface for the cpp windows app to show
    strikes = []
    ytes = []
    ivs = []

    for expiry in option_chain.expiries:
        for c in expiry.calls:  # you could also add puts if desired
            strikes.append(c.strike)
            ytes.append(c.yte)
            ivs.append(c.iv)

    # Convert to numpy arrays
    strikes = np.array(strikes)
    ytes = np.array(ytes)
    ivs = np.array(ivs)

    # Create 3D scatter plot
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(strikes, ytes, ivs, c=ivs, cmap="viridis")
    ax.set_xlabel("Strike Price")
    ax.set_ylabel("Years to Expiration (YTE)")
    ax.set_zlabel("Implied Volatility")
    ax.set_title(f"IV Surface for {ticker}")
    fig.colorbar(sc, ax=ax, label="IV")

    png_path = os.path.join("img", f"{ticker}civ.png")
    bmp_path = os.path.join("img", f"{ticker}civ.bmp")

    plt.savefig(png_path, dpi=150)
    plt.close()

    print("scripts/options.py :: PNG iv surface chart saved to", png_path)

    with Image.open(png_path) as png:
        png = png.resize((400,300), Image.LANCZOS)
        png.convert("RGB").save(bmp_path, "BMP")

    # Clean up
    try:
        os.remove(png_path)
        print(f"scripts/options.py :: Deleted temporary PNG: {png_path}\n")
    except:
        pass
