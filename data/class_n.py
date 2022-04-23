import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class Classes(SqlAlchemyBase, UserMixin):
    __tablename__ = 'class_n'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    school_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("schools.id"))
