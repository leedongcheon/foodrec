import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import numpy as np

import re

def split_np(str_):
    p1 = re.compile('[0-9]+,[0-9]+원')
    p2 = re.compile('[0-9]+원')
    
    try:
        a1 = p1.search(str_).group()
        name = str_.replace(a1, "").strip().split("\n")[0]
        return name, a1
    except:
        a2 = p2.search(str_).group()
        name = str_.replace(a2, "").strip().split("\n")[0]
        return name, a2

def extract_from_map(input_, target):
    # input_ 사용자가 검색할 단어
    # target: 어떤 정보를 원하는지 분류한 변수
    
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 창 없애는 옵션 (이건 작동 안한다)
    # chrome_options.add_argument("headless")
    # 브라우저 창을 숨기는 옵션
    #chrome_options.add_argument("--window-position=-32000,-32000")

    # 웹드라이버 초기화
    driver = webdriver.Chrome(options=chrome_options)

    # 네이버 지도 접속
    url = "https://map.naver.com/p?c=15.00,0,0,0,dh"
    driver.get(url)
    time.sleep(2)

    # 현재 위치로 조정
    current_location = driver.find_element(By.XPATH, '//*[@id="app-layout"]/div[2]/div[1]/div[3]/div[1]/div/button')
    current_location.click()
    time.sleep(2)

    # 줌 아웃
    zoom_out = driver.find_element(By.XPATH, '//*[@id="app-layout"]/div[2]/div[1]/div[3]/div[2]/button[2]')
    zoom_out.click()
    time.sleep(1)

    # 검색창에 음식 검색하기
    input_button = driver.find_element(By.CLASS_NAME, 'input_search')
    input_button.send_keys(input_)
    input_button.send_keys(Keys.ENTER)
    time.sleep(2)

    # 가게 정보 저장
    shop_dict = {}

    # 가게 정보 접근하기
    driver.switch_to.frame('searchIframe')
    temp = driver.find_elements(By.XPATH, '//*[@id="_pcmap_list_scroll_container"]/ul/li')
    
    information = {}
    
    # 제일 위에 있는 음식점을 가져온다.
    # 가게 클릭
    try:
        try:
            shop = temp[0].find_element(By.XPATH, 'div[1]/div[2]/a[1]/div/div')
            shop_name = shop.text
            shop.click()
            time.sleep(2)
            
            driver.switch_to.default_content()
            driver.switch_to.frame('entryIframe')
        except:
            shop = temp[0].find_element(By.XPATH, 'div[1]/a/div/div')
            shop_name = shop.text
            shop.click()
            time.sleep(2)
            
            driver.switch_to.default_content()
            driver.switch_to.frame('entryIframe')
    except:   
        driver.switch_to.default_content()
        driver.switch_to.frame('entryIframe')
    
    if target == "menu":
        menu_button = driver.find_elements(By.CLASS_NAME, 'veBoZ')
        for s in range(len(menu_button)):
            if menu_button[s].text == "메뉴":
                menu_button[s].click()
                break
        time.sleep(2)
        
        # 메뉴 정보 가져오기 (메뉴 이름, 가격, 이미지)
        
        # 메뉴 이름, 가격
        bb = driver.find_elements(By.CLASS_NAME, 'MXkFw')
        menu_list = np.array(list(map(lambda x: split_np(x.text), bb)))
        print(menu_list)
        
        # 메뉴 이미지
        images = driver.find_elements(By.CLASS_NAME, 'E2jtL')
        image_list = list(map(lambda x: x.find_element(By.TAG_NAME, "img").get_attribute('src'), images))
        
        
        # information에 정보 저장하기
        information["menu_name"] = list(menu_list[:, 0])
        information["menu_price"] = list(menu_list[:, 1])
        information["menu_image"] = image_list 
        
    if target == "review":
        menu_button = driver.find_elements(By.CLASS_NAME, 'veBoZ')
        for s in range(len(menu_button)):
            if menu_button[s].text == "리뷰":
                menu_button[s].click()
                break
        time.sleep(2)

        # 리뷰 정보 가져오기
        bb = driver.find_elements(By.CLASS_NAME, 'zPfVt')
        review_list = list(map(lambda x: x.text, bb))

        # information에 정보 저장하기
        information["review"] = review_list
        
    # shop_dict에 information 저장하기
    shop_dict[shop_name] = information

    driver.quit()
    
    return shop_dict

# 예시로 실행
#output = extract_from_map("동향", "menu")
#print(output)
