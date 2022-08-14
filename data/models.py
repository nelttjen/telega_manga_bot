import sqlalchemy

from sqlalchemy import Column as _
from .db_session import SqlAlchemyBase as Model


class AllowedUsers(Model):

    __tablename__ = 'al_users'

    id = _(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_id = _(sqlalchemy.Integer, unique=True)


class RegisteredUsers(Model):
    __tablename__ = 'users'

    id = _(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_id = _(sqlalchemy.Integer, unique=True)
    is_admin = _(sqlalchemy.Boolean, default=False)


class ToptoonManga(Model):
    __tablename__ = 'toptoon'

    id = _(sqlalchemy.Integer, autoincrement=True, primary_key=True)

    preview_link = _(sqlalchemy.String)

    index = _(sqlalchemy.Integer, unique=True)
    str_index = _(sqlalchemy.String)

    original_title = _(sqlalchemy.String)
    eng_title = _(sqlalchemy.String)
    translated_title = _(sqlalchemy.String)

    original_description = _(sqlalchemy.String)
    translated_description = _(sqlalchemy.String)

    original_tags = _(sqlalchemy.String)
    translated_tags = _(sqlalchemy.String)

    current_chapter = _(sqlalchemy.Integer)
    views = _(sqlalchemy.Integer)
    rating = _(sqlalchemy.Float)


class ToomicsManga(Model):
    __tablename__ = 'toomics'

    id = _(sqlalchemy.Integer, autoincrement=True, primary_key=True)

    preview_link = _(sqlalchemy.String)

    index = _(sqlalchemy.Integer, unique=True)

    ko_title = _(sqlalchemy.String)
    eng_title = _(sqlalchemy.String)
    rus_title = _(sqlalchemy.String)

    ko_description = _(sqlalchemy.String)
    rus_description = _(sqlalchemy.String)

    ko_tags = _(sqlalchemy.String)
    rus_tags = _(sqlalchemy.String)

    current_chapter = _(sqlalchemy.Integer)
