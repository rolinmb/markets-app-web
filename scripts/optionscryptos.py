from consts import TRADINGDAYS, OPTIONSURL5, OPTIONSURL6
import re
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
        print("Usage: python optionscryptos.py <ticker>")
        sys.exit(1)

    ticker = sys.argv[1].upper() + "1!"
    url = f"{OPTIONSURL5}{ticker}{OPTIONSURL6}"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
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
            exp_text = btn.text.strip()
            if not exp_text:
                continue
            # Extract days to expiration and calculate YTE
            match = re.search(r"\((\d+)\)$", exp_text)
            if match:
                days_to_exp = int(match.group(1))
                yte = days_to_exp / TRADINGDAYS
            else:
                yte = None
            # Click expiration button
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-jOonPmbB tbody tr"))
            )
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table-jOonPmbB")
            if not table:
                continue
            rows = table.find_all("tr")[1:]  # skip header
            calls_list = []
            puts_list = []
            for row in rows:
                cols = row.find_all("td")
                cell_texts = [c.get_text(strip=True) for c in cols]
                if not cell_texts or len(cell_texts) < 28:
                    continue
                call_cols = cell_texts[:12]
                strike_col = cell_texts[12]
                put_cols = cell_texts[13:]
                call_row = {
                    "Strike": strike_col,
                    "BidIV": call_cols[0],
                    "AskIV": call_cols[1],
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
                }
                put_row = {
                    "Strike": strike_col,
                    "IV": put_cols[0],
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
                    "AskIV": put_cols[12],
                    "BidIV": put_cols[13],
                }
                calls_list.append(call_row)
                puts_list.append(put_row)
            option_chain.append({
                "Expiration": exp_text,
                "YTE": yte,
                "Calls": calls_list,
                "Puts": puts_list
            })

    finally:
        driver.quit()

    # Option chain is now a nested list/dict structure
    for expiry in option_chain:
        print(f"Expiration: {expiry['Expiration']}, YTE: {expiry['YTE']:.2f}")
        print(f"Calls: {len(expiry['Calls'])} rows, Puts: {len(expiry['Puts'])} rows")
