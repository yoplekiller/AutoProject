import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import subprocess
import os
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

STEPS = [
    ("Selenium 코드 생성",       "generate_selenium.py"),
    ("테스트 실행",              "run_tests.py"),
    ("Jira 버그 등록",           "create_jira_bugs.py"),
    ("Google Sheets 동기화",     "sync_sheets.py"),
    ("Slack 알림 전송",          "notify_slack.py"),
    ("대시보드 생성",            "generate_dashboard.py"),
]

print("=" * 55)
print(" AutoProject QA 자동화 파이프라인")
print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 55)

results = []

for step_name, script in STEPS:
    print(f"\n[STEP] {step_name} ({script})")
    print("-" * 40)

    ret = subprocess.run(
        [sys.executable, os.path.join(SRC_DIR, script)],
        cwd=ROOT_DIR,
    )

    status = "OK" if ret.returncode == 0 else "FAIL"
    results.append((step_name, status))
    print(f"--> {status}")

print("\n" + "=" * 55)
print(" 파이프라인 실행 결과")
print("=" * 55)
for name, status in results:
    mark = "[OK]  " if status == "OK" else "[FAIL]"
    print(f"  {mark} {name}")

all_ok = all(s == "OK" for _, s in results)
print()
print("완료!" if all_ok else "일부 실패 — 위 로그 확인")
print("=" * 55)
