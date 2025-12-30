import matplotlib.pyplot as plt
import numpy as np

def plot_sample_paths(paths, S0, n=100):
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(paths[:, :n], alpha=0.3)
    ax.axhline(S0, linestyle="--", color="black")
    ax.set_title("Sample Paths")
    return fig


def plot_final_distribution(paths):
    final = paths[-1]
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(final, bins=100)
    for p in [5,25,50,75,95]:
        ax.axvline(np.percentile(final,p), linestyle="--")
    ax.set_title("Final NAV Distribution")
    return fig


def plot_drawdown_distribution(paths):
    def max_dd(p):
        peak = np.maximum.accumulate(p)
        return ((p-peak)/peak).min()

    dds = [max_dd(paths[:,i]) for i in range(paths.shape[1])]
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(dds, bins=100)
    ax.set_title("Max Drawdown Distribution")
    return fig


def plot_sip_final_distribution(results):
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(results["final_values"], bins=100)
    ax.set_title("SIP Final Value Distribution")
    return fig


def plot_xirr_distribution(results):
    fig, ax = plt.subplots(figsize=(10,6))
    ax.hist(results["xirr"]*100, bins=100)
    ax.set_title("XIRR Distribution (%)")
    return fig


def probability_reaching_target(paths, target_value):
    final_values = paths[-1]
    prob = np.mean(final_values >= target_value)
    return prob