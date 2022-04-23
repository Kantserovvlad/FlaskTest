import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class School(SqlAlchemyBase, UserMixin):
    __tablename__ = 'schools'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
