from groq import Groq
from dotenv import load_dotenv
import os
import json
import glob

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# reports/ 에서 가장 최신 JSON 파일 로드
json_files = sorted(glob.glob(os.path.join(ROOT_DIR, "reports", "tc_*.json")))
if not json_files:
    print("[ERROR] TC JSON 파일이 없습니다. generate_tc.py 먼저 실행하세요.")
    exit()

latest_file = json_files[-1]
print(f"=== TC 파일 로드: {latest_file} ===\n")

with open(latest_file, "r", encoding="utf-8") as f:
    tc_data = json.load(f)

# tests/ 폴더 생성
tests_dir = os.path.join(ROOT_DIR, "tests")
os.makedirs(tests_dir, exist_ok=True)

for item in tc_data:
    issue_key = item["issue_key"]
    summary   = item["summary"]
    tc_list   = item["test_cases"]

    print(f"[{issue_key}] {summary} → Selenium 코드 생성 중...")
    print("-" * 50)

    tc_text = json.dumps(tc_list, ensure_ascii=False, indent=2)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """당신은 Selenium Python 자동화 전문가입니다.
테스트 케이스를 받아서 Selenium + pytest 코드로 변환해주세요.
반드시 아래 규칙을 따르세요:
- pytest 형식으로 작성
- 각 TC는 별도의 test_ 함수로 작성
- import는 파일 상단에 한 번만 작성
- selenium.webdriver 사용 (Chrome)
- webdriver-manager 사용: from selenium.webdriver.chrome.service import Service / from webdriver_manager.chrome import ChromeDriverManager
- WebDriverWait + expected_conditions 으로 요소 대기
- 각 test_ 함수 안에서 driver 생성하고 마지막에 driver.quit() 호출
- 마켓컬리(https://www.kurly.com) 기준
- 코드만 출력, 설명 없음"""
            },
            {
                "role": "user",
                "content": f"""다음 테스트 케이스를 Selenium Python pytest 코드로 변환해주세요.

티켓: {summary}

테스트 케이스:
{tc_text}"""
            }
        ]
    )

    code = response.choices[0].message.content.strip()

    # 마크다운 코드블록 제거
    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:])
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]

    filename = os.path.join(tests_dir, f"test_{issue_key.lower().replace('-', '_')}.py")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code.strip())

    print(f"[OK] 저장 완료: {filename}\n")

print("=== 전체 Selenium 코드 생성 완료 ===")
