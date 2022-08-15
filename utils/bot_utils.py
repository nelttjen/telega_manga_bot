import string

from aiogram import types

from data import db_session
from data import __all_models as models


def get_clear_number(text):
    rem = ''
    for i in text:
        if i in string.digits:
            rem += i
    return rem


def get_start_keyboard(message):
    keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if check_admin(message.from_user.id):
        button = types.KeyboardButton('Добавить пользователя в бота')
        keyb.add(button)
    else:
        keyb = types.ReplyKeyboardRemove()
    return keyb


def check_admin(user_id):
    sess = db_session.create_session()
    user = sess.query(models.RegisteredUsers).filter_by(user_id=user_id).first()
    if user:
        return user.is_admin
    return False

