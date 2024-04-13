#SEO対策用
import functools,os
# print(os.listdir())
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('SEO', __name__)

@bp.route('/robots.txt', methods=['GET'])
def robots():
    return render_template('SEO/robots.txt',full_categories_list=[])

@bp.route('/sitemap.xml', methods=['GET'])
def sitemap():
    return render_template('SEO/sitemap.xml',full_categories_list=[])
@bp.route('/categories_sitemap.xml', methods=['GET'])
def categories_sitemap():
    return render_template('SEO/categories_sitemap.xml',full_categories_list=[])
#就活用のポートフォリオ表示用
# @bp.route('/ぽ/お/と/ふ/ぉ/り/お', methods=['GET'])
# def portfolio():
#     return render_template('others/portfolio.html',full_categories_list=[])