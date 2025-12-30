import streamlit as st
import pandas as pd

from data_fetcher import fetch_nav_data, add_log_returns
from config import BootstrapConfig, SIPConfig
from bootstrap_engine import block_bootstrap_simulation, run_stress_tests
from sip_engine import sip_simulation
from visualisations import *
from stats import *

st.set_page_config(page_title="Mutual Fund Risk Simulator", layout="wide")

st.title("📊 Mutual Fund Risk & SIP Simulator")

# -----------------------------
# Sidebar – Inputs
# -----------------------------
st.sidebar.header("Simulation Settings")

start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2021-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today"))

drift_method = st.sidebar.selectbox(
    "Drift Estimation",
    ["mean", "median", "trimmed"]
)

rolling_window = st.sidebar.selectbox(
    "Rolling Window",
    ["All", "3 Years", "5 Years"]
)

block_length = st.sidebar.slider("Volatility Memory (L)", 5, 60, 20)

regime = st.sidebar.selectbox(
    "Market Regime",
    ["all", "bull", "bear", "mixed"]
)

stress_vol = st.sidebar.slider("Stress Volatility Multiplier", 1.0, 3.0, 1.0)

sip_amount = st.sidebar.number_input("Monthly SIP Amount (₹)", 1000, 100000, 10000)

sip_years = st.sidebar.slider(
    "🕒 SIP Duration (Years)",
    min_value=1,
    max_value=20,
    value=3,
    step=1
)



target_nav = st.sidebar.number_input(
    "🎯 Target NAV (₹)",
    min_value=10,
    max_value=10000,
    value=100,
    step=5
)


run_button = st.sidebar.button("Run Simulation")

# -----------------------------
# Run simulation
# -----------------------------
if run_button:
    with st.spinner("Fetching NAV data..."):
        df = fetch_nav_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        df = add_log_returns(df)

    window_map = {
        "All": None,
        "3 Years": 756,
        "5 Years": 1260
    }
    HORIZON_DAYS = sip_years * 252
    config = BootstrapConfig(
        horizon_days=HORIZON_DAYS,
        drift_method=drift_method,
        rolling_window=window_map[rolling_window],
        block_length=block_length,
        regime=regime,
        stress_vol_multiplier=stress_vol
    )

    st.success("Simulation running...")

    paths = block_bootstrap_simulation(df, config)

    # Starting NAV
    S0 = df["Direct_NAV"].iloc[-1]
    st.subheader("📍 Current Fund Status")

    st.metric(
        "Today's NAV",
        f"₹{S0:.2f}"
    )

    # SIP simulation
    sip_config = SIPConfig(
        sip_amount=sip_amount,
        total_days=HORIZON_DAYS
    )
    sip_results = sip_simulation(paths, sip_config)

    # -----------------------------
    # Friendly stats (PLAIN ENGLISH)
    # -----------------------------
    prob_target = sip_probability_reaching_target(
    sip_results,
    target_amount=target_nav
    )

    prob_profit = probability_of_profit(paths, S0)
    prob_loss = 1 - prob_profit
    median_val = typical_outcome(paths)
    worst_5 = worst_reasonable_outcome(paths, percentile=5)

    # Risk label
    label, color = risk_label(prob_loss)

    # Drawdown stats (needed for SIP logic)
    from stats import drawdown_stats
    dd = drawdown_stats(paths)

    # SIP guidance
    sip_signal = sip_increase_signal(
        prob_loss=prob_loss,
        worst_drawdown=dd["worst_5_dd"],
        vol_multiplier=stress_vol
    )

    # -----------------------------
    # SUMMARY UI
    # -----------------------------
    st.subheader("📌 Easy-to-understand Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        f"Chance of reaching ₹{target_nav}",
        f"{prob_target * 100:.1f}%"
    )

    col2.metric(
        "Chance of making profit",
        f"{prob_profit * 100:.1f}%"
    )

    col3.metric(
        "Typical outcome",
        f"₹{median_val:.2f}"
    )

    col4.metric(
        "Worst 5% outcome",
        f"₹{worst_5:.2f}"
    )

    st.markdown(
        f"### Risk Level: <span style='color:{color}'>{label}</span>",
        unsafe_allow_html=True
    )

    st.subheader("📈 SIP Action Guidance")
    st.info(sip_signal)

    # -----------------------------
    # Visuals
    # -----------------------------
    st.subheader("📈 Sample Price Paths")
    st.pyplot(plot_sample_paths(paths, S0))

    st.subheader("📊 Final NAV Distribution")
    st.pyplot(plot_final_distribution(paths))

    st.subheader("📉 Drawdown Risk")
    st.pyplot(plot_drawdown_distribution(paths))

    st.subheader("💰 SIP Results")
    st.pyplot(plot_sip_final_distribution(sip_results))
    st.pyplot(plot_xirr_distribution(sip_results))

    st.subheader("🔥 Stress Test Summary")
    stress_df = run_stress_tests(df, config)
    st.dataframe(stress_df)
