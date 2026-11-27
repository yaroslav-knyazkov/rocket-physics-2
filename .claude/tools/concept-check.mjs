// Self-check of the clickable concept model (dev/concept/app) in a headless browser.
//
//   node .claude/tools/concept-check.mjs [appDir] [--shot <screen>[,<screen>...]] [--out <dir>]
//
//   appDir   folder with index.html (default: dev/concept/app)
//   --shot   also save 1280x800 screenshots of these screens (route names, e.g. tasks,task?id=t1)
//   --out    where screenshots go (default: <appDir>/../shots)
//
// Opens index.html#/_check — the runtime (concept.js) crawls the model from the start screen and
// reports: screens that throw, links to missing screens, actions without handlers, dead controls.
// Exit codes: 0 = check OK, 1 = the model has errors, 2 = the check could not run
// (no browser, page did not render). Needs Microsoft Edge or Google Chrome; another Chromium —
// set CONCEPT_BROWSER to its path.
import { existsSync, mkdirSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import os from "node:os";

const args = process.argv.slice(2);
function option(name) {
  const i = args.indexOf(name);
  if (i < 0) return null;
  const value = args[i + 1];
  args.splice(i, 2);
  return value || "";
}
const shots = (option("--shot") || "").split(",").map((s) => s.trim()).filter(Boolean);
const outArg = option("--out");
const appDir = resolve(args[0] || "dev/concept/app");
const outDir = resolve(outArg || join(appDir, "..", "shots"));
const index = join(appDir, "index.html");

if (!existsSync(index)) {
  console.error("No index.html in " + appDir);
  process.exit(2);
}

const BROWSERS = [
  process.env.CONCEPT_BROWSER,
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/microsoft-edge",
].filter(Boolean);
const browser = BROWSERS.find((p) => existsSync(p));
if (!browser) {
  console.error("No Edge/Chrome found. Set CONCEPT_BROWSER to a Chromium-based browser binary.");
  process.exit(2);
}

const base = pathToFileURL(index).href;
const profile = join(os.tmpdir(), "concept-check-" + process.pid);

function run(extra, route) {
  return spawnSync(
    browser,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--user-data-dir=" + profile,
      "--virtual-time-budget=3000",
      ...extra,
      base + "#/" + route,
    ],
    { timeout: 45000, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }
  );
}

function decode(text) {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

let code = 2;
try {
  const res = run(["--dump-dom"], "_check");
  const dom = res.stdout || "";
  const scriptError = dom.match(/<div id="concept-error">([\s\S]*?)<\/div>/);
  const report = dom.match(/<pre id="concept-check" data-check="(ok|fail)">([\s\S]*?)<\/pre>/);

  if (scriptError) {
    console.log("SCRIPT ERROR: " + decode(scriptError[1]));
    console.log("  (file:// hides the details — run `node --check <file>` on data.js and each screens*.js)");
  }
  if (report) {
    console.log(decode(report[2]));
    code = report[1] === "ok" && !scriptError ? 0 : 1;
  } else {
    console.error(
      "The check page did not render" +
        (res.error ? " (" + (res.error.code || res.error.message) + ")" : "") +
        ". Open " + index + " in a browser and look at the console."
    );
    code = scriptError ? 1 : 2;
  }

  if (shots.length) {
    mkdirSync(outDir, { recursive: true });
    for (const route of shots) {
      const file = join(outDir, route.replace(/[^A-Za-z0-9_-]+/g, "_") + ".png");
      rmSync(file, { force: true });
      const shot = run(["--window-size=1280,800", "--screenshot=" + file], route);
      const done = existsSync(file) && !shot.error;
      console.log((done ? "shot  " : "FAIL  ") + route + (done ? "  -> " + file : ""));
    }
  }
} finally {
  rmSync(profile, { recursive: true, force: true });
}
process.exit(code);
