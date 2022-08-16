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
        # DEBUG CODE
        await send_admins('[ADMIN] Bot started in DEBUG mode')


async def notify(_):
    if _ is None:
        await send_admins(f'[ADMIN] Bot aborted by console at {datetime.datetime.now()} UTC+5')
    else:
        await send_admins(f'[ADMIN] CRITICAL ERROR: Bot crushed')


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


if __name__ == "__main__":
    load_dotenv(dotenv_path=Path('.env'))
    db_session.global_init(ROOT_DIR + '\\db\\db.sqlite3')
    init_logger()
    init_dirs()

    DEBUG = False
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=start_scheduler, on_shutdown=notify)
    except KeyboardInterrupt:
        notify(None)
        driver.quit()
        driver_mics.quit()
        quit()
