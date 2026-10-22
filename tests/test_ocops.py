import os

import pytest

import ocops
from conftest import FakeResponse


def test_paginate_follows_cursor(fake_api):
    queue, calls = fake_api
    queue.append(FakeResponse(200, {"datastores": [{"name": "a"}], "nextPageCursor": "c1"}))
    queue.append(FakeResponse(200, {"datastores": [{"name": "b"}]}))
    result = ocops.paginate("standard-datastores", "datastores")
    assert [d["name"] for d in result] == ["a", "b"]
    assert calls[1][2]["params"]["cursor"] == "c1"


def test_retries_then_succeeds(fake_api):
    queue, calls = fake_api
    queue += [FakeResponse(503), FakeResponse(200, {"ok": True})]
    assert ocops.api_request("GET", "x") == {"ok": True}
    assert len(calls) == 2


def test_404_is_not_retried(fake_api):
    queue, calls = fake_api
    queue.append(FakeResponse(404))
    with pytest.raises(ocops.ApiError) as err:
        ocops.api_request("GET", "x")
    assert err.value.status == 404
    assert len(calls) == 1


def test_guard_blocks_real_datastores():
    with pytest.raises(SystemExit):
        ocops.require_safe("Data_4")


def test_dry_run_writes_nothing(fake_api):
    queue, calls = fake_api
    queue.append(FakeResponse(200, {"coins": 1}))  # the read of the old value
    ocops.apply_change("set", "ocops_x", "k", {"coins": 2}, dry_run=True)
    assert [method for method, _, _ in calls] == ["GET"]
    assert not os.path.exists(ocops.AUDIT_FILE)


def test_set_audits_old_value(fake_api):
    queue, calls = fake_api
    queue.append(FakeResponse(200, {"coins": 1}))  # old value
    queue.append(FakeResponse(200))                # the write returns an empty body
    ocops.apply_change("set", "ocops_x", "k", {"coins": 2}, dry_run=False)
    record = ocops.last_audit("ocops_x", "k")
    assert record["old"] == {"coins": 1}
    assert record["new"] == {"coins": 2}
    assert [method for method, _, _ in calls] == ["GET", "POST"]

def test_backoff_grows_and_is_capped():
    assert 1 <= ocops.backoff_delay(0) < 2
    assert 8 <= ocops.backoff_delay(3) < 9
    assert 30 <= ocops.backoff_delay(10) < 31


def test_profile_name_is_lowercase(monkeypatch):
    monkeypatch.setenv("PROD_API_KEY", "k")
    monkeypatch.setenv("PROD_UNIVERSE_ID", "1")
    ocops.load_profile("prod")
    assert ocops._active["name"] == "prod"


def test_prod_requires_confirmation(monkeypatch):
    ocops._active["name"] = "prod"
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    with pytest.raises(SystemExit):
        ocops.confirm_prod("set x")


def test_restore_writes_old_value(fake_api):
    queue, calls = fake_api
    queue += [FakeResponse(200, {"coins": 1}), FakeResponse(200)]
    ocops.apply_change("set", "ocops_x", "k", {"coins": 2}, dry_run=False)
    queue += [FakeResponse(200, {"coins": 2}), FakeResponse(200)]
    record = ocops.last_audit("ocops_x", "k")
    ocops.apply_change("restore", "ocops_x", "k", record["old"], dry_run=False)
    assert calls[-1][2]["json"] == {"coins": 1}


def test_safe_prefix_can_be_overridden(monkeypatch):
    monkeypatch.setattr(ocops, "SAFE_PREFIX", "mygame_")
    ocops.require_safe("mygame_data")  # allowed
    with pytest.raises(SystemExit):
        ocops.require_safe("ocops_data")
