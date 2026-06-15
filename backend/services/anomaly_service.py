import numpy as np


class AnomalyService:

    @staticmethod
    def calculate_statistics(values):

        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "current": float(values[-1])
        }

    @staticmethod
    def z_score(values):

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return 0

        return (values[-1] - mean) / std

    @staticmethod
    def percentile_anomaly(values):

        p95 = np.percentile(values, 95)

        return values[-1] > p95

    @staticmethod
    def rolling_window_anomaly(values):

        if len(values) < 20:
            return False

        current_window = np.mean(values[-5:])
        historical_window = np.mean(values[:-5])

        return current_window > (historical_window * 1.5)