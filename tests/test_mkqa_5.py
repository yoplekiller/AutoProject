import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@pytest.mark.parametrize("tc_id, test_item, precondition, test_steps, expected_result", [
    ("TC-001", "상품 상세에서 장바구니 담기 클릭 시 장바구니에 추가됨", "로그인 상태, 특정 상품 상세 페이지에 접근함", 
     "1. 로그인 상태에서 특정 상품 상세 페이지에 접근\n2. \"장바구니 담기\" 버튼 클릭\n3. 장바구니 페이지에서 해당 상품의 existence 확인", 
     "장바구니 페이지에 해당 상품이 추가되어 표시됨"),
    ("TC-002", "장바구니에서 수량 증가/감소 시 합계 금액 재계산", "로그인 상태, 장바구니에 특정 상품이存在", 
     "1. 장바구니 페이지에서 수량을 1 증가시킴\n2. 합계 금액이 정상적으로 증가하는지 확인\n3. 수량을 1 감소시킴\n4. 합계 금액이 정상적으로 감소하는지 확인", 
     "합계 금액이 현재 수량에 따라 정상적으로 계산됨"),
    ("TC-003", "비로그인状态에서 장바구니 담기 시 로그인 페이지 이동", "비로그인 상태, 특정 상품 상세 페이지에 접근함", 
     "1. 비로그인 상태에서 특정 상품 상세 페이지에 접근\n2. \"장바구니 담기\" 버튼 클릭\n3. 페이지 이동 확인", 
     "로그인 페이지로 이동함")
])
def test_kurly(tc_id, test_item, precondition, test_steps, expected_result):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com")

    if tc_id == "TC-001":
        # 로그인
        driver.find_element(By.XPATH, "//a[@href='/login']").click()
        driver.find_element(By.NAME, "username").send_keys("username")
        driver.find_element(By.NAME, "password").send_keys("password")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # 상품 상세 페이지 접근
        driver.get("https://www.kurly.com/shop/goods/goods_view.php?goodsno=12345")
        
        # 장바구니 담기 클릭
        driver.find_element(By.XPATH, "//button[@id='add_cart']").click()
        
        # 장바구니 페이지에서 해당 상품의 existence 확인
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='cart-item']")))
        
    elif tc_id == "TC-002":
        # 로그인
        driver.find_element(By.XPATH, "//a[@href='/login']").click()
        driver.find_element(By.NAME, "username").send_keys("username")
        driver.find_element(By.NAME, "password").send_keys("password")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # 장바구니 페이지 접근
        driver.get("https://www.kurly.com/member/cart.php")
        
        # 수량 증가
        driver.find_element(By.XPATH, "//button[@class='increase']").click()
        
        # 합계 금액 확인
        total_price = driver.find_element(By.XPATH, "//span[@class='total-price']").text
        
        # 수량 감소
        driver.find_element(By.XPATH, "//button[@class='decrease']").click()
        
        # 합계 금액 확인
        new_total_price = driver.find_element(By.XPATH, "//span[@class='total-price']").text
        
        # 확인
        assert total_price != new_total_price
        
    elif tc_id == "TC-003":
        # 상품 상세 페이지 접근
        driver.get("https://www.kurly.com/shop/goods/goods_view.php?goodsno=12345")
        
        # 장바구니 담기 클릭
        driver.find_element(By.XPATH, "//button[@id='add_cart']").click()
        
        # 로그인 페이지 이동 확인
        WebDriverWait(driver, 10).until(EC.url_contains("login"))

    driver.quit()

def test_kurly_detail():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com")

    # 로그인
    driver.find_element(By.XPATH, "//a[@href='/login']").click()
    driver.find_element(By.NAME, "username").send_keys("username")
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # 상품 상세 페이지 접근
    driver.get("https://www.kurly.com/shop/goods/goods_view.php?goodsno=12345")
    
    # 장바구니 담기 클릭
    driver.find_element(By.XPATH, "//button[@id='add_cart']").click()
    
    # 장바구니 페이지에서 해당 상품의 existence 확인
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='cart-item']")))
    
    driver.quit()

def test_kurly_cart():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com")

    # 로그인
    driver.find_element(By.XPATH, "//a[@href='/login']").click()
    driver.find_element(By.NAME, "username").send_keys("username")
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # 장바구니 페이지 접근
    driver.get("https://www.kurly.com/member/cart.php")
    
    # 수량 증가
    driver.find_element(By.XPATH, "//button[@class='increase']").click()
    
    # 합계 금액 확인
    total_price = driver.find_element(By.XPATH, "//span[@class='total-price']").text
    
    # 수량 감소
    driver.find_element(By.XPATH, "//button[@class='decrease']").click()
    
    # 합계 금액 확인
    new_total_price = driver.find_element(By.XPATH, "//span[@class='total-price']").text
    
    # 확인
    assert total_price != new_total_price
    
    driver.quit()

def test_kurly_no_login():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.kurly.com")

    # 상품 상세 페이지 접근
    driver.get("https://www.kurly.com/shop/goods/goods_view.php?goodsno=12345")
    
    # 장바구니 담기 클릭
    driver.find_element(By.XPATH, "//button[@id='add_cart']").click()
    
    # 로그인 페이지 이동 확인
    WebDriverWait(driver, 10).until(EC.url_contains("login"))
    
    driver.quit()