#app.run()を__init__.pyではディレクトリの上下の関係でできなかったので、ここでやってしまう
#https://qiita.com/Jazuma/items/521cf31538cb618d285a　を参考にしました
from app.__init__ import app
if __name__ == "__main__":
    app.run()