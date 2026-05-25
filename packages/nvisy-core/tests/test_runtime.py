"""Tests for the shared runtime helpers."""

from nvisy_core.runtime import request_id, resolve_model


def test_path_env_takes_precedence(monkeypatch):
    monkeypatch.setenv("NVISY_MODEL_PATH", "/custom/weights")
    monkeypatch.setenv("NVISY_MODEL_NAME", "ignored/name")
    assert resolve_model("default") == "/custom/weights"


def test_name_env_used_when_no_path(monkeypatch):
    monkeypatch.delenv("NVISY_MODEL_PATH", raising=False)
    monkeypatch.setenv("NVISY_MODEL_NAME", "org/some-model")
    # /models is absent in the test env, so the name wins over the default.
    assert resolve_model("default") == "org/some-model"


def test_default_when_nothing_set(monkeypatch):
    monkeypatch.delenv("NVISY_MODEL_PATH", raising=False)
    monkeypatch.delenv("NVISY_MODEL_NAME", raising=False)
    assert resolve_model("default-model") == "default-model"


def test_request_id_falls_back_without_headers():
    assert request_id(object()) == "-"


def test_request_id_reads_header():
    class _Ctx:
        request = type("R", (), {"headers": {"x-request-id": "abc-123"}})()

    assert request_id(_Ctx()) == "abc-123"
