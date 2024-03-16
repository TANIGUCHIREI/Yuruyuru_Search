import os,time

from flask import Flask
from flask import render_template

test_config=None

# create and configure the app
application = Flask(__name__, instance_relative_config=True)
application.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(application.instance_path, 'app.sqlite'),
)

if test_config is None:
    # load the instance config, if it exists, when not testing
    application.config.from_pyfile('config.py', silent=True)
else:
    # load the test config if passed in
    application.config.from_mapping(test_config)

# ensure the instance folder exists
try:
    os.makedirs(application.instance_path)
except OSError:
    pass

# a simple page that says hello
@application.route('/test')
def test():
    return 'This is test page'

@application.errorhandler(404)
def page_not_found(error):
    return render_template('search/page_not_found.html',full_categories_list=[])


from . import db
db.init_app(application)

from . import auth
application.register_blueprint(auth.bp)

from . import search
application.register_blueprint(search.bp)

from . import nav
application.register_blueprint(nav.bp)


application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #https://qiita.com/hiroyuki-inaba/items/6c9db8648240e61d4e80　にかいてあったやる
application.config['TEMPLATES_AUTO_RELOAD'] = True #自動的にリロードするようにする
# app.config['DEBUG'] =True
# # app.debug = True
# print("debug mode on !!!!!")
@application.context_processor
def inject_now():
    return {'now': lambda: int(time.time())} #ブラウザがキャッシュをしないようにcssなどのurlを変更するための対策用。こう書くことによってjinja2がみることができるようになる
