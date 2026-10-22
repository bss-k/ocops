import pytest
import ocops


class FakeResponse:
    def __init__(self, status=200, json_data=None, headers=None):
        self.status_code = status
        self._json = json_data
        self.headers = headers or {}
        self.content = b"" if json_data is None else b"x"
        self.text = str(json_data)

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._json


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    """Runs before every test: fake config, no sleeping, audit file in a temp dir."""
    monkeypatch.setattr(
        ocops, "_active", {"name": "test", "api_key": "k", "universe_id": "1"}
    )
    monkeypatch.setattr(ocops.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(ocops, "AUDIT_FILE", str(tmp_path / "audit.jsonl"))


@pytest.fixture
def fake_api(monkeypatch):
    """Queue up responses; every requests.request call pops the next one."""
    queue, calls = [], []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return queue.pop(0)

    monkeypatch.setattr(ocops.requests, "request", fake_request)
    return queue, calls