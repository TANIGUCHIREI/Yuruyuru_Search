import functools,os
# print(os.listdir())
from send_mail import send_gmail #ルート直下に置かないと取得できないっぽい
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

@bp.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'GET':
        return render_template('nav/contact.html',full_categories_list=[])
    elif request.method == 'POST':
        name=request.form["name"]
        email=request.form["email"]
        message=request.form["message"]
        # print(f"{name},{email},{message}")
        mail_subject = f"{name}様よりお問い合わせ"
        mail_body =f"名前:{name}\nメールアドレス:{email}\n\n{message}"
        send_gmail(mail_from="yuruyurusearch@gmail.com" , mail_to="yuruyurusearch@gmail.com" , mail_subject=mail_subject, mail_body=mail_body) #ここで自分自身にメールを送信している
        return render_template('nav/thanks_for_your_post.html',full_categories_list=[])

