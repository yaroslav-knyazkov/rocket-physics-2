/* Concept runtime — the shared shell of the clickable concept model.
 * Kit file: copied into dev/concept/app/ as is. Do not edit it per project —
 * the project lives in data.js and screens.js.
 *
 * Works from file:// (double-click index.html): classic scripts only, no modules, no fetch.
 *
 *   Concept.setup({ project, version, start, nav })     nav: "top" | "side" | "none"
 *   Concept.screen({ id, name, title, note, nav, parent, sample, render(ctx), actions })
 *   Concept.scenario({ title, steps: ["text", { text, go: "name?x=1" }] })
 *
 *   ctx = { data, params, go(name, params), href(name, params), toast(msg), esc(v), uid() }
 *
 * Markup conventions inside render():
 *   <a href="#/order?id=3">            go to a screen
 *   <button data-go="order?id=3">      the same on a non-link
 *   <button data-action="remove" data-id="3">   calls actions.remove(ctx, {id:"3"}, el), then re-renders
 *   <form data-submit="create">        calls actions.create(ctx, {field: value, ...}, form), then re-renders
 *   <button data-stub="Экспорт в PDF"> drawn but not wired: a click says so
 *
 * Built-in screens: #/_map (screens + scenarios), #/_check (self-check, machine-readable).
 */
(function () {
  "use strict";

  var screens = {};
  var order = [];
  var scenarios = [];
  var problems = [];
  var cfg = { project: "Проект", version: "v1", start: null, nav: "top" };
  var state = null;
  var lastRoute = null;
  var uidCounter = 0;
  var toastTimer = null;
  var KEY = "concept:" + location.pathname;

  // ---------------------------------------------------------------- helpers

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function clone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function uid() {
    uidCounter += 1;
    return "n" + Date.now().toString(36) + uidCounter;
  }

  function seed() {
    return clone(window.CONCEPT_DATA || {});
  }

  // Saved state is tied to the concept version: a new round with a new seed starts clean.
  function load() {
    try {
      var saved = JSON.parse(localStorage.getItem(KEY) || "null");
      if (saved && saved.version === cfg.version) return saved.data;
    } catch (e) { /* storage unavailable — in-memory only */ }
    return seed();
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify({ version: cfg.version, data: state }));
    } catch (e) { /* storage unavailable — in-memory only */ }
  }

  function parse(hash) {
    var h = String(hash || "").replace(/^#\/?/, "");
    var q = h.indexOf("?");
    var params = {};
    if (q >= 0) {
      h.slice(q + 1).split("&").forEach(function (pair) {
        if (!pair) return;
        var i = pair.indexOf("=");
        try {
          params[decodeURIComponent(i < 0 ? pair : pair.slice(0, i))] =
            i < 0 ? "" : decodeURIComponent(pair.slice(i + 1));
        } catch (e) { /* malformed escape — skip the pair */ }
      });
    }
    return { name: q < 0 ? h : h.slice(0, q), params: params };
  }

  function href(name, params) {
    var q = Object.keys(params || {}).map(function (k) {
      return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]);
    }).join("&");
    return "#/" + name + (q ? (name.indexOf("?") < 0 ? "?" : "&") + q : "");
  }

  function go(name, params) {
    location.hash = href(name, params);
  }

  function toast(msg) {
    var el = document.getElementById("concept-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "concept-toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = "is-on";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.className = ""; }, 2800);
  }

  function ctx(params, data) {
    return { data: data || state, params: params || {}, go: go, href: href, toast: toast, esc: esc, uid: uid };
  }

  function startName() {
    return cfg.start && screens[cfg.start] ? cfg.start : order[0];
  }

  function currentRoute() {
    var route = parse(location.hash);
    if (!route.name) route.name = startName() || "_map";
    return route;
  }

  function inspect(html) {
    var box = document.createElement("div");
    box.innerHTML = html;
    return box;
  }

  // ----------------------------------------------------------- registration

  function setup(options) {
    Object.keys(options || {}).forEach(function (k) { cfg[k] = options[k]; });
  }

  function screen(def) {
    if (!def || !def.name || !def.id || !def.title || typeof def.render !== "function") {
      problems.push("screen registered without name/id/title/render: " +
        JSON.stringify(def && (def.name || def.id || def.title) || null));
      return;
    }
    if (/^_/.test(def.name)) problems.push(def.id + ": screen name must not start with '_' (" + def.name + ")");
    if (order.some(function (n) { return screens[n].id === def.id; })) problems.push("duplicate screen id: " + def.id);
    if (screens[def.name]) {
      problems.push("duplicate screen name: " + def.name);
      return;
    }
    screens[def.name] = def;
    order.push(def.name);
  }

  function scenario(def) {
    if (def && def.title && def.steps && def.steps.length) scenarios.push(def);
    else problems.push("scenario registered without title/steps");
  }

  // ----------------------------------------------------------------- render

  function drawBar(label) {
    document.getElementById("concept-bar").innerHTML =
      '<span class="cb-tag">КОНЦЕПЦИЯ ' + esc(cfg.version) + "</span>" +
      '<span class="cb-project">' + esc(cfg.project) + "</span>" +
      '<span class="cb-screen">' + esc(label) + "</span>" +
      '<span class="cb-spacer"></span>' +
      '<a href="#/' + esc(startName() || "_map") + '">В начало</a>' +
      '<a href="#/_map">Карта экранов</a>' +
      '<button type="button" data-concept-reset>Сбросить данные</button>';
  }

  function drawNav(current) {
    var items = order.filter(function (n) { return screens[n].nav; });
    var active = (screens[current] && screens[current].parent) || current;
    document.body.className = "nav-" + (items.length ? cfg.nav : "none");
    document.getElementById("concept-nav").innerHTML = items.map(function (n) {
      var d = screens[n];
      return '<a href="#/' + esc(n) + '"' + (n === active ? ' class="is-current"' : "") + ">" +
        esc(d.nav === true ? d.title : d.nav) + "</a>";
    }).join("");
  }

  function errorBox(def, e) {
    return '<div class="c-error"><b>' + esc(def.id) + ": экран упал при отрисовке</b><br>" +
      esc(e && e.message) + "</div>";
  }

  function render() {
    var route = currentRoute();
    var def = screens[route.name];
    var html, label;

    if (route.name === "_map") {
      html = mapView();
      label = "Карта экранов";
    } else if (route.name === "_check") {
      var result = check();
      html = checkView(result);
      label = "Проверка: " + (result.errors.length ? "ошибок " + result.errors.length : "OK");
    } else if (!def) {
      html = '<div class="c-empty">Экрана «' + esc(route.name) + '» в модели нет. <a href="#/_map">Карта экранов</a></div>';
      label = "нет экрана";
    } else {
      try { html = def.render(ctx(route.params)); } catch (e) { html = errorBox(def, e); }
      label = def.id + " · " + def.title;
    }

    var app = document.getElementById("concept-app");
    app.innerHTML = html;
    app.setAttribute("data-screen", route.name);
    drawBar(label);
    drawNav(route.name);
    document.title = label + " — " + cfg.project + " (концепция)";

    var key = location.hash;
    if (key !== lastRoute) window.scrollTo(0, 0);
    lastRoute = key;
  }

  // ---------------------------------------------------------- built-in: map

  function mapView() {
    var rows = order.map(function (n) {
      var d = screens[n];
      var stubs;
      try {
        stubs = inspect(d.render(ctx(d.sample || {}, seed()))).querySelectorAll("[data-stub]").length;
      } catch (e) {
        stubs = "ошибка";
      }
      return "<tr><td><b>" + esc(d.id) + "</b></td>" +
        '<td><a href="' + esc(href(n, d.sample)) + '">' + esc(d.title) + "</a></td>" +
        "<td>" + esc(d.note || "") + "</td><td>" + stubs + "</td></tr>";
    }).join("");

    var flows = scenarios.map(function (s, i) {
      var steps = s.steps.map(function (step) {
        var text = typeof step === "string" ? step : step.text;
        var link = step && step.go ? ' <a href="#/' + esc(step.go) + '">открыть</a>' : "";
        return "<li>" + esc(text) + link + "</li>";
      }).join("");
      return '<div class="c-card"><b>Сценарий ' + (i + 1) + ". " + esc(s.title) + "</b><ol>" + steps + "</ol></div>";
    }).join("");

    return "<h1>Карта экранов</h1>" +
      '<p class="c-muted">В замечаниях называйте экран по ID: «на S3 не хватает фильтра по дате». ' +
      "Пунктирная рамка — заглушка: элемент нарисован, но в концепции не работает.</p>" +
      '<table class="c-table"><thead><tr><th>ID</th><th>Экран</th><th>Что здесь</th><th>Заглушек</th></tr></thead>' +
      "<tbody>" + rows + "</tbody></table>" +
      "<h2>Сценарии для прокликивания</h2>" +
      (flows || '<p class="c-muted">Сценарии не заданы.</p>') +
      '<p class="c-muted"><a href="#/_check">Проверка модели</a> — для агентов: мёртвые кнопки, битые переходы.</p>';
  }

  // -------------------------------------------------------- built-in: check

  // Static crawl from the start screen: every screen renders, every link lands on a real screen,
  // every action has a handler, every clickable either works or is marked as a stub.
  function check() {
    var errors = {};
    var warnings = {};
    var seen = {};
    var reached = {};
    var stubsBy = {};
    var queue = [];
    var data = seed();
    var guard = 0;

    problems.forEach(function (p) { errors[p] = 1; });
    if (!order.length) errors["no screens registered (screens.js did not load or is empty)"] = 1;
    if (cfg.start && !screens[cfg.start]) errors["setup.start points to a missing screen: " + cfg.start] = 1;

    function visit(name, params, from) {
      if (name === "_map" || name === "_check") return;
      if (!screens[name]) {
        errors[from + ": link to a missing screen '" + name + "'"] = 1;
        return;
      }
      var key = href(name, params);
      if (seen[key]) return;
      seen[key] = 1;
      reached[name] = 1;
      queue.push({ name: name, params: params });
    }

    function wired(el, box) {
      for (var n = el; n && n !== box; n = n.parentNode) {
        if (n.hasAttribute("data-stub") || n.hasAttribute("data-action") || n.hasAttribute("data-go")) return true;
      }
      if (el.tagName === "A") return /^(#\/|https?:|mailto:|tel:)/.test(el.getAttribute("href") || "");
      var form = el.closest("form");
      return !!(form && form.hasAttribute("data-submit") && (el.getAttribute("type") || "submit") === "submit");
    }

    function scan(d, params) {
      var box;
      try {
        box = inspect(d.render(ctx(params, data)));
      } catch (e) {
        errors[d.id + " " + href(d.name, params) + ": render threw — " + (e && e.message)] = 1;
        return;
      }
      [].forEach.call(box.querySelectorAll('a[href^="#/"], [data-go]'), function (el) {
        var target = parse(el.hasAttribute("data-go") ? "#/" + el.getAttribute("data-go") : el.getAttribute("href"));
        visit(target.name, target.params, d.id);
      });
      [].forEach.call(box.querySelectorAll("[data-action], form[data-submit]"), function (el) {
        var name = el.getAttribute("data-action") || el.getAttribute("data-submit");
        if (!(d.actions && typeof d.actions[name] === "function")) {
          errors[d.id + ": no handler for '" + name + "' in actions"] = 1;
        }
      });
      [].forEach.call(box.querySelectorAll("form:not([data-submit])"), function () {
        errors[d.id + ": <form> without data-submit — wire it, or drop the form and mark the button data-stub"] = 1;
      });
      [].forEach.call(box.querySelectorAll("button, a, [role=button]"), function (el) {
        if (!wired(el, box)) {
          var text = (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40);
          errors[d.id + ": dead control '" + text + "' — wire it (href / data-go / data-action) or mark data-stub"] = 1;
        }
      });
      stubsBy[d.name] = Math.max(stubsBy[d.name] || 0, box.querySelectorAll("[data-stub]").length);
    }

    if (order.length) {
      visit(startName(), {}, "start");
      order.forEach(function (n) { if (screens[n].nav) visit(n, {}, "nav"); });
    }
    while (queue.length && guard < 600) {
      guard += 1;
      var r = queue.shift();
      scan(screens[r.name], r.params);
    }

    order.forEach(function (n) {
      if (reached[n]) return;
      warnings[screens[n].id + " (" + n + "): not reachable from the start screen — no link leads here"] = 1;
      scan(screens[n], screens[n].sample || {});
    });
    scenarios.forEach(function (s) {
      s.steps.forEach(function (step) {
        if (step && step.go && !screens[parse("#/" + step.go).name]) {
          errors["scenario '" + s.title + "': step opens a missing screen '" + step.go + "'"] = 1;
        }
      });
    });
    if (!scenarios.length) warnings["no scenarios registered — the user gets no guided path to click through"] = 1;

    return {
      errors: Object.keys(errors),
      warnings: Object.keys(warnings),
      screens: order.length,
      scenarios: scenarios.length,
      stubs: Object.keys(stubsBy).reduce(function (sum, n) { return sum + stubsBy[n]; }, 0)
    };
  }

  function checkView(r) {
    var ok = !r.errors.length;
    var lines = [
      "CHECK " + (ok ? "OK" : "FAIL"),
      "version: " + cfg.version,
      "screens: " + r.screens,
      "scenarios: " + r.scenarios,
      "stubs: " + r.stubs,
      "errors: " + r.errors.length
    ].concat(r.errors.map(function (e) { return "  - " + e; }))
      .concat(["warnings: " + r.warnings.length])
      .concat(r.warnings.map(function (w) { return "  - " + w; }));
    return "<h1>Проверка модели</h1>" +
      '<pre id="concept-check" data-check="' + (ok ? "ok" : "fail") + '">' + esc(lines.join("\n")) + "</pre>";
  }

  // ----------------------------------------------------------------- events

  function runAction(name, arg, el) {
    var route = currentRoute();
    var def = screens[route.name];
    var fn = def && def.actions && def.actions[name];
    if (typeof fn !== "function") {
      toast("Нет обработчика действия «" + name + "»");
      return;
    }
    var before = location.hash;
    try {
      fn(ctx(route.params), arg, el);
    } catch (e) {
      toast("Ошибка в действии «" + name + "»: " + (e && e.message));
      if (window.console) console.error(e);
    }
    save();
    if (location.hash === before) render();
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    if (t.closest("[data-concept-reset]")) {
      state = seed();
      save();
      toast("Данные сброшены к исходным");
      render();
      return;
    }
    var el = t.closest("[data-stub], [data-action], [data-go]");
    if (!el) return;
    ev.preventDefault();
    if (el.hasAttribute("data-stub")) {
      toast("Заглушка: " + (el.getAttribute("data-stub") || "в концепции не работает"));
    } else if (el.hasAttribute("data-action")) {
      runAction(el.getAttribute("data-action"), Object.assign({}, el.dataset), el);
    } else {
      go(el.getAttribute("data-go"));
    }
  });

  document.addEventListener("submit", function (ev) {
    var form = ev.target;
    ev.preventDefault();
    var name = form.getAttribute("data-submit");
    if (!name) {
      toast("Заглушка: форма в концепции не отправляется");
      return;
    }
    var values = {};
    new FormData(form).forEach(function (v, k) { values[k] = typeof v === "string" ? v : v.name; });
    runAction(name, values, form);
  });

  // A broken data.js / screens.js must be visible, not a blank page.
  window.addEventListener("error", function (ev) {
    var el = document.getElementById("concept-error");
    if (!el) {
      el = document.createElement("div");
      el.id = "concept-error";
      document.body.insertBefore(el, document.body.firstChild);
    }
    el.textContent = "Ошибка скрипта: " + ev.message + " (" +
      String(ev.filename || "").split("/").pop() + ":" + ev.lineno + ")";
  });

  function start() {
    state = load();
    window.addEventListener("hashchange", render);
    render();
  }

  var api = { setup: setup, screen: screen, scenario: scenario, go: go, href: href, toast: toast, esc: esc, uid: uid, check: check };
  Object.defineProperty(api, "data", { get: function () { return state; } });
  window.Concept = api;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
