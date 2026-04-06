from groq import Groq
from dotenv import load_dotenv
import os
import json
import glob

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# reports/ 에서 가장 최신 JSON 파일 로드
json_files = sorted(glob.glob("reports/tc_*.json"))
if not json_files:
    print("❌ TC JSON 파일이 없습니다. generate_tc.py 먼저 실행하세요.")
    exit()

latest_file = json_files[-1]
print(f"=== TC 파일 로드: {latest_file} ===\n")

with open(latest_file, "r", encoding="utf-8") as f:
    tc_data = json.load(f)

# tests/ 폴더 생성
os.makedirs("tests", exist_ok=True)

for item in tc_data:
    issue_key = item["issue_key"]
    summary = item["summary"]
    tc_list = item["test_cases"]

    print(f"[{issue_key}] {summary} → Playwright 코드 생성 중...")
    print("-" * 50)

    # TC 목록을 텍스트로 변환
    tc_text = json.dumps(tc_list, ensure_ascii=False, indent=2)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """당신은 Playwright Python 자동화 전문가입니다.
테스트 케이스를 받아서 Playwright pytest 코드로 변환해주세요.
반드시 아래 규칙을 따르세요:
- pytest 형식으로 작성
- 각 TC는 별도의 test_ 함수로 작성
- 마켓컬리(https://www.kurly.com) 기준
- sync_playwright 사용
- 코드만 출력, 설명 없음"""
            },
            {
                "role": "user",
                "content": f"""다음 테스트 케이스를 Playwright Python 코드로 변환해주세요.

티켓: {summary}

테스트 케이스:
{tc_text}"""
            }
        ]
    )

    code = response.choices[0].message.content.strip()

    # ```python 마크다운 제거
    if code.startswith("```"):
        code = code.split("\n", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]

    # tests/ 폴더에 저장
    filename = f"tests/test_{issue_key.lower().replace('-', '_')}.py"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code.strip())

    print(f"✅ 저장 완료: {filename}\n")

print("=== 전체 Playwright 코드 생성 완료 ===")
