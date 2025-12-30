# from turtle import st
import requests
import pandas as pd
from io import StringIO

AMFI_MASTER = "https://www.amfiindia.com/spages/NAVAll.txt"
MFAPI = "https://api.mfapi.in/mf/{}"


# -------------------------------------------------
# Load AMFI master
# -------------------------------------------------
def load_master():
    txt = requests.get(AMFI_MASTER).text
    df = pd.read_csv(StringIO(txt), sep=";")

    df = df.dropna(subset=["Scheme Code", "Scheme Name"])
    df["Scheme Code"] = df["Scheme Code"].astype(int)

    # Extract Fund House from Scheme Name
    df["Fund House"] = df["Scheme Name"].str.split(" - ").str[0]

    return df


# -------------------------------------------------
# Fund → Scheme mapping
# -------------------------------------------------
def get_fund_scheme_map():
    df = load_master()

    mapping = {}
    for _, r in df.iterrows():
        fund = r["Fund House"]
        scheme = r["Scheme Name"]
        code = r["Scheme Code"]

        mapping.setdefault(fund, [])
        mapping[fund].append({
            "scheme_name": scheme,
            "scheme_code": code
        })

    return mapping


# -------------------------------------------------
# Get available NAV date range for a scheme
# -------------------------------------------------
def get_date_range(scheme_code):
    url = MFAPI.format(scheme_code)
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()["data"]
    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")

    return df["date"].min().date(), df["date"].max().date()


# -------------------------------------------------
# Fetch NAV history for scheme + date range
# -------------------------------------------------
def fetch_nav_history(scheme_code, start_date, end_date):
    url = MFAPI.format(scheme_code)
    response = requests.get(url)
    response.raise_for_status()

    df = pd.DataFrame(response.json()["data"])
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = df["nav"].astype(float)

    df = df.sort_values("date")

    mask = (df["date"] >= pd.to_datetime(start_date)) & \
           (df["date"] <= pd.to_datetime(end_date))

    return df.loc[mask].reset_index(drop=True)

def fetch_latest_nav(scheme_code):
    df = fetch_nav_history(
        scheme_code=scheme_code,
        start_date="1900-01-01",
        end_date=pd.Timestamp.today().strftime("%Y-%m-%d")
    )
    return df.iloc[-1]
