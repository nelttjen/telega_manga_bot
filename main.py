import asyncio
import datetime
import inspect
import json
import logging
import os
import aioschedule
import pyquery as pq
import requests


from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from sqlalchemy.exc import IntegrityError
from pathlib import Path
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.support.ui import WebDriverWait

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from data.config import ADMINS
from data import db_session
import data.__all_models as models

load_dotenv(dotenv_path=Path('.env'))

bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

db_session.global_init('./db/db.sqlite3')

toptoon_s = requests.Session()

driver = Chrome('./chromedriver.exe')


class States(StatesGroup):
    id_wait = State()


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
    await message.reply('Добавить пользователя по ID\n\nID можно узнать: @getmyid_bot, @username_to_id_bot', reply_markup=keyb)


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
    except Exception:
        await message.reply('Ошибка, попробуйте ещё раз (/cancel)')


async def first_load():
    driver.get('https://toptoon.com/latest')
    await load_cookie_to_driver()


async def load_cookie_to_driver():
    with open('cookie.json', 'r', encoding='utf-8') as cookie:
        data = json.load(cookie)
        for i in data:
            cookie_now = {}
            if i['domain'].startswith('.'):
                cookie_now['domain'] = i['domain'][1:]
            else:
                cookie_now['domain'] = i['domain']
            cookie_now['name'] = i['name']
            cookie_now['value'] = i['value']
            driver.add_cookie(cookie_now)


async def login_topton_manual():
    try:
        driver.delete_all_cookies()
        driver.get('https://toptoon.com/latest')
        await asyncio.sleep(5)
        elem = driver.find_element(By.CLASS_NAME, 'switch_19mode')
        if elem.get_attribute('data-adult') != '3':
            elem.click()
            await asyncio.sleep(1)
            login = driver.find_element(By.NAME, 'userId')
            passw = driver.find_element(By.NAME, 'userPw')
            button = driver.find_element(By.CLASS_NAME, 'confirm-button')
            login.send_keys(os.getenv('TOPTOON_USERNAME'))
            await asyncio.sleep(1)
            passw.send_keys(os.getenv('TOPTOON_PASSWORD'))
            await asyncio.sleep(1)
            button.click()
            await asyncio.sleep(5)
            driver.get('https://toptoon.com/latest')
            switch = driver.find_element(By.CLASS_NAME, 'switch_19mode')
            if switch.get_attribute('data-adult') != '3':
                driver.get('https://toptoon.com/latest')
                switch = driver.find_element(By.CLASS_NAME, 'switch_19mode')
                switch.click()
            await login_toptoon()
        else:
            await login_toptoon()
    except Exception:
        await login_toptoon()


async def login_toptoon():
    driver.get('https://toptoon.com/latest')
    with open('cookie.json', 'w', encoding='utf-8') as cookie:
        cookies = []
        for i in driver.get_cookies():
            if i['domain'] == 'toptoon.com' or i['domain'] == '.toptoon.com':
                cookies.append({
                    'domain': i['domain'],
                    'name': i['name'],
                    'value': i['value'],
                })
        json.dump(cookies, cookie)
    with open('cookie.json', 'r', encoding='utf-8') as cookie:
        data = json.load(cookie)
        for i in data:
            toptoon_s.cookies.set(name=i['name'], value=i['value'], domain=i['domain'])


def make_translations(texts: list, from_lang='ko', to_lang='ru'):
    token = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens',
                          json={'yandexPassportOauthToken': os.getenv('YA_TOKEN')}).json()['iamToken']
    data = {
        'sourceLanguageCode': from_lang,
        'targetLanguageCode': to_lang,
        'texts': texts,
        'folderId': os.getenv('YA_FOLDER'),
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    resp = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate', json=data, headers=headers)
    return resp.json()['translations']


async def fetch_toptoon():
    global count
    session = db_session.create_session()
    m_resp = toptoon_s.get('https://toptoon.com/latest').text
    html = pq.PyQuery(m_resp)
    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(m_resp)
    created = session.query(models.ToptoonManga).all()

    data = []

    if html('a.switch_19mode').attr('data-adult') == '3':
        if count > 0:
            await send_admins(f'[ADMIN] TOPTOON Re-logged in successfully at {datetime.datetime.now()} UTC+5')
        count = 0
        for item in html('.jsComicObj').items():
            if int(item.attr('data-comic-idx')) not in [i.index for i in created]:
                img_url = item.find('.thumbbox').attr('data-bg')
                index = int(item.attr('data-comic-idx'))
                str_index = item.attr('data-comic-id')

                curr_chapter = int(item.find('.tit_thumb_e').text().replace('제', '').replace('화', ''))
                views = int(float(item.find('.viewCountTxt').text().replace('만', '')) * 10000)

                orig_title = item.find('.thumb_tit_text').text()
                eng_title = make_translations([orig_title, ], to_lang="en")[0]['text']
                transl_title = make_translations([orig_title, ])[0]['text']

                html2 = pq.PyQuery(toptoon_s.get(f'https://toptoon.com/comic/ep_list/{str_index}').text)

                orig_desc = html2('.story_synop').text()
                transl_desc = make_translations([orig_desc, ])[0]['text']

                orig_tags = [i.text() for i in html2('.comic_tag span').items()]
                for i, cell in enumerate(orig_tags):
                    str_cell = '_'.join(cell.split(' '))
                    orig_tags[i] = str_cell
                transl_tags = make_translations(orig_tags)

                rating = float(html2('.comic_spoint').text())

                text = f"""
                #toptoon #{str_index}
                
                Новая манга!
                Ссылка: https://toptoon.com/comic/ep_list/{str_index}
                
                DEBUG: {index}
                
                ===Название===
                {transl_title} / {eng_title} / {orig_title}
                
                ===Описание=== 
                Перевод: {transl_desc}
                Оригинал: {orig_desc}
                
                Теги: {' '.join(orig_tags)} {
                ' '.join(['_'.join(i['text'].replace('# ', '#').split(' ')) for i in transl_tags])
                }

                Всего глав: {curr_chapter}
                Просмотров: {views}
                Рейтинг: {rating}
                """

                text = inspect.cleandoc(text)

                data.append({'text': text, 'media': img_url})

                new = models.ToptoonManga(
                    preview_link=img_url,
                    index=index,
                    str_index=str_index,
                    original_title=orig_title,
                    eng_title=eng_title,
                    translated_title=transl_title,
                    original_description=orig_desc,
                    translated_description=transl_title,
                    original_tags=' '.join(orig_tags),
                    translated_tags=' '.join(['_'.join(i['text'].replace('# ', '#').split(' ')) for i in transl_tags]),
                    current_chapter=curr_chapter,
                    views=views,
                    rating=rating,
                )
                session.add(new)
                print(f'created: {index}')
        session.commit()
        return {'success': True, 'data': data}
    else:
        if count == 3:
            await send_admins('[ADMIN] FAILED TO LOG IN TOPTOON, aborting...')
            quit()
        count += 1
        await login_topton_manual()
        await send_admins(f'[ADMIN] BAD SESSION! Trying to re-log in {count}/3')

        return {'success': False}


async def fetch_manga():
    global noticed
    data = await fetch_toptoon()
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).all()
    if data['success']:
        for item in data['data']:
            for user in users:
                await bot.send_photo(user.user_id,
                                     item['media'],
                                     caption=item['text'])
            await asyncio.sleep(1)


async def scheduler():
    aioschedule.every(30).seconds.do(fetch_manga)
    # aioschedule.every(30).minutes.do(login_toptoon)
    while True:
        await asyncio.sleep(1)
        await aioschedule.run_pending()


async def start_scheduler(_):
    _start = datetime.datetime.now()
    # await first_load()
    # await login_toptoon()
    await login_topton_manual()
    await fetch_manga()
    asyncio.create_task(scheduler())
    await send_admins(f'[ADMIN] Bot started in {(datetime.datetime.now() - _start)} seconds')


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


def init_logger():
    logger = logging.getLogger()
    logger_handler = logging.StreamHandler()
    logger.addHandler(logger_handler)
    logger.removeHandler(logger.handlers[0])

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s: %(message)s")
    logger_handler.setFormatter(formatter)


if __name__ == "__main__":
    init_logger()
    noticed = False
    count = 0
    executor.start_polling(dp, skip_updates=True, on_startup=start_scheduler)
