"""
MKQA 티켓 품질 개선 스크립트
- Acceptance Criteria, 테스트 환경, Precondition, Out of Scope 추가
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from jira import JIRA
from dotenv import load_dotenv
import os

load_dotenv()
jira = JIRA(server=os.getenv("JIRA_URL"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")))

# ── 티켓별 개선 내용 ────────────────────────────────────────────────

TICKETS = {
    "MKQA-1": {
        "summary": "상품 키워드 검색 기능 검증",
        "description": """마켓컬리 상단 검색바에서 키워드로 상품을 검색하는 기능을 테스트합니다.

[기능 설명]
* 검색창에 키워드 입력 후 검색 실행
* 검색 결과 페이지에 관련 상품 목록 표시
* 검색 결과 없을 경우 안내 문구 표시

[Acceptance Criteria]
* Given 로그인된 사용자가 검색바에 "딸기"를 입력하고 검색 버튼을 클릭하면 / Then 상품명 또는 태그에 "딸기"가 포함된 상품 목록이 표시된다
* Given 검색 결과가 없는 키워드("없는상품123")를 입력하면 / Then "검색 결과가 없습니다" 안내 문구가 표시된다
* Given 특수문자("!@#$")를 입력하면 / Then 에러 없이 처리되고 결과 없음 또는 적절한 안내가 표시된다
* Given 공백만 입력 후 검색 버튼을 클릭하면 / Then 검색이 실행되지 않거나 "검색어를 입력해주세요" 안내가 표시된다
* Given 검색 결과 목록이 표시된 경우 / Then 각 상품 카드에 상품명, 가격, 이미지가 포함되어 있다
* Given 검색어와 일치하는 결과가 있을 때 / Then 검색 결과는 3초 이내에 표시된다

[테스트 환경]
* Platform: Web (Chrome 최신 버전 / Firefox 최신 버전)
* URL: https://www.kurly.com
* 해상도: 1920x1080 (PC)

[Precondition]
* 로그인된 상태의 테스트 계정 준비
* 검색 키워드에 해당하는 상품이 DB에 존재
* 네트워크 정상 상태

[Out of Scope]
* 모바일 앱 검색 기능
* 검색 순위/랭킹 알고리즘 검증
* 검색 자동완성 기능
* 필터/정렬 기능 검증""",
    },

    "MKQA-4": {
        "summary": "이메일 로그인 기능 검증",
        "description": """마켓컬리 로그인 페이지에서 이메일/비밀번호로 로그인하는 기능을 테스트합니다.

[기능 설명]
* URL: https://www.kurly.com/login
* 이메일 입력 필드, 비밀번호 입력 필드, 로그인 버튼으로 구성
* 로그인 성공 시 메인 페이지로 이동
* 로그인 실패 시 에러 메시지 표시

[Acceptance Criteria]
* Given 유효한 이메일과 비밀번호를 입력하고 로그인 버튼을 클릭하면 / Then 메인 페이지로 이동하고 헤더에 로그인 상태(마이페이지)가 표시된다
* Given 유효한 이메일에 잘못된 비밀번호를 입력하면 / Then "이메일 또는 비밀번호가 올바르지 않습니다" 에러 메시지가 표시된다
* Given 존재하지 않는 이메일을 입력하면 / Then 에러 메시지가 표시되고 로그인이 거부된다
* Given 이메일 형식이 아닌 값(예: "testuser")을 입력하면 / Then 필드 아래에 이메일 형식 오류 메시지가 표시된다
* Given 비밀번호 필드를 비워두고 로그인 버튼을 클릭하면 / Then "비밀번호를 입력해주세요" 안내가 표시된다
* Given 비밀번호 입력 시 / Then 입력값이 마스킹(●●●) 처리되어 표시된다

[테스트 환경]
* Platform: Web (Chrome 최신 버전 / Firefox 최신 버전)
* URL: https://www.kurly.com/login
* 해상도: 1920x1080 (PC)

[Precondition]
* 테스트용 가입 완료 계정 준비 (이메일, 비밀번호)
* 계정이 정지/탈퇴 상태가 아님
* 비로그인 상태에서 테스트 시작

[Out of Scope]
* 소셜 로그인 (카카오, 네이버 등)
* 비밀번호 찾기/재설정 기능
* 자동 로그인 / 로그인 유지 기능
* 모바일 앱 로그인""",
    },

    "MKQA-5": {
        "summary": "장바구니 상품 추가/삭제 기능 검증",
        "description": """상품 상세 페이지에서 장바구니에 상품을 추가하고 삭제하는 기능을 테스트합니다.

[기능 설명]
* 상품 상세 페이지에서 "장바구니 담기" 버튼 클릭
* 장바구니 페이지에서 수량 변경 및 삭제 가능
* 장바구니 합계 금액 자동 계산

[Acceptance Criteria]
* Given 로그인된 사용자가 상품 상세 페이지에서 "장바구니 담기"를 클릭하면 / Then 장바구니에 해당 상품이 추가되고 장바구니 아이콘의 수량이 증가한다
* Given 이미 담긴 상품을 다시 "장바구니 담기"하면 / Then 수량이 1 증가하거나 "이미 담긴 상품입니다" 안내가 표시된다
* Given 장바구니에서 수량 + 버튼을 클릭하면 / Then 수량이 1 증가하고 합계 금액이 재계산된다
* Given 장바구니에서 수량이 1인 상품의 - 버튼을 클릭하면 / Then 삭제 확인 팝업이 표시되거나 수량이 1 이하로 감소하지 않는다
* Given 장바구니에서 상품의 삭제 버튼을 클릭하면 / Then 해당 상품이 장바구니에서 제거되고 합계 금액이 재계산된다
* Given 비로그인 상태에서 "장바구니 담기"를 클릭하면 / Then 로그인 페이지로 이동하거나 로그인 유도 팝업이 표시된다

[테스트 환경]
* Platform: Web (Chrome 최신 버전)
* URL: https://www.kurly.com
* 해상도: 1920x1080 (PC)

[Precondition]
* 로그인된 테스트 계정 준비
* 장바구니가 비어있는 상태에서 시작
* 테스트 대상 상품이 품절이 아닌 상태

[Out of Scope]
* 주문/결제 프로세스
* 쿠폰/포인트 적용
* 배송비 계산 로직
* 찜하기(위시리스트) 기능""",
    },

    "MKQA-6": {
        "summary": "상품 상세 페이지 옵션 선택 기능 검증",
        "description": """상품 상세 페이지에서 옵션(중량, 수량 등)을 선택하는 기능을 테스트합니다.

[기능 설명]
* 일부 상품은 중량/용량 옵션 선택 가능
* 수량 선택 후 장바구니 또는 바로 구매 가능
* 품절 상품의 경우 구매 버튼 비활성화

[Acceptance Criteria]
* Given 옵션이 있는 상품 상세 페이지에서 옵션을 변경하면 / Then 선택한 옵션에 따라 가격이 업데이트된다
* Given 옵션을 선택하지 않고 "장바구니 담기"를 클릭하면 / Then "옵션을 선택해주세요" 안내 메시지가 표시된다
* Given 수량 입력 필드에 최대 구매 수량을 초과한 값을 입력하면 / Then 최대 수량으로 자동 조정되거나 경고 메시지가 표시된다
* Given 수량 입력 필드에 0 또는 음수를 입력하면 / Then 1로 자동 조정되거나 유효하지 않은 값임을 안내한다
* Given 품절 상품의 상세 페이지에 진입하면 / Then "품절" 배지가 표시되고 "장바구니 담기" 및 "바로 구매" 버튼이 비활성화된다
* Given 정상 옵션을 선택하고 수량을 입력한 후 "바로 구매"를 클릭하면 / Then 주문서 페이지로 이동한다

[테스트 환경]
* Platform: Web (Chrome 최신 버전)
* URL: https://www.kurly.com (옵션 있는 상품 상세 페이지)
* 해상도: 1920x1080 (PC)

[Precondition]
* 로그인된 테스트 계정 준비
* 옵션이 존재하는 테스트 상품 URL 확보
* 품절 상태인 테스트 상품 URL 확보

[Out of Scope]
* 실제 결제/주문 완료 프로세스
* 재입고 알림 신청 기능
* 상품 리뷰/평점 기능
* 상품 상세 이미지 슬라이더 기능""",
    },

    "MKQA-7": {
        "summary": "회원가입 유효성 검사 기능 검증",
        "description": """마켓컬리 회원가입 페이지에서 입력 필드 유효성 검사를 테스트합니다.

[기능 설명]
* URL: https://www.kurly.com/join
* 이메일, 비밀번호, 이름, 휴대폰 번호 입력 필드 존재
* 각 필드별 유효성 조건 존재

[Acceptance Criteria]
* Given 이메일 형식이 아닌 값(예: "testuser")을 입력하면 / Then "이메일 형식으로 입력해주세요" 에러 메시지가 표시된다
* Given 비밀번호를 8자 미만으로 입력하면 / Then "비밀번호는 8자 이상이어야 합니다" 에러 메시지가 표시된다
* Given 비밀번호와 비밀번호 확인 값이 다르면 / Then "비밀번호가 일치하지 않습니다" 에러 메시지가 표시된다
* Given 이미 가입된 이메일로 가입을 시도하면 / Then "이미 사용 중인 이메일입니다" 에러 메시지가 표시된다
* Given 휴대폰 번호를 숫자가 아닌 값 또는 형식에 맞지 않게 입력하면 / Then 휴대폰 번호 형식 오류 메시지가 표시된다
* Given 필수 입력 항목(이메일, 비밀번호, 이름)을 비워두고 가입 버튼을 클릭하면 / Then 미입력 필드에 오류 메시지가 표시되고 가입이 진행되지 않는다
* Given 모든 필드를 올바르게 입력하고 가입 버튼을 클릭하면 / Then 가입 완료 페이지 또는 이메일 인증 안내 페이지로 이동한다

[테스트 환경]
* Platform: Web (Chrome 최신 버전)
* URL: https://www.kurly.com/join
* 해상도: 1920x1080 (PC)

[Precondition]
* 비로그인 상태
* 테스트용 신규 이메일 주소 준비 (기존 가입 이력 없음)
* 중복 테스트를 위한 기가입 계정 이메일 준비

[Out of Scope]
* 이메일 인증 발송/수신 프로세스
* SNS 회원가입 (카카오, 네이버 등)
* 본인인증 프로세스
* 가입 후 로그인 자동화 여부""",
    },
}

# ── 업데이트 실행 ───────────────────────────────────────────────────

print("=== MKQA 티켓 품질 개선 시작 ===\n")

for key, data in TICKETS.items():
    try:
        issue = jira.issue(key)
        issue.update(fields={"description": data["description"]})
        print(f"  [OK] {key} — {data['summary']} 업데이트 완료")
    except Exception as e:
        print(f"  [FAIL] {key}: {e}")

print("\n=== 완료 ===")
print("이제 python src/generate_tc_from_url.py MKQA-1 로 TC 생성 품질을 확인하세요.")
