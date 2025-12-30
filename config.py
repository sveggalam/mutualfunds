from dataclasses import dataclass

@dataclass
class BootstrapConfig:
    horizon_days: int = 252
    simulations: int = 100_000

    drift_method: str = "trimmed"     # mean | median | trimmed
    trim_ratio: float = 0.1
    rolling_window: int | None = None

    regime: str = "all"               # all | bull | bear | mixed
    bull_weight: float = 0.8

    block_length: int = 20

    stress_vol_multiplier: float = 1.0
    stress_drift_shift: float = 0.0


@dataclass
class SIPConfig:
    sip_amount: float = 10_000
    sip_frequency_days: int = 21
    total_days: int = 252
