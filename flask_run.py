#app.run()を__init__.pyではディレクトリの上下の関係でできなかったので、ここでやってしまう
from app.__init__ import create_app
if __name__ == ('__main__'):
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)