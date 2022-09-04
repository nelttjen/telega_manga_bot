import asyncio
import os
import uuid
import zipfile
import shutil

import pyquery as pq

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import IntegrityError

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data import db_session
from data import __all_models as models
from login import driver, driver_mics
from utils import ROOT_DIR
from utils.bot_utils import get_start_keyboard, check_admin, get_notify_keyboard, get_keyboard, get_cancel_keyboard
from data.config import ADMINS
from login.session import toptoon_s, toomics_s

with open(ROOT_DIR + '\\bot\\token.txt', 'r') as token:
    bot = Bot(token=token.read())
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    id_wait = State()
    notify_wait = State()
    message_all = State()
    message_admin = State()
    link_wait_toon = State()
    link_wait_mics = State()


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


@dp.message_handler(commands='notification', state='*')
@dp.message_handler(Text(equals='Настроить уведомления', ignore_case=True), state='*')
async def change_notification(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.notify_wait.set()
    keyb = get_notify_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('0 - Никакие, 1 - Вкл, выкл, ошибки, 2 - Все (Введите цифру или нажмите кнопку ниже)',
                        reply_markup=keyb)


@dp.message_handler(commands='send_all', state='*')
@dp.message_handler(Text(equals='Сообщение всем', ignore_case=True), state='*')
async def send_all_call(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.message_all.set()
    keyb = get_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('Введите сообщение (Всем пользователям)', reply_markup=keyb)


@dp.message_handler(commands='send_admins', state='*')
@dp.message_handler(Text(equals='Сообщение админам', ignore_case=True), state='*')
async def send_all_call(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.message_admin.set()
    keyb = get_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('Введите сообщение (Администраторам)', reply_markup=keyb)


@dp.message_handler(commands='parse_toon', state='*')
@dp.message_handler(Text('Parse TopToon', ignore_case=True), state='*')
async def parse_toon_call(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.link_wait_toon.set()
    keyb = get_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('Введите ссылку', reply_markup=keyb)


@dp.message_handler(commands='parse_mics', state='*')
@dp.message_handler(Text('Parse TooMics', ignore_case=True), state='*')
async def parse_mics_call(message: types.Message, state: FSMContext):
    if not check_admin(message.from_user.id):
        return

    await States.link_wait_mics.set()
    keyb = get_keyboard()
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    await message.reply('Введите ссылку', reply_markup=keyb)


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
        await send_admins('[ADMIN] Bot aborted by @nelttjen', level=1)
        quit()


@dp.message_handler(state=States.notify_wait)
async def notify_set(message: types.Message, state: FSMContext):
    messages = ['Никакие', 'Вкл, выкл, ошибки', 'Все']
    int_msg = ['0', '1', '2']
    if message.text in messages or message.text in int_msg:
        try:
            int_set = int(message.text)
        except ValueError:
            int_set = messages.index(message.text)
    else:
        await message.reply('Ошибка, попробуйте ещё раз (/cancel)')
        return
    sess = db_session.create_session()
    user = sess.query(models.RegisteredUsers).filter_by(user_id=message.from_user.id).first()
    user.notification_level = int_set
    sess.commit()
    await state.finish()
    await message.reply('Уведомления изменены', reply_markup=get_start_keyboard(message))


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
        await message.reply('Ошибка, попробуйте ещё раз (Возможно пользователь уже был добавлен) (/cancel)')


@dp.message_handler(state=States.message_all)
async def send_message_all(message: types.Message, state: FSMContext):
    await state.finish()
    await send_all(message.text, exclude=(message.from_user.id,), starts='[ОПОВЕЩЕНИЕ]')
    await bot.send_message(message.from_user.id, 'Сообщение отправлено', reply_markup=get_start_keyboard(message))


@dp.message_handler(state=States.message_admin)
async def send_message_admin(message: types.Message, state: FSMContext):
    await state.finish()
    await send_admins(message.text, exclude=(message.from_user.id,), starts='[ОПОВЕЩЕНИЕ (admin)]')
    await bot.send_message(message.from_user.id, 'Сообщение отправлено', reply_markup=get_start_keyboard(message))


@dp.message_handler(state=States.link_wait_toon)
async def parse_toon(message: types.Message, state: FSMContext):
    if message.text.startswith('https://'):
        uid = uuid.uuid4().hex
        try:
            link_list = message.text.replace('https://', '').split('/')
            index = link_list.index('ep_view')
            arcname = f'{link_list[index + 1]}_{link_list[index + 2]}'
        except:
            arcname = None
        await bot.send_message(message.from_user.id, f'Ваш id запроса: {uid}\n\n'
                                                     f'Архив готовится... (Может занять около минуты)')
        succ = await parse_chapter(toptoon_s, message.text, '.comic_img', 'data-src', uid, arcname=arcname)
        if succ:
            try:
                await bot.send_message(message.from_user.id, 'Архив готов, отправка...' if len(succ) == 1 else
                                                             f'Архивы готовы, всего: {len(succ)}, отправка...')
                for item in succ:
                    with open(item, 'rb') as file:
                        await bot.send_document(message.from_user.id, file, reply_markup=get_start_keyboard(message))
                await state.finish()
                try:
                    shutil.rmtree(f'{ROOT_DIR}\\temp\\chapters\\{uid}')
                except:
                    pass
            except Exception as e:
                await bot.send_message(message.from_user.id, f'Что-то пошло не так, попробуйте ещё раз\n{e.__str__()}')
        else:
            await bot.send_message(message.from_user.id, 'Что-то пошло не так, попробуйте ещё раз'
                                                         '\nВозможно ссылка неправильная '
                                                         'или глава не открыта на аккаунте')
    else:
        await bot.send_message(message.from_user.id, 'Введите ссылку', reply_markup=get_cancel_keyboard())


@dp.message_handler(state=States.link_wait_mics)
async def parse_mics(message: types.Message, state: FSMContext):
    if message.text.startswith('https://'):
        uid = uuid.uuid4().hex
        try:
            link_list = message.text.replace('https://', '').split('/')
            index = link_list.index('ep')
            arcname = f'{link_list[-1]}_{link_list[index + 1]}'
        except:
            arcname = None
        await bot.send_message(message.from_user.id, f'Ваш id запроса: {uid}\n\n'
                                                     f'Архив готовится... (Может занять около минуты)')
        succ = await parse_chapter(toomics_s, message.text, '.viewer__img', 'src', uid, arcname=arcname)
        if succ:
            try:
                await bot.send_message(message.from_user.id, 'Архив готов, отправка...' if len(succ) == 1 else
                                                             f'Архивы готовы, всего: {len(succ)}, отправка...')
                for item in succ:
                    with open(item, 'rb') as file:
                        await bot.send_document(message.from_user.id, file, reply_markup=get_start_keyboard(message))
                await state.finish()
                try:
                    shutil.rmtree(f'{ROOT_DIR}\\temp\\chapters\\{uid}')
                except:
                    pass
            except Exception as e:
                await bot.send_message(message.from_user.id, f'Что-то пошло не так, попробуйте ещё раз\n{e.__str__()}')
        else:
            await bot.send_message(message.from_user.id, 'Что-то пошло не так, попробуйте ещё раз'
                                                         '\nВозможно ссылка неправильная '
                                                         'или глава не открыта на аккаунте')
    else:
        await bot.send_message(message.from_user.id, 'Введите ссылку', reply_markup=get_cancel_keyboard())


async def parse_chapter(session, link, find, attr, uid, arcname=None):
    files_list = []
    directory = f'{ROOT_DIR}\\temp\\chapters\\{uid}'
    os.mkdir(directory)
    try:
        response = session.get(link)
    except:
        return
    with open(f'{directory}\\test.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    query = pq.PyQuery(response.text)
    items = list(query.find(f'{find} > img').items())
    if len(items) == 0:
        return
    names = []
    for i, item in enumerate(items):
        item_link = item.attr(attr)
        with open(f'{directory}\\{i}.jpg', 'wb') as out:
            out.write(session.get(item_link).content)
        names.append(f'{directory}\\{i}.jpg')
        await asyncio.sleep(0.1)
    sorted_list = []
    cur_list = []
    for path in names:
        size = sum([os.path.getsize(i) for i in cur_list])
        if size + os.path.getsize(path) < 20000000:
            cur_list.append(path)
            if names.index(path) + 1 == len(names):
                sorted_list.append(cur_list)
        else:
            sorted_list.append(cur_list)
            cur_list = [path,]
    for i, cell in enumerate(sorted_list):
        if arcname is not None:
            zip_f = f'{directory}\\{arcname}_part{i + 1}.zip'
        else:
            zip_f = f'{directory}\\{uid}_part{i + 1}.zip'
        with zipfile.ZipFile(zip_f, 'w') as zip_o:
            for item in cell:
                zip_o.write(item, arcname=item.split('\\')[-1])
        files_list.append(zip_f)
    return files_list


async def send_admins(text: str, level=0, exclude=(), starts=''):
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).filter_by(is_admin=True).all()
    for user in users:
        if user.notification_level >= level and user.user_id not in exclude:
            await bot.send_message(user.user_id, ' '.join([starts, text]) if starts else text)


async def send_all(text: str, exclude=(), starts=''):
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).all()
    for user in users:
        if user.user_id not in exclude:
            await bot.send_message(user.user_id, ' '.join([starts, text]) if starts else text)