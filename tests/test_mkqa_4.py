import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@pytest.mark.parametrize("test_case", [
    {"tc_id": "TC-001", "email": "test@example.com", "password": "test1234", "expected_result": "메인 페이지로 이동"},
    {"tc_id": "TC-002", "email": "test@example.com", "password": "wrong_password", "expected_result": "에러 메시지 표시"},
    {"tc_id": "TC-003", "email": "non_existent@example.com", "password": "test1234", "expected_result": "에러 메시지 표시"}
])
def test_login(test_case):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com/member/login")

    if test_case["tc_id"] == "TC-001":
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(test_case["email"])
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(test_case["password"])
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        assert driver.title == "마켓컬리"

    elif test_case["tc_id"] == "TC-002":
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(test_case["email"])
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(test_case["password"])
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
        assert error_message.text != ""

    elif test_case["tc_id"] == "TC-003":
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(test_case["email"])
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(test_case["password"])
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
        assert error_message.text != ""

    driver.quit()

def test_login_with_normal_input():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com/member/login")
    email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    email_input.send_keys("test@example.com")
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys("test1234")
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    assert driver.title == "마켓컬리"
    driver.quit()

def test_login_with_wrong_password():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com/member/login")
    email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    email_input.send_keys("test@example.com")
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys("wrong_password")
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
    assert error_message.text != ""
    driver.quit()

def test_login_with_non_existent_email():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com/member/login")
    email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    email_input.send_keys("non_existent@example.com")
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys("test1234")
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    error_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
    assert error_message.text != ""
    driver.quit()