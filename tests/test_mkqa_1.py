import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_module():
    global driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def teardown_module():
    global driver
    driver.quit()

@pytest.mark.parametrize("tc_id, keyword, expected_result", [
    ("TC-001", "딸기", "관련 상품 목록이 표시됨"),
    ("TC-002", "없는상품", "\"검색 결과가 없습니다\" 안내 문구가 표시됨"),
    ("TC-003", "!@#", "정상적으로 처리되어 \"검색 결과가 없습니다\" 안내 문구가 표시됨")
])
def test_search(tc_id, keyword, expected_result):
    driver.get("https://www.kurly.com")
    search_bar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search_inp")))
    search_bar.send_keys(keyword)
    search_button = driver.find_element(By.CLASS_NAME, "btn_search")
    search_button.click()
    
    if keyword == "딸기":
        product_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list_item")))
        assert len(product_list) > 0
    else:
        result_message = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".no_result_txt")))
        assert result_message.text == "검색 결과가 없습니다"

    driver.quit()