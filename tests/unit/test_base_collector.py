from datetime import datetime, timedelta
from src.collectors.base_collector import BaseCollector


class DummyCollector(BaseCollector):
    def authenticate(self):
        return True

    def collect_billing_data(self, start_date, end_date):
        return [
            {"service_name": "A", "cost": 1.5},
            {"service_name": "A", "cost": 2.5},
            {"service_name": "B", "cost": 1.0},
        ]

    def collect_resource_data(self):
        return []

    def get_required_config_fields(self):
        return ["project_id"]


def test_validate_config_missing():
    c = DummyCollector({"foo": "bar"})
    assert c.validate_config() is False


def test_validate_config_present():
    c = DummyCollector({"project_id": "pid"})
    assert c.validate_config() is True


def test_get_cost_by_service_sums():
    c = DummyCollector({"project_id": "pid"})
    res = c.get_cost_by_service(datetime.now() - timedelta(days=1), datetime.now())
    assert res["A"] == 4.0
    assert res["B"] == 1.0