import pickle

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.db import get_db

import sys
sys.path.append('../')
from use_database4 import search_database,return_manga_info,decode_filename
# -> 最終的にapp内に移動させる


with open("./data_for_search/categories_list.pickle","rb") as f:
    category_list = pickle.load(f)

with open("./data_for_search/actor_list.pickle","rb") as f:
    full_actor_list = pickle.load(f)

category_list +=[ "担当:"+actor for actor in full_actor_list]

bp = Blueprint('search', __name__)



@bp.route('/', methods=['GET'])
def index():
    return render_template('search/index.html',full_categories_list=category_list,start_year=1900, end_year=2024)

@bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search/index.html',full_categories_list=category_list)
    elif request.method == 'POST':
        return redirect(url_for(
            'search.results',
            input=request.form["inputText"],
            gpt=request.form.get("useGPT"),
            searchall=request.form.get("searchall"),
            character=request.form.get("character_rate"),
            story=request.form.get("story_rate"),
            overview=request.form.get("overview_rate"),
            liData = request.form.get('liData'),
            AndOr = request.form.get("AndOR"),
            toggleSliders = request.form.get("toggleSliders"),
            story_age_checkbox =  request.form.get("story_age_checkbox"),
            ))

@bp.route('/results', methods=['GET'])
def results():
    input_text = "" if request.args.get('input')== None else request.args.get('input')
    print(input_text)
    use_gpt = True if request.args.get('gpt') == 'on' else False
    searchall = True if request.args.get('searchall') == 'on' else False
    AndOr = "OR" if request.args.get("AndOr")==None else request.args.get("AndOr") #デフォルトはOR検索にしておく
    toggleSliders = True if request.args.get('toggleSliders') == 'on' else False #概要・ストーリー・キャラクタを任意に変更するか否かのやつ
    story_age_checkbox = True if request.args.get('story_age_checkbox') == 'on' else False
    # print(AndOr)

    actor_select = False
    categories =  request.args.get('liData').split(",")
    categories =None if categories== [''] else categories
    if categories and any('担当:' in category for category in categories): actor_select=True #声優などのカテゴリが選択されている！
    # print(categories)
    

    if request.args.get('character'):
        rate_sum = int(request.args.get('character')) + int(request.args.get('story')) + int(request.args.get('overview'))
        character_rate = int(request.args.get('character')) / rate_sum * 100
        story_rate = int(request.args.get('story')) / rate_sum * 100
        overview_rate = int(request.args.get('overview')) / rate_sum * 100
        rate = {"character": character_rate, "story": story_rate, "overview": overview_rate}
    else:
        character_rate, story_rate, overview_rate = 33, 33, 33
        rate = None

    return_results = search_database(
        input_text,
        input_categories= categories,
        Search_Type= AndOr,
        Use_Auto_Suggest_Categories = (False if searchall else True),
        Use_Auto_Split_And_Create_Query_From_Input = True,
        Use_GPT = use_gpt,
        Use_GTP_Query = True,
        search_init_year=1900,
        search_final_year =2024,
        story_rate = story_rate,
        overview_rate = overview_rate,
        character_rate = character_rate,
        emphasize_category_rate = 0.015,
        suggest_category_num= 5,
        return_num = 100,
        show_result = False,
    )

    form_info = {'useGPT':use_gpt,'searchall':searchall,'toggleSlider':toggleSliders,'story_age_checkbox':story_age_checkbox,'AndOR':AndOr}
    return render_template('search/results.html',full_categories_list=category_list, results=return_results, input_text=input_text, rate=rate,form_info=form_info,categories=categories,actor_select=actor_select)


@bp.route('/manga_page', methods=['GET'])
def manga_page():
    title = decode_filename(request.args.get('title')) #タイトルをdecodeしている
    year = int(request.args.get('year'))
    info = return_manga_info(title,year)
    character_id =  "#" + request.args.get('character_id') if request.args.get('character_id') else ""
    return render_template('search/manga_page.html',info = info,character_id = character_id,full_categories_list=[])
    #以下のコードは完成時に上２つを置き換える（エラー処理ができるようになっている）
    # try:
    #     info = return_manga_info(title,year)
    #     return render_template('search/manga_page.html',info = info)
    # except Exception as e:
    #     print(e)
    #     return render_template('search/page_not_found.html')
    
    


@bp.route('/search_by_category/', methods=['GET'])
def search_by_category():

    liData = request.args.get('category')
    # print(liData)
    return redirect(url_for(
        'search.results',
        input_text ="",
        liData = liData,
        ))


