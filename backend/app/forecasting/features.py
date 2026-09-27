"""Direct multi-horizon features. Every target feature uses a frozen origin."""
from datetime import date, timedelta
import math
import numpy as np

HORIZON = 14
FEATURES = ["horizon", "weekday", "annual_sin", "annual_cos", "trend",
    "lag1_ratio", "lag2_ratio", "lag7_ratio", "lag14_ratio", "lag28_ratio",
    "mean7_ratio", "mean14_ratio", "std28_ratio", "growth7", "log_scale",
    "facility_type", "log_catchment", "beds", "scheduled_staff", "latitude", "medicine_index"]
MODEL_NAMES = ["naive", "seasonal_naive", "moving_average", "hist_gradient_boosting"]


def feature_block(values, origin: int, start: date, context: dict, horizon: int = HORIZON):
    """origin is the last observed index; future entries in values are never read."""
    if origin < 27 or not 1 <= horizon <= HORIZON:
        raise ValueError("Need 28 past values and a horizon between 1 and 14")
    past = np.asarray(values[origin-27:origin+1], dtype=float)
    if len(past) != 28 or np.any(~np.isfinite(past)) or np.any(past < 0):
        raise ValueError("Invalid past observations")
    scale = max(1.0, float(past.mean()))
    mean7, mean14 = past[-7:].mean(), past[-14:].mean()
    growth = mean7 / max(1.0, past[-14:-7].mean()) - 1
    static = [*(past[-lag] / scale for lag in (1, 2, 7, 14, 28)), mean7 / scale,
        mean14 / scale, past.std() / scale, growth, math.log1p(scale), context["type_index"],
        math.log1p(context["catchment"]), context["beds"], context["scheduled_staff"],
        context["latitude"], context.get("medicine_index", -1)]
    rows, baselines = [], []
    for h in range(1, horizon+1):
        target = start + timedelta(days=origin+h)
        annual = 2 * math.pi * target.timetuple().tm_yday / 365.25
        rows.append([h, target.weekday(), math.sin(annual), math.cos(annual),
            (origin+h+context.get("trend_offset", 0))/365.25, *static])
        baselines.append([past[-1], past[-7 + (h-1) % 7], mean7])
    return np.asarray(rows, dtype=np.float32), scale, np.asarray(baselines, dtype=np.float32)


def split_bounds(days: int):
    if days < 365:
        raise ValueError("At least 365 historical days are required")
    a, b, c = int(days*.7), int(days*.8), int(days*.9)
    return [(28, a), (a, b), (b, c), (c, days)]


def origins_for(days: int, series_index: int):
    for split, (start, end) in enumerate(split_bounds(days)):
        # Train with staggered weekly origins; evaluate rolling 14-day origins.
        first = start - 1 + (series_index % 7 if split == 0 else 0)
        origins = list(range(first, end-HORIZON, 7 if split == 0 else HORIZON))
        # Include each held-out window's last day. The final block can overlap
        # its predecessor; these are forecast-origin/horizon errors, not IID days.
        if split and origins[-1] != end-HORIZON-1:
            origins.append(end-HORIZON-1)
        for origin in origins:
            yield split, origin
