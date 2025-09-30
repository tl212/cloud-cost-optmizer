import os
from src.config_loader import load_config, expand_env_vars


def test_expand_env_vars(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    cfg = {"a": "$FOO", "nested": {"b": "$FOO"}, "plain": "x"}

    out = expand_env_vars(cfg)

    assert out["a"] == "bar"
    assert out["nested"]["b"] == "bar"
    assert out["plain"] == "x"


def test_load_config(tmp_path):
    p = tmp_path / "conf.yaml"
    p.write_text("x: 1\ny: two\n", encoding="utf-8")

    data = load_config(str(p))

    assert data == {"x": 1, "y": "two"}