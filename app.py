import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# Session state init
# =========================================================
if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

if "run_id" not in st.session_state:
    st.session_state.run_id = 0

# =========================================================
# Data layer
# =========================================================
from data_fetching import (
    get_fund_scheme_map,
    get_date_range,
    fetch_nav_history,
    fetch_latest_nav
)
from data_fetcher import add_log_returns

@st.cache_data(show_spinner=False)
def get_latest_nav_cached(scheme_code):
    return fetch_latest_nav(scheme_code)

# =========================================================
# Simulation engines
# =========================================================
from config import BootstrapConfig, SIPConfig
from bootstrap_engine import block_bootstrap_simulation, run_stress_tests
from sip_engine import sip_simulation
from visualisations import *
from stats import *

# =========================================================
# Page config
# =========================================================
st.set_page_config(page_title="Mutual Fund Risk & SIP Simulator", layout="wide")
# =========================================================
# Widen Sidebar (CSS Override)
# =========================================================
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 600px !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 600px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Mutual Fund Risk & SIP Simulator")

# =========================================================
# Explainer
# =========================================================
with st.expander("What does this simulator do? (Click to understand)"):
    st.markdown("""
### What this simulator is (and is NOT)

This simulator **does NOT predict future returns**.

Instead, it answers practical questions like:
- *What could reasonably happen based on history?*
- *How risky is my SIP?*
- *What are realistic worst-case and best-case outcomes?*

It works like a **stress test**, not a crystal ball.

---

## How the simulation works (high level)

1. Uses **actual historical NAV movements** of the selected fund  
2. Preserves **volatility clustering** (good and bad periods stay together)  
3. Generates **thousands of alternative future paths** using Monte Carlo  
4. Tests your **SIP strategy across all futures**  

The output shows **probabilities**, not promises.

---

## What each setting means (and what happens when you change it)

### Drift Estimation
**What it controls:**  
The *average return tendency* of the fund.

**Options:**
- **Mean** → Uses historical average return  
- **Median** → More robust to extreme years  
- **Trimmed** → Removes extreme good & bad periods  

**When to change:**  
- Use *median / trimmed* if you want **conservative realism**
- Mean assumes history repeats cleanly

---

### Rolling Window
**What it controls:**  
How much historical data is used to estimate risk.

**Options:**
- **All** → Uses entire history  
- **3 Years** → Focuses on recent market behaviour  
- **5 Years** → Balanced long-term view  

**When to change:**  
- Shorter windows = more sensitive to recent volatility  
- Longer windows = smoother, slower-changing risk

---

### 🌊 Volatility Memory (Block Length L)
**What it controls:**  
How long market conditions persist in simulations.

**Low L (5–10):**
- Rapid switches between calm & volatile days

**High L (30–60):**
- Long bull & bear stretches (more realistic)

**Rule of thumb:**  
Higher L = **more realistic drawdowns**

---

### Market Regime
**What it controls:**  
Which type of historical days are sampled.

- **All** → Full market history  
- **Bull** → Positive-return environments  
- **Bear** → Stress & crash periods  
- **Mixed** → Alternates between bull & bear  

**When to use:**  
- Bear = stress testing  
- Mixed = realistic long-term planning

---

### Stress Volatility Multiplier
**What it controls:**  
Artificially increases volatility to test resilience.

- **1.0** → Normal conditions  
- **>1.0** → Crisis-like scenarios  

**Use this to answer:**  
> “What if things go much worse than normal?”

---

### Monthly SIP Amount
**What it controls:**  
How much money you invest every month.

The simulator tracks:
- Total invested
- Final corpus distribution
- XIRR outcomes

---

### SIP Duration (Years)
**What it controls:**  
How long the SIP runs.

Longer durations:
- Reduce downside risk
- Improve probability of positive outcomes

---

### Target NAV
**What it controls:**  
Your personal goal.

The simulator calculates:
- Probability of reaching this target
- Risk-adjusted feasibility

---

## What the results mean

- **Expected value** → Average outcome across all futures  
- **Typical value (Median)** → Most likely scenario  
- **Worst 5%** → Severe but realistic downside  
- **Best 95%** → Optimistic but plausible upside  
- **Probability of loss** → Chance of ending below invested amount  

---
---

## 💼 Lumpsum Investment

**What it is:**  
A one-time investment made at the start of the simulation.

**How it is simulated:**
- Lumpsum is invested **at today’s NAV**
- It participates fully in all simulated future paths
- No averaging benefit like SIP — more sensitive to timing

**What happens when you change it:**
- Higher lumpsum → higher upside *and* higher short-term risk
- In volatile or bear regimes, lumpsum risk is more visible
- Over long horizons, risk smooths out

**Best use case:**
- Long-term investors (10+ years)
- Investors adding money during market corrections

**Important:**  
SIP and Lumpsum are simulated **together**, so you can see:
- Total invested
- Final combined corpus
- Risk contribution of each

## SIP Action Guidance (Increase / Reduce / Hold)

The simulator suggests actions based on:
- Probability of loss
- Severity of drawdowns
- Stress-test outcomes

This is **guidance**, not advice — meant to improve discipline.

---

### Final takeaway

> This tool helps you **prepare**, not predict.  
> The goal is **better decisions under uncertainty**.
""")


st.divider()

# =========================================================
# Fund selection
# =========================================================
st.sidebar.header("Fund Selection")

fund_scheme_map = get_fund_scheme_map()

fund = st.sidebar.selectbox(
    "Select Mutual Fund",
    sorted(fund_scheme_map.keys()),
    help="Mutual Fund house (AMC)"
)

schemes = fund_scheme_map[fund]
scheme_name = st.sidebar.selectbox(
    "Select Scheme",
    [s["scheme_name"] for s in schemes]
)
scheme_code = next(s["scheme_code"] for s in schemes if s["scheme_name"] == scheme_name)

# =========================================================
# Date range
# =========================================================
min_date, max_date = get_date_range(scheme_code)

start_date = st.sidebar.date_input("From Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("To Date", max_date, min_value=min_date, max_value=max_date)

# =========================================================
# Current NAV
# =========================================================
latest = get_latest_nav_cached(scheme_code)
# S0 = df["Direct_NAV"].iloc[-1]

latest_nav = float(latest["nav"])


st.subheader(f"📌 {scheme_name} overview")

with st.container():
    st.markdown(f"### Fund House: {fund}")
    # st.write(fund)

    st.markdown(f"### Scheme: {scheme_name}")
    # st.write(scheme_name)

    st.markdown(f"### Latest NAV is {latest_nav:.2f} ₹".format(latest_nav=latest_nav))
    # st.metric(label="", value=f"₹{latest_nav:.2f}")


st.divider()

# =========================================================
# Simulation settings
# =========================================================
st.sidebar.header("Simulation Settings")

drift_method = st.sidebar.selectbox("Drift Estimation", ["mean", "median", "trimmed"])
rolling_window = st.sidebar.selectbox("Rolling Window", ["All", "3 Years", "5 Years"])
block_length = st.sidebar.slider("Volatility Memory (L)", 5, 60, 20)
stress_vol = st.sidebar.slider("Stress Volatility Multiplier", 1.0, 3.0, 1.0)

st.sidebar.header("SIP/Lumpsum Settings")
sip_amount = st.sidebar.number_input("Monthly SIP Amount (₹)", 1000, 100000, 10000)
sip_years = st.sidebar.slider("SIP Duration (Years)", 1, 20, 3)
lumpsum_amount = st.sidebar.number_input(
    "💼 Lumpsum Investment (₹)",
    min_value=0,
    max_value=1_00_00_000,
    value=0,
    step=10_000,
    help="One-time investment made at today's NAV"
)


target_nav = st.sidebar.number_input("Target NAV (₹)", 10, 10000, 100, step=5)

# =========================================================
# Run button
# =========================================================
run_button = st.sidebar.button(
    "Run Simulation",
    disabled=st.session_state.simulation_running,
    key=f"run_{st.session_state.run_id}"
)

# =========================================================
# Run simulation
# =========================================================
if run_button and not st.session_state.simulation_running:

    st.session_state.simulation_running = True
    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("Fetching NAV data")
        progress.progress(15)

        df = fetch_nav_history(scheme_code, start_date, end_date)
        df.rename(columns={"nav": "Direct_NAV"}, inplace=True)
        df = add_log_returns(df)

        progress.progress(35)

        window_map = {"All": None, "3 Years": 756, "5 Years": 1260}
        horizon_days = sip_years * 252

        config = BootstrapConfig(
            horizon_days=horizon_days,
            drift_method=drift_method,
            rolling_window=window_map[rolling_window],
            block_length=block_length,
            regime="all",
            stress_vol_multiplier=stress_vol
        )

        status.info("Running Monte Carlo")
        progress.progress(60)

        paths = block_bootstrap_simulation(df, config)
        S0 = paths[0, 0]
        status.info("Simulating SIP")
        progress.progress(80)

        sip_config = SIPConfig(sip_amount=sip_amount, total_days=horizon_days)
        sip_results = sip_simulation(paths, sip_config)
        lumpsum_invested = lumpsum_amount
        # =====================================================
        # LUMPSUM SIMULATION
        # =====================================================
        if lumpsum_amount > 0:
            lumpsum_units = lumpsum_amount / S0
            lumpsum_final_values = lumpsum_units * paths[-1, :]
        else:
            lumpsum_final_values = np.zeros(paths.shape[1])
    
        progress.progress(100)
        status.success("Simulation complete")

        # =====================================================
        # SIP stats
        # =====================================================
        final_vals = sip_results["final_values"]
        invested = sip_results["invested"]

        prob_sip_loss = np.mean(final_vals < invested)

        sip_expected = final_vals.mean()
        sip_median = np.median(final_vals)
        sip_worst = np.percentile(final_vals, 5)
        sip_best = np.percentile(final_vals, 95)

        st.subheader(f"SIP Outcome After {sip_years} Years")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Invested", f"₹{invested:,.0f}")
        c2.metric("Expected Value", f"₹{sip_expected:,.0f}")
        c3.metric("Typical Value", f"₹{sip_median:,.0f}")
        c4,c5 = st.columns(2)
        c4.metric("Worst 5%", f"₹{sip_worst:,.0f}")
        c5.metric("Best 95%", f"₹{sip_best:,.0f}")

        st.metric("Probability of SIP Loss", f"{prob_sip_loss*100:.1f}%")
        
        
        # =====================================================
        # COMBINED SIP + LUMPSUM STATS
        # =====================================================
        combined_final_values = final_vals + lumpsum_final_values
        combined_invested = invested + lumpsum_invested

        prob_combined_loss = np.mean(combined_final_values < combined_invested)

        combined_expected = combined_final_values.mean()
        combined_median = np.median(combined_final_values)
        combined_worst_5 = np.percentile(combined_final_values, 5)
        combined_best_95 = np.percentile(combined_final_values, 95)

        st.subheader(f"💼 SIP + Lumpsum Outcome After {sip_years} Years")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Invested", f"₹{combined_invested:,.0f}")
        c2.metric("Expected Value", f"₹{combined_expected:,.0f}")
        c3.metric("Typical Value", f"₹{combined_median:,.0f}")
        c4.metric("Worst 5%", f"₹{combined_worst_5:,.0f}")
        c5.metric("Best 95%", f"₹{combined_best_95:,.0f}")

        st.metric(
            "Probability of Loss (SIP + Lumpsum)",
            f"{prob_combined_loss * 100:.1f}%"
        )

        
        # =====================================================
        # SIP Action guidance
        # =====================================================
        st.subheader("📈 Investment Action Guidance")

        if prob_combined_loss > 0.35:
            st.error(
                "🔻 Consider REDUCING investment\n\n"
                "High probability of loss across SIP + Lumpsum."
            )
        elif prob_combined_loss < 0.15:
            st.success(
                "🔼 Consider INCREASING investment\n\n"
                "Low loss probability with favorable long-term risk."
            )
        else:
            st.info(
                "➡️ Maintain current strategy\n\n"
                "Risk–reward appears balanced."
            )

        # =====================================================
        # Visuals
        # =====================================================
        st.subheader("Sample Price Paths")
        st.pyplot(plot_sample_paths(paths, df["Direct_NAV"].iloc[-1]))

        st.subheader("SIP Distribution")
        st.pyplot(plot_sip_final_distribution(sip_results))

        st.subheader("Stress Tests")
        st.dataframe(run_stress_tests(df, config))

    finally:
        st.session_state.simulation_running = False
        st.session_state.run_id += 1
