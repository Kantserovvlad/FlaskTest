from flask import Flask, render_template, url_for, redirect, request
from flask_restful import abort
from waitress import serve

from data.class_n import Classes
from data.homeworks import Homework
from forms.forms import LoginForm, AddHomework, get_class_change_homework, AddSchoolClass
from forms.forms import RegisterForm, SetSchool, SetClass, NewPassword, ChangeInfo
from data import db_session
from data.users import User
from data.schools import School
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


def check_id(id_is_check, class_is_check):
    db_sess = db_session.create_session()
    my_class_one = db_sess.query(class_is_check).filter(class_is_check.id == id_is_check).first()
    if my_class_one is None:
        return False
    return True


# -------------------------------------------------------------
# Авторизация, регистрация, личный кабинет

@app.route('/personal')
def personal_account():
    if current_user.is_authenticated:
        # ----------------------------------
        # Получаем названия класса и школы пользователя
        db_sess = db_session.create_session()
        school = db_sess.query(School).filter(current_user.school_id == School.id).first()
        class_n = db_sess.query(Classes).filter(current_user.class_n_id == Classes.id).first()
        if school is not None:
            school = school.name
        if class_n is not None:
            class_n = class_n.name
        # ----------------------------------
        # Если пользователь администратор, то выясняем дополнительную информацию
        if current_user.admin:
            info = list()
            info.append(('Число зарегистрировавшихся', len(db_sess.query(User).all())))
            info.append(('Число администраторов', len(db_sess.query(User).filter(User.admin).all())))
            return render_template('personal.html', school=school, class_n=class_n, info=info)
        return render_template('personal.html', school=school, class_n=class_n)
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if not current_user.is_authenticated:
        # Показываем эту страницу, только если пользователь не авторизован
        form = RegisterForm()
        if form.validate_on_submit():
            # Если пароли не совпадают, то:
            if form.password.data != form.password_again.data:
                return render_template('registration.html', form=form,
                                       message="Пароли не совпадают")
            db_sess = db_session.create_session()
            # Если повторяется почта, которая уже есть в базе данных, то:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('registration.html', form=form,
                                       message="Такой пользователь уже есть")
            # ---------------------------------------
            # Если всё успешно, то
            # Создаём нового пользователя
            user = User(
                name=form.name.data,
                surname=form.surname.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)  # Устанавливаем пароль
            db_sess.add(user)  # Добавляем в базу данных
            db_sess.commit()  # Сохраняем
            # И перенаправляем на авторизацию
            return redirect('/login')
        # Если кнопку не нажали, то:
        return render_template('registration.html', form=form)
    # Если пользователь авторизирован, то отправляем его в личный кабинет
    return redirect('/personal')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated:
        # Показываем эту страницу, только если пользователь не авторизован
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Ищем пользователя с таким же e-mail
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            # И проверяем пароль
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                # Если всё правильно, то перенаправляем пользователя на главную
                return redirect("/")
            # Иначе выводим ошибку
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', form=form)
    # Если пользователь авторизирован, то отправляем его в личный кабинет
    return redirect('/personal')


@app.route('/logout')
@login_required
def logout():
    # Выход из аккаунта
    logout_user()
    return redirect("/")


# -------------------------------------------------------------
# Функции для каждого пользователя
# Изменение пароля, личной информации, школы и класса
# Показ домашних заданий

@app.route('/set/school', methods=['GET', 'POST'])
def set_school():
    if current_user.is_authenticated:
        form = SetSchool()
        title = 'Установить школу'
        db_sess = db_session.create_session()
        # Получаем все школы
        schools = [(i.id, i.name) for i in db_sess.query(School).all()]
        # И устанавливаем в select для выбора одной из школ
        form.school_id.choices = schools
        if form.validate_on_submit():
            # Ищем пользователя
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            # Устанавливаем id школы
            user.school_id = form.school_id.data
            # И ставим значение id класс на NULL, так как изменилась школа
            user.class_n_id = None
            db_sess.commit()  # Сохраняем
            return redirect('/set/class')
        return render_template('set_school_or_class.html', form=form, title=title)
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/set/class', methods=['GET', 'POST'])
def set_class():
    if current_user.is_authenticated:
        if current_user.school_id:
            form = SetClass()
            title = 'Установить класс'
            db_sess = db_session.create_session()
            # Ищем все классы для школы пользователя
            classes = [(i.id, i.name) for i in
                       db_sess.query(Classes).filter(Classes.school_id == current_user.school_id).all()]
            # И устанавливаем в select для выбора одной из класс
            form.class_n_id.choices = classes
            if form.validate_on_submit():
                # Ищем пользователя
                user = db_sess.query(User).filter(User.id == current_user.id).first()
                # Устанавливаем id класса
                user.class_n_id = form.class_n_id.data
                db_sess.commit()  # Сохраняем
                return redirect('/personal')
            return render_template('set_school_or_class.html', form=form, title=title)
        # Если нет школы, то отправляем его выбрать школу
        return redirect('/set/school')
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/change/password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        form = NewPassword()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Находим пользователя
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            if not user.check_password(form.password_old.data):
                # Если старый пароль не совпадает, то ошибка:
                return render_template('change_password.html', form=form, message='Старый пароль не совпадает')
            if form.password_new.data != form.password_new_again.data:
                # Если новый пароль не совпадает повторным новым паролем, то ошибка:
                return render_template('change_password.html', form=form,
                                       message="Пароли не совпадают")
            # Если всё успешно, то устанавливаем новый пароль
            user.set_password(form.password_new.data)
            db_sess.commit()  # И сохраняем
            return redirect('/personal')
        return render_template('change_password.html', form=form)
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/change/info', methods=['GET', 'POST'])
def change_info():
    if current_user.is_authenticated:
        form = ChangeInfo()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Находим пользователя
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            # -----------------------
            # Обновляем данные
            user.name = form.name.data
            user.surname = form.surname.data
            user.email = form.email.data
            # -----------------------
            # Сохраняем
            db_sess.commit()
            return redirect('/personal')
        return render_template('change_info.html', form=form)
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/homeworks')
def my_homeworks():
    if current_user.is_authenticated:
        if current_user.school_id and current_user.class_n_id:
            # Если указаны у пользователя id школы и id класса
            db_sess = db_session.create_session()
            # Находим всё д/з
            homeworks = db_sess.query(Homework).filter(Homework.class_n_id == current_user.class_n_id).all()
            return render_template('homeworks.html', homeworks=homeworks, class_n_id=current_user.class_n_id)
        elif not current_user.school_id:
            # Если не указана школа, то перенаправляем его на выбор школы:
            return redirect('/set/school')
        elif not current_user.class_n_id:
            # Если не указан класс, то перенаправляем его на выбор класса:
            return redirect('/set/class')
    # Если пользователь не авторизован, то перенаправляем на авторизацию
    return redirect('/login')


@app.route('/sitesbox')
def sites_box():
    return render_template('sites_box.html')


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/about/site')
def about_site():
    return render_template('about_site.html')


# --------------------------------------------------------------
# Функции для администратора

# Вывод информации

@app.route('/users')
def users_site():
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        # Делаем список всех пользователей
        users = db_sess.query(User).all()
        return render_template('users.html', users=users)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/diaries')
def diaries():
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        classes = db_sess.query(Classes).all()
        # ---------------------------------------
        schools_classes = dict()
        for class_n in classes:
            school = db_sess.query(School).filter(School.id == class_n.school_id).first()
            if school.name in schools_classes.keys():
                schools_classes[school.name].append(class_n)
            else:
                schools_classes[school.name] = [class_n]
        # ----------------------------------------
        return render_template('diaries.html', schools_classes=schools_classes)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/schools')
def schools_site():
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        # Создаём список школ
        schools = db_sess.query(School).all()
        # И список пользователей
        users = db_sess.query(User).all()
        users_schools = dict()  # Словарь для указания сколько учеников в каждой школе
        # --------------------------------
        for school in schools:
            k = 0
            for user in users:
                if school.id == user.school_id:
                    k += 1
            users_schools[school.name] = k
        # ---------------------------------
        return render_template('schools.html', schools=schools, users_schools=users_schools)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/<int:school_id>/classes')
def classes_site(school_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(school_id, School):
            return abort(404)
        db_sess = db_session.create_session()
        # Создаём список всех классов
        classes = db_sess.query(Classes).filter(Classes.school_id == school_id).all()
        # Сортируем классы
        classes = sorted(classes, key=lambda x: x.name)
        # Создаём список всех пользователей
        users = db_sess.query(User).filter(User.school_id).all()
        users_classes = dict()  # Словарь для указания сколько учеников в каждом классе
        # -----------------------------------------
        for class_n in classes:
            k = 0
            for user in users:
                if user.class_n_id == class_n.id:
                    k += 1
            users_classes[class_n.name] = k
        # ------------------------------------------
        # В title указываем название школы
        title = db_sess.query(School).filter(School.id == school_id).first().name
        return render_template('classes.html', classes=classes, title=title,
                               users_classes=users_classes, school_id=school_id)
    return abort(404)


@app.route('/homeworks/<int:class_n_id>')
def homeworks_school_class(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        if not check_id(class_n_id, Classes):
            return abort(404)
        school_id = db_sess.query(Classes).filter(Classes.id == class_n_id).first().school_id
        school_name = db_sess.query(School).filter(School.id == school_id).first().name
        class_n_name = db_sess.query(Classes).filter(Classes.id == class_n_id).first().name
        # Создаём список всего д/з
        homeworks = db_sess.query(Homework).filter(Homework.class_n_id == class_n_id).all()
        return render_template('homeworks.html', homeworks=homeworks, school_name=school_name,
                               class_n_id=class_n_id, class_n_name=class_n_name)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


# ---------------------------------------------------------------------------------
# Давать или удалять админа


@app.route('/give/admin/<int:id_user>')
def give_admin(id_user):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(id_user, User):
            return abort(404)
        db_sess = db_session.create_session()
        # Находим пользователя
        user = db_sess.query(User).filter(User.id == id_user).first()
        # Делаем его администратором
        user.admin = True
        # Сохраняем
        db_sess.commit()
        return redirect('/users')
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/delete/admin/<int:id_user>')
def delete_admin(id_user):
    if current_user.is_authenticated and current_user.admin:
        if id_user == 1:
            return redirect('/users')
        if not check_id(id_user, User):
            return abort(404)
        db_sess = db_session.create_session()
        # Находим пользователя
        user = db_sess.query(User).filter(User.id == id_user).first()
        # Удаляем его из администраторов
        user.admin = False
        # Сохраняем
        db_sess.commit()
        return redirect('/users')
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


# ---------------------------------------------------------------------------
# Функции добавления

@app.route('/add/school', methods=['GET', 'POST'])
def add_school():
    if current_user.is_authenticated and current_user.admin:
        title = 'Добавление школы'
        form = AddSchoolClass()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Создаём новую школу
            school = School(name=form.name.data)
            # Добавляем в базу данных
            db_sess.add(school)
            # Сохраняем
            db_sess.commit()
            return redirect('/schools')
        return render_template('add_school.html', form=form, title=title)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/add/<int:school_id>/class', methods=['GET', 'POST'])
def add_class(school_id):
    if current_user.is_authenticated and current_user.admin:
        form = AddSchoolClass()
        title = "Добавить класс"
        if not check_id(school_id, School):
            return abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Создаём новый школьный класс
            class_n = Classes(name=form.name.data, school_id=school_id)
            # Добавляем в базу данных
            db_sess.add(class_n)
            # Сохраняем
            db_sess.commit()
            return redirect(f'/{school_id}/classes')
        return render_template('add_class.html', form=form, title=title)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/add/homework/<int:class_n_id>', methods=['GET', 'POST'])
def add_homework(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        form = AddHomework()
        db_sess = db_session.create_session()
        if not check_id(class_n_id, Classes):
            return abort(404)
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        school = db_sess.query(School).filter(School.id == class_n.school_id).first()
        school = school.name
        class_n_name = class_n.name
        if form.validate_on_submit():
            # Создаём новое д/з
            homework = Homework(
                title=form.title.data,
                content=form.content.data,
                school_id=class_n.school_id,
                class_n_id=class_n_id
            )
            # Добавляем в базу данных
            db_sess.add(homework)
            # Сохраняем
            db_sess.commit()
            return redirect(f'/homeworks/{class_n_id}')
        return render_template('add_homework.html', form=form, school=school, class_n=class_n_name)
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


# --------------------------------------------------------------------------
# Функции изменения

@app.route('/change/homeworks/<int:class_n_id>', methods=['GET', 'POST'])
def change_homework(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        if not check_id(class_n_id, Classes):
            return abort(404)
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        school = db_sess.query(School).filter(School.id == class_n.school_id).first().name
        class_n = class_n.name
        # Создаём список всего д/з
        homeworks = db_sess.query(Homework).filter(Homework.class_n_id == class_n_id).all()
        # Получаем класс с указанным количеством д/з
        form = get_class_change_homework(len(homeworks))
        # -----------------------------------------------
        if request.method == 'POST':
            # Изменяем данные на новые из "форм в форме"
            for i in range(len(homeworks)):
                homeworks[i].title = form.homeworks[i].form.title.data
                homeworks[i].content = form.homeworks[i].form.content.data
            # Сохраняем
            db_sess.commit()
            # Перенаправляем админа в просмотр д/з
            return redirect(f'/homeworks/{class_n_id}')
        return render_template('change_homeworks.html', form=form, homeworks=homeworks,
                               school=school, class_n=class_n, n=len(homeworks))
    # Если пользователь не админ, то выводим, что такой страницы нет
    return abort(404)


@app.route('/change/class/<int:class_n_id>', methods=['GET', 'POST'])
def change_class(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(class_n_id, Classes):
            return abort(404)
        title = "Переименовать класс"
        db_sess = db_session.create_session()
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        form = AddSchoolClass()
        if form.validate_on_submit():
            class_n.name = form.name.data
            # Сохраняем
            db_sess.commit()
            return redirect(f'/{class_n.school_id}/classes')
        return render_template('add_class.html', form=form, title=title, old_name=class_n.name)
    return abort(404)


@app.route('/change/school/<int:school_id>', methods=['GET', 'POST'])
def change_school(school_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(school_id, School):
            return abort(404)
        title = "Переименовать школу"
        db_sess = db_session.create_session()
        school = db_sess.query(School).filter(School.id == school_id).first()
        form = AddSchoolClass()
        if form.validate_on_submit():
            school.name = form.name.data
            # Сохраняем
            db_sess.commit()
            return redirect(f'/schools')
        return render_template('add_school.html', form=form, title=title, old_name=school.name)
    return abort(404)


# -------------------------------------------------------------------------------------
# Функции удаления

@app.route('/delete/homeworks/<int:class_n_id>')
def delete_homeworks(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        db_sess = db_session.create_session()
        if not check_id(class_n_id, Classes):
            return abort(404)
        homeworks = db_sess.query(Homework).filter(Homework.class_n_id == class_n_id).all()
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        school = db_sess.query(School).filter(School.id == class_n.school_id).first()
        return render_template(f'homeworks_delete.html', homeworks=homeworks, class_n_id=class_n_id,
                               class_n=class_n, school=school)
    return abort(404)


@app.route('/delete/homework/<int:homework_id>')
def delete_homework(homework_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(homework_id, Homework):
            return abort(404)
        db_sess = db_session.create_session()
        homework = db_sess.query(Homework).filter(Homework.id == homework_id).first()
        class_n_id = db_sess.query(Classes).filter(Classes.id == homework.class_n_id).first().id
        db_sess.delete(homework)
        db_sess.commit()
        return redirect(f'/delete/homeworks/{class_n_id}')
    return abort(404)


@app.route('/delete/school/<int:school_id>')
def delete_school(school_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(school_id, School):
            return abort(404)
        db_sess = db_session.create_session()
        school = db_sess.query(School).filter(School.id == school_id).first()
        # --------------------------------------------------------------------
        # Удаляем у пользователей школу и класс
        users = db_sess.query(User).filter(User.school_id == school_id).all()
        for user in users:
            user.school_id = None
            user.class_n_id = None
        # ------------------------------------------------------------------------
        # Удаляем всё д/з по id этой школы
        homeworks = db_sess.query(Homework).filter(Homework.school_id == school_id).all()
        for homework in homeworks:
            db_sess.delete(homework)
            db_sess.commit()
        # ------------------------------------------------------------------------
        # Удаляем все классы относящиеся к этой школе
        classes = db_sess.query(Classes).filter(Classes.school_id == school_id).all()
        for class_n in classes:
            db_sess.delete(class_n)
            db_sess.commit()
        # ------------------------------------------------------------------------
        # Удаляем саму школу
        db_sess.delete(school)
        db_sess.commit()
        return redirect('/schools')
    return abort(404)


@app.route('/delete/class/<int:class_n_id>')
def delete_class(class_n_id):
    if current_user.is_authenticated and current_user.admin:
        if not check_id(class_n_id, Classes):
            return abort(404)
        db_sess = db_session.create_session()
        class_n = db_sess.query(Classes).filter(Classes.id == class_n_id).first()
        school_id = class_n.school_id
        # --------------------------------------------------------------------
        # Удаляем у пользователей класс
        users = db_sess.query(User).filter(User.class_n_id == class_n_id).all()
        for user in users:
            user.class_n_id = None
        # ------------------------------------------------------------------------
        # Удаляем всё д/з по id этой школы
        homeworks = db_sess.query(Homework).filter(Homework.class_n_id == class_n_id).all()
        for homework in homeworks:
            db_sess.delete(homework)
            db_sess.commit()
        # ------------------------------------------------------------------------
        # Удаляем саму школу
        db_sess.delete(class_n)
        db_sess.commit()
        return redirect(f'/{school_id}/classes')
    return abort(404)


if __name__ == '__main__':
    db_session.global_init("db/diary.db")
    # app.run(host='0.0.0.0', port=5000)
    serve(app, port=5000)
