"""
구글 시트 폴링 기반 TC 자동 생성 스크립트

[동작 방식]
1. 구글 시트 '티켓 입력' 탭의 A열(티켓 URL/키)을 스캔
2. B열(상태)이 비어있는 행을 '미처리'로 인식
3. Groq AI로 TC 생성 후 '매뉴얼 TC' 탭에 append
4. B열 → '완료', C열 → 처리 시각으로 업데이트
5. Slack 알림 발송

[시트 구조 - '티켓 입력' 탭]
  A열: 티켓 URL 또는 이슈 키 (예: MKQA-1 또는 Jira URL)
  B열: 상태 (비워두면 대기 → 완료로 자동 업데이트)
  C열: 처리 시각 (자동 기입)

[실행]
  python src/watch_sheet.py
  python src/watch_sheet.py --sheet-id YOUR_SHEET_ID  # 시트 ID 직접 지정
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime

import requests
from jira import JIRA
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS_PATH = os.path.join(ROOT_DIR, os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
JIRA_URL = os.getenv("JIRA_URL", "")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

INPUT_SHEET_NAME = "티켓 입력"
OUTPUT_SHEET_NAME = "매뉴얼 TC"


# ── gspread 클라이언트 ────────────────────────────────────────────────

def _get_gspread_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("[오류] gspread 또는 google-auth 패키지가 없습니다.")
        print("  pip install gspread google-auth")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # GitHub Actions 환경: GOOGLE_CREDENTIALS_JSON 환경변수에서 직접 읽기
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        import json as _json
        info = _json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)

    return gspread.authorize(creds)


def get_or_create_worksheet(sh, title: str, rows=1000, cols=10):
    """시트가 없으면 생성, 있으면 반환."""
    import gspread
    try:
        return sh.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=rows, cols=cols)
        print(f"  '{title}' 시트 새로 생성")
        return ws


# ── 미처리 행 스캔 ────────────────────────────────────────────────────

def scan_pending_rows(ws_input) -> list:
    """
    '티켓 입력' 시트에서 B열이 비어있는 행을 반환.
    반환: [{"row_idx": 2, "raw_value": "MKQA-1"}, ...]
    """
    all_values = ws_input.get_all_values()  # 전체 행 리스트

    pending = []
    for i, row in enumerate(all_values):
        if i == 0:  # 헤더 스킵
            continue
        a_val = row[0].strip() if len(row) > 0 else ""
        b_val = row[1].strip() if len(row) > 1 else ""
        if a_val and not b_val:
            pending.append({"row_idx": i + 1, "raw_value": a_val})  # 1-based

    return pending


# ── Jira ─────────────────────────────────────────────────────────────

def extract_issue_key(input_str: str) -> str:
    url_match = re.search(r"/browse/([A-Z][A-Z0-9_]+-\d+)", input_str)
    if url_match:
        return url_match.group(1)
    key_match = re.fullmatch(r"[A-Z][A-Z0-9_]+-\d+", input_str.strip())
    if key_match:
        return input_str.strip()
    raise ValueError(f"유효하지 않은 티켓: {input_str}")


def fetch_issue(jira: JIRA, issue_key: str) -> dict:
    issue = jira.issue(issue_key)
    return {
        "key": issue.key,
        "summary": issue.fields.summary,
        "status": issue.fields.status.name,
        "description": issue.fields.description or "설명 없음",
        "issue_type": issue.fields.issuetype.name,
    }


# ── Groq TC 생성 ─────────────────────────────────────────────────────

def generate_test_cases(groq_client: Groq, issue: dict) -> list:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 경력 있는 QA 엔지니어입니다. "
                    "Jira 티켓 정보를 바탕으로 매뉴얼 테스트 케이스를 작성합니다. "
                    "정상 흐름(Happy Path), 예외 처리, 경계값 등을 고려하여 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"""다음 Jira 티켓에 대한 매뉴얼 테스트 케이스를 작성해주세요.

티켓 키: {issue['key']}
티켓 유형: {issue['issue_type']}
티켓 제목: {issue['summary']}

티켓 설명:
{issue['description']}

반드시 아래 JSON 배열 형식으로만 응답하세요. 설명이나 마크다운 코드블록 없이 JSON만 출력하세요.

[
  {{
    "tc_id": "TC-001",
    "테스트항목": "",
    "사전조건": "",
    "테스트단계": "1. 단계1\\n2. 단계2\\n3. 단계3",
    "기대결과": "",
    "우선순위": "High/Medium/Low"
  }}
]""",
            },
        ],
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [경고] JSON 파싱 실패")
        return [{"tc_id": "TC-ERROR", "테스트항목": raw, "사전조건": "", "테스트단계": "", "기대결과": "", "우선순위": ""}]


# ── 구글 시트 결과 저장 (append) ──────────────────────────────────────

def ensure_output_header(ws_output):
    """'매뉴얼 TC' 시트 헤더가 없으면 추가."""
    headers = ["티켓 키", "요약", "상태", "우선순위", "TC ID", "테스트 항목", "사전 조건", "테스트 단계", "기대 결과", "생성 시각"]
    existing = ws_output.row_values(1)
    if not existing or existing[0] != "티켓 키":
        ws_output.insert_row(headers, index=1)
        ws_output.format("A1:J1", {
            "backgroundColor": {"red": 0.267, "green": 0.447, "blue": 0.769},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
        })
        print(f"  '{OUTPUT_SHEET_NAME}' 헤더 추가")


def append_tc_rows(ws_output, issue: dict, tc_list: list, generated_at: str):
    """TC 결과를 '매뉴얼 TC' 시트에 append."""
    priority_colors = {
        "High":   {"red": 1.0,  "green": 0.8,  "blue": 0.8},
        "Medium": {"red": 1.0,  "green": 0.95, "blue": 0.8},
        "Low":    {"red": 0.85, "green": 0.92, "blue": 0.85},
    }

    rows_to_add = []
    for tc in tc_list:
        rows_to_add.append([
            issue["key"],
            issue["summary"],
            issue["status"],
            tc.get("우선순위", ""),
            tc.get("tc_id", ""),
            tc.get("테스트항목", ""),
            tc.get("사전조건", ""),
            tc.get("테스트단계", ""),
            tc.get("기대결과", ""),
            generated_at,
        ])

    ws_output.append_rows(rows_to_add, value_input_option="RAW")

    # 우선순위 색상 적용
    start_row = len(ws_output.col_values(1)) - len(tc_list) + 1
    for i, tc in enumerate(tc_list):
        color = priority_colors.get(tc.get("우선순위", ""))
        if color:
            ws_output.format(f"D{start_row + i}", {"backgroundColor": color})


def mark_row_done(ws_input, row_idx: int, timestamp: str):
    """입력 시트 해당 행의 B열=완료, C열=처리시각으로 업데이트."""
    ws_input.update_cell(row_idx, 2, "완료")
    ws_input.update_cell(row_idx, 3, timestamp)


# ── Slack 알림 ────────────────────────────────────────────────────────

def notify_slack(processed: list, sheet_id: str):
    """처리 완료된 티켓 목록을 Slack으로 알림."""
    if not SLACK_WEBHOOK_URL:
        return

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    lines = [f"*[TC 자동 생성 완료]* {len(processed)}개 티켓 처리됨"]
    for item in processed:
        tc_count = item["tc_count"]
        lines.append(f"  • `{item['key']}` {item['summary']} — TC {tc_count}개")
    lines.append(f"\n<{sheet_url}|구글 시트에서 확인>")

    payload = {"text": "\n".join(lines)}
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            print("  Slack 알림 발송 완료")
        else:
            print(f"  [경고] Slack 알림 실패: {resp.status_code}")
    except Exception as e:
        print(f"  [경고] Slack 알림 오류: {e}")


# ── 메인 ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="구글 시트 폴링 기반 TC 자동 생성")
    parser.add_argument("--sheet-id", default=SPREADSHEET_ID, help="구글 스프레드시트 ID")
    args = parser.parse_args()

    sheet_id = args.sheet_id
    if not sheet_id:
        print("[오류] SPREADSHEET_ID 환경변수 또는 --sheet-id 인자가 필요합니다.")
        sys.exit(1)

    print(f"\n=== 구글 시트 폴링 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # 클라이언트 초기화
    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)

    # 입력 시트 확인
    ws_input = get_or_create_worksheet(sh, INPUT_SHEET_NAME)

    # 헤더 확인 (1행이 비어있으면 헤더 추가)
    first_row = ws_input.row_values(1)
    if not first_row or first_row[0] != "티켓 URL 또는 이슈 키":
        ws_input.insert_row(["티켓 URL 또는 이슈 키", "상태", "처리 시각"], index=1)
        ws_input.format("A1:C1", {
            "backgroundColor": {"red": 0.267, "green": 0.447, "blue": 0.769},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
        })
        print(f"  '{INPUT_SHEET_NAME}' 헤더 추가 완료")

    # 출력 시트 확인
    ws_output = get_or_create_worksheet(sh, OUTPUT_SHEET_NAME)
    ensure_output_header(ws_output)

    # 미처리 행 스캔
    pending = scan_pending_rows(ws_input)

    if not pending:
        print("  미처리 티켓 없음 - 종료")
        return

    print(f"  미처리 티켓 {len(pending)}개 발견: {[p['raw_value'] for p in pending]}")

    # Jira / Groq 클라이언트
    jira = JIRA(
        server=os.getenv("JIRA_URL"),
        basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")),
    )
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    processed = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in pending:
        raw = item["raw_value"]
        row_idx = item["row_idx"]

        print(f"\n처리 중: {raw} (행 {row_idx})")

        # 티켓 키 추출
        try:
            issue_key = extract_issue_key(raw)
        except ValueError as e:
            print(f"  [건너뜀] {e}")
            ws_input.update_cell(row_idx, 2, "오류: 유효하지 않은 티켓")
            ws_input.update_cell(row_idx, 3, timestamp)
            continue

        # Jira 조회
        try:
            issue = fetch_issue(jira, issue_key)
        except Exception as e:
            print(f"  [건너뜀] Jira 조회 실패: {e}")
            ws_input.update_cell(row_idx, 2, "오류: Jira 조회 실패")
            ws_input.update_cell(row_idx, 3, timestamp)
            continue

        print(f"  제목: {issue['summary']} | 상태: {issue['status']}")

        # TC 생성
        print(f"  TC 생성 중...")
        tc_list = generate_test_cases(groq_client, issue)
        print(f"  생성된 TC: {len(tc_list)}개")
        for tc in tc_list:
            print(f"    [{tc.get('tc_id')}] [{tc.get('우선순위', '-')}] {tc.get('테스트항목')}")

        # 결과 시트에 append
        append_tc_rows(ws_output, issue, tc_list, timestamp)

        # 입력 시트 상태 업데이트
        mark_row_done(ws_input, row_idx, timestamp)
        print(f"  상태 업데이트: 완료")

        processed.append({"key": issue["key"], "summary": issue["summary"], "tc_count": len(tc_list)})

    # 슬랙 알림
    if processed:
        notify_slack(processed, sheet_id)

    print(f"\n=== 완료: {len(processed)}개 티켓 처리 / {sum(p['tc_count'] for p in processed)}개 TC 생성 ===")


if __name__ == "__main__":
    main()
