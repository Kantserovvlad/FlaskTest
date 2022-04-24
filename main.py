from flask import Flask, render_template, url_for, redirect
from flask_restful import abort
from waitress import serve

from data.class_n import Classes
from forms.login import LoginForm, SetSchool, SetClass
from data import db_session
from data.users import User
from data.schools import School
from forms.users import RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/personal')
def personal_account():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        school = db_sess.query(School).filter(current_user.school_id == School.id).first()
        class_n = db_sess.query(Classes).filter(current_user.class_n_id == Classes.id).first()
        if school is not None:
            school = school.name
        if class_n is not None:
            class_n = class_n.name
        return render_template('personal.html', school=school, class_n=class_n)
    return redirect('/')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if not current_user.is_authenticated:
        form = RegisterForm()
        if form.validate_on_submit():
            if form.password.data != form.password_again.data:
                return render_template('registration.html', form=form,
                                       message="Пароли не совпадают")
            db_sess = db_session.create_session()
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('registration.html', form=form,
                                       message="Такой пользователь уже есть")
            user = User(
                name=form.name.data,
                surname=form.surname.data,
                email=form.email.data,
            )

            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        return render_template('registration.html', form=form)
    return redirect('/personal')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated:
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', form=form)
    return redirect('/personal')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/set/school', methods=['GET', 'POST'])
def set_school():
    if current_user.is_authenticated:
        form = SetSchool()
        title = 'Установить школу'
        db_sess = db_session.create_session()
        schools = [(i.id, i.name) for i in db_sess.query(School).all()]
        form.school_id.choices = schools
        if form.validate_on_submit():
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            if user:
                user.school_id = form.school_id.data
                db_sess.commit()
                return redirect('/set/class')
            else:
                abort(404)
        return render_template('set_school_or_class.html', form=form, title=title)
    return redirect('/login')


@app.route('/set/class', methods=['GET', 'POST'])
def set_class():
    if current_user.is_authenticated:
        if current_user.school_id:
            form = SetClass()
            title = 'Установить класс'
            db_sess = db_session.create_session()
            classes = [(i.id, i.name) for i in
                       db_sess.query(Classes).filter(Classes.school_id == current_user.school_id).all()]
            form.class_n_id.choices = classes
            if form.validate_on_submit():
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                if user:
                    user.class_n_id = form.class_n_id.data
                    db_sess.commit()
                    return redirect('/personal')
                else:
                    abort(404)
            return render_template('set_school_or_class.html', form=form, title=title)
        return redirect('/set/school')
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init("db/diary.db")
    # app.run(host='0.0.0.0', port=5000)
    serve(app, port=5000)
