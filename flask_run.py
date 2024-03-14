#app.run()を__init__.pyではディレクトリの上下の関係でできなかったので、ここでやってしまう
from app.__init__ import create_app
app = create_app()
app.run(debug=False, host='127.0.0.1', port=5000)