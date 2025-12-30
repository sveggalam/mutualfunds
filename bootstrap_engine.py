import numpy as np
import pandas as pd
from scipy.stats import trim_mean
from config import BootstrapConfig

def classify_regime(returns, window=60):
    rolling_mean = pd.Series(returns).rolling(window).mean()
    return np.where(rolling_mean >= 0, "bull", "bear")


def estimate_drift(returns, method, trim_ratio):
    if method == "mean":
        return returns.mean()
    if method == "median":
        return np.median(returns)
    if method == "trimmed":
        return trim_mean(returns, trim_ratio)
    raise ValueError("Invalid drift method")


def create_blocks(returns, L):
    return np.array([returns[i:i+L] for i in range(len(returns)-L+1)])


def block_bootstrap_simulation(df, config: BootstrapConfig):
    returns = df["log_return"].values
    S0 = df["Direct_NAV"].iloc[-1]

    if config.rolling_window:
        returns = returns[-config.rolling_window:]

    if config.regime != "all":
        regimes = classify_regime(returns)
        bull = returns[regimes == "bull"]
        bear = returns[regimes == "bear"]

        if config.regime == "bull":
            returns = bull
        elif config.regime == "bear":
            returns = bear
        elif config.regime == "mixed":
            n_bull = int(len(returns) * config.bull_weight)
            returns = np.concatenate([
                np.random.choice(bull, n_bull, replace=True),
                np.random.choice(bear, len(returns)-n_bull, replace=True)
            ])

    mu = estimate_drift(
        returns,
        config.drift_method,
        config.trim_ratio
    ) + config.stress_drift_shift

    sigma = returns.std() * config.stress_vol_multiplier

    blocks = create_blocks(returns, config.block_length)

    N, M = config.horizon_days, config.simulations
    paths = np.zeros((N+1, M))
    paths[0] = S0

    for sim in range(M):
        sim_returns = []
        while len(sim_returns) < N:
            sim_returns.extend(blocks[np.random.randint(len(blocks))])
        sim_returns = sim_returns[:N]

        for t in range(1, N+1):
            paths[t, sim] = paths[t-1, sim] * np.exp(sim_returns[t-1])

    return paths


def run_stress_tests(df, base_config):
    scenarios = {
        "Normal": base_config,
        "High Vol": BootstrapConfig(**{**base_config.__dict__, "stress_vol_multiplier": 1.5}),
        "Crash": BootstrapConfig(**{
            **base_config.__dict__,
            "stress_vol_multiplier": 2.0,
            "stress_drift_shift": -0.0005
        })
    }

    results = {}
    for name, cfg in scenarios.items():
        paths = block_bootstrap_simulation(df, cfg)
        final = paths[-1]
        results[name] = {
            "5%": np.percentile(final, 5),
            "Median": np.percentile(final, 50),
            "95%": np.percentile(final, 95),
            "Prob_Loss": np.mean(final < paths[0,0])
        }

    return pd.DataFrame(results)
