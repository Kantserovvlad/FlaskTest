from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, SelectField, StringField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class SetSchool(FlaskForm):
    school_id = SelectField('Выберите школу')
    submit = SubmitField('Сохранить и указать класс')


class SetClass(FlaskForm):
    class_n_id = SelectField('Выберите класс')
    submit = SubmitField('Сохранить')


class NewPassword(FlaskForm):
    password_old = PasswordField('Старый пароль', validators=[DataRequired()])
    password_new = PasswordField('Новый пароль', validators=[DataRequired()])
    password_new_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Сохранить новый пароль')


class ChangeInfo(FlaskForm):
    email = EmailField('Почта', validators=[Email()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    submit = SubmitField('Сохранить данные')


class AddSchoolClass(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Сохранить')
