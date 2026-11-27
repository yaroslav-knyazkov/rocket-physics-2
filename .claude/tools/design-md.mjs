#!/usr/bin/env node
// Wrapper around the Google Labs DESIGN.md CLI (@google/design.md), pinned to one version.
// Agents call this instead of `npx @google/design.md …`, so one narrow permission rule covers it:
//   Bash(node .claude/tools/design-md.mjs:*)
//
// Usage (from the project root):
//   node .claude/tools/design-md.mjs lint   [DESIGN.md]           zero errors expected
//   node .claude/tools/design-md.mjs export [DESIGN.md]           writes tokens.json + theme.css next to DESIGN.md
//   node .claude/tools/design-md.mjs diff   <old.md> [DESIGN.md]  regressions between two versions
//   node .claude/tools/design-md.mjs spec                         prints the format spec
// Default DESIGN.md: dev/design/DESIGN.md
//
// Why a wrapper:
// - the package's main binary is named `design.md`; on Windows that opens a Markdown file
//   instead of running — the `designmd` alias is used;
// - export output is written by this script, no shell redirection (`>`), which write-guard hooks block;
// - the version is pinned: a new release never runs unreviewed.

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const PKG = "@google/design.md@0.4.0";
const DEFAULT = "dev/design/DESIGN.md";
const [cmd, ...rest] = process.argv.slice(2);

function die(msg) { console.error("design-md: " + msg); process.exit(2); }

function mdPath(p) {
  const f = p || DEFAULT;
  if (!/\.md$/i.test(f)) die("expected a .md file, got: " + f);
  if (!existsSync(f)) die("file not found: " + f);
  if (/["%!^&|<>]/.test(f)) die("unsupported characters in path: " + f);
  const r = relative(process.cwd(), f);
  return r && !r.startsWith("..") ? r.replaceAll("\\", "/") : f;
}

function run(args, capture) {
  const win = process.platform === "win32";
  const full = ["-y", "-p", PKG, "designmd", ...args];
  // Windows: npx is a .cmd and needs a shell; quote every argument (paths may contain spaces)
  const r = win
    ? spawnSync("npx", full.map((a) => '"' + a + '"'), { shell: true, encoding: "utf8", stdio: capture ? ["ignore", "pipe", "inherit"] : "inherit" })
    : spawnSync("npx", full, { encoding: "utf8", stdio: capture ? ["ignore", "pipe", "inherit"] : "inherit" });
  if (r.error) die(r.error.message);
  return r;
}

// ---- tokens.css sync check ----
// tokens.css is hand-maintained (it also holds CSS-only tokens the DESIGN.md format has no place for),
// so nothing regenerates it. Instead, lint verifies that every colour of the DESIGN.md YAML exists in
// tokens.css as --<name> or --color-<name> with the same resolved value.
function yamlColors(md) {
  const text = readFileSync(md, "utf8");
  const fm = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!fm) return null;
  const out = {};
  let inColors = false;
  for (const line of fm[1].split(/\r?\n/)) {
    if (/^\S/.test(line)) { inColors = /^colors:\s*$/.test(line); continue; }
    if (!inColors) continue;
    const m = line.match(/^\s{2}([\w-]+):\s*"?([^"#\s][^"]*|#[0-9a-fA-F]{3,8})"?\s*(#.*)?$/);
    if (m) out[m[1]] = m[2].trim();
  }
  return out;
}
function cssVars(css) {
  const out = {};
  for (const m of readFileSync(css, "utf8").matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) out[m[1]] = m[2].trim();
  return out;
}
function resolve(v, get, depth = 0) {
  if (depth > 20 || v == null) return null;
  const ref = v.match(/^\{colors\.([\w-]+)\}$/) || v.match(/^var\((--[\w-]+)\)$/);
  if (ref) return resolve(get(ref[1]), get, depth + 1);
  return v.toLowerCase();
}
function checkTokensCss(md) {
  const css = join(dirname(md), "lab", "system", "tokens.css");
  if (!existsSync(css)) { console.log("tokens.css sync: skipped (no " + css.replaceAll("\\", "/") + ")"); return 0; }
  const colors = yamlColors(md);
  if (!colors) { console.log("tokens.css sync: skipped (no YAML front matter)"); return 0; }
  const vars = cssVars(css);
  const problems = [];
  for (const [name, value] of Object.entries(colors)) {
    const want = resolve(value, (n) => colors[n]);
    const cssName = ["--color-" + name, "--" + name].find((n) => n in vars);
    if (!cssName) { problems.push("missing  " + name + " (expected --color-" + name + " or --" + name + ")"); continue; }
    const have = resolve(vars[cssName], (n) => vars[n]);
    if (want && have && want !== have) problems.push("differs  " + name + ": DESIGN.md " + want + " vs " + cssName + " " + have);
  }
  const n = Object.keys(colors).length;
  if (!problems.length) { console.log("tokens.css sync: ok (" + n + " colours match)"); return 0; }
  console.error("tokens.css sync: " + problems.length + " problem(s) of " + n + " colours");
  for (const p of problems) console.error("  " + p);
  return 1;
}

switch (cmd) {
  case "lint": {
    const md = mdPath(rest[0]);
    const r = run(["lint", md]);
    const sync = checkTokensCss(md);
    process.exit((r.status ?? 1) || sync);
  }
  case "spec": {
    const r = run(["spec"]);
    process.exit(r.status ?? 1);
  }
  case "diff": {
    if (!rest[0]) die("usage: diff <old.md> [DESIGN.md]");
    const r = run(["diff", mdPath(rest[0]), mdPath(rest[1])]);
    process.exit(r.status ?? 1);
  }
  case "export": {
    const md = mdPath(rest[0]);
    const outs = [["dtcg", "tokens.json"], ["css-tailwind", "theme.css"]];
    for (const [format, name] of outs) {
      const r = run(["export", "--format", format, md], true);
      if (r.status !== 0) { console.error("design-md: export " + format + " failed (exit " + r.status + ")"); process.exit(r.status ?? 1); }
      if (!r.stdout.trim()) die("export " + format + " printed nothing");
      const out = join(dirname(md), name);
      writeFileSync(out, r.stdout);
      console.log("wrote " + out.replaceAll("\\", "/") + " (" + r.stdout.length + " bytes)");
    }
    process.exit(0);
  }
  default:
    die("unknown command «" + (cmd || "") + "». Use: lint | export | diff | spec");
}
