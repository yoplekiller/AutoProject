import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_URL   = os.getenv("JIRA_URL")
EMAIL      = os.getenv("JIRA_EMAIL")
TOKEN      = os.getenv("JIRA_API_TOKEN")
PROJECT    = os.getenv("JIRA_PROJECT_KEY")

auth    = (EMAIL, TOKEN)
headers = {"Content-Type": "application/json", "Accept": "application/json"}

filters = [
    {
        "name": "[MKQA] 자동 등록 버그 목록",
        "jql": f'project = {PROJECT} AND issuetype = Bug AND summary ~ "[자동버그]" ORDER BY created DESC',
        "description": "Playwright 자동화 실패 → 자동 등록된 버그 티켓",
    },
    {
        "name": "[MKQA] 전체 TC 티켓",
        "jql": f'project = {PROJECT} AND issuetype != Bug ORDER BY created ASC',
        "description": "MKQA 프로젝트 전체 테스트 케이스 티켓",
    },
    {
        "name": "[MKQA] 이슈 유형별 현황",
        "jql": f'project = {PROJECT} ORDER BY issuetype ASC',
        "description": "MKQA 전체 이슈 (TC + 버그 포함)",
    },
]

print("=== Jira 필터 생성 ===\n")

created_filters = []
for f in filters:
    payload = {
        "name": f["name"],
        "description": f["description"],
        "jql": f["jql"],
        "favourite": True,
        "sharePermissions": [{"type": "global"}],
    }
    resp = requests.post(
        f"{JIRA_URL}/rest/api/3/filter",
        json=payload,
        auth=auth,
        headers=headers,
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        filter_id = data["id"]
        filter_url = f"{JIRA_URL}/issues/?filter={filter_id}"
        print(f"  [OK] {f['name']}")
        print(f"       ID: {filter_id} | {filter_url}")
        created_filters.append({"name": f["name"], "id": filter_id, "url": filter_url})
    else:
        print(f"  [FAIL] {f['name']}: {resp.status_code} {resp.text[:100]}")

print(f"\n=== 완료: {len(created_filters)}개 필터 생성 ===")
print("\n[다음 단계] Jira 대시보드에서 아래 가젯 추가:")
print("  1. Filter Results    → [MKQA] 자동 등록 버그 목록")
print("  2. Pie Chart         → [MKQA] 이슈 유형별 현황 / 이슈 유형 기준")
print("  3. Filter Results    → [MKQA] 전체 TC 티켓")
