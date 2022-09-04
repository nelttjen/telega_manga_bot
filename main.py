from dotenv import load_dotenv
from pathlib import Path

import asyncio
import datetime
import logging
import os
import aioschedule

import data.__all_models as models

from data import db_session
from utils import ROOT_DIR
from login.session import login_toomics_manual, login_topton_manual, driver, driver_mics
from bot.actions import fetch_toptoon, fetch_toomics

from bot.bot import bot, dp, send_admins
from aiogram import executor

load_dotenv(dotenv_path=Path('/.env'))


async def fetch_manga(forced=False):
    if datetime.datetime.now().strftime('%H:%M') in \
            ['16:59', '17:00', '17:59', '18:00', '18:59', '19:00', '19:59', '20:00'] and \
            not forced:
        logging.info('Basic task has been canceled')
        return
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


async def fetch_20():
    times = 0
    while times < 25:
        await fetch_manga(forced=True)
        await asyncio.sleep(3)
        times += 1
        logging.info(f'Manual fetch {times}/25')


async def scheduler():
    aioschedule.every(40).seconds.do(fetch_manga)
    aioschedule.every().day.at('16:59').do(fetch_20)
    aioschedule.every().day.at('17:59').do(fetch_20)
    aioschedule.every().day.at('18:59').do(fetch_20)
    aioschedule.every().day.at('19:59').do(fetch_20)
    while True:
        await asyncio.sleep(1)
        await aioschedule.run_pending()


async def start_scheduler(_):
    _start = datetime.datetime.now()
    if not DEBUG:
        driver.set_window_rect(1920, 0, 850, 1000)
        driver_mics.set_window_rect(2800, 0, 1100, 1000)
        await login_topton_manual()
        await login_toomics_manual()
        await send_admins(f'[ADMIN] Bot started '
                          f'({(datetime.datetime.now() - _start).seconds} seconds)', level=1)
        driver.set_window_rect(3920, 0, 850, 1000)
        driver_mics.set_window_rect(4790, 0, 1100, 1000)
        await fetch_manga()
        asyncio.create_task(scheduler())

    else:
        # DEBUG CODE

        await login_topton_manual()
        await send_admins('[ADMIN] Bot started in DEBUG mode', level=1)


async def notify(_):
    if _:
        await send_admins(f'[ADMIN] Bot aborted by console at {datetime.datetime.now()} UTC+5', level=1)
    else:
        await send_admins(f'[ADMIN] CRITICAL ERROR: Bot crushed', level=1)


def init_logger():
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger()
    logger_handler = logging.StreamHandler()
    logger.addHandler(logger_handler)
    logger.removeHandler(logger.handlers[0])

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s: %(message)s")
    logger_handler.setFormatter(formatter)


def init_dirs():
    os.mkdir(ROOT_DIR + '\\temp') if not os.path.exists(ROOT_DIR + '\\temp') else None
    os.mkdir(ROOT_DIR + '\\temp\\cookies') if not os.path.exists(ROOT_DIR + '\\temp\\cookies') else None
    os.mkdir(ROOT_DIR + '\\temp\\chapters') if not os.path.exists(ROOT_DIR + '\\temp\\chapters') else None


if __name__ == "__main__":
    load_dotenv(dotenv_path=Path('.env'))
    db_session.global_init(ROOT_DIR + '\\db\\db.sqlite3')
    init_logger()
    init_dirs()

    DEBUG = False
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=start_scheduler, on_shutdown=notify)
    except KeyboardInterrupt:
        notify(True)
        driver.quit()
        driver_mics.quit()
        quit()
