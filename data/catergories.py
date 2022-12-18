import datetime
import sqlalchemy
from sqlalchemy import orm
from data.db_session import SqlAlchemyBase


class Category(SqlAlchemyBase):
    """Модель категории"""
    __tablename__ = 'categories'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    items = orm.relation('Item', back_populates='category')  # привязываем записи к категории

    def __repr__(self):
        return f'<Category> {self.name}'
