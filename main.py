from flask import Flask, render_template, url_for
from waitress import serve

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    serve(app, host='0.0.0.0', port=5000)
