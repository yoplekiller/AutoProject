import subprocess
import json
import os
import sys
from datetime import datetime

# 프로젝트 루트 기준으로 경로 설정
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_report_path = os.path.join(REPORTS_DIR, f"test_results_{timestamp}.json")

print(f"=== Playwright 테스트 실행 시작 ({timestamp}) ===\n")

# pytest 실행 (--json-report 플러그인 사용)
result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        TESTS_DIR,
        "-v",
        "--tb=short",
        f"--json-report",
        f"--json-report-file={json_report_path}",
        "--json-report-indent=2",
        "--no-header",
    ],
    cwd=ROOT_DIR,
    capture_output=False,
)

print(f"\n=== 테스트 종료 (exit code: {result.returncode}) ===")

# 결과 JSON 파싱 및 요약 출력
if os.path.exists(json_report_path):
    with open(json_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    summary = report.get("summary", {})
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    error = summary.get("error", 0)
    total = summary.get("total", 0)

    print(f"\n[결과 요약]")
    print(f"  전체: {total} | 통과: {passed} | 실패: {failed} | 에러: {error}")
    print(f"  저장 경로: {json_report_path}")

    # 실패 목록 출력
    failed_tests = [
        t for t in report.get("tests", [])
        if t.get("outcome") in ("failed", "error")
    ]

    if failed_tests:
        print(f"\n[실패 항목]")
        for t in failed_tests:
            print(f"  [FAIL] {t['nodeid']}")
            longrepr = t.get("call", {}).get("longrepr", "")
            if longrepr:
                # 마지막 줄(에러 요약)만 출력
                short = longrepr.strip().split("\n")[-1]
                print(f"    -> {short}")
    else:
        print("\n  모든 테스트 통과!")
else:
    print(f"\n❌ 결과 파일 생성 실패: {json_report_path}")
    print("   pytest-json-report 플러그인 설치 확인: pip install pytest-json-report")
