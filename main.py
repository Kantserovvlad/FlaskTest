from flask import Flask, render_template, url_for
from waitress import serve
from data import db_session
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registration')
def registration():
    return render_template('registration.html')


if __name__ == '__main__':
    db_session.global_init("db/diary.db")
    # app.run(host='0.0.0.0', port=5000)
    serve(app, host='0.0.0.0', port=5000)
