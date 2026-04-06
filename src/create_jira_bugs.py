import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from jira import JIRA
from dotenv import load_dotenv
import os
import json
import glob

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

# Jira 클라이언트
jira = JIRA(
    server=os.getenv("JIRA_URL"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
)
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

# 가장 최신 test_results_*.json 로드
result_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "test_results_*.json")))
if not result_files:
    print("[ERROR] test_results 파일이 없습니다. run_tests.py 먼저 실행하세요.")
    exit()

latest = result_files[-1]
print(f"=== 결과 파일 로드: {latest} ===\n")

with open(latest, "r", encoding="utf-8") as f:
    report = json.load(f)

# 실패/에러 테스트만 필터링
failed_tests = [
    t for t in report.get("tests", [])
    if t.get("outcome") in ("failed", "error")
]

if not failed_tests:
    print("[OK] 실패 항목 없음 - 버그 티켓 생성 불필요")
    exit()

print(f"[실패 항목 {len(failed_tests)}건 -> Jira 버그 티켓 생성]\n")

# 기존 자동버그 티켓 조회 (중복 방지) - issue_key 기준
existing = jira.search_issues(
    f'project={PROJECT_KEY} AND issuetype=Bug AND summary ~ "[자동버그]" AND statusCategory != Done',
    maxResults=200
)
# "[자동버그] MKQA-1" 형태로 issue_key만 추출
existing_keys = set()
for issue in existing:
    parts = issue.fields.summary.split("]")
    if len(parts) > 1:
        key = parts[1].strip().split(" ")[0]  # e.g. "MKQA-1"
        existing_keys.add(key)
print(f"기존 버그 티켓 {len(existing_keys)}건 확인 (중복 스킵)\n")

created = []
skipped = []

for t in failed_tests:
    nodeid = t["nodeid"]  # e.g. tests/test_mkqa_1.py::test_tc_001
    outcome = t["outcome"]

    # 에러 메시지 추출
    call = t.get("call", {})
    longrepr = call.get("longrepr", "에러 메시지 없음")
    longrepr_short = longrepr[:2000] if len(longrepr) > 2000 else longrepr

    # 파일명에서 티켓 키 추론 (test_mkqa_1.py -> MKQA-1)
    filename = nodeid.split("/")[-1].split("::")[0]  # test_mkqa_1.py
    test_func = nodeid.split("::")[-1]               # test_tc_001

    raw = filename.replace("test_", "").replace(".py", "")  # mkqa_1
    issue_key = raw.upper().replace("_", "-", 1)            # MKQA-1

    summary = f"[자동버그] {issue_key} / {test_func} - {outcome}"

    # 중복 체크 (issue_key 기준)
    if issue_key in existing_keys:
        print(f"  [SKIP] 이미 존재: {summary}")
        skipped.append(summary)
        continue

    description = f"""*자동 생성 버그 티켓 (run_tests.py)*

||항목||내용||
|테스트 파일|{filename}|
|테스트 함수|{test_func}|
|결과|{outcome}|
|연관 티켓|{issue_key}|

*에러 로그:*
{{code}}
{longrepr_short}
{{code}}
"""

    try:
        issue = jira.create_issue(
            project=PROJECT_KEY,
            summary=summary,
            description=description,
            issuetype={"name": "Bug"},
        )
        print(f"  [OK] 생성됨: {issue.key} - {summary}")
        created.append(issue.key)
    except Exception as e:
        print(f"  [FAIL] 생성 실패 ({nodeid}): {e}")

print(f"\n=== 완료: {len(created)}개 생성, {len(skipped)}개 스킵 ({', '.join(created)}) ===")
