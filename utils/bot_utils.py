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
        button2 = types.KeyboardButton('Настроить уведомления')
        message_all = types.KeyboardButton('Сообщение всем')
        message_admins = types.KeyboardButton('Сообщение админам')
        parse_toon = types.KeyboardButton('Parse TopToon')
        parse_mics = types.KeyboardButton('Parse TooMics')
        keyb.add(button)
        keyb.add(button2)
        keyb.row(message_admins, message_all)
        keyb.row(parse_toon, parse_mics)
    else:
        keyb = types.ReplyKeyboardRemove()
    return keyb


def get_notify_keyboard():
    keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Все')
    btn2 = types.KeyboardButton('Вкл, выкл, ошибки')
    btn3 = types.KeyboardButton('Никакие')
    keyb.row(btn1, btn2, btn3)
    return keyb


def get_keyboard():
    return types.ReplyKeyboardMarkup(resize_keyboard=True)


def get_cancel_keyboard():
    keyb = get_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    return keyb


def check_admin(user_id):
    sess = db_session.create_session()
    user = sess.query(models.RegisteredUsers).filter_by(user_id=user_id).first()
    if user:
        return user.is_admin
    return False

