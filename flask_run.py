#app.run()を__init__.pyではディレクトリの上下の関係でできなかったので、ここでやってしまう
#https://qiita.com/Jazuma/items/521cf31538cb618d285a　を参考にしました
#結果：__init__.py内でcreate_app()関数を作成していたことが二重に起動してしまうことの原因だった。そのまま直に書く必要があった？
from app.__init__ import application
if __name__ == "__main__":
    application.run()