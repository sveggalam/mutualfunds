import numpy as np
from config import SIPConfig


def sip_simulation(paths, sip_config: SIPConfig):
    """
    Simulates SIP investing over Monte Carlo paths.

    paths: numpy array of shape (T+1, M)
           T = total simulation days
           M = number of simulations
    """

    T, M = paths.shape[0] - 1, paths.shape[1]

    # Safety check
    if sip_config.total_days > T:
        raise ValueError(
            f"SIP duration ({sip_config.total_days} days) "
            f"exceeds simulation horizon ({T} days)"
        )

    sip_days = np.arange(
        0,
        sip_config.total_days + 1,
        sip_config.sip_frequency_days
    )

    final_values = np.zeros(M)
    xirrs = np.zeros(M)

    years = sip_config.total_days / 252

    for sim in range(M):
        units = 0.0
        invested = 0.0

        for d in sip_days:
            nav = paths[d, sim]
            units += sip_config.sip_amount / nav
            invested += sip_config.sip_amount

        final_value = units * paths[sip_config.total_days, sim]
        xirr = (final_value / invested) ** (1 / years) - 1

        final_values[sim] = final_value
        xirrs[sim] = xirr

    return {
        "final_values": final_values,
        "xirr": xirrs,
        "invested": invested
    }
