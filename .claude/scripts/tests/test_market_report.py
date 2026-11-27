# -*- coding: utf-8 -*-
"""Тесты для .claude/scripts/market_report.py.

Запуск из корня репозитория:
    PYTHONUTF8=1 python -m pytest .claude/scripts/tests -v

Всё на синтетических фикстурах в tmp_path.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import market_report as mr  # noqa: E402


def make_registry() -> dict:
    return {
        "schema": 1,
        "updated": "2026-11-06",
        "features": [
            {"id": "F-001", "name": "Офлайн-режим", "category": "Ядро", "description": "Работа без сети",
             "kind": "table-stakes", "suggested_priority": "must", "origin": "market"},
            {"id": "F-002", "name": "Совместное редактирование", "category": "Команда",
             "description": "Несколько авторов", "kind": "differentiator", "suggested_priority": "should",
             "origin": "market", "decision": {"priority": "must", "stage": 2, "note": "ключ к B2B"}},
            {"id": "F-003", "name": "ИИ-резюме <b>", "category": "Ядро", "description": "Сводка заметок",
             "kind": "innovation", "suggested_priority": "could", "origin": "vision"},
        ],
    }


def make_competitor(cid: str, name: str, feats: dict) -> dict:
    return {
        "id": cid, "name": name, "url": f"https://{cid}.example", "type": "direct",
        "pricing": "freemium", "platforms": ["web"],
        "strengths": [{"text": f"{name}: быстрый", "sources": ["s1"]}],
        "weaknesses": ["нет экспорта"],
        "features": feats,
    }


def make_study(kind: str = "task", n: int = 3) -> dict:
    comps = [make_competitor(f"c{i}", f"Prod{i}", {"F-001": "full", "F-002": "partial" if i % 2 else "none"})
             for i in range(1, n + 1)]
    return {
        "schema": 1, "slug": "notes-sync", "kind": kind, "title": "Анализ аналогов: синхронизация",
        "date": "2026-11-06", "question": "Как конкуренты делают синхронизацию",
        "summary": ["Офлайн есть у всех"], "competitors": comps,
        "opportunities": [{"text": "Никто не делает резюме", "features": ["F-003"]}],
        "recommendations": ["Делать офлайн в MVP"],
        "methodology": {"criteria": ["активная поддержка"], "limitations": ["платные тарифы не проверены"]},
        "sources": [{"id": "s1", "title": "Сайт", "url": "https://s1.example", "accessed": "2026-11-06"}],
    }


def write(tmp_path: Path, study: dict, reg: dict) -> Path:
    (tmp_path / mr.REGISTRY_NAME).write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    p = tmp_path / f"{study['slug']}.json"
    p.write_text(json.dumps(study, ensure_ascii=False), encoding="utf-8")
    return p


# ---------------------------------------------------------------- валидация


def test_valid_study_has_no_errors():
    errors, warnings = mr.validate_study(make_study(), make_registry())
    assert errors == []
    # weakness given as a plain string has no source -> warning, not error
    assert any("no source" in w for w in warnings)


def test_registry_rejects_bad_ids_and_enums():
    reg = make_registry()
    reg["features"].append(dict(reg["features"][0]))  # duplicate F-001
    reg["features"].append({"id": "X1", "name": "a", "category": "b", "description": "c",
                            "kind": "weird", "suggested_priority": "maybe"})
    errors, _ = mr.validate_registry(reg)
    joined = "\n".join(errors)
    assert "duplicate id F-001" in joined
    assert "must look like F-001" in joined
    assert "kind 'weird'" in joined
    assert "suggested_priority 'maybe'" in joined


def test_registry_rejects_bad_decision():
    reg = make_registry()
    reg["features"][0]["decision"] = {"priority": "top"}
    errors, _ = mr.validate_registry(reg)
    assert any("decision.priority" in e for e in errors)


def test_study_requires_pros_and_cons():
    st = make_study()
    st["competitors"][0]["strengths"] = []
    st["competitors"][1]["weaknesses"] = []
    errors, _ = mr.validate_study(st, make_registry())
    assert any("Prod1: at least one strength" in e for e in errors)
    assert any("Prod2: at least one weakness" in e for e in errors)


def test_study_rejects_unknown_feature_source_and_coverage():
    st = make_study()
    st["competitors"][0]["features"]["F-999"] = "full"
    st["competitors"][0]["features"]["F-001"] = "yes"
    st["competitors"][0]["strengths"][0]["sources"] = ["s404"]
    st["opportunities"][0]["features"] = ["F-777"]
    errors, _ = mr.validate_study(st, make_registry())
    joined = "\n".join(errors)
    assert "F-999 is not in the registry" in joined
    assert "coverage of F-001 'yes'" in joined
    assert "unknown source id 's404'" in joined
    assert "F-777 is not in the registry" in joined


def test_study_missing_required_keys():
    errors, _ = mr.validate_study({"competitors": []}, make_registry())
    for key in ("slug", "title", "kind", "question", "summary", "sources"):
        assert any(f"'{key}' is required" in e for e in errors)


def test_baseline_needs_five_competitors_warning():
    _, warnings = mr.validate_study(make_study(kind="baseline", n=3), make_registry())
    assert any("expected at least 5" in w for w in warnings)
    _, warnings = mr.validate_study(make_study(kind="baseline", n=5), make_registry())
    assert not any("expected at least" in w for w in warnings)


def test_empty_matrix_is_an_error():
    st = make_study()
    for c in st["competitors"]:
        c["features"] = {}
    errors, _ = mr.validate_study(st, make_registry())
    assert any("matrix would be empty" in e for e in errors)


# ---------------------------------------------------------------- рендер


def test_render_study_contains_sections_and_escapes(tmp_path):
    p = write(tmp_path, make_study(), make_registry())
    assert mr.main(["render", str(p)]) == 0
    out = (tmp_path / "notes-sync.html").read_text(encoding="utf-8")
    for anchor in ('id="summary"', 'id="landscape"', 'id="cards"', 'id="matrix"', 'id="registry"',
                   'id="insights"', 'id="method"', 'id="sources"', 'id="c-c1"'):
        assert anchor in out
    assert "Преимущества" in out and "Недостатки" in out
    assert "Prod1: быстрый" in out
    assert 'href="#src-s1"' in out
    assert "cov-full" in out and "cov-partial" in out and "cov-none" in out
    # F-003 has no competitor coverage but is an opportunity -> still in the matrix (as unknown)
    matrix = out.split('id="matrix"')[1].split('id="registry"')[0]
    assert "ИИ-резюме" in matrix and "cov-unknown" in matrix
    assert 'href="feature-registry.html"' in out
    # self-contained: no external scripts/styles
    assert "<script src" not in out and "<link" not in out
    assert out.startswith("<!doctype html>")


def test_render_escapes_html(tmp_path):
    st = make_study()
    st["competitors"][0]["name"] = "<script>alert(1)</script>"
    p = write(tmp_path, st, make_registry())
    assert mr.main(["render", str(p)]) == 0
    out = (tmp_path / "notes-sync.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


def test_render_refuses_on_errors(tmp_path, capsys):
    st = make_study()
    st["competitors"][0]["type"] = "enemy"
    p = write(tmp_path, st, make_registry())
    assert mr.main(["render", str(p)]) == 1
    assert not (tmp_path / "notes-sync.html").exists()
    assert "render skipped" in capsys.readouterr().out


def test_render_registry_aggregates_studies(tmp_path):
    reg = make_registry()
    write(tmp_path, make_study(n=3), reg)
    other = make_study(n=2)
    other["slug"] = "second"
    (tmp_path / "second.json").write_text(json.dumps(other, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "junk.json").write_text("{not json", encoding="utf-8")  # ignored
    assert mr.main(["registry", "--dir", str(tmp_path)]) == 0
    out = (tmp_path / "feature-registry.html").read_text(encoding="utf-8")
    # F-001 is full in 3 + 2 competitors
    assert "5 есть" in out
    assert "ключ к B2B" in out  # decision note
    assert "не принято" in out  # undecided feature
    assert 'href="second.html"' in out and 'href="notes-sync.html"' in out
    assert "ИИ-резюме &lt;b&gt;" in out


def test_next_id(tmp_path, capsys):
    (tmp_path / mr.REGISTRY_NAME).write_text(json.dumps(make_registry()), encoding="utf-8")
    assert mr.main(["next-id", "--dir", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == "F-004"
    assert mr.main(["next-id", "--dir", str(tmp_path / "missing")]) == 0
    assert capsys.readouterr().out.strip() == "F-001"


def test_invalid_json_reported(tmp_path, capsys):
    (tmp_path / mr.REGISTRY_NAME).write_text(json.dumps(make_registry()), encoding="utf-8")
    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    assert mr.main(["validate", str(p)]) == 1
    assert "invalid JSON" in capsys.readouterr().out


def test_templates_are_valid_json():
    tdir = Path(__file__).resolve().parents[2] / "templates"
    for name in ("market-study.template.json", "feature-registry.template.json"):
        json.loads((tdir / name).read_text(encoding="utf-8"))
