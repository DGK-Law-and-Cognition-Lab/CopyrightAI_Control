#!/usr/bin/env python3
"""Run complete test-mode sessions of a study in headless Chrome and save their CSVs.

    python3 tools/run_headless_tests.py --study B1 --out DIR [--jobs 6]
    python3 tools/run_headless_tests.py --study A1 --out DIR [--jobs 6]

Copies the study folder to a temporary site (so the real open_rows.json is
never touched), serves it on 127.0.0.1, and opens index.html?test=1&... once
per scenario in headless Google Chrome. Test mode answers every page
automatically and puts the session's CSV (the same text the page saves or
downloads) into the page, where this script reads it. Scenarios, B1:
  * one code for every row (code mod 24 = k), covering all three option orders;
  * a closed-rows file (only some rows open), where the row is open[code mod n];
  * a forced row (?row=), a non-numeric PILOT id, and the early exits and
    failures (?test_fail=comp, comp1, captcha, instructed, recall, decline);
  * the timing-gate remedy (control and the "would" block dropped).
A1:
  * 120 codes, 10a + k for a = 0 to 11 and list k = 0 to 9, which give every
    combination of list, option order (floor(code/10) mod 3), creativity-item
    order (floor(code/30) mod 2) and story-recall trial (floor(code/60) mod 2);
  * a closed-rows file, a forced row, a non-numeric PILOT id, every early exit
    and failure, and the timing-gate remedy (the "would" block dropped).
  Each complete A1 session walks every page of the 1 November 2026 revision
  (engine 1.4.0, config 1.5.0): the story page, first-image page, change
  page, question page and written-reason page (below the quoted decision) of
  every trial, the two end scales, the
  follow-up section (introductory page, then for slots 6 and 7 the "would"
  page and the stop-others page), the rule, the story-recall page and the end
  pages; in the timing-gate scenario the "would" pages are skipped.
  Each complete B1 session (engine 1.5.0, config 1.1.0) walks the prompt page,
  the page of what was done with the image, the question page and the
  written-reason page of all twelve trials, story recall about the last trial,
  the "would" block and the end pages with the two scales.
Then run tools/test_formulas_B1.py or tools/test_formulas_A1.py --csv-dir DIR.
"""
import argparse
import concurrent.futures as cf
import functools
import html
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    handler = functools.partial(Quiet, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def run_one(port, query, prof):
    url = f"http://127.0.0.1:{port}/index.html?{query}"
    try:
        out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                              f"--user-data-dir={prof}", "--virtual-time-budget=120000", "--dump-dom", url],
                             capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:      # a heavily loaded machine; reported as no output
        return None
    m = re.search(r'<pre id="csv-dump"[^>]*>(.*?)</pre>', out.stdout, re.S)
    return html.unescape(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default="B1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pb_headless_"))

    site_all = tmp / "site_all"
    shutil.copytree(HERE / a.study, site_all)
    site_part = tmp / "site_part"
    shutil.copytree(HERE / a.study, site_part)
    partial_open = [1, 4, 5, 9, 13, 22, 23] if a.study == "B1" else [0, 3, 4, 7, 9]
    (site_part / "open_rows.json").write_text(json.dumps({"open_rows": partial_open, "updated": "test"}))
    site_drop = tmp / "site_drop"
    shutil.copytree(HERE / a.study, site_drop)
    cfg = (site_drop / "config.js").read_text(encoding="utf-8")
    drop = "['control', 'would_block']" if a.study == "B1" else "['would_block']"
    assert "var DROP_ITEMS = [];" in cfg
    (site_drop / "config.js").write_text(cfg.replace("var DROP_ITEMS = [];", f"var DROP_ITEMS = {drop};"), encoding="utf-8")

    servers = {}
    for name, d in [("all", site_all), ("part", site_part), ("drop", site_drop)]:
        servers[name] = serve(d)

    scen = []
    if a.study == "A1":
        # code = 120 * 90 + 10a + k: list k (all ten open), and a = 0..11 gives every
        # combination of option order, creativity-item order and story-recall trial.
        for k in range(10):
            for aa in range(12):
                code = 10800 + 10 * aa + k
                scen.append(("all", f"rows_k{k}_a{aa:02d}_code{code}", f"test=1&code={code}"))
        for code in [10007, 20011, 30013, 40009, 51234, 60001, 77777]:
            scen.append(("part", f"partial_code{code}", f"test=1&code={code}"))
        scen += [
            ("all", "forced_row7_code12345", "test=1&code=12345&row=7"),
            ("all", "pilot_nonnumeric", "test=1&participant=PILOT_HEADLESS1"),
            ("all", "fail_comp_code23456", "test=1&code=23456&test_fail=comp"),
            ("all", "fail_comp1_code23457", "test=1&code=23457&test_fail=comp1"),
            ("all", "fail_captcha_code23458", "test=1&code=23458&test_fail=captcha"),
            ("all", "fail_instructed_code23459", "test=1&code=23459&test_fail=instructed"),
            ("all", "fail_recall_code23460", "test=1&code=23460&test_fail=recall"),
            ("all", "decline_code23461", "test=1&code=23461&test_fail=decline"),
            ("drop", "drop_would_code34567", "test=1&code=34567"),
        ]
    else:
        # Every row with all rows open: code = 24 * m + k, m chosen so the three option orders all occur.
        for k in range(24):
            m = 400 + k            # floor(code/24) = m, so option order index = m mod 3
            scen.append(("all", f"rows_k{k:02d}_code{24 * m + k}", f"test=1&code={24 * m + k}"))
        for code in [10007, 20011, 30013, 40009, 51234, 60001, 77777]:
            scen.append(("part", f"partial_code{code}", f"test=1&code={code}"))
        scen += [
            ("all", "forced_row17_code12345", "test=1&code=12345&row=17"),
            ("all", "pilot_nonnumeric", "test=1&participant=PILOT_HEADLESS1"),
            ("all", "fail_comp_code23456", "test=1&code=23456&test_fail=comp"),
            ("all", "fail_comp1_code23457", "test=1&code=23457&test_fail=comp1"),
            ("all", "fail_captcha_code23458", "test=1&code=23458&test_fail=captcha"),
            ("all", "fail_instructed_code23459", "test=1&code=23459&test_fail=instructed"),
            ("all", "fail_recall_code23460", "test=1&code=23460&test_fail=recall"),
            ("all", "decline_code23461", "test=1&code=23461&test_fail=decline"),
            ("drop", "drop_control_would_code34567", "test=1&code=34567"),
        ]

    def job(i, s):
        site, name, q = s
        prof = tmp / f"prof{i % a.jobs}_{i}"
        csv_text = run_one(servers[site][1], q, prof)
        return name, q, csv_text

    results = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for name, q, csv_text in ex.map(lambda p: job(*p), enumerate(scen)):
            if csv_text is None:
                print(f"NO OUTPUT  {name}  ({q})")
            elif csv_text.strip() == "DECLINED":
                print(f"declined   {name}  (nothing saved, as intended)")
            else:
                (out / f"{name}.csv").write_text(csv_text, encoding="utf-8")
                print(f"saved      {name}.csv  ({len(csv_text.splitlines()) - 1} rows)")
            results.append((name, csv_text is not None))
    for srv, _ in servers.values():
        srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(ok for _, ok in results)} of {len(results)} scenarios produced output; CSVs in {out}")


if __name__ == "__main__":
    main()
