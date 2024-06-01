#下記の内容は　テスト用/タイトル中にクエリがあるかを調べる.ipynb に記載したもののコピペ

#次の処理でカテゴリから～の小説　というものから作者名を取得する必要があるが、そこからさらに国名を除外するための国名リストを作成します
import json
full_countries_name_list = []
with open("../../Country_list.json","r",encoding="utf-8") as f:
    country_list = json.load(f)["countries"]
    for a in country_list:
        if a["name"]["full"]!="": full_countries_name_list.append(a["name"]["full"])
        if a["name"]["short"] and a["name"]["short"]!="":full_countries_name_list.append(a["name"]["short"])

# for country in full_countries_name_list:
#     print(country)

#カテゴリから作者名を作成します→どうやらこれは小説だけに有用なようだ
import re
def create_authors_from_categories(categories_list):
    pattern = r'\d{4}'
    selected_genre_list = []
    for category in categories_list:
        if category[-2:] == "小説" or category[-2:] == "作品" :
            if any([deletename in category for deletename in ["朝鮮","アニメ","実写","映画","ブシロード","テレビ","製作","コミックス","コミック","ワーナー・ブラザース","よしもと","ミュージック","スピンオフ","マーベル・コミック","東映","クロスオーバー","特撮","ユニバーサル","エンターテイメント","エンタテインメント","エンターテインメント","カルチュア・コンビニエンス・クラブ","マンガ","未完","シネマ","アニプレックス","ピクチャーズ","賞","本誌","バンダイ","ソビエト連邦","ファミ通","冷戦","ヤング","エンタープライズ","ちゃんねる","ライオンズゲート","東宝","グループ","関連","世紀","電撃","女性セブン","ROBOT","ディズニー","ユナイテッド","月刊","週刊","日刊","ニコニコ","NHK","ネイバー","ちゃお","ダ・ヴィンチ","ジョジョの奇妙な冒険","ミラマックス","フィルム","コモンズ","ルパン三世","スタジオ","りぼん","ミュージック","コロコロ","ジャパン","デジタルモンスター","星のカービィ","継続中","ドラゴンクエスト","ドリームワークス","ジャンプ","サンデー","マガジン","休止","映像","形式","パブリッシング","アクション","なかよし","ポケットモンスター","信頼できない語り手","小学館","リメイク","モーニング","シュルレアリスト","プロダクション","社","KADOKAWA","COM"]]):continue
            if re.findall(pattern,category) or any([ True if word in category else False for word in ["が舞台","を舞台","を題材","を主人公","に関連","を扱った","製作に協力","掲載","連載","に関する","を主題","された","における","を基にした","に基づいた","が描かれた","をベースとした"]]):continue
            # if "の" in category:print(category)
            if "の" in category:
                if "シリーズ" in category:continue
                _isContriyName= False
                for counry in full_countries_name_list:
                    if counry in category:
                        _isContriyName=True
                        break
                if not _isContriyName and not any([deletename in category for deletename in ["カクヨム","小説家になろう","が登場する"]]) :selected_genre_list.append(category)

    return_list =  []
    for category in selected_genre_list:
        no_split = category.split("の")
        if len(no_split)==2:return_list.append(no_split[0])
        else:
            #つのだじろう、つの丸　のように作者名に　の　が含まれる場合はここを通る
            for index,word in enumerate(reversed(category)):
                if word=="の":
                    return_list.append(category[:-index-1])
                    break
                                        
    return return_list