from datetime import datetime

alerts = []


class AlertService:

    @staticmethod
    def add_alert(metric, severity, message):

        alert = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "severity": severity,
            "message": message
        }

        alerts.append(alert)

    @staticmethod
    def get_alerts():
        return alerts

    @staticmethod
    def clear_alerts():
        alerts.clear()