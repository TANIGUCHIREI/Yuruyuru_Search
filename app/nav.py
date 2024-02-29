import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('nav', __name__)

@bp.route('/aboutsite', methods=['GET'])
def aboutsite():
    return render_template('nav/aboutsite.html',full_categories_list=[])

@bp.route('/sitepolicy', methods=['GET'])
def sitepolicy():
    return render_template('nav/sitepolicy.html',full_categories_list=[])

@bp.route('/contact', methods=['GET'])
def contact():
    return render_template('nav/contact.html',full_categories_list=[])

