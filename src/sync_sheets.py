import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json
import glob
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime
from jira import JIRA

load_dotenv()

ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
CREDS_PATH  = os.path.join(ROOT_DIR, os.getenv("GOOGLE_CREDENTIALS_PATH"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
JIRA_URL   = os.getenv("JIRA_URL")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

# Google Sheets 연결
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds  = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
gc     = gspread.authorize(creds)
sh     = gc.open_by_key(SPREADSHEET_ID)

print("Google Sheets 연결 완료")

# Jira 연결
jira = JIRA(
    server=JIRA_URL,
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
)

# 최신 TC JSON 로드
tc_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "tc_*.json")))
tc_data  = []
if tc_files:
    with open(tc_files[-1], "r", encoding="utf-8") as f:
        tc_data = json.load(f)

# 최신 테스트 결과 JSON 로드
result_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "test_results_*.json")))
test_map = {}  # "test_mkqa_1::test_tc_001" -> outcome
if result_files:
    with open(result_files[-1], "r", encoding="utf-8") as f:
        report = json.load(f)
    for t in report.get("tests", []):
        nodeid = t["nodeid"]  # tests/test_mkqa_1.py::test_tc_001
        fname  = nodeid.split("/")[-1].split("::")[0].replace(".py", "")  # test_mkqa_1
        func   = nodeid.split("::")[-1] if "::" in nodeid else ""
        key    = f"{fname}::{func}"
        call   = t.get("call", {})
        longrepr = call.get("longrepr", "")
        short_err = longrepr.strip().split("\n")[-1][:100] if longrepr else ""
        test_map[key] = {"outcome": t["outcome"], "error": short_err}

# Jira 버그 조회
bug_issues = jira.search_issues(
    f'project={PROJECT_KEY} AND issuetype=Bug AND summary ~ "[자동버그]" ORDER BY created ASC',
    maxResults=100
)
# 버그 매핑: "MKQA-1::test_tc_001" -> bug_key
bug_map = {}
for b in bug_issues:
    s = b.fields.summary  # [자동버그] MKQA-1 / test_tc_001 - failed
    try:
        tc_key  = s.split("]")[1].strip().split("/")[0].strip()   # MKQA-1
        func    = s.split("/")[1].strip().split(" - ")[0].strip() # test_tc_001
        map_key = f"{tc_key}::{func}"
        bug_map[map_key] = b.key
    except:
        pass

now = datetime.now().strftime("%Y-%m-%d %H:%M")

# ── 시트 1: TC 실행 결과 ──────────────────────────────────────────
print("시트 작성 중: TC 실행 결과...")

try:
    ws1 = sh.worksheet("TC 실행 결과")
    ws1.clear()
except gspread.exceptions.WorksheetNotFound:
    ws1 = sh.add_worksheet(title="TC 실행 결과", rows=200, cols=10)

headers1 = ["TC ID", "Jira 티켓", "기능명", "테스트 항목", "사전 조건", "테스트 단계", "기대 결과", "실행 결과", "상태", "버그 티켓"]
rows1 = [headers1]

for item in tc_data:
    issue_key = item["issue_key"]   # MKQA-1
    summary   = item["summary"]
    tc_list   = item["test_cases"]

    file_key = f"test_{issue_key.lower().replace('-', '_')}"  # test_mkqa_1

    for tc in tc_list:
        tc_id    = tc.get("tc_id", "")
        subject  = tc.get("테스트항목", "")
        precond  = tc.get("사전조건", "")
        steps    = tc.get("테스트단계", "")
        expected = tc.get("기대결과", "")

        # 테스트 함수 매핑 (TC-001 → test_tc_001)
        tc_num   = tc_id.replace("TC-", "").zfill(3)
        func_key = f"test_tc_{tc_num}"
        map_key  = f"{file_key}::{func_key}"

        result_info = test_map.get(map_key, {})
        outcome  = result_info.get("outcome", "-")
        raw_error = result_info.get("error", "")

        if outcome == "passed":
            error = "-"
        elif "TimeoutError" in raw_error or "Timeout" in raw_error:
            error = "요소 미발견 (Timeout)"
        elif "AttributeError" in raw_error:
            error = "코드 오류 (AttributeError)"
        elif "AssertionError" in raw_error:
            error = "검증 실패 (AssertionError)"
        elif "fixture" in raw_error:
            error = "픽스처 오류 (fixture not found)"
        elif raw_error:
            error = f"오류 ({raw_error.split(':')[0].strip()})"
        else:
            error = "-"

        status_kr = {"passed": "PASS", "failed": "FAIL", "error": "ERROR"}.get(outcome, "-")

        bug_map_key = f"{issue_key}::{func_key}"
        bug_ticket  = bug_map.get(bug_map_key, "-")

        jira_link   = f'=HYPERLINK("{JIRA_URL}/browse/{issue_key}", "{issue_key}")'
        bug_link    = f'=HYPERLINK("{JIRA_URL}/browse/{bug_ticket}", "{bug_ticket}")' if bug_ticket != "-" else "-"

        rows1.append([
            tc_id, jira_link, summary, subject,
            precond, steps, expected,
            error if error else outcome,
            status_kr,
            bug_link
        ])

ws1.update(rows1, value_input_option="USER_ENTERED")

# 헤더 스타일
ws1.format("A1:J1", {
    "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
    "horizontalAlignment": "CENTER"
})

# PASS/FAIL 색상
all_rows = ws1.get_all_values()
for i, row in enumerate(all_rows[1:], start=2):
    status = row[8] if len(row) > 8 else ""
    if status == "PASS":
        ws1.format(f"I{i}", {"backgroundColor": {"red": 0.7, "green": 0.9, "blue": 0.7}})
    elif status in ("FAIL", "ERROR"):
        ws1.format(f"I{i}", {"backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8}})

print(f"  [OK] TC 실행 결과: {len(rows1)-1}행 작성")

# ── 시트 2: 요약 ──────────────────────────────────────────────────
print("시트 작성 중: 요약...")

try:
    ws2 = sh.worksheet("요약")
    ws2.clear()
except gspread.exceptions.WorksheetNotFound:
    ws2 = sh.add_worksheet(title="요약", rows=30, cols=4)

total  = sum(1 for r in rows1[1:] if r[8] != "-")
passed = sum(1 for r in rows1[1:] if r[8] == "PASS")
failed = sum(1 for r in rows1[1:] if r[8] in ("FAIL", "ERROR"))
pass_rate = round(passed / total * 100) if total > 0 else 0

summary_rows = [
    ["MKQA QA 자동화 결과 요약", "", "", ""],
    ["생성일시", now, "", ""],
    ["", "", "", ""],
    ["항목", "값", "", ""],
    ["전체 TC 수", total, "", ""],
    ["통과 (PASS)", passed, "", ""],
    ["실패 (FAIL/ERROR)", failed, "", ""],
    ["통과율", f"{pass_rate}%", "", ""],
    ["자동 등록 버그", len(bug_issues), "", ""],
    ["", "", "", ""],
    ["Jira 프로젝트", f"{JIRA_URL}/jira/software/projects/{PROJECT_KEY}/boards", "", ""],
]

ws2.update(summary_rows, value_input_option="RAW")
ws2.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
ws2.format("A4:B4", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

print(f"  [OK] 요약 시트 작성 완료")

# 기본 시트 이름 변경 (Sheet1 → 삭제)
try:
    default = sh.worksheet("Sheet1")
    sh.del_worksheet(default)
except:
    pass

print(f"\n[OK] Google Sheets 동기화 완료!")
print(f"     {SPREADSHEET_ID}")
