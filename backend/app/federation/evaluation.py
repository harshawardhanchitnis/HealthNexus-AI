import math
import numpy as np
from app.federation.schemas import Metric


def evaluate_arrays(normalized_actual, normalized_predicted, scale):
    actual = normalized_actual.astype(np.float64)*scale
    predicted = np.maximum(0,normalized_predicted.astype(np.float64))*scale
    error = actual-predicted
    absolute = float(np.abs(error).sum()); squared = float(np.square(error).sum()); total = float(np.abs(actual).sum())
    return Metric(samples=len(actual),absolute_error=absolute,squared_error=squared,target_total=total,
        mae=absolute/len(actual),rmse=math.sqrt(squared/len(actual)),wape=absolute/total if total else None,
        normalized_mae=float(np.abs(normalized_actual-np.maximum(0,normalized_predicted)).mean()))


def aggregate_metrics(metrics):
    n = sum(m.samples for m in metrics); absolute = sum(m.absolute_error for m in metrics)
    squared = sum(m.squared_error for m in metrics); total = sum(m.target_total for m in metrics)
    return Metric(samples=n,absolute_error=absolute,squared_error=squared,target_total=total,
        mae=absolute/n,rmse=math.sqrt(squared/n),wape=absolute/total if total else None,
        normalized_mae=sum(m.normalized_mae*m.samples for m in metrics)/n)
