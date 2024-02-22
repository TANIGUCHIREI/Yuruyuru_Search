import bs4
from bs4 import BeautifulSoup
import re
pattern = r'\[.*?\]'
def create_actor_list_from_dl(h2_title,element):
    actor_dict = {}
    ignore_elements = [] #dlなどに入っている重複しているものは除くためのリスト
    for index,e in enumerate(element):
        if e in ignore_elements:continue #すでに処理したエレメントについては処理を飛ばす
        if bool(e.find_all('dl')):
            actor_dict.update(create_actor_list_from_dl(h2_title,e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])))
        else:
            #dlは含まれていない,dd,dtのみで構成されている
            if e.name =='dt':
                dd_text =''
               
                dd_index = index+1
                while True:
                    try:
                        if element[dd_index].name == 'dd':
                            
                            dd_text+=re.sub(pattern, '',element[dd_index].get_text())
                            if dd_index == index+1 and ('声' in element[dd_index].get_text()): 
                                actors = element[dd_index].find_all('a')
                                # print(actors_disc)
                                for actor in actors:
                                    actor_name = re.sub(pattern, '',actor.get_text())
                                    if actor_name!='':
                                        actor_dict[actor_name]=re.sub(pattern, '',e.get_text())

                        
                            ignore_elements.append(element[dd_index]) #これ以降forの中でdl以外でこのddが出てきても無視する
                            ignore_elements+=element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])#中身も全て消す
                            dd_index+=1
                        
                        elif element[dd_index].name == 'dl':
                            actor_dict.update(create_actor_list_from_dl(h2_title,element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])))
                            ignore_elements.append(element[dd_index])
                            ignore_elements+=element[dd_index].find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])#中身も全て消す
                            dd_index+=1
                        else:break #dtなどが来たらbreak
                    
                    except:break #list index out of range になるときがある対策

            elif e.name =='dl':
                # print('dl来た！！')
                actor_dict.update(create_actor_list_from_dl(h2_title,e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])))
                ignore_elements+=e.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl']) #中身も全て消す

    return actor_dict

def create_table_dict(init_table):
    all_table_dict = {}
    tr_list = init_table.find_all("tr")
    
    for tr in tr_list:
        if tr.find("tr"):
            # print("aaa")
            tr_list.remove(tr) #リゼロの漫画ようにtrの中にさらにtrが入っている場合は処理が面倒になるので消去してしまう


    #wikiのてーぶるについて処理・tableの中はtrがたくさん入っていて、trの中にタイトルがth,詳細がtdでさらにtdの中にaが含まれている。tr{th{td[a,a,a,...a]}}の関係
    index = 0
    template_note = False
    
    while True:
        if template_note:break
        th = tr_list[index].find("th") 
        td = tr_list[index].find("td")
        if td==None :
            #tableタイトルだけしかない時
            if th!=None:
                if th.get("colspan") :
                    #タイトル(濃い紫色)が来た場合
                    title = th.get_text().replace("\n","")
                    title = re.sub(pattern, '',title )
                    # print(f"#######{title}#########")
                    disc_dict = {}
                    index+=1
                    while True:
                        next_tr = tr_list[index]
                        next_th = next_tr.find("th") 
                        next_td = next_tr.find("td")
                        if not next_th:
                            if next_td.get("colspan") and next_td.find_all("a") and any(["テンプレート" in word.get_text() for word in next_td.find_all("a")]):
                                template_note = True
                                break #テンプレート-ノート（tdにcolspanがある）が来た時はwhileを抜け出す
                            else:
                                # print(next_td.get_text())
                                index+=1
                                continue #タイトルのイメージ画像などが入っている場合は飛ばす
                        if not next_td and not next_th.get("colspan"):
                            index+=1
                            continue #これは「その他の出版社」的な中にliが入ったりするタイプなので飛ばしてしまう

                        if next_th.get("colspan"):
                            index-=1 #なんかこれしたら正常に動いたぞ
                            break #次のタイトルが来た時はwhileを抜け出す
                        
                        
                        #これまでの処理で残ったのはsubtitle:discriptionの形のみのはずなので、通常の辞書に格納する処理をする
                        subtitle = next_th.get_text().replace("\n","")
                        subtitle = re.sub(pattern, '',subtitle )
                        a_list = next_td.find_all("a")
                        a_list = [a_list[i].text.replace("\n","") for i in range(len(a_list)) if a_list[i].text !="" and not re.match(pattern,a_list[i].text)]
                        if len(a_list)==0:a_list = [next_td.get_text().replace("\n","")]
                        a_list  = [word for word in a_list if word!="独自研究?"  ]
                        disc_dict[subtitle] = a_list
                        index+=1
                        # print(f"{subtitle}:{','.join(a_list)}")
                        # print(title)
                    # print("抜けました")
                    if len(disc_dict) !=0: all_table_dict[title] = disc_dict #中身が空じゃない時は追加する
                    
                    
        index+=1
    return all_table_dict

def create_categories(soup)->dict:
    category_divs = soup.find_all('div', class_='mw-normal-catlinks')



    categories = category_divs[-1].find_all('a', href=True) #一番最後のカテゴリdivがいちばん大切だから、結局これだけでいいのでは？
    categories =  [categories[i].text for i in range(len(categories))]
    categories.remove('カテゴリ') #これは必要ないので消す


    main_div:bs4.element.Tag = soup.find("div",class_ ="mw-body-content" )
    pattern = r'\[.*?\]'
    all_table_dict = {}
    init_table = soup.find("table",class_ ="infobox bordered" )
    if init_table:
        try:
            all_table_dict = create_table_dict(init_table)
        except:
            try:
                init_table = soup.find("table",class_ ="infobox" ) #1966のウルトラマンみたいなはじめのtableのclassの名前がinfoboxのときの対策
                all_table_dict = create_table_dict(init_table)
            
            except:
                all_table_dict ={}
        

                    
        init_table.decompose() #一番初めにはテーブルは必要ないので消去する
    elements = main_div.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])

    
    ##鬼滅の刃のように,ddの中にNavFrameが入っている場合があるので、この場合はddから取り出してNavFrameのみを残す。(後の処理がめんどくなるから)
    for element in elements:
        if element.name=='dd' and bool(element.find('div')):
            elements.remove(element) #このNavFrame入りのddは消去してしまう
        

    actor_dict = {}

    h2_title = "要約"
    for element in elements:
        managed_text = re.sub(pattern, '',element.get_text())
        if element.name =='h2':
            h2_title  = managed_text

        if element.name=='dl' and any([ word in h2_title for word in ["登場人物", "キャラクター","キャスト"]]):
            dl_elements = element.find_all([ 'p','h2', 'h3', 'h4','dd','dt','ul','table','div','dl'])
            actor_dict.update(create_actor_list_from_dl(h2_title,dl_elements))
            for e in dl_elements:
                try:
                    elements.remove(e) #dlの中身は全て消してしまう（dlが一番初めに来ることを仮定しているが果たして・・・？）
                except:
                    continue
                

    #次にtableから漫画の重要な情報を取得していく(use_database3.pyからtableを作成する部分をほぼコピペして改変している)
    
    # for k,v in all_table_dict.items():
    #     print(f"#######{k}########")
    #     for k_,v_ in v.items():
    #         print(f"{k_}: {v_}")

            
    pattern = r"\[.*?\]|（.*?）|\(.*?\)"
    return_table_dict = {} #表示するinfobox用
    return_table_list = [] #検索時に利用するinfoboxの情報用
    choice_list = ["ジャンル","作者","出版社","掲載誌","巻数","原作","原案","作画","レーベル","発売","原作","監督","デザイン","放送局","音楽","話数","製作","著者","掲載サイト","連載","配信","制作","パーソナリティ","構成","発売","演出","ディレクター","製作","販売","枚数","発表期間","監修"] #ここを増やせば保存されるカテゴリが増えます
    for title,table_dict in all_table_dict.items():
        subtitle_dict = {}
        for k,v in table_dict.items():
            k = k.replace("\n","")
            table_list  = []
            if any( choice_word in k  for choice_word in choice_list) :
                if  any(choice_word in k  for choice_word in ["巻数","話数","製作","発売日","期間","回数","配信日","フォーマット","枚数","期間"]) or any("#"in a for a in v) or any("放送局"in a for a in v) :
                    for table_categoriy in v:
                        table_categoriy = re.sub(pattern, "", table_categoriy)
                        table_list.append(table_categoriy)
        
                else:

                    #wikiのページによっては正しく分割できていない時があるのでその対策をする([1]や（原作）や、 といったものが入っている場合がある！)
                    table_categoriy_buff = []
                    for table_categoriy in v:
                        table_categoriy_buff += table_categoriy.split("、")
                    
                    v = table_categoriy_buff
                    #次に[1],[2]などを分割
                    table_categoriy_buff = []
                    for table_categoriy in v:
                        replaced_str = re.sub(pattern, ",", table_categoriy)
                        table_categoriy_buff+= replaced_str.split(",")# カンマで分割して配列を作成
                        # print(table_categoriy_buff)
                    if '' in table_categoriy_buff:table_categoriy_buff = table_categoriy_buff[:-1]
                    v = table_categoriy_buff
                    return_table_list += v
                    table_list = v

                subtitle_dict[k] = table_list
            return_table_dict[title] = subtitle_dict

    #次にinfoboxのデータからジャンルを出力する
    genre = []
    try:
        for title,v in return_table_dict.items():
            for subtitle,disc in v.items():
                # print(subtitle)
                if "ジャンル" in subtitle:
                    # print("aaaaaaaaaaa")
                    # print(disc)
                    genre = disc
                    return_table_dict.pop(title)
                    break
            if genre:break #ジャンルを取得できたらbreak
    except:
        genre = ""

    return_table_list = list(set(return_table_list)) #重複を消す


    return categories,actor_dict,return_table_list,return_table_dict,genre




if __name__ == '__main__':
    import pickle,re
    with open("./manga_wiki_html/2020/僕とロボコ.pickle","rb") as f:
        res = pickle.load(f)
        
    soup = BeautifulSoup(res, 'html.parser')
    categories,actor_dict,return_table_list,return_table_dict,genre = create_categories(soup)
    # if '大塚剛央' in actor_dict:
    #     print(actor_dict['大塚剛央'])
    for k,v in return_table_dict.items():

        print(f"{k} : {v}")
    print(genre)
    print(re.split(r"<a.*?>",genre.replace("</a>,",""))[1:]) #この処理で一応genreのhtmlからリスト形式のgenreを取得することができる！
    # for v in return_table_list:

    #     print(f"{v}")