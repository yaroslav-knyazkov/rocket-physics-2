#!/usr/bin/env python
"""Анализ аналогов: валидация данных и рендер HTML-отчёта и реестра фич.

Агент market-analyst не пишет HTML руками: он собирает структурированные данные в JSON,
а этот скрипт проверяет их и рендерит единообразный, самодостаточный (без внешних
зависимостей, открывается офлайн) HTML-файл. Так отчёты выглядят одинаково от проекта
к проекту, а реестр фич остаётся машиночитаемым для product-manager.

Файлы (по умолчанию в dev/docs/market/):
    feature-registry.json   — реестр фич проекта, накопительный, один на проект
    <slug>.json             — данные одного исследования (baseline — стартовое)
    <slug>.html             — отчёт по исследованию (генерируется, руками не править)
    feature-registry.html   — весь реестр с покрытием по всем исследованиям (генерируется)

    python .claude/scripts/market_report.py validate dev/docs/market/baseline.json
    python .claude/scripts/market_report.py render   dev/docs/market/baseline.json
    python .claude/scripts/market_report.py registry [--dir dev/docs/market]
    python .claude/scripts/market_report.py next-id  [--dir dev/docs/market]

Реестр ищется рядом с файлом исследования (или --registry). Ошибки валидации — код 1,
рендер при ошибках не выполняется; предупреждения печатаются, но не блокируют.
Схема и пример — .claude/templates/market-study.template.json и
.claude/templates/feature-registry.template.json.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DIR = REPO / "dev" / "docs" / "market"
REGISTRY_NAME = "feature-registry.json"

FEATURE_ID_RE = re.compile(r"^F-\d{3,}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

COVERAGE = {
    "full": ("✓", "есть"),
    "partial": ("◐", "частично"),
    "none": ("✗", "нет"),
    "unknown": ("?", "нет данных"),
}
PRIORITY = {"must": "Must", "should": "Should", "could": "Could", "wont": "Won't"}
PRIORITY_RU = {"must": "обязательно", "should": "желательно", "could": "можно", "wont": "не делаем"}
KIND = {
    "table-stakes": "Базовая",
    "differentiator": "Отличие",
    "innovation": "Пробел рынка",
}
KIND_HINT = {
    "table-stakes": "есть почти у всех — без неё продукт не воспринимают всерьёз",
    "differentiator": "есть у немногих — повод выбрать именно этот продукт",
    "innovation": "нет ни у кого из рассмотренных — возможность",
}
COMPETITOR_TYPE = {
    "direct": "Прямой",
    "indirect": "Косвенный",
    "substitute": "Заменитель",
    "inspiration": "Референс",
}
STUDY_KIND = {"baseline": "Стартовый анализ", "task": "Исследование задачи"}
ORIGIN = {"market": "рынок", "vision": "видение", "user": "пользователь", "research": "исследование"}

MIN_COMPETITORS = {"baseline": 5, "task": 3}


# --------------------------------------------------------------------------
# загрузка
# --------------------------------------------------------------------------


class DataError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise DataError(f"file not found: {path}")
    except json.JSONDecodeError as e:
        raise DataError(f"{path.name}: invalid JSON at line {e.lineno} col {e.colno}: {e.msg}")
    if not isinstance(data, dict):
        raise DataError(f"{path.name}: top level must be an object")
    return data


def is_study(data: dict) -> bool:
    return isinstance(data.get("competitors"), list)


def iter_studies(directory: Path):
    for p in sorted(directory.glob("*.json")):
        if p.name == REGISTRY_NAME:
            continue
        try:
            data = load_json(p)
        except DataError:
            continue
        if is_study(data):
            yield p, data


# --------------------------------------------------------------------------
# валидация
# --------------------------------------------------------------------------


def _text_items(items) -> list:
    """strengths/weaknesses/...: строка или {"text": ..., "sources": [...]}."""
    out = []
    for it in items or []:
        if isinstance(it, str):
            out.append({"text": it, "sources": []})
        elif isinstance(it, dict):
            src = it.get("sources", it.get("source", []))
            if isinstance(src, str):
                src = [src]
            out.append({"text": str(it.get("text", "")), "sources": list(src or [])})
        else:
            out.append({"text": str(it), "sources": []})
    return out


def validate_registry(reg: dict) -> tuple:
    errors, warnings = [], []
    feats = reg.get("features")
    if not isinstance(feats, list):
        return ["registry: 'features' must be a list"], warnings
    seen = set()
    for i, f in enumerate(feats):
        where = f"registry.features[{i}]"
        if not isinstance(f, dict):
            errors.append(f"{where}: must be an object")
            continue
        fid = f.get("id", "")
        if not FEATURE_ID_RE.match(str(fid)):
            errors.append(f"{where}: id '{fid}' must look like F-001")
        elif fid in seen:
            errors.append(f"{where}: duplicate id {fid}")
        seen.add(fid)
        for key in ("name", "category", "description"):
            if not str(f.get(key, "")).strip():
                errors.append(f"{fid or where}: '{key}' is required")
        kind = f.get("kind")
        if kind not in KIND:
            errors.append(f"{fid or where}: kind '{kind}' not in {sorted(KIND)}")
        prio = f.get("suggested_priority")
        if prio not in PRIORITY:
            errors.append(f"{fid or where}: suggested_priority '{prio}' not in {sorted(PRIORITY)}")
        origin = f.get("origin", "market")
        if origin not in ORIGIN:
            errors.append(f"{fid or where}: origin '{origin}' not in {sorted(ORIGIN)}")
        dec = f.get("decision")
        if dec is not None:
            if not isinstance(dec, dict) or dec.get("priority") not in PRIORITY:
                errors.append(f"{fid or where}: decision.priority must be one of {sorted(PRIORITY)}")
    return errors, warnings


def validate_study(study: dict, reg: dict) -> tuple:
    errors, warnings = [], []
    for key in ("slug", "title", "kind", "date", "question", "summary", "competitors", "sources"):
        if key not in study:
            errors.append(f"study: '{key}' is required")
    slug = str(study.get("slug", ""))
    if slug and not SLUG_RE.match(slug):
        errors.append(f"study: slug '{slug}' must be lowercase latin/digits/dashes")
    kind = study.get("kind")
    if kind not in STUDY_KIND:
        errors.append(f"study: kind '{kind}' not in {sorted(STUDY_KIND)}")
    if not isinstance(study.get("summary", []), list) or not study.get("summary"):
        errors.append("study: 'summary' must be a non-empty list of takeaways")

    source_ids = set()
    for i, s in enumerate(study.get("sources") or []):
        if not isinstance(s, dict) or not s.get("id") or not s.get("url"):
            errors.append(f"sources[{i}]: needs 'id' and 'url'")
            continue
        if s["id"] in source_ids:
            errors.append(f"sources[{i}]: duplicate id {s['id']}")
        source_ids.add(s["id"])

    feature_ids = {f.get("id") for f in reg.get("features", []) if isinstance(f, dict)}
    comps = study.get("competitors") or []
    if not isinstance(comps, list):
        errors.append("study: 'competitors' must be a list")
        comps = []
    minimum = MIN_COMPETITORS.get(kind, 3)
    if len(comps) < minimum:
        warnings.append(
            f"only {len(comps)} competitor(s); expected at least {minimum} for kind '{kind}' "
            "— explain the shortfall in methodology.limitations"
        )
    cids = set()
    used_features = set()
    for i, c in enumerate(comps):
        where = f"competitors[{i}]"
        if not isinstance(c, dict):
            errors.append(f"{where}: must be an object")
            continue
        cid = c.get("id")
        name = c.get("name") or cid or where
        if not cid:
            errors.append(f"{where}: 'id' is required")
        elif cid in cids:
            errors.append(f"{where}: duplicate id {cid}")
        cids.add(cid)
        if not c.get("name"):
            errors.append(f"{where}: 'name' is required")
        if c.get("type") not in COMPETITOR_TYPE:
            errors.append(f"{name}: type '{c.get('type')}' not in {sorted(COMPETITOR_TYPE)}")
        strengths = _text_items(c.get("strengths"))
        weaknesses = _text_items(c.get("weaknesses"))
        if not strengths:
            errors.append(f"{name}: at least one strength is required")
        if not weaknesses:
            errors.append(f"{name}: at least one weakness is required")
        for it in strengths + weaknesses:
            if not it["sources"]:
                warnings.append(f"{name}: '{it['text'][:50]}' has no source — mark it as an assumption")
            for sid in it["sources"]:
                if sid not in source_ids:
                    errors.append(f"{name}: unknown source id '{sid}'")
        for sid in c.get("sources", []) or []:
            if sid not in source_ids:
                errors.append(f"{name}: unknown source id '{sid}'")
        feats = c.get("features") or {}
        if not isinstance(feats, dict):
            errors.append(f"{name}: 'features' must be an object {{F-001: full|partial|none|unknown}}")
            feats = {}
        for fid, cov in feats.items():
            if fid not in feature_ids:
                errors.append(f"{name}: feature {fid} is not in the registry")
            if cov not in COVERAGE:
                errors.append(f"{name}: coverage of {fid} '{cov}' not in {sorted(COVERAGE)}")
            used_features.add(fid)
    for i, o in enumerate(study.get("opportunities") or []):
        for fid in (o.get("features") or []) if isinstance(o, dict) else []:
            if fid not in feature_ids:
                errors.append(f"opportunities[{i}]: feature {fid} is not in the registry")
    if comps and not used_features:
        errors.append("study: no competitor has a 'features' coverage map — the matrix would be empty")
    return errors, warnings


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

E = html.escape

CSS = """
:root{--bg:#f7f6f2;--surface:#fff;--ink:#1d1d1b;--muted:#6b6a64;--line:#e3e1d9;--accent:#2f5d8a;
--accent-soft:#e6eef6;--good:#2e7d4f;--good-soft:#e5f3ea;--bad:#b0412e;--bad-soft:#f8e7e3;
--warn:#9a6a00;--warn-soft:#f7eed6;--none:#a3a29b;--radius:10px;
--font:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--surface:#1f1f1d;--ink:#ecebe6;--muted:#a09f98;
--line:#34332f;--accent:#8db7e0;--accent-soft:#1f2c39;--good:#7cc79a;--good-soft:#1c2c22;--bad:#ec917f;
--bad-soft:#35201c;--warn:#e0b65a;--warn-soft:#332a15;--none:#6d6c66}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--font)}
a{color:var(--accent)}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:32px;max-width:1280px;margin:0 auto;padding:24px 16px 64px}
nav.toc{position:sticky;top:16px;align-self:start;font-size:14px}
nav.toc b{display:block;margin-bottom:8px;color:var(--muted);font-weight:600;text-transform:uppercase;font-size:12px;letter-spacing:.06em}
nav.toc a{display:block;padding:4px 0;color:var(--ink);text-decoration:none}nav.toc a:hover{color:var(--accent)}
nav.toc a.sub{padding-left:12px;color:var(--muted);font-size:13px}
header.hero{margin-bottom:28px}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:12px;font-weight:600}
h1{font-size:28px;line-height:1.2;margin:10px 0 6px}h2{font-size:21px;margin:40px 0 14px;padding-top:8px}
h3{font-size:17px;margin:0 0 4px}.muted{color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.kpi .v{font-size:24px;font-weight:700}.kpi .l{color:var(--muted);font-size:13px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px}
ul.tight{margin:0;padding-left:20px}ul.tight li{margin:4px 0}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--surface);position:sticky;top:0;font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}
.matrix td.cov,.matrix th.comp{text-align:center;white-space:nowrap}
.cov-full{color:var(--good);font-weight:700}.cov-partial{color:var(--warn);font-weight:700}
.cov-none{color:var(--none)}.cov-unknown{color:var(--muted)}
.cards{display:grid;gap:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:18px}
.card .meta{display:flex;flex-wrap:wrap;gap:6px 16px;margin:6px 0 12px;font-size:13px;color:var(--muted)}
.pc{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.pros,.cons{border-radius:8px;padding:10px 12px}.pros{background:var(--good-soft)}.cons{background:var(--bad-soft)}
.pros h4,.cons h4{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.05em}
.pros h4{color:var(--good)}.cons h4{color:var(--bad)}
sup.src a{text-decoration:none;font-size:11px}
.tag{display:inline-block;padding:1px 8px;border-radius:6px;font-size:12px;border:1px solid var(--line);white-space:nowrap}
.k-table-stakes{background:var(--accent-soft)}.k-differentiator{background:var(--warn-soft)}.k-innovation{background:var(--good-soft)}
.p-must{font-weight:700}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px}
.filters input,.filters select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}
.filters input{flex:1;min-width:200px}
.legend{font-size:13px;color:var(--muted);margin:8px 0}
footer{margin-top:48px;font-size:12px;color:var(--muted)}
@media (max-width:860px){.layout{grid-template-columns:1fr}nav.toc{position:static;border-bottom:1px solid var(--line);padding-bottom:12px}.pc{grid-template-columns:1fr}}
@media print{nav.toc,.filters{display:none}.layout{display:block}body{background:#fff}.card,.panel,.scroll{break-inside:avoid}}
"""

FILTER_JS = """
(function(){
  var t=document.getElementById('reg-table'); if(!t) return;
  var q=document.getElementById('reg-q'), c=document.getElementById('reg-cat'),
      k=document.getElementById('reg-kind'), p=document.getElementById('reg-prio'),
      n=document.getElementById('reg-count');
  function apply(){
    var s=(q.value||'').toLowerCase(), shown=0;
    t.querySelectorAll('tbody tr').forEach(function(r){
      var ok=(!s||r.textContent.toLowerCase().indexOf(s)>=0)
        &&(!c.value||r.dataset.cat===c.value)&&(!k.value||r.dataset.kind===k.value)
        &&(!p.value||r.dataset.prio===p.value);
      r.style.display=ok?'':'none'; if(ok) shown++;
    });
    n.textContent=shown;
  }
  [q,c,k,p].forEach(function(el){el.addEventListener('input',apply)}); apply();
})();
"""


def _src_refs(ids, sources_by_id) -> str:
    out = []
    for sid in ids:
        s = sources_by_id.get(sid)
        if s:
            num = s["_n"]
            out.append(f'<a href="#src-{E(sid)}" title="{E(s.get("title") or s["url"])}">[{num}]</a>')
    return f'<sup class="src">{"".join(out)}</sup>' if out else ""


def _items_html(items, sources_by_id) -> str:
    lis = "".join(f"<li>{E(it['text'])}{_src_refs(it['sources'], sources_by_id)}</li>" for it in items)
    return f'<ul class="tight">{lis}</ul>'


def _list(items) -> str:
    if not items:
        return '<p class="muted">—</p>'
    return '<ul class="tight">' + "".join(f"<li>{E(str(x))}</li>" for x in items) + "</ul>"


def _cov_cell(cov: str) -> str:
    sym, label = COVERAGE.get(cov, COVERAGE["unknown"])
    return f'<td class="cov cov-{E(cov)}" title="{E(label)}">{sym}</td>'


def _page(title: str, toc: list, body: str, generated: str) -> str:
    links = "".join(
        f'<a href="#{E(a)}" class="{"sub" if sub else ""}">{E(t)}</a>' for a, t, sub in toc
    )
    return (
        "<!doctype html>\n<html lang=\"ru\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{E(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        f'<div class="layout"><nav class="toc"><b>Содержание</b>{links}</nav>\n<main>{body}\n'
        f"<footer>Сгенерировано {E(generated)} скриптом .claude/scripts/market_report.py из JSON-данных. "
        "Руками не править — правьте JSON и перегенерируйте.</footer></main></div>\n"
        f"<script>{FILTER_JS}</script>\n</body>\n</html>\n"
    )


def _coverage_by_feature(studies) -> dict:
    """feature id -> list of (competitor name, coverage, study slug)."""
    cov = {}
    for _, st in studies:
        for c in st.get("competitors", []):
            for fid, v in (c.get("features") or {}).items():
                cov.setdefault(fid, []).append((c.get("name", c.get("id")), v, st.get("slug")))
    return cov


def _registry_table(features, coverage, decision_col=True, comps_total=None) -> str:
    cats = sorted({f["category"] for f in features})
    opts_cat = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in cats)
    opts_kind = "".join(f'<option value="{k}">{E(v)}</option>' for k, v in KIND.items())
    opts_prio = "".join(f'<option value="{k}">{E(v)}</option>' for k, v in PRIORITY.items())
    rows = []
    for f in features:
        fid = f["id"]
        entries = coverage.get(fid, [])
        full = [n for n, v, _ in entries if v == "full"]
        partial = [n for n, v, _ in entries if v == "partial"]
        cov_txt = f"{len(full)} есть"
        if partial:
            cov_txt += f", {len(partial)} частично"
        if comps_total:
            cov_txt += f" из {comps_total}"
        who = ", ".join(full + [p + " (частично)" for p in partial]) or "—"
        dec = f.get("decision") or {}
        prio = dec.get("priority") or f.get("suggested_priority")
        dec_html = ""
        if decision_col:
            if dec:
                stage = f", стадия {E(str(dec['stage']))}" if dec.get("stage") not in (None, "") else ""
                note = f'<div class="muted">{E(dec.get("note", ""))}</div>' if dec.get("note") else ""
                dec_html = f'<td><span class="p-{E(dec["priority"])}">{E(PRIORITY[dec["priority"]])}</span>{stage}{note}</td>'
            else:
                dec_html = '<td class="muted">не принято</td>'
        value = f'<div class="muted">{E(f["value"])}</div>' if f.get("value") else ""
        rows.append(
            f'<tr id="{E(fid)}" data-cat="{E(f["category"])}" data-kind="{E(f["kind"])}" data-prio="{E(prio)}">'
            f"<td style='white-space:nowrap'><b>{E(fid)}</b></td><td><b>{E(f['name'])}</b><div>{E(f['description'])}</div>{value}</td>"
            f"<td>{E(f['category'])}</td>"
            f'<td><span class="tag k-{E(f["kind"])}" title="{E(KIND_HINT[f["kind"]])}">{E(KIND[f["kind"]])}</span></td>'
            f'<td title="{E(cov_txt)}">{E(cov_txt)}<div class="muted">{E(who)}</div></td>'
            f'<td class="p-{E(f["suggested_priority"])}">{E(PRIORITY[f["suggested_priority"]])}</td>'
            f"{dec_html}"
            f"<td>{E(ORIGIN.get(f.get('origin', 'market'), ''))}</td></tr>"
        )
    dec_th = "<th>Решение проекта</th>" if decision_col else ""
    return (
        '<div class="filters">'
        '<input id="reg-q" type="search" placeholder="Поиск по реестру…">'
        f'<select id="reg-cat"><option value="">Все категории</option>{opts_cat}</select>'
        f'<select id="reg-kind"><option value="">Любой тип</option>{opts_kind}</select>'
        f'<select id="reg-prio"><option value="">Любой приоритет</option>{opts_prio}</select>'
        '</div><p class="legend">Показано: <b id="reg-count"></b>. '
        "Приоритет — предложение аналитика (MoSCoW); «Решение проекта» фиксирует product-manager после утверждения brief.</p>"
        '<div class="scroll"><table id="reg-table"><thead><tr><th>ID</th><th>Фича</th><th>Категория</th>'
        f"<th>Тип</th><th>Покрытие у аналогов</th><th>Предложение</th>{dec_th}<th>Откуда</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def render_study(study: dict, reg: dict) -> str:
    sources = study.get("sources") or []
    sources_by_id = {}
    for n, s in enumerate(sources, 1):
        s = dict(s, _n=n)
        sources_by_id[s["id"]] = s
    comps = study["competitors"]
    reg_by_id = {f["id"]: f for f in reg.get("features", [])}
    used = []
    opp_ids = [fid for o in study.get("opportunities") or [] if isinstance(o, dict) for fid in o.get("features") or []]
    for fid in [fid for c in comps for fid in (c.get("features") or {})] + opp_ids:
        if fid not in used:
            used.append(fid)
    # порядок фич: как в реестре
    used.sort(key=lambda fid: list(reg_by_id).index(fid) if fid in reg_by_id else 10**6)
    feats = [reg_by_id[f] for f in used if f in reg_by_id]

    toc = [("summary", "Кратко", False), ("landscape", "Аналоги — обзор", False), ("cards", "Разбор аналогов", False)]
    toc += [(f"c-{c['id']}", c["name"], True) for c in comps]
    toc += [("matrix", "Матрица фич", False), ("registry", "Реестр фич", False)]
    if study.get("opportunities") or study.get("recommendations"):
        toc.append(("insights", "Выводы и рекомендации", False))
    toc += [("method", "Методология", False), ("sources", "Источники", False)]

    kpis = [
        (len(comps), "аналогов разобрано"),
        (len(feats), "фич в матрице"),
        (sum(1 for f in feats if f["kind"] == "innovation"), "пробелов рынка"),
        (len(sources), "источников"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{E(l)}</div></div>' for v, l in kpis)
    ctx = f'<p>{E(study["product_context"])}</p>' if study.get("product_context") else ""
    body = [
        f'<header class="hero"><span class="badge">{E(STUDY_KIND.get(study["kind"], study["kind"]))}</span>'
        f'<h1>{E(study["title"])}</h1><div class="muted">{E(str(study["date"]))} · '
        f'Вопрос исследования: {E(study["question"])}</div>{ctx}</header>',
        f'<section id="summary"><h2>Кратко</h2><div class="kpis">{kpi_html}</div>'
        f'<div class="panel">{_list(study["summary"])}</div></section>',
    ]

    rows = []
    for c in comps:
        url = f'<a href="{E(c["url"])}" target="_blank" rel="noopener">{E(c["name"])}</a>' if c.get("url") else E(c["name"])
        rows.append(
            f'<tr><td><b>{url}</b></td><td>{E(COMPETITOR_TYPE[c["type"]])}</td>'
            f'<td>{E(c.get("positioning", "—"))}</td><td>{E(c.get("audience", "—"))}</td>'
            f'<td>{E(c.get("pricing", "—"))}</td><td>{E(", ".join(c.get("platforms") or []) or "—")}</td></tr>'
        )
    body.append(
        '<section id="landscape"><h2>Аналоги — обзор</h2><div class="scroll"><table><thead><tr>'
        "<th>Продукт</th><th>Тип</th><th>Позиционирование</th><th>Для кого</th><th>Цена</th><th>Платформы</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>"
    )

    cards = []
    for c in comps:
        meta = [f"Тип: {COMPETITOR_TYPE[c['type']]}"]
        for key, label in (("pricing", "Цена"), ("audience", "Для кого"), ("maturity", "Зрелость")):
            if c.get(key):
                meta.append(f"{label}: {c[key]}")
        if c.get("url"):
            link = f'<a href="{E(c["url"])}" target="_blank" rel="noopener">{E(c["url"])}</a>'
        else:
            link = ""
        desc = f"<p>{E(c['description'])}</p>" if c.get("description") else ""
        take = ""
        if c.get("takeaways"):
            take = f'<p style="margin:12px 0 4px"><b>Что это значит для нас</b></p>{_list(c["takeaways"])}'
        refs = _src_refs(c.get("sources") or [], sources_by_id)
        refs_html = f'<p class="muted">Источники: {refs}</p>' if refs else ""
        meta_html = "".join(f"<span>{E(m)}</span>" for m in meta)
        pros = _items_html(_text_items(c["strengths"]), sources_by_id)
        cons = _items_html(_text_items(c["weaknesses"]), sources_by_id)
        cards.append(
            f'<article class="card" id="c-{E(c["id"])}"><h3>{E(c["name"])}</h3>'
            f'<div class="meta">{meta_html}{link}</div>{desc}'
            f'<div class="pc"><div class="pros"><h4>Преимущества</h4>{pros}</div>'
            f'<div class="cons"><h4>Недостатки</h4>{cons}</div></div>'
            f"{take}{refs_html}</article>"
        )
    body.append(f'<section id="cards"><h2>Разбор аналогов</h2><div class="cards">{"".join(cards)}</div></section>')

    head = "".join(f'<th class="comp">{E(c["name"])}</th>' for c in comps)
    mrows = []
    for f in feats:
        cells = "".join(_cov_cell((c.get("features") or {}).get(f["id"], "unknown")) for c in comps)
        mrows.append(
            f'<tr><td><a href="#{E(f["id"])}">{E(f["id"])}</a> {E(f["name"])}</td>'
            f'<td><span class="tag k-{E(f["kind"])}">{E(KIND[f["kind"]])}</span></td>{cells}</tr>'
        )
    legend = " · ".join(f"{s} {l}" for s, l in COVERAGE.values())
    body.append(
        f'<section id="matrix"><h2>Матрица фич</h2><p class="legend">{E(legend)}</p>'
        f'<div class="scroll"><table class="matrix"><thead><tr><th>Фича</th><th>Тип</th>{head}</tr></thead>'
        f"<tbody>{''.join(mrows)}</tbody></table></div></section>"
    )

    coverage = _coverage_by_feature([(None, study)])
    body.append(
        '<section id="registry"><h2>Реестр фич</h2><p class="muted">Фичи, затронутые этим исследованием. '
        'Полный накопительный реестр проекта — <a href="feature-registry.html">feature-registry.html</a>.</p>'
        f"{_registry_table(feats, coverage, comps_total=len(comps))}</section>"
    )

    if study.get("opportunities") or study.get("recommendations") or study.get("risks"):
        parts = []
        if study.get("opportunities"):
            lis = []
            for o in study["opportunities"]:
                if isinstance(o, dict):
                    refs = " ".join(f'<a href="#{E(x)}">{E(x)}</a>' for x in o.get("features") or [])
                    lis.append(f"<li>{E(o.get('text', ''))} {refs}</li>")
                else:
                    lis.append(f"<li>{E(str(o))}</li>")
            parts.append(f'<h3>Возможности</h3><ul class="tight">{"".join(lis)}</ul>')
        if study.get("recommendations"):
            parts.append(f'<h3 style="margin-top:14px">Рекомендации</h3>{_list(study["recommendations"])}')
        if study.get("risks"):
            parts.append(f'<h3 style="margin-top:14px">Риски</h3>{_list(study["risks"])}')
        body.append(f'<section id="insights"><h2>Выводы и рекомендации</h2><div class="panel">{"".join(parts)}</div></section>')

    m = study.get("methodology") or {}
    mparts = []
    if m.get("criteria"):
        mparts.append(f"<p><b>Критерии отбора и сравнения</b></p>{_list(m['criteria'])}")
    if m.get("approach"):
        mparts.append(f"<p><b>Как искали</b></p><p>{E(m['approach'])}</p>")
    if m.get("limitations"):
        mparts.append(f"<p><b>Ограничения</b></p>{_list(m['limitations'])}")
    body.append(
        f'<section id="method"><h2>Методология</h2><div class="panel">{"".join(mparts) or "<p class=muted>—</p>"}</div></section>'
    )

    slis = []
    for s in sources_by_id.values():
        acc = f' <span class="muted">({E(str(s["accessed"]))})</span>' if s.get("accessed") else ""
        slis.append(
            f'<li id="src-{E(s["id"])}"><a href="{E(s["url"])}" target="_blank" rel="noopener">'
            f'{E(s.get("title") or s["url"])}</a>{acc}</li>'
        )
    body.append(f'<section id="sources"><h2>Источники</h2><ol>{"".join(slis)}</ol></section>')
    return _page(study["title"], toc, "\n".join(body), date.today().isoformat())


def render_registry(reg: dict, studies: list) -> str:
    feats = reg.get("features", [])
    coverage = _coverage_by_feature(studies)
    title = reg.get("title") or "Реестр фич проекта"
    by_kind = {k: sum(1 for f in feats if f["kind"] == k) for k in KIND}
    decided = sum(1 for f in feats if f.get("decision"))
    kpis = [(len(feats), "фич в реестре"), (decided, "с решением проекта")]
    kpis += [(by_kind[k], KIND[k].lower()) for k in KIND]
    kpi_html = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{E(l)}</div></div>' for v, l in kpis)
    st_links = "".join(
        f'<li><a href="{E(p.with_suffix(".html").name)}">{E(st.get("title", p.stem))}</a> '
        f'<span class="muted">({E(str(st.get("date", "")))}, {len(st.get("competitors", []))} аналогов)</span></li>'
        for p, st in studies
    )
    body = (
        f'<header class="hero"><span class="badge">Реестр</span><h1>{E(title)}</h1>'
        f'<div class="muted">Обновлён {E(str(reg.get("updated", "")))}</div></header>'
        f'<section id="summary"><h2>Сводка</h2><div class="kpis">{kpi_html}</div></section>'
        f'<section id="registry"><h2>Фичи</h2>{_registry_table(feats, coverage)}</section>'
        f'<section id="studies"><h2>Исследования</h2><ul class="tight">{st_links or "<li class=muted>пока нет</li>"}</ul></section>'
    )
    toc = [("summary", "Сводка", False), ("registry", "Фичи", False), ("studies", "Исследования", False)]
    return _page(title, toc, body, date.today().isoformat())


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _print_report(errors, warnings) -> None:
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")


def _registry_path(study_path: Path, explicit) -> Path:
    return Path(explicit) if explicit else study_path.parent / REGISTRY_NAME


def cmd_validate(args) -> int:
    path = Path(args.study)
    try:
        study = load_json(path)
        reg = load_json(_registry_path(path, args.registry))
    except DataError as e:
        print(f"ERROR {e}")
        return 1
    errors, warnings = validate_registry(reg)
    e2, w2 = validate_study(study, reg)
    errors += e2
    warnings += w2
    _print_report(errors, warnings)
    print(f"{'FAILED' if errors else 'OK'}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def cmd_render(args) -> int:
    path = Path(args.study)
    if cmd_validate(args):
        print("render skipped: fix the errors above")
        return 1
    study = load_json(path)
    reg = load_json(_registry_path(path, args.registry))
    out = Path(args.out) if args.out else path.with_suffix(".html")
    out.write_text(render_study(study, reg), encoding="utf-8")
    print(f"written: {out}")
    return 0


def cmd_registry(args) -> int:
    directory = Path(args.dir)
    path = Path(args.registry) if args.registry else directory / REGISTRY_NAME
    try:
        reg = load_json(path)
    except DataError as e:
        print(f"ERROR {e}")
        return 1
    errors, warnings = validate_registry(reg)
    _print_report(errors, warnings)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    studies = list(iter_studies(path.parent))
    out = Path(args.out) if args.out else path.with_suffix(".html")
    out.write_text(render_registry(reg, studies), encoding="utf-8")
    print(f"written: {out} ({len(reg['features'])} features, {len(studies)} studies)")
    return 0


def cmd_next_id(args) -> int:
    path = Path(args.registry) if args.registry else Path(args.dir) / REGISTRY_NAME
    try:
        reg = load_json(path)
    except DataError:
        print("F-001")
        return 0
    nums = [int(f["id"][2:]) for f in reg.get("features", []) if FEATURE_ID_RE.match(str(f.get("id", "")))]
    print(f"F-{(max(nums) + 1 if nums else 1):03d}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate and render competitor-analysis reports.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("validate", cmd_validate), ("render", cmd_render)):
        p = sub.add_parser(name)
        p.add_argument("study", help="path to dev/docs/market/<slug>.json")
        p.add_argument("--registry", help="registry path (default: feature-registry.json next to the study)")
        if name == "render":
            p.add_argument("--out", help="output html (default: <study>.html)")
        p.set_defaults(fn=fn)
    p = sub.add_parser("registry")
    p.add_argument("--dir", default=str(DEFAULT_DIR))
    p.add_argument("--registry")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_registry)
    p = sub.add_parser("next-id")
    p.add_argument("--dir", default=str(DEFAULT_DIR))
    p.add_argument("--registry")
    p.set_defaults(fn=cmd_next_id)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # cp866/cp437 consoles vs Cyrillic names
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
