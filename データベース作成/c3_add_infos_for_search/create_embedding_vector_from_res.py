
import bs4
from bs4 import BeautifulSoup
import requests
import pickle,re
from gpt_async_create_embedding_query  import create_embedding_queries

###################################################################################################
#文字をエスケープするための関数
def encode_filename(filename):
    """Windowsとhtmlでファイル名として使用できない文字を全角文字に置換"""
    replacements = {
        '<': '_enc-01',
        '>': '_enc-02',
        ':': '_enc-03',
        '"': '_enc-04',
        '/': '_enc-05',
        '\\': '_enc-06',  
        '|': '_enc-07',
        '?': '_enc-08',
        '*': '_enc-09',
        '&': '_enc-10',
        '+': '_enc-11',
        '#': '_enc-12',
        '%': '_enc-13',
        "'": '_enc-14',    
        '`':  '_enc-15',   
        '^': '_enc-16',   
        ')': '_enc-17',   
        '(': '_enc-18',   
        '}': '_enc-19',   
        '{': '_enc-20',   
        ']': '_enc-21',   
        '[': '_enc-22',   
        ';': '_enc-23',   
        '@': '_enc-24',   
        '=': '_enc-25',   
        '$': '_enc-26',   
        ',': '_enc-27',   
        ' ': '_enc-28',
        '　':'_enc-29',
        '（':'_enc-30', #なんか全角の場合もCSSセレクタとして使用するのはだめっぽい
        '）':'_enc-31',
    }
    for src, target in replacements.items():
        filename = filename.replace(src, target)
    return filename

def decode_filename(filename):
    """encodeしたファイル名をdecodeして戻す"""
    replacements = {
        '_enc-01': '<',
        '_enc-02': '>',
        '_enc-03': ':',
        '_enc-04': '"',
        '_enc-05': '/',
        '_enc-06': '\\',
        '_enc-07': '|',
        '_enc-08': '?',
        '_enc-09': '*',
        '_enc-10': '&',
        '_enc-11': '+',
        '_enc-12': '#',
        '_enc-13': '%',
        '_enc-14': "'",
        '_enc-15': '`',
        '_enc-16': '^',
        '_enc-17': ')',
        '_enc-18': '(',
        '_enc-19': '}',
        '_enc-20': '{',
        '_enc-21': ']',
        '_enc-22': '[',
        '_enc-23': ';',
        '_enc-24': '@',
        '_enc-25': '=',
        '_enc-26': '$',
        '_enc-27': ',',
        '_enc-28': ' ',
        '_enc-29': '　',
        '_enc-30':'（',
        '_enc-31':'）',
    }
    for src, target in replacements.items():
        filename = filename.replace(src, target)
    return filename
###################################################################################################

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

    for h2_title,text in return_dict.items():
        return_dict[h2_title] = text[:5000] if len(text) > 5000 else text #embeddingの大きさに収まるようにstlipする
        # print(f"{h2_title}   : {text}")

    return_embedding_vector = []
    #概要は必ずあるので、ストーリーと登場人物がない場合を下に記述する。基本は概要をコピペか、ストーリーと登場人物は相互に補完し合う。
    #効率化のため、embeddingしたvectorをほかにコピペするという操作を行う
    # bool("") = False らしいのでこの性質を利用している
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
    elif return_dict["ストーリー"] and return_dict["登場人物"]:
        #すべてが揃っている場合
        r = create_embedding_queries([return_dict["概要"],return_dict["ストーリー"],return_dict["登場人物"]])
        overview_vecotr,story_vector,character_vector = r[0],r[1],r[2]
        return_embedding_vector = [overview_vecotr,story_vector,character_vector]


    return  return_embedding_vector

if __name__ =="__main__":
    res = requests.get("https://ja.wikipedia.org/wiki/%E3%82%B8%E3%83%A3%E3%83%B3%E3%82%B0%E3%83%AB%E5%A4%A7%E5%B8%9D")    
    soup = BeautifulSoup(res.content, 'html.parser')
    result =  create_embedding_vector_from_res(soup)
    for r in result:
        print(len(r))