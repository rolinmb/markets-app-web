from consts import BONDURL, HEADERS
import os
import sys
import csv
import requests
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Make sure stdout is UTF-8 (Windows console fix)
    sys.stdout.reconfigure(encoding="utf-8")
    print("scripts/bonds.py :: Requesting cnbc.com/bonds for the html table content...")

    response = requests.get(BONDURL, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="data-table")

    if not table:
        print("scripts/bonds.py :: No yield curve table found.")
    else:
        thead = table.find("thead")
        headers = []
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]

        tbody = table.find("tbody")
        rows = []
        if tbody:
            for tr in tbody.find_all("tr"):
                # Include both th (for Name) and td (for the rest)
                cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)

        with open("data/bonds.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
        
        print("scripts/bonds.py :: data/bonds.csv written successfully")

        df = pd.read_csv("data/bonds.csv")

        # Clean Yield column: remove % and convert to float
        df["Yield"] = df["Yield"].str.replace("%", "", regex=False).astype(float)

        x_labels = df["Name"]
        y_values = df["Yield"]

        plt.figure(figsize=(10, 5))
        plt.plot(x_labels, y_values, marker="o", linestyle="-", color="blue")
        plt.title("Current Treasury Yield Curve")
        plt.xlabel("Tenor")
        plt.ylabel("Yield (%)")
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        
        png_path = os.path.join("img", "bonds.png")
        plt.savefig(png_path, dpi=150, bbox_inches="tight")
        plt.close()

        bmp_path = os.path.join("img", "bonds.bmp")
        with Image.open(png_path) as png:
            png = png.resize((400,300), Image.LANCZOS)
            png.convert("RGB").save(bmp_path, "BMP")
        
        if os.path.exists(png_path):
            os.remove(png_path)
        
        print("scripts/bonds.py :: img/bonds.bmp written successfully\n")
        

        
