import asyncio
import datetime
import inspect
import json
import logging
import os
import string

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
toomics_s = requests.Session()

driver = Chrome('./chromedriver.exe')
driver_mics = Chrome('./chromedriver.exe')

driver.set_window_rect(1920, 0, 850, 1000)
driver_mics.set_window_rect(2790, 0, 1100, 1000)


class States(StatesGroup):
    id_wait = State()


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


def get_cookie_from_driver(dr, domain):
    cookies = []
    for i in dr.get_cookies():
        if domain in i['domain']:
            cookies.append({
                'domain': i['domain'],
                'name': i['name'],
                'value': i['value'],
            })
    return cookies


def load_to_session(file, session):
    try:
        data = json.load(file)
        for i in data:
            session.cookies.set(name=i['name'], value=i['value'], domain=i['domain'])
    except:
        return


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


async def login_toomics_manual():
    try:
        driver_mics.delete_all_cookies()
        driver_mics.get('https://www.toomics.com/webtoon/toon_list/display/G2')
        try:
            driver_mics.find_element(By.CSS_SELECTOR, '.mode3.active')
            succ = True
        except Exception:
            succ = False
        if not succ:
            element = driver_mics.find_element(By.CLASS_NAME, 'mode3')
            element.click()
            await asyncio.sleep(3)
            driver_mics.find_element(By.CSS_SELECTOR, '.auths__login > a').click()
            await asyncio.sleep(3)
            login = driver_mics.find_element(By.NAME, 'user_id')
            passw = driver_mics.find_element(By.NAME, 'user_pw')
            login.send_keys(os.getenv('TOOMICS_USERNAME'))
            passw.send_keys(os.getenv('TOOMICS_PASSWORD'))
            driver_mics.find_element(By.CSS_SELECTOR, '#login_frm > p > button').click()
            await login_toomics()
        else:
            print(driver_mics.find_element(By.CSS_SELECTOR, '.mode3.active'))
            await login_toomics()
    except Exception as e:
        print(e)
        quit()
        await login_toomics()


async def login_toomics():
    # driver_mics.get('https://www.toomics.com/webtoon/toon_list/display/G2')
    # with open('cookie_toomics.json', 'w', encoding='utf-8') as f:
    #     cookies = get_cookie_from_driver(driver_mics, 'toomics.com')
    #     json.dump(cookies, f)
    with open('cookie_toomics.json', 'r', encoding='utf-8') as f:
        load_to_session(f, toomics_s)


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
    with open('cookie_toptoon.json', 'w', encoding='utf-8') as cookie:
        cookies = get_cookie_from_driver(driver, 'toptoon.com')
        json.dump(cookies, cookie)
    with open('cookie_toptoon.json', 'r', encoding='utf-8') as cookie:
        load_to_session(cookie, toptoon_s)


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
    global count_toptoon
    if count_toptoon > 3:
        return {'success': False}
    session = db_session.create_session()
    m_resp = toptoon_s.get('https://toptoon.com/latest').text
    html = pq.PyQuery(m_resp)
    with open('./debug/toptoon.html', 'w', encoding='utf-8') as f:
        f.write(m_resp)
    created = session.query(models.ToptoonManga).all()

    data = []

    if html('a.switch_19mode').attr('data-adult') == '3':
        if count_toptoon > 0:
            await send_admins(f'[ADMIN] TOPTOON Re-logged in successfully at {datetime.datetime.now()} UTC+5')
        count_toptoon = 0
        for item in html('.jsComicObj').items():
            if int(item.attr('data-comic-idx')) not in [i.index for i in created]:
                img_url = item.find('.thumbbox').attr('data-bg')
                index = int(item.attr('data-comic-idx'))
                str_index = item.attr('data-comic-id')

                curr_chapter = int(get_clear_number(item.find('.tit_thumb_e').text()))
                views = int(float(get_clear_number(item.find('.viewCountTxt').text())) * 10000)

                orig_title = item.find('.thumb_tit_text').text()

                html2 = pq.PyQuery(toptoon_s.get(f'https://toptoon.com/comic/ep_list/{str_index}').text)

                orig_desc = html2('.story_synop').text()

                orig_tags = [i.text() for i in html2('.comic_tag span').items()]
                for i, cell in enumerate(orig_tags):
                    str_cell = '_'.join(cell.split(' '))
                    orig_tags[i] = str_cell

                rating = float(html2('.comic_spoint').text())

                try:
                    eng_title = make_translations([orig_title, ], to_lang="en")[0]['text']
                    transl_title = make_translations([orig_title, ])[0]['text']
                    transl_desc = make_translations([orig_desc, ])[0]['text']
                    transl_tags = make_translations(orig_tags)
                except:
                    eng_title, transl_title, transl_desc, transl_tags = ['err'] * 4

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
Рейтинг: {rating}"""

                text = inspect.cleandoc(text)
                if len(text) > 4096:
                    text = text.replace('Перевод: ', '').replace(f'Оригинал: {orig_desc}', '')
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
                print(f'toptoon created: {index}')
        session.commit()
        return {'success': True, 'data': data}
    else:
        if count_toptoon == 3:
            await send_admins('[ADMIN] FAILED TO LOG IN TOPTOON, DISABLED!')
            count_toptoon = 10
            return {'success': False}
        count_toptoon += 1
        await send_admins(f'[ADMIN] TOPTOON BAD SESSION! Trying to re-log in {count_toptoon}/3')
        await login_topton_manual()

        return {'success': False}


async def fetch_toomics():
    global count_toomics
    if count_toomics > 3:
        return {'success': False}
    session = db_session.create_session()

    m_resp = toomics_s.get('https://www.toomics.com/webtoon/toon_list/display/G2')
    html = pq.PyQuery(m_resp.text)
    with open('./debug/toomics.html', 'w', encoding='utf-8') as f:
        f.write(m_resp.text)

    data = []

    if html('.mode3.active'):
        if count_toomics > 3:
            count_toomics = 0
            await send_admins(f'[ADMIN] Toomics re-logged in succesfully at {datetime.datetime.now()} UTC+5')
        items = html('.grid__li').items()
        exists = session.query(models.ToomicsManga).all()
        exists_indexes = [item.index for item in exists]
        for item in items:
            if int(item.find('a').attr('href').split('/')[-1]) not in exists_indexes:
                item_link = f'https://www.toomics.com{item.find("a").attr("href")}'
                html2 = pq.PyQuery(toomics_s.get(item_link).text)

                preview_img = item.find('.toon-dcard__thumbnail img').attr('data-original')

                index = int(item.find('a').attr("href").split('/')[-1])

                ko_title = item.find('.toon-dcard__title').text()
                ko_desc = html2('.episode__summary').text().replace('+ 더보기', '')
                ko_tags = ' '.join(['_'.join(tag.text().split(" ")) for tag in html2('.episode__tags .tag').items()])

                chapter = int(get_clear_number(item.find('.toon-dcard__subtitle').text()[:4]))

                try:
                    eng_title = make_translations([ko_title, ], to_lang='en')[0]['text']
                    rus_title = make_translations([ko_title, ])[0]['text']
                    rus_desc = make_translations([ko_desc, ])[0]['text']
                    rus_tags = make_translations([ko_tags, ])[0]['text']\
                        .replace("# ", '#').replace('"', '').replace('-', '_')
                except:
                    eng_title, rus_title, rus_desc, rus_tags = ['err'] * 4

                # #Сериал Тойо #драма -> #Сериал_Тойо #драма
                rus_tags = rus_tags[1:].split('#')
                rus_tags = f"#{' #'.join(['_'.join(tag.strip().capitalize().split(' ')) for tag in rus_tags])}"

                print(*[index, ko_title, ko_desc, ko_tags, eng_title, rus_title, rus_desc, rus_tags, chapter], sep='\n')

                _new = models.ToomicsManga(
                    preview_link=preview_img,
                    index=index,
                    ko_title=ko_title,
                    eng_title=eng_title,
                    rus_title=rus_title,
                    ko_description=ko_desc,
                    rus_description=rus_desc,
                    ko_tags=ko_tags,
                    rus_tags=rus_tags,
                    current_chapter=chapter,
                )
                session.add(_new)
                print(f'toomics created: {index}')
                text = f"""
#toomics #{index}
                
Новая манга!
Ссылка: {item_link}
                
Индекс: {index}
                
===Название===
{ko_title} / {eng_title} / {rus_title}
                
===Описание===
Перевод: {rus_desc}
Оригинал: {ko_desc}
                
Теги: {ko_tags} {rus_tags}
                
Всего глав: {chapter}"""
                text = inspect.cleandoc(text)
                if len(text) > 4096:
                    text = text.replace(f'Оригинал: {ko_desc}', '').replace('Перевод: ', '')
                data.append({'text': text, 'media': preview_img})
        session.commit()
        return {'success': True, 'data': data}
    else:
        if count_toomics == 3:
            await send_admins('[ADMIN] FAILED TO ENABLE 18+ TOOMICS, DISABLED!')
            count_toomics = 10
            return {'success': False}
        count_toomics += 1
        await send_admins(f'[ADMIN] TOOMICS BAD SESSION! Trying to re-log in {count_toomics}/3')
        await login_toomics_manual()
        return {'success': False}


async def fetch_manga():
    session = db_session.create_session()
    users = session.query(models.RegisteredUsers).all()
    data = await fetch_toptoon()
    data2 = await fetch_toomics()

    async def send_by_data(dict_data):
        for item in dict_data['data']:
            print(len(item['text']), item['media'])
            print(item['text'])
            for user in users:
                try:
                    await bot.send_photo(user.user_id,
                                         item['media'],
                                         caption=item['text'])
                except:
                    continue
            await asyncio.sleep(1)

    if data['success']:
        await send_by_data(data)
    if data2['success']:
        await send_by_data(data2)


async def scheduler():
    aioschedule.every(30).seconds.do(fetch_manga)
    # aioschedule.every(30).minutes.do(login_toptoon)
    while True:
        await asyncio.sleep(1)
        await aioschedule.run_pending()


async def start_scheduler(_):
    _start = datetime.datetime.now()
    if not DEBUG:
        await login_topton_manual()
        await login_toomics_manual()
        await send_admins(f'[ADMIN] Bot started in PRODUCTION mode '
                          f'({(datetime.datetime.now() - _start).seconds} seconds)')
        await fetch_manga()
        asyncio.create_task(scheduler())

    else:
        pass
        await send_admins('[ADMIN] Bot started in DEBUG mode')


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

    DEBUG = False

    count_toptoon = 0
    count_toomics = 0

    try:
        os.mkdir('./debug')
    except:
        pass

    executor.start_polling(dp, skip_updates=True, on_startup=start_scheduler)
