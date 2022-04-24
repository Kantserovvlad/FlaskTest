from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, SelectField
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

