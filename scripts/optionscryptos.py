from consts import TRADINGDAYS, OPTIONSURL5, OPTIONSURL6
from util import sanitize_cell
import re
import csv
import sys
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("scripts/optionscryptos.py :: Usage: python optionscryptos.py <ticker>")
        sys.exit(1)

    ticker = sys.argv[1].upper() + "1"
    url = f"{OPTIONSURL5}{ticker}{OPTIONSURL6}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        # Wait for expiration buttons
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "button.apply-common-tooltip.item-XO65o9RZ.button-D4RPB3ZC")
            )
        )
        expiration_buttons = driver.find_elements(
            By.CSS_SELECTOR, "button.apply-common-tooltip.item-XO65o9RZ.button-D4RPB3ZC"
        )
        option_chain = []  # list of expirations

        for btn in expiration_buttons:
            title_text = btn.get_attribute("title").strip()  # use title attribute
            if not title_text:
                continue
            # Example: "Sep 22, 2025 (1) BTCU25 P4A"
            match = re.match(r"(.+)\s+\((\d+)\)", title_text)
            if match:
                exp_text = match.group(1).strip()  # "Sep 22, 2025"
                days_to_exp = int(match.group(2))  # 1
                yte = days_to_exp / TRADINGDAYS
            else:
                exp_text = title_text
                yte = 0.0
            # Click expiration button
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-jOonPmbB tbody tr"))
            )
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table-jOonPmbB")
            if not table:
                continue
            print(f"scripts/optionscryptos.py :: Parsing {ticker} option chain expiration {exp_text}")
            rows = table.find_all("tr")[1:]  # skip header
            calls_list = []
            puts_list = []
            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue
                strike_td = row.find("span", class_="ellipsisContainer-bYDQcOkp")
                if not strike_td:
                    continue
                strike = strike_td.get_text(strip=True)
                cell_texts = [sanitize_cell(c.get_text(strip=True)) for c in cols]
                call_cols = cell_texts[:13]
                put_cols = cell_texts[14:]
                call_row = {
                    "Strike": strike,
                    "StrikeIV%": put_cols[0],
                    "BidIV%": call_cols[0],
                    "AskIV%": call_cols[1],
                    "IntrValue": call_cols[2],
                    "TimeValue": call_cols[3],
                    "Rho": call_cols[4],
                    "Vega": call_cols[5],
                    "Theta": call_cols[6],
                    "Gamma": call_cols[7],
                    "Delta": call_cols[8],
                    "Price": call_cols[9],
                    "Ask": call_cols[10],
                    "Bid": call_cols[11],
                    "Volume": call_cols[12],
                }
                put_row = {
                    "Strike": strike,
                    "StrikeIV%": put_cols[0],
                    "Volume": put_cols[1],
                    "Bid": put_cols[2],
                    "Ask": put_cols[3],
                    "Price": put_cols[4],
                    "Delta": put_cols[5],
                    "Gamma": put_cols[6],
                    "Theta": put_cols[7],
                    "Vega": put_cols[8],
                    "Rho": put_cols[9],
                    "TimeValue": put_cols[10],
                    "IntrValue": put_cols[11],
                    "AskIV%": put_cols[12],
                    "BidIV%": put_cols[13],
                }
                calls_list.append(call_row)
                puts_list.append(put_row)
            # Append after all rows processed for this expiration
            option_chain.append({
                "Expiration": exp_text,
                "YTE": yte,
                "Calls": calls_list,
                "Puts": puts_list
            })
    finally:
        driver.quit()
    # Save to CSV
    csv_file = f"static/data/{ticker}chain.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header
        header = [
            "Ticker", "Expiration", "YTE", "Strike", "StrikeIV%",
            # Call columns
            "callBidIV%", "callAskIV%", "callIntrValue", "callTimeValue", "callRho", "callVega", 
            "callTheta", "callGamma", "callDelta", "callPrice", "callAsk", "callBid", "callVolume",
            # Put columns
            "putIV%", "putVolume", "putBid", "putAsk", "putPrice", "putDelta", "putGamma",
            "putTheta", "putVega", "putRho", "putTimeValue", "putIntrValue", "putAskIV%", "putBidIV%"
        ]
        writer.writerow(header)

        # Iterate expirations
        for expiry in option_chain:
            expiration = expiry["Expiration"]
            yte = expiry["YTE"]
            calls = expiry["Calls"]
            puts = expiry["Puts"]
            for call_row, put_row in zip(calls, puts):
                row = [
                    ticker,
                    expiration,
                    f"{yte:.2f}",
                    call_row["Strike"],
                    call_row["StrikeIV%"],
                    # Call values
                    call_row["BidIV%"], call_row["AskIV%"], call_row["IntrValue"], call_row["TimeValue"], 
                    call_row["Rho"], call_row["Vega"], call_row["Theta"], call_row["Gamma"], 
                    call_row["Delta"], call_row["Price"], call_row["Ask"], call_row["Bid"], call_row["Volume"],
                    # Put values
                    put_row["Volume"], put_row["Bid"], put_row["Ask"], put_row["Price"],
                    put_row["Delta"], put_row["Gamma"], put_row["Theta"], put_row["Vega"], put_row["Rho"],
                    put_row["TimeValue"], put_row["IntrValue"], put_row["AskIV%"], put_row["BidIV%"]
                ]
                writer.writerow(row)
    print(f"scripts/optionscryptos.py :: Option chain saved to {csv_file}")
