
import bs4
from bs4 import BeautifulSoup
import requests
import pickle,re
from gpt_async_create_embedding_query  import create_embedding_queries

def create_embedding_vector_from_res(soup):
   
    main_div:bs4.element.Tag = soup.find("div",class_ ="mw-body-content" )
    elements = main_div.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','h5']) #ここのdlを消してもそれなりには動作します

    pattern = r'\[.*?\]'

    h2_dict = {}
    h2_title = "要約"
    word_buff = ""
    for element in elements:
        managed_text = re.sub(pattern, '',element.get_text())
        if element.name =='h2':
            # print(f"=========={h2_title}==========")
            # print(word_buff)
            h2_dict[h2_title] = word_buff
            h2_title  = managed_text
            word_buff = ""
            continue
        else:
            word_buff += managed_text

    return_dict = {"概要":"","ストーリー":"","登場人物":""}
    for h2_title,text in h2_dict.items():
        text = text.replace("\n","")
        if text =="":continue #文章がない場合は何も記載しない
        if any(keyword in h2_title for keyword in ["概要", "沿革","概説","作品内容","要約"]):return_dict["概要"]+=text
        elif any(keyword in h2_title for keyword in ["あらすじ", "ストーリー", "物語", "粗筋"]):return_dict["ストーリー"]+=text
        elif any(keyword in h2_title for keyword in ["登場人物", "キャラクター","登場"]):return_dict["登場人物"]+=text

    # for h2_title,text in return_dict.items():
    #     print(f"{h2_title}   : {text}")

    return_embedding_vector = []
    #概要は必ずあるので、ストーリーと登場人物がない場合を下に記述する。基本は概要をコピペか、ストーリーと登場人物は相互に補完し合う。
    #効率化のため、embeddingしたvectorをほかにコピペするという操作を行う
    if not  return_dict["ストーリー"] and not  return_dict["登場人物"]:
        overview_vecotr = create_embedding_queries([return_dict["概要"]])[0]
        return_embedding_vector = [overview_vecotr,overview_vecotr,overview_vecotr] #概要ベクトルをコピペする
    elif   return_dict["ストーリー"] and not  return_dict["登場人物"]:
        r = create_embedding_queries([return_dict["概要"],return_dict["ストーリー"]])
        overview_vecotr,story_vector = r[0],r[1]
        return_embedding_vector = [overview_vecotr,story_vector,story_vector] #ストーリーをコピペする
    elif not return_dict["ストーリー"] and return_dict["登場人物"]:
        r = create_embedding_queries([return_dict["概要"],return_dict["登場人物"]])
        overview_vecotr,character_vector = r[0],r[1]
        return_embedding_vector = [overview_vecotr,character_vector,character_vector] #キャラクターをコピペする


    return  return_embedding_vector

if __name__ =="__main__":
    res = requests.get("https://ja.wikipedia.org/wiki/%E3%82%AF%E3%82%BA%E3%81%8C%E8%81%96%E5%89%A3%E6%8B%BE%E3%81%A3%E3%81%9F%E7%B5%90%E6%9E%9C#%E3%81%82%E3%82%89%E3%81%99%E3%81%98")    
    soup = BeautifulSoup(res.content, 'html.parser')
    result =  create_embedding_vector_from_res(soup)
    for r in result:
        print(len(r))