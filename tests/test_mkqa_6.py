import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def setup_module():
    global driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def teardown_module():
    driver.quit()

@pytest.mark.usefixtures("setup_module", "teardown_module")
class TestMarketKurly:
    def test_option_price_change(self):
        driver.get("https://www.kurly.com")
        product_link = driver.find_element(By.CSS_SELECTOR, ".product-link")
        product_link.click()
        
        # 옵션 선택
        option_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".option-button"))
        )
        option_button.click()
        
        # 가격 변동 확인
        price_element = driver.find_element(By.CSS_SELECTOR, ".price")
        initial_price = price_element.text
        
        # 다른 옵션 선택
        another_option_button = driver.find_element(By.CSS_SELECTOR, ".another-option-button")
        another_option_button.click()
        
        # 가격 변동 확인
        new_price_element = driver.find_element(By.CSS_SELECTOR, ".price")
        new_price = new_price_element.text
        
        assert initial_price != new_price

    def test_max_quantity_exceeded(self):
        driver.get("https://www.kurly.com")
        product_link = driver.find_element(By.CSS_SELECTOR, ".product-link")
        product_link.click()
        
        # 수량 입력 필드에 최대 수량을 초과하는 값 입력
        quantity_input = driver.find_element(By.CSS_SELECTOR, ".quantity-input")
        quantity_input.send_keys("1000")
        
        # 입력한 수량으로 수량을 확인
        quantity_element = driver.find_element(By.CSS_SELECTOR, ".quantity")
        quantity = quantity_element.text
        
        # 장바구니 또는 바로 구매 버튼 클릭
        cart_button = driver.find_element(By.CSS_SELECTOR, ".cart-button")
        cart_button.click()
        
        # 에러 메시지 확인
        error_message_element = driver.find_element(By.CSS_SELECTOR, ".error-message")
        error_message = error_message_element.text
        
        assert error_message == "수량이 최대 수량을 초과합니다."

    def test_sold_out_product(self):
        driver.get("https://www.kurly.com")
        sold_out_product_link = driver.find_element(By.CSS_SELECTOR, ".sold-out-product-link")
        sold_out_product_link.click()
        
        # "품절" 표시 확인
        sold_out_element = driver.find_element(By.CSS_SELECTOR, ".sold-out")
        sold_out_text = sold_out_element.text
        
        # 구매 버튼 비활성화 확인
        buy_button = driver.find_element(By.CSS_SELECTOR, ".buy-button")
        buy_button_enabled = buy_button.is_enabled()
        
        assert sold_out_text == "품절"
        assert not buy_button_enabled