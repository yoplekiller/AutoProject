import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def create_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('window-size=1920,1080')
    return webdriver.Chrome(service=service, options=options)

@pytest.mark.parametrize("tc_id, email, password, confirm_password, expected_result", [
    ("TC-001", "invalid_email", "password123!", "password123!", "에러 메시지"),
    ("TC-002", "test@example.com", "password123!", "password1234", "에러 메시지"),
    ("TC-003", "existing@example.com", "password123!", "password123!", "중복 안내 메시지")
])
def test_signup_validation(tc_id, email, password, confirm_password, expected_result):
    driver = create_driver()
    driver.get("https://www.kurly.com/member/join")
    
    # 이메일 입력란에 형식에 맞지 않는 이메일을 입력
    if tc_id == "TC-001":
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(email)
    elif tc_id == "TC-002":
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(email)
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(password)
        confirm_password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "passwordConfirm"))
        )
        confirm_password_input.send_keys(confirm_password)
    elif tc_id == "TC-003":
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(email)
    
    # 가입 버튼을 클릭
    join_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    )
    join_button.click()
    
    # 에러 메시지 노출 여부 확인
    if tc_id == "TC-001" or tc_id == "TC-002":
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        assert error_message.text == expected_result
    elif tc_id == "TC-003":
        duplicate_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".duplicate-message"))
        )
        assert duplicate_message.text == expected_result
    
    driver.quit()

def test_signup_validation_existing_email():
    driver = create_driver()
    driver.get("https://www.kurly.com/member/join")
    
    # 이미 가입된 이메일을 입력
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_input.send_keys("existing@example.com")
    
    # 가입 버튼을 클릭
    join_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    )
    join_button.click()
    
    # 중복 안내 메시지 노출 여부 확인
    duplicate_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".duplicate-message"))
    )
    assert duplicate_message.text == "중복 안내 메시지"
    
    driver.quit()