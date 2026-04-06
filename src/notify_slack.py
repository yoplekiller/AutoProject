import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json
import glob
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
JIRA_URL = os.getenv("JIRA_URL")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

# 최신 테스트 결과 JSON 로드
result_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "test_results_*.json")))
if not result_files:
    print("[ERROR] test_results 파일이 없습니다. run_tests.py 먼저 실행하세요.")
    exit()

with open(result_files[-1], "r", encoding="utf-8") as f:
    report = json.load(f)

s = report.get("summary", {})
total      = s.get("total", 0)
passed     = s.get("passed", 0)
failed     = s.get("failed", 0)
error      = s.get("error", 0)
fail_total = failed + error
pass_rate  = round(passed / total * 100) if total > 0 else 0

failed_tests = [
    t for t in report.get("tests", [])
    if t.get("outcome") in ("failed", "error")
]

now = datetime.now().strftime("%Y-%m-%d %H:%M")
jira_link = f"{JIRA_URL}/jira/software/projects/{PROJECT_KEY}/boards"

if fail_total == 0:
    status_emoji = ":white_check_mark:"
    status_text  = "전체 통과"
else:
    status_emoji = ":x:"
    status_text  = f"{fail_total}건 실패"

# 실패 항목 (최대 10개)
fail_lines = []
for t in failed_tests[:10]:
    nodeid = t["nodeid"].split("/")[-1]
    call = t.get("call", {})
    longrepr = call.get("longrepr", "")
    short_err = longrepr.strip().split("\n")[-1][:60] if longrepr else "-"
    fail_lines.append(f"• `{nodeid}` {short_err}")
if len(failed_tests) > 10:
    fail_lines.append(f"_...외 {len(failed_tests) - 10}건_")

fail_text = "\n".join(fail_lines) if fail_lines else "없음"

blocks = [
    {"type": "divider"},
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"{status_emoji} *MKQA Playwright 테스트 결과* | {now}"
        }
    },
    {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*전체 테스트*\n{total}건"},
            {"type": "mrkdwn", "text": f"*통과 / 실패*\n{passed} / {fail_total}  ({pass_rate}%)"},
        ]
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*실패 항목*\n{fail_text}"
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"AutoProject · AI 기반 QA 자동화 · `{os.path.basename(result_files[-1])}`  |  <{jira_link}|Jira 보드 열기>"
            }
        ]
    },
    {"type": "divider"},
]

payload = {
    "text": f"{status_emoji} MKQA 테스트 결과: {status_text} ({passed}/{total})",
    "blocks": blocks
}

resp = requests.post(SLACK_WEBHOOK_URL, json=payload)
if resp.status_code == 200 and resp.text == "ok":
    print(f"[OK] Slack 알림 전송 완료 ({status_text})")
else:
    print(f"[FAIL] 전송 실패: {resp.status_code} / {resp.text}")
