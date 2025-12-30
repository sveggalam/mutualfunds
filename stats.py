import numpy as np

def probability_reaching_target(paths, target_value):
    """
    Returns probability that final value >= target_value
    """
    final_values = paths[-1]
    return np.mean(final_values >= target_value)


def probability_of_profit(paths, S0):
    final_values = paths[-1]
    return np.mean(final_values > S0)


def worst_reasonable_outcome(paths, percentile=5):
    return np.percentile(paths[-1], percentile)


def typical_outcome(paths):
    return np.percentile(paths[-1], 50)


def risk_label(prob_loss):
    if prob_loss <= 0.10:
        return "🟢 Low Risk", "green"
    elif prob_loss <= 0.25:
        return "🟡 Medium Risk", "orange"
    else:
        return "🔴 High Risk", "red"


def sip_increase_signal(prob_loss, worst_drawdown, vol_multiplier):
    if prob_loss < 0.10 and worst_drawdown > -0.30 and vol_multiplier > 1.2:
        return "🟢 Yes – Conditions are favorable"
    elif prob_loss < 0.20:
        return "🟡 Maybe – Increase cautiously"
    else:
        return "🔴 No – Maintain or pause SIP"


def max_drawdown(path):
    peak = np.maximum.accumulate(path)
    drawdown = (path - peak) / peak
    return drawdown.min()


def drawdown_stats(paths):
    drawdowns = np.array([max_drawdown(paths[:, i]) for i in range(paths.shape[1])])
    return {
        "median_dd": np.percentile(drawdowns, 50),
        "worst_5_dd": np.percentile(drawdowns, 5)
    }

def sip_probability_reaching_target(sip_results, target_amount):
    """
    Probability that SIP final value >= target_amount
    """
    final_values = sip_results["final_values"]
    return np.mean(final_values >= target_amount)
