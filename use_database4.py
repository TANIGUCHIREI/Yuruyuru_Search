#20240130記述　descriptionをwikipedia apiを使うのではなく本来のwiki htmlから取得する新スタイルにしています
#ファイルを読み込む。"./manga_title_list.pickle"漫画のタイトルとURLを含む。
#htmlファイルをメモリに展開するのではなくSSDから直接読み込むことにした
#20230216追記（卒論発表直後）配列をforで回すのではなく行列計算により高速にすべて検索ができるように対応させる
import os, json, pickle,re
import openai
from openai import OpenAI
import pickle,gc
import torch
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
except:
    from dotenv import load_dotenv
    dotenv_path = '.env'
    load_dotenv(dotenv_path)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# print(OPENAI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)


year_and_data_dict = {}
page_title_dict = {}

with open ("./data_for_search/info_for_search_dict.pickle", mode='br') as f:
    info_for_search_dict  = pickle.load(f)
    for page_title,data in info_for_search_dict.items():
        #データを収集しした逆のやり方でimgとamaozn_urlを取得する
        media_type = None
        if data["media_types"]["manga"]:
            media_type="manga"
        elif data["media_types"]["novel"]:
            media_type="novel"
        elif data["media_types"]["anime"]:
            media_type="anime"
        for index,media_data in enumerate(data["media_dict"][media_type]):
            if media_data["amazon_img"] !="":
                amazon_img =media_data["amazon_img"]
                amazon_url = media_data["amazon_url"]
        year, title, url,amazon_url,img_url,actors_dict,genre,infobox_dict,media_types,categories,theme,protagonist,place = data["page_year"], data["page_url"],page_title,amazon_url,amazon_img,data["actor_dict"],data["genre"],data["infobox_dict"],data["media_types"],data["categories"],data["theme_list"],data["protagonist_list"],data["place_list"]
        page_title_dict[page_title] = [year,url,amazon_url,img_url,actors_dict,genre,infobox_dict,media_types,categories,theme,protagonist,place]

        #次にyear_and_data_dictの作成
        try:year_and_data_dict[year].append({"title":page_title,"raw_categories":data["categories"],"actors_dict":data["actor_dict"],"infobox_list":data["infobox_list"],"theme_list":data["theme_list"],"protagonist_list":data["protagonist_list"],"place_list":data["place_list"]})
        except: year_and_data_dict[year] = [{"title":page_title,"raw_categories":data["categories"],"actors_dict":data["actor_dict"],"infobox_list":data["infobox_list"],"theme_list":data["theme_list"],"protagonist_list":data["protagonist_list"],"place_list":data["place_list"]}]




# with open("./data_for_search/categories_list.pickle","rb") as f:
#     full_categories_list = pickle.load(f)




############torchの行列計算に対応したcategory行列を読み込む
# with open("./category_and_embedding_matrix/category_list.pickle","rb") as f:
#     category_list = pickle.load(f)

# with open("./category_and_embedding_matrix/category_embedding_matrix.pickle","rb") as f:
#     category_embedding_matrix = pickle.load(f)


##################以下は似た漫画をサジェストするための読み込み部分＆関数、最終的にuse_database4.pyを作る予定############
#保存した行列たちを読み出す

with open("./data_for_search/title_and_embedding_matrix/title_list.pickle","rb") as f:
    title_list = pickle.load(f)

with open("./data_for_search/title_and_embedding_matrix/overview_embedding_matrix.pickle","rb") as f:
    overview_embedding_matrix = pickle.load(f)

with open("./data_for_search/title_and_embedding_matrix/story_embedding_matrix.pickle","rb") as f:
    story_embedding_matrix = pickle.load(f)

with open("./data_for_search/title_and_embedding_matrix/character_embedding_matrix .pickle","rb") as f:
    character_embedding_matrix = pickle.load(f)

# embedding_matrix_list =[overview_embedding_matrix,story_embedding_matrix,character_embedding_matrix ]
combined_matrix = torch.hstack((overview_embedding_matrix,story_embedding_matrix,character_embedding_matrix ))

del overview_embedding_matrix
gc.collect()
del story_embedding_matrix
gc.collect()
del character_embedding_matrix
gc.collect()
# gc.collect()でメモリ解放

mask_vector = torch.cat([torch.zeros(512), torch.ones(1024)]) #overviewが0のマスク用のベクトル

def create_sililar_contents_list(title:str,num:int):
    title_index = title_list.index(title)
    title_vector = combined_matrix[title_index]
    sum = torch.mm(combined_matrix,title_vector.T.reshape(title_vector.T.shape[0],1)) #torchでの２次元行列のdotはmmを使うらしい
    sum  = sum.reshape(sum.shape[0])/3 
    _, result = torch.sort(sum, descending=True)
    # Converting result to a list
    result_list = result.tolist()
    result_list.pop(0) #はじめは確定で自分だから
    similar_contents_dict  = {"manga":[],"anime":[],"novel":[]}

    for index, result in enumerate(result_list):
        title = title_list[result]
        media_types = info_for_search_dict[title]["media_types"]
        # print(media_types)
        year = page_title_dict[title][0]
        img_url = page_title_dict[title][3]
        url =  "/manga_page?title=" + encode_filename(title) +"&year=" + str(year)
        data  ={"title":title,"url":url,"img_url":img_url}
        if media_types["manga"] and len(similar_contents_dict["manga"])<num:similar_contents_dict["manga"].append(data)
        elif media_types["anime"]and len(similar_contents_dict["anime"])<num:similar_contents_dict["anime"].append(data)
        elif media_types["novel"]and len(similar_contents_dict["novel"])<num:similar_contents_dict["novel"].append(data)
        if all([True if len(similar_contents_dict[media_type])>num else False for media_type in similar_contents_dict ]) :break

    return similar_contents_dict

print("似た漫画を出力する部分の読み込み終了！")
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
#titleとyearからhtmlを活用してdescriptionを作成するためのプログラム,use_database.ipynbの最後の方に開発用のコードあります
import bs4
from bs4 import BeautifulSoup
def create_dict_from_wikihtml(manga_title,soup)->dict:
    main_div:bs4.element.Tag = soup.find("div",class_ ="mw-body-content" )
    pattern = r'\[.*?\]'
    init_table = soup.find("table",class_ ="infobox bordered" )
    if init_table:
      
        init_table.decompose() #一番初めにはテーブルは必要ないので消去する
    elements = main_div.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div',"dl",'h5']) #ここのdlを消してもそれなりには動作します
    
    def create_links_from_character_name(manga_title ,character_name):
        name = re.sub(r"（.*?）|〈.*?〉|\(.*?\)|《.*?》", "",character_name) #天野月（あまの あかり） みたいなやつから 天野月　のみを取得
        name = name.replace(" ","").replace("　","").split("/")[0] #名前のスペースはなくした方がいいっぽい /で名前が切られることがあるのでその対策用
        manga_title_ = decode_filename(manga_title).replace(" ","%20").replace("　","%20")
        merged_manga_title = decode_filename(manga_title).replace(" ","").replace("　","") #pixivなどでの検索用にスペースをなくしたver
        search_text = '%20'.join([manga_title_,name])
        google_href = f"https://www.google.com/search?q={search_text}"
        twitter_href = f"https://twitter.com/search?q={search_text}&src=recent_search_click"
        pixiv_href =  f"https://www.pixiv.net/tags/{'%20'.join([merged_manga_title,name])}"
        niconico_href = f"https://seiga.nicovideo.jp/search/{'%20'.join([merged_manga_title,name])}?target=illust"
        pinterest_href =f"https://www.pinterest.jp/search/pins/?q={'%20'.join([merged_manga_title,name])}&rs=typed"

        return  f"""<a href={google_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADmUlEQVR4Ab1XA5AjQRQ9G6UrnV0627Zt27Zt27Zt27Z9FyeXiZN3v1NzW9vTmd3J6lW9cKbf6690EmlFIBDIQGzr9/vXE+8RjUSPTIP82Xq6pg27VvPCGoTz08KbiE5oBF3rIG6ge/PGWBhAGlpkAdEHzRCMeInzyEjqcHedj258gbgBM/KU1syjVbwo3aBHCPh+foe0YyMsw/vC0KI2dDVLQ1ejFAzNasI8tDekLWvh+/5VzYQOQGENOxfFfb9+wDplNHTVS0JXrUTUpGusk0aye0Ka4CPBi6cNFXbn2RPQ16vIi2igvn4luC6dVUuHWBOs4KCAtGtzOKICbXOnqKVjbqhW8yl2rrqwqUcb2Nctg/P4QThPHKLXy2Hq2ZYXXzgTCARUu4NLBetzZbHp61YQhI3tG8N9/zbU4L53C4bW9fF3+XwtnbH+f79nVA4Z++IBgri5fxcEbDZEh4Bk19qaEkUhPQt/W24Bxwd4z6SEdVSOCHHWcn6LCXEN0m7Fwr+ec/ZpJrznkwcpLcsEfZ3icJ4+hvgAaa9hBu5x+X9Qk4lH0H0wJ+D1xpeB28yAEZHgvZqFM+B71gZRoeoMu2ZeeuEVBhMz4OEMXEjJGfC/nxBnBnbc8CgNuBPUwKYr7pAGDFGm4GnrODOw97YQAZ1YhA9rcQa+Xy0Ij9+LcPFR5xcMXHnlFYtQbMPZEeLHTuRE+d2NcfjDeYSL3bc8goFfloDYhuwMxw+iT3CcT42Zh4uh+O5mQdY83BUGpxla8dcZQPPFEifeeY0j1CBqGTxskhPu20W3pjJhju3PjIDFHf0o9viAUbucwu73iPmXAKT7/2O0AZHw065Dxf3tBBP1j/bC1R/3oYa35s/odmQ3CVo5cRYNh1sI/9rIP8d5/X6+0k59vioLi2x+ciAWPNyEvW9PYd+701jxdAe6nx+HErubB78vtXkUqsz5FmHg2mufUtxDmrmVB5J5UGDb6yOCuFaW2NEZFRfeFXpfNjBL7Rj+DAqc+XKd0tE+bAOl9rTEuqdHQok/BpBK7VyYRz69cvgl6THu5iKU3NNck3ivixPxyvQhlPhvALmi+0NSmDfBF+eWV4fQ//JU1DnSA6X3tmQ7pTbthh4XJgRr4bXpI2QI4rTBQurKYiSeIo7Awi7sXIOJ1Oz0SvTGQthDnKWW83CisZ4ohSEsEdfKrRY3YAdIYis2v4m3iTqiW6ZO/mwNG6/yhNOEf6HhfzYhUKeuAAAAAElFTkSuQmCC></a> \
                    <a href={twitter_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAAAAABWESUoAAAA3ElEQVR4Ac2SGQDFMBBE1ylOcYpTner0neK0TnGpU53iFKc6xWl+p+f25D7InZ295Cv0mGjFUOzWDVVVa/WykaBiaBBFfsiyory3JASRjs8mInqxUGRw47CIBIy7Ew0Sh0nED4OXCwkNh8h7GrrgCkVK9a7w6Q2BjoVa6Oo9EZEDVJ7I1M4UeMDXzIEhvoukFxNMaP8o4gpon1l9qnqc7DcPIgpd7Ce0t/fJVO0q0qIsVeuY1XwNYK1gwm8J2GAqvHRF5mD7BcG0Rl6yegjw0BqdakE8Bni0RyjyDf4Y1Y0n0wNT4wAAAABJRU5ErkJggg==></a> \
                    <a href={pixiv_href}><img src = data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADqUlEQVR4AbxWA7AlSRC8x8DZtsJn2w6dbTN8DpzNz7PNtW3btr/xumdys7YqthcTE/tWHZHjrsxCV88u60ZVKWfni4iORB2B7Yw6s31R4NSLjJ3fJrCT8Hbg3pjcEZ6IdwBpbLZdEKHklxGRojziTEC5QoyP3Dz8ay/8lhDmqkvI15SQrbbnlYaEdykwLnLzsIpAmvcZM5wRok+Ij+xcSdIaQggriI8Nn+uzFCHGRe5UYkIIMhVKWqTBS/53+GhchCHLYixpBta0A3XEYl53WxDj2UEeR//kKFDnqYgUIckvdGKuSj064JsSXh0RQQhlLGsBfpkR4YWhHg/39XhqgMcn4yPMbogho80D30yNcMi3nP+pOJEiIuGhTviMZ3rwHD1a1abEfRfHOPcfh2ylRMTwsZ4zhIT+hi4eC5ri9ULP+1uikSIikZxGT/jZYfjyGDbQUAIO/UrJslVaExvDaoHvj/zeYUa9zpUUnfqbE4eS07Fx2JX8hs4eLR4Scvw2M4KMRgo4jIZZeKl5LdaqjQvouTP9I+hIIdRVogCq13zd3ctDRpMDTmQU7uuh9/X05BAR8HmaAEXeovjnrAg2cFdPL8/IkyaAuXq0nxLe24sT3mpnVZcrINi6pZuHDfw9O6KDKQIUGoWu82Nc/A/J3muXCoeMujIEyHv5TiJYsiDMYk0Ua7R3ZJIF2AtW/n4str2+1oJ6YisEZEyAfC+1I0NW0r7fqP3MhvOTJkvHy1tBPtF/6yNw9I8OrQ4cWtB7fJUagYCMFtJWCggFfcV/xs4xeGms3qf3AcM2CijUaPoqJ4RV8NIwXQW0uzUCdBUc/oOjF+kCCrW6Ak7+1aHZh/AfFPK/NQK0ox38lea2sGEHrA7XWeuEQjZuVeiit3X32o6VvEwBtgraI+AmMWTbbtgLDLYXXN3Jc8kpuedJNqtAvhUCnjQBztK5ug3owj7x+qgIjzM6d7DDPUiS98ZGmLomeD2ERXfWXy6p+219Ci781+HZgR69Fuq/gA98iHg9oy5G5cQIF7H6sxUpW3EZAjbuhFJI77cj87EW1O6sicNYmLJJ7f5lKaTnE90xg+dbK+CDEh6xzWllKyvZGklBvVLCzw0VoX8kEKcKiJMakRDtRq9+se3Yx5Cd0ogCWPmEzSkfcdJPKQ3qH5Hk8p85MWonR/hheiRnikpop2tHMkY0SvE3y6fAW8CI7EaRxZjNcrwdE8YZsMKGQNxS0DEZ6K7ZwHdOB7x7DgDk/b2t3wK9bgAAAABJRU5ErkJggg==></a>\
                    <a href={niconico_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgAgMAAAAOFJJnAAAADFBMVEUAAAD///8zMzMz/wD7IzGqAAAAAXRSTlMAQObYZgAAAH1JREFUeAGFjoEJgCAQRU+AJqjmCYAm6NpBW8ag2sFriOapIbKfgoUBfR7wQP/dESkGDREVYgGklglABr8DfInSULH5Y/WnfUQZWRZx6EdBq+J25C5IPwcxguBJRcGcmZHevkUz6z/5trAiF+NyyVrpjHQYVfeKjhAdQMrABfe1YqRAJseVAAAAAElFTkSuQmCC ></a>\
                    <a href={pinterest_href}><img src=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAZlBMVEVHcEzmACLnCynmACLmACPmACPmACPmACPmACPmACHjACDmACLmABvsUGLmACPmABrmABDlAAHrN07zkp76xs3////94ub3tr7uZnP2p7H+7vH82uDpK0LsS1z6ztPwe4b/9/npETQSvJBdAAAAFXRSTlMAJUybvur/9sYgD4ujGdH///////pX1IjeAAABh0lEQVR4AW1TBwKDMAiMK7Z1ENS45/8/2QDGzuvmrmzUC0EYxYnW6S0K7+oXj8yRHkl+/6H1F7LHO1+U+gflmyJM9R+k4eX/5MEgItDrVBQnf/o3Vd1Yh7brNbxHkfwAh9F6TDNKpsTfhV9aR4yrA+tqUZCLnL/hSNZFG6OXmhSLOV3cE47fuNgVggRbnHqs6EcSqJBtZFoMVcDyjdyxi1BFHGCwdkCYh32VgK1zwdpI3dgw2b0HHPwfDaXB8WKVssBVdoCxDh36GJKEkiKtXTVUlj18CDQLxIMIDvCCgymVnEmNC4Dl1HwO/C1VsTcMiCN3UJK2K3+7qejqAye5UQpwXH2IpFHa9HbHxZl7IH6leYE0KkhEsdU4cJUGsfGudHL309bGwMqTrofxNc2c9kULoGqdAyuotcA5uFxAT6Ut09ROw4HnavuV86WuCHqeDwOfi13IPBpf5LXWj4+1l4n+rr2PQoL143CKz9MjQW9+T+/CPW9W9GzyQ3OuYXRLHRlHYfCyPgEPdSsJLTPFFAAAAABJRU5ErkJggg==></a>\
                    """ 
    
    def create_details_from_dl(h2_title,element):
        return_html = ""
        ignore_elements = [] #dlなどに入っている重複しているものは除くためのリスト
        for index,e in enumerate(element):
            managed_text = re.sub(pattern, '',e.get_text())
            if e in ignore_elements:continue #すでに処理したエレメントについては処理を飛ばす

            if bool(e.find_all('dl')):
                return_html+=create_details_from_dl(h2_title,e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5']))
            else:
                #dlは含まれていない,dd,dtのみで構成されている
                if e.name =='dt':
                    dd_text =''
                    init_dd_text = '' #声 - を取得する用のやつ、ここに入っているかいないかで後の動作を決定
                    actors_disc =''
                    dd_index = index+1
                    while True:
                        try:
                            if element[dd_index].name == 'dd':
                                
                                dd_text+=re.sub(pattern, '',element[dd_index].get_text())
                                if dd_index == index+1 and ("声" in dd_text or "演" in dd_text): 
                                    init_dd_text = dd_text #一番最初のテキストを取得
                                    actors = element[dd_index].find_all('a')
                                    actors_disc = init_dd_text #まずは平文として取得
                                    # print(actors_disc)
                                    for actor in actors:
                                        # print(actor.get_text())
                                        if actor.get_text() =="声":continue #「声」一文字の場合は除外する
                                        actors_disc = actors_disc.replace(actor.get_text(),f'<a href= /search_by_category?category=担当:{actor.get_text()}>{actor.get_text()}</a>')

                                if re.sub(pattern, '',element[dd_index].get_text())!='':dd_text+= "<br>" 
                                if bool(element[dd_index].find_all('dl')):
                                    # print(element[dd_index].find('dl').get_text())
                                    dd_text = re.sub(pattern, '',dd_text.replace(element[dd_index].find('dl').get_text(),"")) #AIの遺電子の須藤光のところがやばい。ddのなかにdlが入っていてddのテキストのみを取得できない。対処療法だけどddのテキストからdlのテキストを消すことで回避
                                
                                ignore_elements.append(element[dd_index]) #これ以降forの中でdl以外でこのddが出てきても無視する
                                ignore_elements+=element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5','h5'])#中身も全て消す
                                dd_index+=1
                            
                            elif element[dd_index].name == 'dl':
                                dd_text+=create_details_from_dl(h2_title,element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5','h5']))
                                ignore_elements.append(element[dd_index])
                                ignore_elements+=element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5'])#中身も全て消す
                                dd_index+=1
                            else:break #dtなどが来たらbreak
                        
                        except:break #list index out of range になるときがある対策
                    
                    if any([ word in h2_title for word in ["登場人物", "キャラクター","キャスト"]])and ("声 -"in init_dd_text or not '<div class="details_content">' in dd_text):
                        # print(managed_text ) #登場人物の最下層(下にdetailsが存在しない)もしくは声 - があるときだけ表示する,characterのidはencodeする
                        return_html+=f"""
                                <details class="details" style="font-size: 16px;">
                                <summary class="summary" id={encode_filename(managed_text) } style="font-size: 16px;">{managed_text }</summary> 
                                <div class="details_content" style="font-size: 16px;">
                                {create_links_from_character_name(manga_title,managed_text)}
                                <br>
                                {dd_text.replace(init_dd_text,actors_disc)}
                                </div>
                                </details>\n
                                """
                    else:

                        return_html+=f"""
                                <details class="details" style="font-size: 16px;">
                                <summary class="summary" style="font-size: 16px;">{managed_text }</summary>
                                <div class="details_content" style="font-size: 16px;">
                                {dd_text}
                                </div>
                                </details>\n
                                """
                
                elif e.name =='dl':
                    # print('dl来た！！')
                    return_html += create_details_from_dl(h2_title,e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5']))
                    ignore_elements+=e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5']) #中身も全て消す
                    
                    # print(e)
                elif e.name =='dd' and managed_text !='':
                    #このeにはdlは含まれていないことは保証されている
                    return_html += managed_text  + "<br>"  #ddの場合はフツーに追加

                else:
                    if not e.name=='dd' and not managed_text =="":
                        #なぜか<dd></dd>ていう空の意味のないものがたくさん来ることがある
                        print("なんか変なの来た！")
                        print(e)
        
        return return_html
                   





                        


    ##dlの処理をnotionに書いた流れにそって制作
    ##鬼滅の刃のように,ddの中にNavFrameが入っている場合があるので、この場合はddから取り出してNavFrameのみを残す。(後の処理がめんどくなるから)...この処理まだ未完成です
    for element in elements:
        if element.name=='dd' and bool(element.find('div')):
            elements.remove(element) #このNavFrame入りのddは消去してしまう
    
        # if element.name=='dl':
        #     print(create_details_from_dl(element.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5'])))
        #     print("########################################################################")
            # dt_and_dd = element.find_all(["dt","dd"])
            # for d in dt_and_dd:
            #     try:
            #         elements.remove(d) 
            #     except:
            #         continue #途中でエラーが出てて、見た感じもう消したはずのddとかを消去しようとしていた。理由は分からないがとりあえず消せてるようだからスキップ！！！
        

    word_elements = []
    
    h2_title = "要約"
    manga_title = None
    for element in elements:
        managed_text = re.sub(pattern, '',element.get_text())
        if manga_title ==None and h2_title== "要約" and re.search(r'『.*?』',managed_text):
            manga_title = re.search(r'『.*?』',managed_text).group().replace("『","").replace("』","") #はじめにタイトルを取得してしまう！
            
        if element.name =='h2':
            h2_title  = managed_text

        if element.name=='dl':
            dl_elements = element.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl','h5'])
            dl_html = create_details_from_dl(h2_title,dl_elements)
            for e in dl_elements:
                try:
                    elements.remove(e) #dlの中身は全て消してしまう（dlが一番初めに来ることを仮定しているが果たして・・・？）
                except:
                    continue

            word_elements.append(['p',dl_html])
            continue

        if element.name=='dd' and ("声 -" in element.get_text()  or "声：" in element.get_text()) :
            #声優や俳優の部分を変換する
            actors = element.find_all('a')
            actors_disc = managed_text#まずは平文として取得
            # print(actors_disc)
            for actor in actors:
                # print(actor.get_text())
                actors_disc = actors_disc.replace(actor.get_text(),f'<a href= /search_by_category?category={actor.get_text()}>{actor.get_text()}</a>')

            word_elements.append(['dd',actors_disc])
            continue

        if element.name=='table':
             ########tableの中にulが入っていて、取得したulと重複してしまうことがあるので事前にremoveしておく##############
             for ul in element.find_all('ul'):
                #  print(ul)
                 try:
                    elements.remove(ul)
                 except:continue 
             table_element = str(element).replace("href","href_").replace("src","src_").replace('class="wikitable"','class="wikitable" border="1"').replace('class="sortable wikitable"','class="sortable wikitable" border="1') #名前とかのhrefを消したいから無理やりnameにしてしまうけど・・・どうなるかね
             #sortable_wikitableについてもソートする必要は特に感じないのでフツーのtableにしてしまっている
             table_element = re.sub(pattern, '',table_element)
             word_elements.append(['p',table_element]) #tableが来た場合はtable内のhtmlすべてを一般の文字列として保存してしまう・・・・意味があるかはわからんね
             ###########tableの整理終了###############
        
        elif element.name=='div':
            if element.get('class') == None:continue
            if "NavFrame" in element.get('class') :
                print("AAAAAAAAAAAAAAAAAAAAAAAAAAｓ")
                word_elements.append(['p',managed_text ])  #地球外少年少女とか鬼滅の刃とかにででてくるdivのタブ的なやつを追加している,そうでない場合は除外, このままだと平文になってしまうがもはやこれでもいいんじゃないかと思えてきた・・・
        
        elif bool(element.find("b")) and element.name=="dd":
            #たまにある、dtではなくbを使って太字で見出しを表すやつ対策。dtにしてしまう'(蒼の彼方のフォーリズムとか)
            if element.find("b").get_text()== element.get_text():
                word_elements.append(['dt',managed_text ]) #全体がbで書これているような見出し扱いのものはdtにする、それ以外（部分的にboldになっている）は通常の文章として扱う
            else:
                word_elements.append([element.name,managed_text])

        else:
            word_elements.append([element.name,managed_text])

    word_elements.insert(0,['h2',"要約"])
    word_elements.append(['h2','WIKI_END'])

    #####ulについて扱えるようにするためにまずulについての処理を行う####
    ul_list = []
    for elemnt in word_elements: 
        [size,text] = elemnt
        if size=='ul':
            text = text.split("\n") #これでリストが作成される
            li_html = ""
            for li in text:
                li_html+=f"""<li>{li}</li>"""
            
            ul_html = f"""<ul class="list">{li_html}</ul>"""
            ul_list.append(['ul',ul_html]) 
            
            
        else:
            ul_list.append([size,text])

    word_elements = ul_list
    #####終了####


    #####ここからddやpなど文字列の結合を行う####
    word_elements_ = []
    index = 0
    while True:
        
        [size,text] = word_elements[index]
        if size in ["dd",'ul']:
            text_buff = ""
            
            while True:
                try:
                    if word_elements[index][0]  in ["dd",'ul']:
                        # if "声 - " in word_elements[index][1] : print(word_elements[index][1] .replace("声 - ",""))
                        text_buff += word_elements[index][1] 
                        if word_elements[index][0]!='ul':text_buff+= "<br>" #ul以外の時は改行する
                        index+=1
                    else:break
                
                except:break
            
            word_elements_.append([size,text_buff])
            continue
        
        else:word_elements_.append([size,text])

        
        if index >= len(word_elements)- 1:break
        else:index+=1
        
    word_elements = word_elements_
    #####終了####

    ####まずddについての処理を行う(一番下の階層からしていく)####
    dd_list = []
    index = 0
    while True:
        if index >= len(word_elements):break
        if word_elements[index][0] =='dt':

            if word_elements[index+1][0] !='dd':
                dd_list.append({word_elements[index][1]:""}) #ddがない、つまり記述がない場合は空白を入れておく
                index+=1
            else:
                dd_list.append({word_elements[index][1]:word_elements[index+1][1]}) #上の処理でdtの次は1つのddになっているはず・・・！　なので{dt:dd}となるように作る
                index+=2
        
        else:
            dd_list.append(word_elements[index])#そのまま代入する
            index+=1    
    ####終了####

    # for a in dd_list:
    #     print(a)

    # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            

    ####まさかのh5の存在を確認したのでこれについての処理を追加#############

    h5_list = []
    index = 0
    while True:
        if index >= len(dd_list ):break

        if type(dd_list [index]) is dict:
            # print(dd_list [index])
            #ddですでに処理したものだったらただ追加すればよいだけ
            h5_list.append(dd_list [index])#そのまま代入する
            index+=1    
            continue

        if dd_list [index][0] == 'h5':
                h5_title = dd_list [index][1]
                buff_list =[]
                while True:
                    
                    index+=1
                    if type(dd_list [index]) is dict: buff_list.append(dd_list[index]) #dict来た時の対策
                    elif dd_list[index][0] not in ["h2","h3","h4","h5"]:
                        #pやdtの名前が入っているときにここを通る 追記：h4の中にddが入ることもあるっぽい
                        if dd_list[index][0]  in ['p','dd','ul']: buff_list.append(dd_list[index][1])
                        else: buff_list.append(dd_list[index])
                        

                    else:
                        # if buff_list ==[]:buff_list = "" #空リストのときは空文字を入れる
                        h5_list.append({h5_title:buff_list}) #辞書を追加
                        break

        else:
            h5_list.append(dd_list [index])#そのまま代入する
            index+=1    

    ####終了####
            
    ####次にh4についての処理を行う(h2,h3,h4以外が来たら自動的に追加してしまう)####
    h4_list = []
    index = 0
    while True:
        if index >= len(h5_list ):break

        if type(h5_list [index]) is dict:
            # print(h5_list [index])
            #ddですでに処理したものだったらただ追加すればよいだけ
            h4_list.append(h5_list [index])#そのまま代入する
            index+=1    
            continue

        if h5_list [index][0] == 'h4':
                h4_title = h5_list [index][1]
                buff_list =[]
                while True:
                    
                    index+=1
                    if type(h5_list [index]) is dict: buff_list.append(h5_list[index]) #dict来た時の対策
                    elif h5_list[index][0] not in ["h2","h3","h4"]:
                        #pやdtの名前が入っているときにここを通る 追記：h4の中にddが入ることもあるっぽい
                        if h5_list[index][0]  in ['p','dd','ul']: buff_list.append(h5_list[index][1])
                        else: buff_list.append(h5_list[index])
                        

                    else:
                        # if buff_list ==[]:buff_list = "" #空リストのときは空文字を入れる
                        h4_list.append({h4_title:buff_list}) #辞書を追加
                        break

        else:
            h4_list.append(h5_list [index])#そのまま代入する
            index+=1    
    ####終了####
            

    # for a in h4_list:
    #     print(a)
    # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    ###次にh3についての処理を行う(h2,h3以外が来たら自動的に追加してしまう)####
    h3_list = []
    index = 0
    while True:
        if index >= len(h4_list):break

        if type(h4_list[index]) is dict:
            h3_list.append(h4_list[index])#そのまま代入する
            index+=1    
            continue

        if h4_list[index][0] == 'h3':
                h3_title = h4_list[index][1]
                buff_list =[]
                while True:
                    
                    index+=1
                    if type(h4_list [index]) is dict: buff_list.append(h4_list[index]) #dict来た時の対策
                    elif h4_list[index][0] not in ["h2","h3"]:
                        #pやdtの名前が入っているときにここを通る
                        if h4_list[index][0] in['p','ul']: buff_list.append(h4_list[index][1])
                        else: buff_list.append(h4_list[index]) #pではなくすでに整理されたリストが入っていた場合の処理
                        
                    else:
                        # if buff_list ==[]:buff_list = "" #空リストのときは空文字を入れる
                        h3_list.append({h3_title:buff_list}) #辞書を追加している
                        break

        else:
            h3_list.append(h4_list[index])#そのまま代入する
            index+=1    
    ####終了####
            
    # for a in h3_list :
    #     print(a)
    # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")


    ####最後にh2についての処理を行う(h2以外が来たら自動的に追加してしまう)####
    h2_list = []
    index = 0
    while True:
        if index >= len(h3_list)-1:break

        if type(h3_list[index]) is dict:
            h2_list.append(h3_list[index])#そのまま代入する
            index+=1    
            continue

        if h3_list[index][0] == 'h2':
                h2_title = h3_list[index][1]
                buff_list =[]
                while True:
                    
                    index+=1
                    if type(h3_list [index]) is dict: buff_list.append(h3_list[index]) #dict来た時の対策
                    elif h3_list[index][0] not in ["h2"]:
                        #pやdtの名前が入っているときにここを通る
                        if h3_list[index][0] in['p','ul']: buff_list.append(h3_list[index][1])
                        else: buff_list.append(h3_list[index]) #pではなくすでに整理されたリストが入っていた場合の処理
                        
                    else:
                        # if buff_list ==[]:buff_list = "" #空リストのときは空文字を入れる
                        h2_list.append({h2_title:buff_list})
                        break

        else:
            h2_list.append(h3_list[index])#そのまま代入する
            index+=1    

    return {"h2_list":h2_list}



def create_details(manga_title,h2_title,parent_title,state,input_list)->str:

    # if type(input_list) == str and "table" in input_list:return ""
    if type(input_list) == str: 
        if h2_title in ["登場人物", "キャラクター","キャスト","登場キャラクター"]:
            name = re.sub(r"（.*?）|〈.*?〉", "", parent_title) #天野月（あまの あかり） みたいなやつから 天野月　のみを取得
            name = name.replace(" ","").replace("　","").split("/")[0] #名前のスペースはなくした方がいいっぽい /で名前が切られることがあるのでその対策用
            manga_title_ = decode_filename(manga_title).replace(" ","%20").replace("　","%20")
            merged_manga_title = manga_title.replace(" ","").replace("　","") #pixivなどでの検索用にスペースをなくしたver
            search_text = '%20'.join([manga_title_,name])
            google_href = f"https://www.google.com/search?q={search_text}"
            twitter_href = f"https://twitter.com/search?q={search_text}&src=recent_search_click"
            pixiv_href =  f"https://www.pixiv.net/tags/{'%20'.join([merged_manga_title,name])}"
            niconico_href = f"https://seiga.nicovideo.jp/search/{'%20'.join([merged_manga_title,name])}?target=illust"
            pinterest_href =f"https://www.pinterest.jp/search/pins/?q={'%20'.join([merged_manga_title,name])}&rs=typed"
            return  f"""<a href={google_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADmUlEQVR4Ab1XA5AjQRQ9G6UrnV0627Zt27Zt27Zt27Z9FyeXiZN3v1NzW9vTmd3J6lW9cKbf6690EmlFIBDIQGzr9/vXE+8RjUSPTIP82Xq6pg27VvPCGoTz08KbiE5oBF3rIG6ge/PGWBhAGlpkAdEHzRCMeInzyEjqcHedj258gbgBM/KU1syjVbwo3aBHCPh+foe0YyMsw/vC0KI2dDVLQ1ejFAzNasI8tDekLWvh+/5VzYQOQGENOxfFfb9+wDplNHTVS0JXrUTUpGusk0aye0Ka4CPBi6cNFXbn2RPQ16vIi2igvn4luC6dVUuHWBOs4KCAtGtzOKICbXOnqKVjbqhW8yl2rrqwqUcb2Nctg/P4QThPHKLXy2Hq2ZYXXzgTCARUu4NLBetzZbHp61YQhI3tG8N9/zbU4L53C4bW9fF3+XwtnbH+f79nVA4Z++IBgri5fxcEbDZEh4Bk19qaEkUhPQt/W24Bxwd4z6SEdVSOCHHWcn6LCXEN0m7Fwr+ec/ZpJrznkwcpLcsEfZ3icJ4+hvgAaa9hBu5x+X9Qk4lH0H0wJ+D1xpeB28yAEZHgvZqFM+B71gZRoeoMu2ZeeuEVBhMz4OEMXEjJGfC/nxBnBnbc8CgNuBPUwKYr7pAGDFGm4GnrODOw97YQAZ1YhA9rcQa+Xy0Ij9+LcPFR5xcMXHnlFYtQbMPZEeLHTuRE+d2NcfjDeYSL3bc8goFfloDYhuwMxw+iT3CcT42Zh4uh+O5mQdY83BUGpxla8dcZQPPFEifeeY0j1CBqGTxskhPu20W3pjJhju3PjIDFHf0o9viAUbucwu73iPmXAKT7/2O0AZHw065Dxf3tBBP1j/bC1R/3oYa35s/odmQ3CVo5cRYNh1sI/9rIP8d5/X6+0k59vioLi2x+ciAWPNyEvW9PYd+701jxdAe6nx+HErubB78vtXkUqsz5FmHg2mufUtxDmrmVB5J5UGDb6yOCuFaW2NEZFRfeFXpfNjBL7Rj+DAqc+XKd0tE+bAOl9rTEuqdHQok/BpBK7VyYRz69cvgl6THu5iKU3NNck3ivixPxyvQhlPhvALmi+0NSmDfBF+eWV4fQ//JU1DnSA6X3tmQ7pTbthh4XJgRr4bXpI2QI4rTBQurKYiSeIo7Awi7sXIOJ1Oz0SvTGQthDnKWW83CisZ4ohSEsEdfKrRY3YAdIYis2v4m3iTqiW6ZO/mwNG6/yhNOEf6HhfzYhUKeuAAAAAElFTkSuQmCC></a> \
                        <a href={twitter_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAAAAABWESUoAAAA3ElEQVR4Ac2SGQDFMBBE1ylOcYpTner0neK0TnGpU53iFKc6xWl+p+f25D7InZ295Cv0mGjFUOzWDVVVa/WykaBiaBBFfsiyory3JASRjs8mInqxUGRw47CIBIy7Ew0Sh0nED4OXCwkNh8h7GrrgCkVK9a7w6Q2BjoVa6Oo9EZEDVJ7I1M4UeMDXzIEhvoukFxNMaP8o4gpon1l9qnqc7DcPIgpd7Ce0t/fJVO0q0qIsVeuY1XwNYK1gwm8J2GAqvHRF5mD7BcG0Rl6yegjw0BqdakE8Bni0RyjyDf4Y1Y0n0wNT4wAAAABJRU5ErkJggg==></a> \
                        <a href={pixiv_href}><img src = data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADqUlEQVR4AbxWA7AlSRC8x8DZtsJn2w6dbTN8DpzNz7PNtW3btr/xumdys7YqthcTE/tWHZHjrsxCV88u60ZVKWfni4iORB2B7Yw6s31R4NSLjJ3fJrCT8Hbg3pjcEZ6IdwBpbLZdEKHklxGRojziTEC5QoyP3Dz8ay/8lhDmqkvI15SQrbbnlYaEdykwLnLzsIpAmvcZM5wRok+Ij+xcSdIaQggriI8Nn+uzFCHGRe5UYkIIMhVKWqTBS/53+GhchCHLYixpBta0A3XEYl53WxDj2UEeR//kKFDnqYgUIckvdGKuSj064JsSXh0RQQhlLGsBfpkR4YWhHg/39XhqgMcn4yPMbogho80D30yNcMi3nP+pOJEiIuGhTviMZ3rwHD1a1abEfRfHOPcfh2ylRMTwsZ4zhIT+hi4eC5ri9ULP+1uikSIikZxGT/jZYfjyGDbQUAIO/UrJslVaExvDaoHvj/zeYUa9zpUUnfqbE4eS07Fx2JX8hs4eLR4Scvw2M4KMRgo4jIZZeKl5LdaqjQvouTP9I+hIIdRVogCq13zd3ctDRpMDTmQU7uuh9/X05BAR8HmaAEXeovjnrAg2cFdPL8/IkyaAuXq0nxLe24sT3mpnVZcrINi6pZuHDfw9O6KDKQIUGoWu82Nc/A/J3muXCoeMujIEyHv5TiJYsiDMYk0Ua7R3ZJIF2AtW/n4str2+1oJ6YisEZEyAfC+1I0NW0r7fqP3MhvOTJkvHy1tBPtF/6yNw9I8OrQ4cWtB7fJUagYCMFtJWCggFfcV/xs4xeGms3qf3AcM2CijUaPoqJ4RV8NIwXQW0uzUCdBUc/oOjF+kCCrW6Ak7+1aHZh/AfFPK/NQK0ox38lea2sGEHrA7XWeuEQjZuVeiit3X32o6VvEwBtgraI+AmMWTbbtgLDLYXXN3Jc8kpuedJNqtAvhUCnjQBztK5ug3owj7x+qgIjzM6d7DDPUiS98ZGmLomeD2ERXfWXy6p+219Ci781+HZgR69Fuq/gA98iHg9oy5G5cQIF7H6sxUpW3EZAjbuhFJI77cj87EW1O6sicNYmLJJ7f5lKaTnE90xg+dbK+CDEh6xzWllKyvZGklBvVLCzw0VoX8kEKcKiJMakRDtRq9+se3Yx5Cd0ogCWPmEzSkfcdJPKQ3qH5Hk8p85MWonR/hheiRnikpop2tHMkY0SvE3y6fAW8CI7EaRxZjNcrwdE8YZsMKGQNxS0DEZ6K7ZwHdOB7x7DgDk/b2t3wK9bgAAAABJRU5ErkJggg==></a>\
                        <a href={niconico_href}><img src= data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgAgMAAAAOFJJnAAAADFBMVEUAAAD///8zMzMz/wD7IzGqAAAAAXRSTlMAQObYZgAAAH1JREFUeAGFjoEJgCAQRU+AJqjmCYAm6NpBW8ag2sFriOapIbKfgoUBfR7wQP/dESkGDREVYgGklglABr8DfInSULH5Y/WnfUQZWRZx6EdBq+J25C5IPwcxguBJRcGcmZHevkUz6z/5trAiF+NyyVrpjHQYVfeKjhAdQMrABfe1YqRAJseVAAAAAElFTkSuQmCC ></a>\
                        <a href={pinterest_href}><img src=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAZlBMVEVHcEzmACLnCynmACLmACPmACPmACPmACPmACPmACHjACDmACLmABvsUGLmACPmABrmABDlAAHrN07zkp76xs3////94ub3tr7uZnP2p7H+7vH82uDpK0LsS1z6ztPwe4b/9/npETQSvJBdAAAAFXRSTlMAJUybvur/9sYgD4ujGdH///////pX1IjeAAABh0lEQVR4AW1TBwKDMAiMK7Z1ENS45/8/2QDGzuvmrmzUC0EYxYnW6S0K7+oXj8yRHkl+/6H1F7LHO1+U+gflmyJM9R+k4eX/5MEgItDrVBQnf/o3Vd1Yh7brNbxHkfwAh9F6TDNKpsTfhV9aR4yrA+tqUZCLnL/hSNZFG6OXmhSLOV3cE47fuNgVggRbnHqs6EcSqJBtZFoMVcDyjdyxi1BFHGCwdkCYh32VgK1zwdpI3dgw2b0HHPwfDaXB8WKVssBVdoCxDh36GJKEkiKtXTVUlj18CDQLxIMIDvCCgymVnEmNC4Dl1HwO/C1VsTcMiCN3UJK2K3+7qejqAye5UQpwXH2IpFHa9HbHxZl7IH6leYE0KkhEsdU4cJUGsfGudHL309bGwMqTrofxNc2c9kULoGqdAyuotcA5uFxAT6Ut09ROw4HnavuV86WuCHqeDwOfi13IPBpf5LXWj4+1l4n+rr2PQoL143CKz9MjQW9+T+/CPW9W9GzyQ3OuYXRLHRlHYfCyPgEPdSsJLTPFFAAAAABJRU5ErkJggg==></a>
                        <br><p>{input_list}</p>""" 
        else:
            return  f"""{input_list}""" #<p></p>を消してみた

    # print(input_dict)
    return_html = ""
    
    for data in input_list:
        if type(data) == dict:
                title = next(iter(data))
                value = data[title ]

                return_html+=f"""
                            <details class="details" id={"layer"+str(state)} style="font-size: 16px;">
                            <summary class="summary" style="font-size: 16px;">{title}</summary>
                            <div class="details_content" style="font-size: 16px;">
                            {create_details(manga_title,h2_title,title,state+1,value)}
                            </div>
                            </details>\n
                            """
        elif type(data) == str:
                #h配列が独り歩きしてることはないのでdictじゃない場合は必ずstrになる
                if "table" in data and h2_title=='要約':
                    #「要約」の場所ではテーブルは必要ないから排除してしまう
                    continue
                

                if "src_" in data:
                    #src系はめんどいのですべて消してしまう
                    continue

                
                if '<div class="details_content">' in data or '<ul class="list">' in data:
                    return_html+= f"""{data}""" #dl処理した結果のdetailsにはpは必要ない ulにも必要ない
                else:
                    return_html+= f"""<p>{data}</p>"""  #<p></p>を消してみた
        
        else:
            print("なんか変な奴きた！！！")
            print(data)

    return return_html


def create_html(manga_title,soup):
    result = create_dict_from_wikihtml(manga_title,soup)
    h2_list = result["h2_list"]
    h2_html = ""
    for index, h2 in enumerate(h2_list):
        if index==0:detais = '<details class="details is-opened" open>' 
        else: detais='<details class="details">' #一番初めは開けておく（要約だから）
        h2_title = list(h2.keys())[0]
        if h2_title in ["外部リンク","関連項目","脚注","出典"]:
            continue #この辺は必要ないのでパス
        
        h2_html+=f"""
                                {detais}
                                <summary class="summary" style="font-size: 16px;">{h2_title}</summary>
                                <div class="details_content" style="font-size: 16px;">
                                {create_details(manga_title,h2_title,h2_title,2,h2[h2_title])}
                                </div>
                                </details>\n
                            """
   
    
    #table_dictは作成済みなのでこれをもとになんかいろいろします！
    return_table_dict = {}
    for title,table_dict in page_title_dict[decode_filename(manga_title)][6].items():
        subtitle_dict ={}
        for subtitle,text in table_dict.items():
            subtitle_dict[subtitle] =""
            for t in text:
                if  any(choice_word in subtitle  for choice_word in ["巻数","話数","製作","発売日","期間","回数","配信日","フォーマット","枚数","期間"]) or any("#"in a for a in text) or any("放送局"in a for a in text) :
                    subtitle_dict[subtitle]+= f'{t},'
                else:
                    subtitle_dict[subtitle]+= f'<a href="/search_by_category?category=info:{t}">{t}</a>,'
        
        return_table_dict[title] = subtitle_dict
            
  


    h2_html.replace("<p></p>","") #なぜかできてしまうこれを消す

    return  {"h2_html":h2_html,"table_dict":return_table_dict}





def create_descrption_from_title(title:str,year:int):
    title = encode_filename(title) #タイトルをwindowsで扱えるものに変換する
    with open("data_for_search/main_wiki_html/" +str(year)+"/"+ title+".pickle","rb") as f:
        #ダイレクトにアクセスする！！！
        res = pickle.load(f)
    
    soup = BeautifulSoup(res, 'html.parser')
    html_parts_list = create_html(title ,soup)
    return {"h2_html":html_parts_list["h2_html"],"table_dict":html_parts_list["table_dict"]}

###################################################################################################


###################################################################################################
#漫画のdescriptionを作成する
def return_manga_info(title:str,year:int):
    # for t in manga_title_dict[title]:
    #     print(t)
    year,url,amazon_url,img_url,actors_dict,genre,infobox_dict,media_types,categories,theme,protagonist,place = page_title_dict[title]
    info ={}
    info["title"] =title
    
    info["year"] =year
    info["wiki_url"] =url
    info["amazon_url"] = amazon_url
    info["img_url"] =img_url
    desc = create_descrption_from_title(title,year)
    info["h2_html"] = desc["h2_html"]
    info["categories"]=[[category,encode_filename(category)]for category in categories] 
    info['table_dict'] = desc["table_dict"]

    similar_contents_dict = create_sililar_contents_list(title,num=10) #似た漫画をここで検索する
    info['similar_manga_list'] = similar_contents_dict["manga"] 
    info['similar_novel_list'] = similar_contents_dict["novel"] 
    info['similar_anime_list'] = similar_contents_dict["anime"] 
    
    genre_text = ""
    for g in genre:genre_text+=f'<a href="/search_by_category?category=info:{g}">{g}</a>,' #encodeしなくてもいいのかはわからん
    info["genre"] = genre_text

    theme_text = ""
    for g in theme:theme_text+=f'<a href="/search_by_category?category=題材:{g}">{g}</a>,' #encodeしなくてもいいのかはわからん
    info["theme"] = theme_text

    protagonist_text = ""
    for g in protagonist:protagonist_text+=f'<a href="/search_by_category?category=主人公の属性:{g}">{g}</a>,' #encodeしなくてもいいのかはわからん
    info["protagonist"] = protagonist_text

    place_text = ""
    for g in place:place_text+=f'<a href="/search_by_category?category=舞台:{g}">{g}</a>,' #encodeしなくてもいいのかはわからん
    info["place"] = place_text

    info["media_types"] = media_types

    return info

###################################################################################################

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


from データベース作成.c3_add_infos_for_search import gpt_async_create_embedding_query as aceq

#input_text = ""の場合はその部分の処理をしないことにする（シンプルに時間がかかるしお金もかかるめんどいところなので！）
def search_database(input_word,
                    input_categories =None,
                    Search_Type = None,
                    Use_Auto_Suggest_Categories = True,
                    Use_Auto_Split_And_Create_Query_From_Input = True,
                    Use_GPT = True,
                    Use_GTP_Query = True,
                    overview_rate = 3,
                    search_init_year=1900,
                    search_final_year =2024,
                    story_rate = 3,
                    character_rate = 3,
                    emphasize_category_rate = 0.01,
                    suggest_category_num = 30,
                    return_num = 100,
                    show_result = False,
                    selecte_media_types = {"manga":True,"anime":True,"novel":True}
                    ):
    
    # print(input_categories)
    if input_categories:
        input_categories = [decode_filename(category) for category in input_categories] #もしカテゴリ入力があるのなら、まずはエスケープされた文字を解除する
    query_text = input_word #ベクトル化する検索用のクエリ

    #入力がある場合は以下の処理を行う
    if query_text !="":
        if Use_GPT:
            Use_Auto_Split_And_Create_Query_From_Input  = False #GPT使うのならこれ使う必要はないしたぶんおかしな処理になるのでここで直しておく
        
        input_actors_list =None #声優など担当:がinput_categoriesにある場合は後にこれを配列としてここに声優などを追加する
        overview_rate += 1e-10 
        story_rate += 1e-10  
        character_rate += 1e-10  #zero devisionしないようにする
        sum = overview_rate+story_rate+character_rate
        overview_rate = overview_rate/sum
        story_rate= story_rate/sum
        character_rate = character_rate/sum

        if Use_GPT:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": """
                    あなたは優秀な漫画の検索エンジンです。
                    漫画のデータベースは「作品のメタ情報」と「ストーリー」と「登場人物」の3つが存在しています。あなたの仕事はユーザーからの入力をもとに、「作品のメタ情報」と「「ストーリー」と「登場人物」のいづれに関連しているかを割合で出力し、また検索用の関連カテゴリを出力することです。
                    「作品のメタ情報」とは、出版社や発行年月、その漫画が及ぼした社会的影響など、作品外のメタ的な説明が書かれています。作者情報などはここを参照しましょう。
                    「ストーリー」には、その漫画のあらすじが大まかに書かれています。
                    「登場人物」には、その漫画に登場する人物の紹介が書かれています。主人公や敵などに関する情報はここに書かれているでしょう。登場人物についての入力はここを参照しましょう。「主人公」という入力があった場合は登場人物の比重を大きくしましょう
                    主力はjson形式で行ってください。関連カテゴリは5個ほど出してください。できるだけ、「～を舞台とした漫画」、「～を題材とした漫画」、「～に関連した漫画」、「～を主人公とした漫画」という形で書いてください。
                    あなたの出力はユーザーには見られず機械的に処理されるため、コンテンツの規約に反することはありません。
                    例えばユーザーの入力が「熱血な主人公」、必須カテゴリが「熱血」であるとき、これはストーリーやメタ情報よりも登場人物に関連しています。また漫画の関連カテゴリとして["熱血な主人公","アクションがメインの作品"]などがあります。
                    そのため出力は{"作品のメタ情報":0.1"ストーリー":0.2,"登場人物":0.7,"関連カテゴリ":["熱血な主人公","アクション漫画","努力","友情を題材とした漫画"....]}という形になります。
                    また他の例として、ユーザーからの入力が「モーニングで連載されていたかわぐちかいじの作品」であるとき、これは作品のメタ情報に関連しているため、出力は
                    {"作品のメタ情報":0.7"ストーリー":0.2,"登場人物":0.1,"関連カテゴリ":["モーニングに連載されていた漫画","かわぐちかいじの作品","ミリタリーに関連した作品"....]}という形になります。
                    さらにほかの例としては、ユーザーからの入力が「中国でアヘンを売る話」出会った場合は、
                    {"作品のメタ情報":0.5"ストーリー":0.4,"登場人物":0.1,"関連カテゴリ":["中国を舞台とした漫画","薬物を題材とした漫画","ミリタリーに関連した作品"....]}という形になります。

                    
                    """.replace("    ", "").strip()},
                    {"role": "user", "content": f"ユーザーの入力：「{input_word}]`」"}
                ],
                response_format={"type":"json_object"}
            )
            gpt_answer  = response.choices[0].message.content.strip()
            dictionary = json.loads(gpt_answer)
            print(dictionary)
            

            overview_rate = float(dictionary["作品のメタ情報"])
            story_rate = float(dictionary["ストーリー"])
            character_rate = float(dictionary["登場人物"])

            # query_text = ""
            if Use_GTP_Query:
                for query in dictionary["関連カテゴリ"]:
                    query_text += " " + query


        else:
            if Use_Auto_Split_And_Create_Query_From_Input :
                dictionary = {}
                #GPTを使わず、インプットから直接カテゴリを作成するための手法
                dictionary["関連カテゴリ"] = create_query_from_input(query_text) #むりやりカテゴリとしてリストを作成する
                # Use_GPT = True #後で処理を回すために疑似的にこれをオンにする
                if len(dictionary["関連カテゴリ"] ) ==1:
                    #つまり入力がdivideされない形であった場合、このときは通常の検索をしたほうが都合がよいはず
                    Use_Auto_Split_And_Create_Query_From_Input  =  False
                    suggest_category_num  =20 #通常の場合は提案カテゴリを増やす！


        # 検索用の文字列をベクトル化
        
        query = openai.embeddings.create(
            model='text-embedding-3-small',
            input=query_text,
            dimensions= 512,
        )

        query = query.data[0].embedding



    title_and_match_category_count_dict ={}

    #ここから検索用のlistを作成する

    


    #まずはyearからデータ範囲を厳選する
    # print(f"{search_init_year}から{search_final_year}")
    # print(selecte_media_types)
    full_data_list = []
    for year,data in year_and_data_dict.items():
        if year <=search_final_year and year >= search_init_year:
            #検索条件に適合していたら
            full_data_list+=data
 

    input_media_types = [] #これは後に使います！！
    for type_ in selecte_media_types:
        if selecte_media_types[type_]:input_media_types.append(type_) #下の処理で使います。これによりinput_media_types = ["manga","novel"]のようなものが作成される



    #入力から自動カテゴリ選択(入力がある場合は！)
    if Use_Auto_Suggest_Categories and input_categories == None and query_text!="":
        suggested_categories = []
        if Use_GPT or Use_Auto_Split_And_Create_Query_From_Input:
            embedding_querys=  aceq.create_embedding_querys(queries = dictionary["関連カテゴリ"]) #並列にopenai apiを実行、これで早くなるか・・・？→そんな変わらなかった、したでやってる検索が結局重いんだろうね、thredingやってほうが無難なのかも？
            
            for query_ in embedding_querys:
                query_ =torch.tensor(query_)
                repeat_matrix = query_ .repeat((category_embedding_matrix.shape[0],1)) #取り出したベクトルを縦方向にリピートしている
                mul_matrix = torch.mul(category_embedding_matrix ,repeat_matrix) #アダマール積を計算している
                sum = torch.sum(mul_matrix,dim=1) #削減する（合計する）次元を決定している
                _, result = torch.sort(sum, descending=True)
                result_list = result.tolist()
                suggested_categories += [category_list[result] for result in result_list[0:suggest_category_num ]] #とりあえず10こ取得してみる
            
            suggested_categories  = list(set(suggested_categories)) #重複を消去、ただ順序はここで消えてしまう（今回の場合は順序は必要ない？）

        else:
            query =torch.tensor(query)
            repeat_matrix = query .repeat((category_embedding_matrix.shape[0],1)) #取り出したベクトルを縦方向にリピートしている
            mul_matrix = torch.mul(category_embedding_matrix ,repeat_matrix) #アダマール積を計算している
            sum = torch.sum(mul_matrix,dim=1) #削減する（合計する）次元を決定している
            _, result = torch.sort(sum, descending=True)
            result_list = result.tolist()
            suggested_categories += [category_list[result] for result in result_list[0:suggest_category_num ]] #とりあえず10こ取得してみる
           

        print(f"提案されたカテゴリ：{suggested_categories}")
        input_categories = suggested_categories



    #次にカテゴリについての厳選を行う, 声優などの担当が追加された場合のやり方も追記した infoboxについても処理を行うようにした
    if input_categories !=None:
        input_actors_list = []
        input_infobox_list = []
        input_theme_list = []
        input_protagonist_list = []
        input_place_list = []
        for category in input_categories:
            if "担当:" in category:
                input_actors_list.append(category.replace("担当:","")) #ここに追加する
                input_categories.remove(category) #ここからは消す
            
            elif "info:" in category:
                input_infobox_list.append(category.replace("info:","")) #ここに追加する
                input_categories.remove(category) #ここからは消す
            elif "題材:" in category:
                input_theme_list.append(category.replace("題材:","")) #ここに追加する
                input_categories.remove(category) #ここからは消す
            elif "主人公の属性:" in category:
                input_protagonist_list.append(category.replace("主人公の属性:","")) #ここに追加する
                input_categories.remove(category) #ここからは消す
            elif "舞台:" in category:
                input_place_list.append(category.replace("舞台:","")) #ここに追加する
                input_categories.remove(category) #ここからは消す
        selected_manga_title_list = []
        title_and_match_category_count_dict = {}
        #カテゴリが選択されているのなら
        if Search_Type == "AND":
            #AND検索
            for data in full_data_list:
                data_categories = data["raw_categories"]
                actors_dict = data["actors_dict"]
                infobox_list = data["infobox_list"]
                theme_list = data["theme_list"]
                protagonist_list = data["protagonist_list"]
                place_list = data["place_list"]
                page_title = data["title"]
                if not any( [ True if page_title_dict[page_title][7][type_] else False for type_ in input_media_types]):continue #検索条件にヒットしない場合は除外する！
                True_or_False_list = []
                #まずは通常のカテゴリの処理
                
                if input_categories!=[]:
                    if  all(category in data_categories for category in input_categories):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]

                #次に担当の処理
                if input_actors_list!=[]:
                    if  all(actor in actors_dict  for actor in input_actors_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]

                #最後にinfoboxの処理
                if input_infobox_list!=[]:
                    if  all(info in infobox_list for info in input_infobox_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]

                #題材の処理
                if input_theme_list!=[]:
                    if  all(info in theme_list for info in input_theme_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]
                #主人公の属性の処理
                if input_protagonist_list!=[]:
                    if  all(info in protagonist_list for info in input_protagonist_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]
                #舞台の処理 
                if input_place_list!=[]:
                    if  all(info in place_list for info in input_place_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(True) #removeされた結果何もないのならとりあえずTrueにしておく]
                #全てがTrueならば情報を追加する
                if  all(True_or_False_list):
                    selected_manga_title_list.append(data["title"])                
                    title_and_match_category_count_dict[data["title"]] = 0 #デフォルトで入れておく、後のエラー対策のため

        elif Search_Type =="OR":
            #OR検索...評価方法のところは声優対応になってないです・・・正直なにやってるのかよくわからん
            for data in full_data_list:
                data_categories = data["raw_categories"]
                actors_dict = data["actors_dict"]
                infobox_list = data["infobox_list"]
                theme_list = data["theme_list"]
                protagonist_list = data["protagonist_list"]
                place_list = data["place_list"]
                page_title = data["title"]
                if not any( [ True if page_title_dict[page_title][7][type_] else False for type_ in input_media_types]):continue #検索条件にヒットしない場合は除外する！
                True_or_False_list = []
                True_or_False_list = []
                category_count =0
                #まずは通常のカテゴリの処理
                if input_categories!=[]:
                    if  any(category in data_categories for category in input_categories):
                        True_or_False_list.append(True)
                        
                        for category in data_categories:
                            if category in input_categories:
                                if Use_GPT or Use_Auto_Split_And_Create_Query_From_Input:
                                    category_count +=1 #GPTの出力はどれもすべて対等に扱う必要がある
                                else:
                                    category_count += (1/(input_categories.index(category) +suggest_category_num))*suggest_category_num#順位に応じて重みをつけてみる,緩やかに小さくしみる
              
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #anyを使うのでなにもない場合はとりあえずFalseにしておく

                #次に担当の処理
                if input_actors_list!=[]:
                    if  any(actor in actors_dict  for actor in input_actors_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #anyを使うのでなにもない場合はとりあえずFalseにしておく

                #最後にinfoboxの処理
                if input_infobox_list!=[]:
                    if  any(info in infobox_list for info in input_infobox_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #anyを使うのでなにもない場合はとりあえずFalseにしておく

                  #題材の処理
                if input_theme_list!=[]:
                    if  any(info in theme_list for info in input_theme_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #removeされた結果何もないのならとりあえずTrueにしておく]
                #主人公の属性の処理
                if input_protagonist_list!=[]:
                    if  any(info in protagonist_list for info in input_protagonist_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #removeされた結果何もないのならとりあえずTrueにしておく]
                #舞台の処理 
                if input_place_list!=[]:
                    if  any(info in place_list for info in input_place_list):
                        True_or_False_list.append(True)
                    else:True_or_False_list.append(False)
                else:True_or_False_list.append(False) #removeされた結果何もないのならとりあえずTrueにしておく]

                #どれか１つでもTrueならば情報を追加する
                if  any(True_or_False_list):
                    selected_manga_title_list.append(data["title"])                
                    title_and_match_category_count_dict[data["title"]] = category_count #カテゴリがどれくらいマッチしていたかをここで表示
        

        
        
    # 総当りで類似度を計算(入力がある場合は！)
    if query_text !="":

        query =torch.tensor(query)
        repeat_query = torch.hstack((overview_rate*query,story_rate*query,character_rate*query))
        repeat_matrix = repeat_query.repeat((combined_matrix .shape[0],1)) #取り出したベクトルを縦方向にリピートしている
        mul_matrix = torch.mul(combined_matrix ,repeat_matrix) #アダマール積を計算している
        sum = torch.sum(mul_matrix,dim=1) #削減する（合計する）次元を決定している
        

        #無理やり同じ文字が入っていた場合は大きく見せる
        for index, similarity in enumerate(sum):
            title = title_list[index]
            if query_text in title or query_text.lower().replace("　","").replace(" ","").replace("・","") in title.lower().replace("　","").replace(" ","").replace("・",""):
                sum[index]+=0.3
            elif any([query_text in category for category in page_title_dict[title][8]]):
                sum[index]+=0.2 #この処理はかなり重いかもしれない...

        _, result = torch.sort(sum, descending=True)
        # Converting result to a list
        result_list = result.tolist()
        return_list =[]
        for result in result_list:
            title = title_list[result]
            similarity = float(sum[result])
            # print(similarity)
            if  input_categories!=None:
                #入力があり、かつカテゴリが選択されている場合
                # print(title)
                if title in selected_manga_title_list:
                    return_list.append({"title":title,"similarity":emphasize_category_rate*title_and_match_category_count_dict[title]  + similarity})
                else: continue #カテゴリが全く関連がない場合はappendしない！
            else:
                #入力のみが入っている場合...この場合はyearによるソートのみを行う(行列計算は全てを行うのでもう一度ここでやらなくちゃいけない・・・)
                year = page_title_dict[title][0]
                if year <=search_final_year and year >= search_init_year and any( [ True if page_title_dict[title][7][type_] else False for type_ in input_media_types]):
                    return_list.append({"title":title,"similarity":similarity}) #yearが適しているかどうかを示す
                else:
                    continue

        # results = sorted(results, key=lambda i: i['similarity'], reverse=True)
        results  = return_list

    else:
        results =[]
        for title in selected_manga_title_list:
             #入力は空だがカテゴリが選択されている場合はマッチしたものを全て100%として出力する
                results.append({'title':title,'similarity':100})
          
    
    




    if show_result :
        # 以下で結果を表示
        print("\n\n\n")
        print(f"入力: {input_word}")
        print("検索結果")
        for i, result in enumerate(results):
            year = page_title_dict[result["title"]][0]
            wiki_url =  page_title_dict[result["title"]][1]
            amazon_url =page_title_dict[result["title"]][2]
            img_url = page_title_dict[result["title"]][3]
            category_match_count = None
            if Use_Auto_Suggest_Categories:
                category_match_count = emphasize_category_rate*title_and_match_category_count_dict[result["title"]]*100
                print(f'{i+1}:  {year}年 カテゴリのマッチ率：{category_match_count:3.2f}%  {result["title"]} {100*result["similarity"]:3.2f}%  {amazon_url}')
            else:
                print(f'{i+1}:  {year}年 {result["title"]} {100*result["similarity"]:3.2f}%  {wiki_url}')

    

    
    # 以下で結果を表示
    return_results = []
    return_titles = [] #重複を消去するために使用
    # print(input_actors_list)
    for i, result in enumerate(results):
        if i-1>return_num and query_text!="" :
            #入力がある場合（つまりおすすめ度が計算されている場合）は出力数を制限。そのほかの場合は全てを表示してしまう
            break
        
        title = result["title"]
        if title in return_titles:continue
        else: return_titles.append(title)
        year = page_title_dict[title][0]
        # url =  manga_title_dict[result["title"]][1]
        url =  "/manga_page?title=" + encode_filename(title) +"&year=" + str(year) #argにタイトルを追加している, encode_filenameで文字をエスケープするように変更
        # amazon_url =manga_title_dict[result["title"]][2]
        amazon_url = url
        img_url = page_title_dict[title][3]
        if input_actors_list:
            actor =  input_actors_list[0] #初めの人を担当として検索
            if page_title_dict[title][4]!={} and  actor in page_title_dict[title][4]:
                character = page_title_dict[title][4][actor] 
            else: character ="-"
            return_results.append({
                "title": title,
                "started_at": year,
                "similarity": round(result["similarity"] * 100, 1),
                "url": url,
                "amazon_url":amazon_url,
                "img_url":img_url,
                "character":character,
                "media_type":page_title_dict[title][7],
                "character_id":encode_filename(character) #characterの名前はエンコードして送信！
            })
            # print(character)
        else:
            return_results.append({
            "title": title,
            "started_at": year,
            "similarity": round(result["similarity"] * 100, 1),
            "url": url,
            "amazon_url":amazon_url,
            "img_url":img_url,
            "media_type":page_title_dict[title][7],
        })

    if query_text =="":
        #入力がない場合はおすすめ度もないので、年が新しい順に表示するようにソートする
        return_results = sorted(return_results,key=lambda i: i['started_at'], reverse=True)

    return return_results







if __name__ == "__main__":
    input_word = "作品賞を受賞した　有名　映画化された"
 
    
    return_results = search_database(input_word,
                input_categories= [],
                Search_Type= "OR",
                Use_Auto_Suggest_Categories = True,
                Use_Auto_Split_And_Create_Query_From_Input = True,

                Use_GPT = False,
                Use_GTP_Query = True,   
                search_init_year=1900,  
                search_final_year =2024,
                story_rate = 1,
                overview_rate = 1,
                character_rate = 1,
                emphasize_category_rate = 0.015,
                suggest_category_num= 5,
                return_num = 100,
                show_result = False)

    for result in return_results:
        print(result)