import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class Homework(SqlAlchemyBase, UserMixin):
    __tablename__ = 'homeworks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    content = sqlalchemy.Column(sqlalchemy.String)

    school_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("schools.id"))
    class_n_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("class_n.id"))
