from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# selenium 4.0 ↑
from selenium.webdriver.common.by import By
from time import sleep
import pickle,re
import unicodedata

chrome_options = Options()
# chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options) 


def create_query_from_input(user_input):
    return_list = []
    word_buffer = ""
    user_input = user_input.replace("シリーズ","") #これは消したほうがよさそう？
    for i,word in enumerate(user_input):
        
        if word in [" ","　",",","、","。","♡","♥","♧","♣","・","+","＋","★","☆",":","：","!","！","~","-","=","～","×",".","♪","♫","♬",";"]:
            return_list.append(word_buffer)
            word_buffer = ""
        else:
            word_buffer += word
        
        if i == len(user_input) -1:
            #最後の状態になったとき
            return_list.append(word_buffer)
    
    return_list = [word for word in return_list if len(word) != 0]

    return return_list

def get_amazon_link_and_img(driver,title,media_type):
    kidle_url = "https://www.amazon.co.jp/b?node=2250738051"
    prime_video_url = "https://www.amazon.co.jp/s?i=instant-video&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=32X0WZ7ZEVPOB&sprefix=%2Cinstant-video%2C170&ref=nb_sb_noss"
    pattern = r"\[.*?\]|（.*?）|\(.*?\)|<.*?>|＜.*?＞|〈.*?〉|《.*?》"
    title = re.sub(pattern, '',title )
    url = None
    if media_type =="manga":
        url=kidle_url
        Word = title + " コミック " + str(1)
    elif media_type=="novel":
        url=kidle_url
        Word = title + " 小説 " + str(1)
    elif media_type =="anime":
        url=prime_video_url
        Word = title

    try:
        driver.get(url)
        # 待機処理
        # driver.implicitly_wait(10)
        sleep(1)
        # wait = WebDriverWait(driver=driver, timeout=60)
        #検索窓 
        
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
        # print(page_url)
       
        return page_url,img_url
    
    except Exception as e:
        print("取得に失敗しました！")
        return None,None


if __name__=="__main__":
    print(get_amazon_link_and_img(driver,title="世界から猫が消えたなら (小説)",media_type="novel"))
    print(get_amazon_link_and_img(driver,title="BLUE DRAGON",media_type="anime"))
    print(get_amazon_link_and_img(driver,title="ONE PIECE",media_type="manga"))
    print(get_amazon_link_and_img(driver,title="明治撃剣-1874-",media_type="anime"))