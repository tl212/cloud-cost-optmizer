import types
import src.collectors.gcp_collector as gmod


class DummyBillingClient:
    def __init__(self, credentials=None):
        self.credentials = credentials

    def get_project_billing_info(self, name):
        return types.SimpleNamespace(
            billing_account_name="billingAccounts/TEST",
            billing_enabled=True,
        )


class DummyAssetClient:
    def __init__(self, credentials=None):
        self.credentials = credentials


class DummyInstancesClient:
    def __init__(self, credentials=None):
        self.credentials = credentials


def test_authenticate_uses_adc(monkeypatch):
    dummy_creds = object()

    # Patch ADC
    monkeypatch.setattr(
        gmod.google.auth,
        "default",
        lambda scopes=None: (dummy_creds, "sevenl33-v2-25"),
    )

    # Patch GCP clients created in authenticate()
    monkeypatch.setattr(gmod.billing, "CloudBillingClient", lambda credentials=None: DummyBillingClient(credentials))
    monkeypatch.setattr(gmod.asset, "AssetServiceClient", lambda credentials=None: DummyAssetClient(credentials))
    monkeypatch.setattr(gmod.compute, "InstancesClient", lambda credentials=None: DummyInstancesClient(credentials))

    collector = gmod.GCPCollector({"project_id": "pid"})
    assert collector.authenticate() is True