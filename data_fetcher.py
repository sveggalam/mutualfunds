import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

def fetch_nav_data(start_date, end_date):
    url = "https://amc.ppfas.com/schemes/nav-history/data.php"
    params = {"dt1": start_date, "dt2": end_date}
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise Exception("NAV table not found")

    rows = table.find_all("tr")[2:]
    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            data.append([cols[0].text.strip(), cols[1].text.strip()])

    df = pd.DataFrame(data, columns=["Date", "Direct_NAV"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Direct_NAV"] = df["Direct_NAV"].astype(float)
    df = df.sort_values("Date").reset_index(drop=True)

    return df


def add_log_returns(df):
    df["log_return"] = np.log(df["Direct_NAV"] / df["Direct_NAV"].shift(1))
    df.dropna(inplace=True)
    return df
