---
description: Анализ аналогов по теме — HTML-отчёт (преимущества/недостатки аналогов, матрица фич) и пополнение реестра фич проекта. Без аргумента — стартовый (baseline) анализ всего продукта.
argument-hint: "[тема или задача, например «онбординг новых пользователей»]"
allowed-tools: Read, Glob, Grep, Agent, SendMessage, AskUserQuestion, Bash(python .claude/scripts/market_report.py:*)
---

Задача: провести анализ аналогов через агента **market-analyst** (процедура — `.claude/agents/orchestrator.md` § «Market analysis»).

Тема: $ARGUMENTS

1. Тема пустая:
   - если `dev/docs/market/baseline.json` ещё нет — это **baseline**: `kind: baseline`, `slug: baseline`, вопрос — идея продукта из `CLAUDE.md` § «О проекте» и `dev/docs/vision.md` (если есть, передай путь — список аналогов из него обязателен);
   - если baseline уже есть — спроси пользователя через `AskUserQuestion`: обновить baseline или исследовать конкретную тему.
2. Тема задана — **task**-исследование: `kind: task`, `slug` — латиницей из темы (`<stage-id>-<topic>`, если тема относится к текущей стадии; стадия — `python .claude/scripts/status_query.py current`), вопрос — тема пользователя дословно + 1-2 строки контекста стадии.
3. Вызови `market-analyst` (промпт на английском, тема пользователя — дословно). Выходная папка — `dev/docs/market/`; в worktree-режиме — та же папка внутри активного worktree и блок `wt.py prompt`.
4. По ответу: покажи пользователю **абсолютный путь** к `<slug>.html` (открыть в браузере), 3-5 ключевых выводов по-русски и вопросы аналитика. Для baseline — гейт «Отчёт принят / Добавить аналоги или поправить / Углубить» через `AskUserQuestion`; правки — `SendMessage` тому же агенту.
5. Запиши пути в `dev/status.json → artifacts` (`market_<slug>`, `feature_registry`) и строку в `decisions`, если пользователь что-то решил.
