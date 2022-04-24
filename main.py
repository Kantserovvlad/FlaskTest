from flask import Flask, render_template, url_for, redirect
from flask_restful import abort
from waitress import serve

from data.class_n import Classes
from data.homeworks import Homework
from forms.forms import LoginForm, SetSchool, SetClass, NewPassword, ChangeInfo, AddSchoolClass, AddHomework
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
        if current_user.admin:
            info = list()
            info.append(('Число зарегистрировавшихся', len(db_sess.query(User).all())))
            info.append(('Число администраторов', len(db_sess.query(User).filter(User.admin).all())))
            return render_template('personal.html', school=school, class_n=class_n, info=info)
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


@app.route('/change/password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        form = NewPassword()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            if not user.check_password(form.password_old.data):
                return render_template('change_password.html', form=form, message='Старый пароль не совпадает')
            if form.password_new.data != form.password_new_again.data:
                return render_template('change_password.html', form=form,
                                       message="Пароли не совпадают")
            user.set_password(form.password_new.data)
            db_sess.commit()
            return redirect('/personal')
        return render_template('change_password.html', form=form)
    return redirect('/login')


@app.route('/change/info', methods=['GET', 'POST'])
def change_info():
    if current_user.is_authenticated:
        form = ChangeInfo()

        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()

            user.name = form.name.data
            user.surname = form.surname.data
            user.email = form.email.data

            db_sess.commit()
            return redirect('/personal')
        return render_template('change_info.html', form=form)
    return redirect('/login')


@app.route('/users')
def users_site():
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        return render_template('users.html', users=users)
    return abort(404)


@app.route('/schools')
def schools_site():
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        schools = db_sess.query(School).all()
        users = db_sess.query(User).all()
        users_schools = dict()
        for school in schools:
            k = 0
            for user in users:
                if school.id == user.school_id:
                    k += 1
            users_schools[school.name] = k
        return render_template('schools.html', schools=schools, users_schools=users_schools)
    return abort(404)


@app.route('/give/admin/<int:id_user>')
def give_admin(id_user):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.admin = True
        db_sess.commit()
        return redirect('/users')
    return abort(404)


@app.route('/delete/admin/<int:id_user>')
def delete_admin(id_user):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.admin = False
        db_sess.commit()
        return redirect('/users')
    return abort(404)


@app.route('/add/school', methods=['GET', 'POST'])
def add_school():
    if current_user.is_authenticated and current_user.admin:
        form = AddSchoolClass()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            school = School(name=form.name.data)
            db_sess.add(school)
            db_sess.commit()
            return redirect('/schools')
        return render_template('add_school.html', form=form)
    return abort(404)


@app.route('/add/class/<int:school_id>', methods=['GET', 'POST'])
def add_class(school_id):
    if current_user.is_authenticated and current_user.admin:
        form = AddSchoolClass()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            class_n = Classes(name=form.name.data, school_id=school_id)
            db_sess.add(class_n)
            db_sess.commit()
            return redirect(f'/{school_id}/classes')
        return render_template('add_class.html', form=form)
    return abort(404)


@app.route('/<int:school_id>/classes')
def classes_site(school_id):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        classes = db_sess.query(Classes).filter(Classes.school_id == school_id).all()
        users = db_sess.query(User).filter(User.school_id).all()
        users_classes = dict()
        for class_n in classes:
            k = 0
            for user in users:
                if user.class_n_id == class_n.id:
                    k += 1
            users_classes[class_n.name] = k
        title = db_sess.query(School).filter(School.id == school_id).first().name
        return render_template('classes.html', classes=classes, title=title,
                               users_classes=users_classes, school_id=school_id)
    return abort(404)


@app.route('/add/homework/<int:school_id>/<int:class_n_id>', methods=['GET', 'POST'])
def add_homework(school_id, class_n_id):
    if current_user.is_authenticated and current_user.admin:
        form = AddHomework()
        db_sess = db_session.create_session()
        school = db_sess.query(School).filter(School.id == school_id).first()
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        if school is not None and class_n is not None:
            school = school.name
            class_n = class_n.name
            if form.validate_on_submit():
                homework = Homework(
                    title=form.title.data,
                    content=form.content.data,
                    school_id=school_id,
                    class_n_id=class_n_id
                )
                db_sess.add(homework)
                db_sess.commit()
                return redirect(f'/{school_id}/classes')
            return render_template('add_homework.html', form=form, school=school, class_n=class_n)
        return abort(404)
    return abort(404)


@app.route('/homeworks')
def my_homeworks():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        homeworks = db_sess.query(Homework).filter(Homework.school_id == current_user.school_id
                                                   and Homework.class_n_id == current_user.class_n_id).all()
        return render_template('homeworks.html', homeworks=homeworks)
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init("db/diary.db")
    # app.run(host='0.0.0.0', port=5000)
    serve(app, port=5000)
