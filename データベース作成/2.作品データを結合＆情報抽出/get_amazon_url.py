from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# selenium 4.0 ↑
from selenium.webdriver.common.by import By
from time import sleep
import pickle
import unicodedata

chrome_options = Options()
# chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options) 


with open("manga_title_list.pickle", mode='br') as fi:
    loaded_manga_list = pickle.load(fi)

def create_query_from_input(user_input):
    return_list = []
    word_buffer = ""
    for i,word in enumerate(user_input):
        
        if word in [" ","　",",","、","。"]:
            return_list.append(word_buffer)
            word_buffer = ""
        else:
            word_buffer += word
        
        if i == len(user_input) -1:
            #最後の状態になったとき
            return_list.append(word_buffer)
    
    return_list = [word for word in return_list if len(word) != 0]
    return return_list




count = 1
manga_title_and_amazon_url_list = []
for data in loaded_manga_list:
    year,title,url = data

    if year < 1900:
        continue
    # amazonのURL開く

    if count%50 == 0:
        with open("manga_title_and_amazon_url_list.pickle",mode="wb") as fi:
            pickle.dump(manga_title_and_amazon_url_list,fi)
    print(f"{count}: {title}")
    try:
        driver.get("https://www.amazon.co.jp/b?node=2250738051")
        # 待機処理
        # driver.implicitly_wait(10)
        sleep(1)
        wait = WebDriverWait(driver=driver, timeout=60)
        #検索窓 
        Word = title + " " + str(1)
        driver.find_element(By.ID, "twotabsearchtextbox").send_keys(Word)
        sleep(1)
        driver.find_element(By.ID,"nav-search-submit-button").click()
        #商品URLの取得 
        # URLS = driver.find_elements(By.CSS_SELECTOR,"a.a-link-normal.s-no-outline")
        #elenet = driver.find_element(By.CLASS_NAME,value = "s-image") #full xpathというものをコピーする
        # img_url = driver.find_element(By.CLASS_NAME,value = "s-image").get_attribute("src")
        # page_url = driver.find_element(By.CSS_SELECTOR,value = "a.a-link-normal.s-no-outline").get_attribute("href")
        # page_url = page_url.split("ref=")[0] #入力文字列などの情報は必要ないのでここで切っている
        elements =  driver.find_elements(By.CSS_SELECTOR,value = "a.a-link-normal.s-no-outline") #a-link-normal s-no-outlineがコピペだが、半角空白は.で埋め合わせる必要がある？

        title = title.replace("(漫画)","")
        title = title.replace("(アニメ)","")
        title = unicodedata.normalize('NFKC', title) #正規化して全角や半角などどちらにも対応させる　例えばRANGEとRANGEとは半角と全角の違いがあっるため一緒に処理はできないのだ
        splited_title_list = create_query_from_input(title)
        for element_ in elements:
            elemtt_title = element_.find_element(By.CLASS_NAME,value = "s-image").get_attribute("alt")
            elemtt_title = unicodedata.normalize('NFKC', elemtt_title)
            if any([splited_title in elemtt_title for splited_title in splited_title_list]):
                element  = element_
                break

        page_url = element.get_attribute("href").split("ref=")[0] 
        # page_url  = "https://www.amazon.co.jp" + page_url
        img_url = element.find_element(By.CLASS_NAME,value = "s-image").get_attribute("src")
        print(page_url)
        manga_title_and_amazon_url_list.append([year,title,url,page_url,img_url]) #年、タイトル、wikiurl,amazonページurl,漫画画像url
        # print(img_url)
    
    except Exception as e:
        continue
    finally:
        count +=1