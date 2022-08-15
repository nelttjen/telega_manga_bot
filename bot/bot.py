import os

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data import db_session
from utils.bot_utils import get_start_keyboard, check_admin
from data.config import ADMINS
from data import __all_models as models
from login import driver, driver_mics
from utils import ROOT_DIR

with open(ROOT_DIR + '\\bot\\token.txt', 'r') as token:
    bot = Bot(token=token.read())
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    id_wait = State()


@dp.message_handler(commands="start", state='*')
async def start(message: types.Message):
    session = db_session.create_session()
    keyb = get_start_keyboard(message)
    if message.from_user.id not in [user.user_id for user in session.query(models.AllowedUsers).all()] and \
            message.from_user.id not in ADMINS:
        await message.answer('Not allowed')
        return
    try:
        session.add(models.RegisteredUsers(
            user_id=message.from_user.id,
            is_admin=message.from_user.id in ADMINS
        ))
        session.commit()
        await message.reply("Уведомления запущены", reply_markup=keyb)
    except IntegrityError:

        await message.reply('Вы уже подписаны', reply_markup=keyb)
    finally:
        session.close()


@dp.message_handler(commands='add_user', state='*')
@dp.message_handler(Text(equals='Добавить пользователя в бота', ignore_case=True), state='*')
async def add_user_call(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.id_wait.set()
    keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('Добавить пользователя по ID\n\nID можно узнать: @getmyid_bot, @username_to_id_bot',
                        reply_markup=keyb)


@dp.message_handler(commands='cancel', state='*')
@dp.message_handler(Text('отмена', ignore_case=True), state='*')
async def cancel_inputs(message: types.Message, state: FSMContext):
    curr = await state.get_state()
    if curr is None:
        await state.finish()
    keyb = get_start_keyboard(message)
    await message.reply('Главное меню', reply_markup=keyb)


@dp.message_handler(commands='stop7115', state='*')
async def stop(m):
    if m.from_user.id == 474761641:
        driver.quit()
        driver_mics.quit()
        await send_admins('[ADMIN] Bot aborted by @nelttjen')
        quit()


@dp.message_handler(state=States.id_wait)
async def add_by_user_id(message: types.Message, state: FSMContext):
    try:
        sess = db_session.create_session()
        new = models.AllowedUsers(
            user_id=int(message.text)
        )
        sess.add(new)
        sess.commit()
        await state.finish()
        keyb = get_start_keyboard(message)
        await bot.send_message(message.from_user.id, 'Пользователь добавлен', reply_markup=keyb)
    except:
        await message.reply('Ошибка, попробуйте ещё раз (/cancel)')


async def send_admins(text: str):
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).filter_by(is_admin=True).all()
    for user in users:
        await bot.send_message(user.user_id, text)


async def send_all(text: str):
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).all()
    for user in users:
        await bot.send_message(user.user_id, text)