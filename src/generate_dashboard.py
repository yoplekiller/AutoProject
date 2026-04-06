import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from jira import JIRA
from dotenv import load_dotenv
import os
import json
import glob
from datetime import datetime

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

jira = JIRA(
    server=os.getenv("JIRA_URL"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
)
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_URL    = os.getenv("JIRA_URL")

print("Jira 데이터 수집 중...")

tc_issues = jira.search_issues(
    f'project={PROJECT_KEY} AND issuetype != Bug ORDER BY created ASC', maxResults=50
)
bug_issues = jira.search_issues(
    f'project={PROJECT_KEY} AND issuetype=Bug AND summary ~ "[자동버그]" ORDER BY created ASC', maxResults=100
)

# 테스트 결과 JSON
result_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "test_results_*.json")))
test_results = []
test_summary = {"total": 0, "passed": 0, "failed": 0, "error": 0, "file": "-"}

if result_files:
    with open(result_files[-1], "r", encoding="utf-8") as f:
        report = json.load(f)
    test_results = report.get("tests", [])
    s = report.get("summary", {})
    test_summary = {
        "total":   s.get("total", 0),
        "passed":  s.get("passed", 0),
        "failed":  s.get("failed", 0),
        "error":   s.get("error", 0),
        "file":    os.path.basename(result_files[-1]),
    }

total   = test_summary["total"]
passed  = test_summary["passed"]
failed  = test_summary["failed"] + test_summary["error"]
pass_pct = round(passed / total * 100) if total > 0 else 0
fail_pct = 100 - pass_pct

# TC별 버그 그룹핑
def extract_tc_key(bug_summary):
    try:
        return bug_summary.split("]")[1].strip().split("/")[0].strip()
    except:
        return "UNKNOWN"

bugs_by_tc = {}
for bug in bug_issues:
    k = extract_tc_key(bug.fields.summary)
    bugs_by_tc.setdefault(k, []).append(bug)

now = datetime.now().strftime("%Y-%m-%d %H:%M")

# 도넛 차트 SVG (순수 SVG, 외부 의존 없음)
def donut_svg(pass_p, fail_p, size=160):
    r = 54
    cx = cy = size // 2
    circumference = 2 * 3.14159 * r
    pass_dash = circumference * pass_p / 100
    fail_dash = circumference * fail_p / 100
    # pass arc (green), fail arc (red)
    pass_offset = 0
    fail_offset = -(circumference - pass_dash)
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#f0f2f5" stroke-width="18"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#51cf66" stroke-width="18"
    stroke-dasharray="{pass_dash:.1f} {circumference:.1f}"
    stroke-dashoffset="0"
    transform="rotate(-90 {cx} {cy})"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#ff6b6b" stroke-width="18"
    stroke-dasharray="{fail_dash:.1f} {circumference:.1f}"
    stroke-dashoffset="{fail_offset:.1f}"
    transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="22" font-weight="700" fill="#1a1a2e">{pass_p}%</text>
  <text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="11" fill="#868e96">통과율</text>
</svg>"""

# 테스트 결과 행
test_rows = ""
for t in test_results:
    nodeid  = t["nodeid"]
    outcome = t["outcome"]
    fname   = nodeid.split("/")[-1].split("::")[0]
    func    = nodeid.split("::")[-1] if "::" in nodeid else nodeid
    call    = t.get("call", {})
    longrepr = call.get("longrepr", "")
    short_err = longrepr.strip().split("\n")[-1][:80] if longrepr else "-"
    dur = t.get("call", {}).get("duration", 0)
    dur_str = f"{dur:.1f}s" if dur else "-"

    if outcome == "passed":
        badge = '<span class="badge pass">PASSED</span>'
    elif outcome == "failed":
        badge = '<span class="badge fail">FAILED</span>'
    else:
        badge = '<span class="badge error">ERROR</span>'

    test_rows += f"""<tr>
      <td class="mono">{fname}</td>
      <td class="mono">{func}</td>
      <td>{badge}</td>
      <td class="dur">{dur_str}</td>
      <td class="err-msg">{short_err}</td>
    </tr>"""

# TC 요약 행
tc_rows = ""
for tc in tc_issues:
    tc_bugs = bugs_by_tc.get(tc.key, [])
    bug_count = len(tc_bugs)
    bug_cell = ""
    for b in tc_bugs:
        func_part = b.fields.summary.split("/")[-1].strip().split(" - ")[0].strip()
        bug_cell += f'<a href="{JIRA_URL}/browse/{b.key}" target="_blank" class="bug-chip">{b.key}</a>'
    tc_rows += f"""<tr>
      <td><a href="{JIRA_URL}/browse/{tc.key}" target="_blank" class="jira-link">{tc.key}</a></td>
      <td>{tc.fields.summary}</td>
      <td><span class="badge {'fail' if bug_count > 0 else 'pass'}">{bug_count}건</span></td>
      <td>{bug_cell if bug_cell else '<span class="none">-</span>'}</td>
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MKQA Test Report</title>
<style>
:root {{
  --pass:   #51cf66;
  --fail:   #ff6b6b;
  --warn:   #ffa94d;
  --blue:   #339af0;
  --bg:     #f8f9fa;
  --card:   #ffffff;
  --border: #e9ecef;
  --text:   #212529;
  --muted:  #868e96;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: var(--bg); color: var(--text); font-size: 14px; }}

/* NAV */
.nav {{ background: #fff; border-bottom: 1px solid var(--border);
       padding: 0 32px; display: flex; align-items: center; height: 52px; gap: 24px; }}
.nav-logo {{ font-weight: 700; font-size: 15px; color: var(--text); }}
.nav-logo span {{ color: var(--blue); }}
.nav-meta {{ font-size: 12px; color: var(--muted); margin-left: auto; }}

/* LAYOUT */
.wrap {{ max-width: 1200px; margin: 0 auto; padding: 28px 24px; }}

/* SUMMARY ROW */
.summary-row {{ display: grid; grid-template-columns: 200px 1fr; gap: 20px; margin-bottom: 24px; }}
.donut-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
              padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; }}
.donut-legend {{ display: flex; gap: 16px; font-size: 12px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 4px; }}

.stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
.stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
             padding: 20px 24px; }}
.stat-label {{ font-size: 11px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 0.6px; color: var(--muted); margin-bottom: 8px; }}
.stat-value {{ font-size: 32px; font-weight: 700; line-height: 1; }}
.stat-sub {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}
.v-pass {{ color: var(--pass); }}
.v-fail {{ color: var(--fail); }}
.v-warn {{ color: var(--warn); }}
.v-blue {{ color: var(--blue); }}

/* PROGRESS BAR */
.progress-wrap {{ margin-top: 10px; }}
.progress {{ height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }}
.progress-fill {{ height: 100%; border-radius: 3px; }}

/* SECTION */
.section {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
           margin-bottom: 20px; overflow: hidden; }}
.section-head {{ padding: 14px 20px; border-bottom: 1px solid var(--border);
                display: flex; align-items: center; justify-content: space-between; }}
.section-title {{ font-size: 13px; font-weight: 600; }}
.section-count {{ font-size: 12px; color: var(--muted);
                 background: var(--bg); padding: 2px 10px; border-radius: 10px; }}

/* TABLE */
table {{ width: 100%; border-collapse: collapse; }}
th {{ padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600;
     text-transform: uppercase; letter-spacing: 0.4px; color: var(--muted);
     background: var(--bg); border-bottom: 1px solid var(--border); }}
td {{ padding: 11px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: #f8f9fa; }}
.mono {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; }}
.dur  {{ color: var(--muted); font-size: 12px; }}
.err-msg {{ font-size: 11px; color: var(--muted); max-width: 340px;
           overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.none {{ color: #ced4da; }}

/* BADGES */
.badge {{ display: inline-block; padding: 2px 9px; border-radius: 4px;
         font-size: 11px; font-weight: 600; letter-spacing: 0.3px; }}
.badge.pass  {{ background: #ebfbee; color: #2f9e44; }}
.badge.fail  {{ background: #fff5f5; color: #e03131; }}
.badge.error {{ background: #fff9db; color: #e67700; }}

/* LINKS */
.jira-link {{ color: var(--blue); text-decoration: none; font-weight: 600; }}
.jira-link:hover {{ text-decoration: underline; }}
.bug-chip {{ display: inline-block; margin: 1px 3px; padding: 1px 7px;
            background: #fff5f5; border: 1px solid #ffc9c9; border-radius: 3px;
            font-size: 11px; color: #c92a2a; text-decoration: none; }}
.bug-chip:hover {{ background: #ffe3e3; }}

/* FOOTER */
.footer {{ text-align: center; padding: 20px; font-size: 11px; color: var(--muted); }}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-logo">Auto<span>Project</span> &nbsp;·&nbsp; MKQA Test Report</div>
  <div class="nav-meta">생성: {now} &nbsp;|&nbsp; {test_summary['file']}</div>
</nav>

<div class="wrap">

  <!-- SUMMARY ROW -->
  <div class="summary-row">
    <div class="donut-card">
      {donut_svg(pass_pct, fail_pct)}
      <div class="donut-legend">
        <span><span class="legend-dot" style="background:var(--pass)"></span>통과 {passed}</span>
        <span><span class="legend-dot" style="background:var(--fail)"></span>실패 {failed}</span>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Tests</div>
        <div class="stat-value v-blue">{total}</div>
        <div class="stat-sub">전체 테스트 케이스</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Passed</div>
        <div class="stat-value v-pass">{passed}</div>
        <div class="progress-wrap">
          <div class="progress"><div class="progress-fill" style="width:{pass_pct}%;background:var(--pass)"></div></div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Failed</div>
        <div class="stat-value v-fail">{test_summary['failed']}</div>
        <div class="stat-sub">에러 {test_summary['error']}건 포함</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Bugs Created</div>
        <div class="stat-value v-warn">{len(bug_issues)}</div>
        <div class="stat-sub">Jira 자동 등록</div>
      </div>
    </div>
  </div>

  <!-- TEST RESULTS TABLE -->
  <div class="section">
    <div class="section-head">
      <div class="section-title">Test Results</div>
      <div class="section-count">{total}건</div>
    </div>
    <table>
      <thead>
        <tr>
          <th>파일</th>
          <th>테스트 함수</th>
          <th>결과</th>
          <th>시간</th>
          <th>에러 요약</th>
        </tr>
      </thead>
      <tbody>{test_rows}</tbody>
    </table>
  </div>

  <!-- TC / BUG MAPPING -->
  <div class="section">
    <div class="section-head">
      <div class="section-title">TC 티켓별 버그 현황</div>
      <div class="section-count">{len(tc_issues)}개 기능</div>
    </div>
    <table>
      <thead>
        <tr>
          <th>티켓</th>
          <th>기능</th>
          <th>버그 수</th>
          <th>자동 등록된 버그</th>
        </tr>
      </thead>
      <tbody>{tc_rows}</tbody>
    </table>
  </div>

</div>

<div class="footer">AutoProject · AI 기반 QA 자동화 파이프라인 · {now}</div>
</body>
</html>"""

output_path = os.path.join(REPORTS_DIR, f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] 대시보드 생성 완료: {output_path}")
