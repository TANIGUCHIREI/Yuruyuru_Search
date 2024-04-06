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