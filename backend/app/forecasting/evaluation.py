import numpy as np


def metrics(actual, predicted):
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    error = actual - predicted
    denom = float(np.abs(actual).sum())
    return {"mae": float(np.abs(error).mean()), "rmse": float(np.sqrt(np.mean(error**2))),
        "wape": float(np.abs(error).sum() / denom) if denom else None, "samples": len(actual)}


def residual_bands(residual_paths):
    # Conservative finite-sample absolute residual quantiles, per horizon.
    residual_paths = np.asarray(residual_paths)
    n = len(residual_paths)
    return {str(level): np.quantile(np.abs(residual_paths), min(1.0, np.ceil((n+1)*level)/n),
        axis=0, method="higher") for level in (.8, .95)}


def intervals(point, scale, bands):
    result = {}
    for key, widths in bands.items():
        width = np.asarray(widths)[:len(point)] * scale
        result[key] = (np.maximum(0, point-width), point+width)
    return result
