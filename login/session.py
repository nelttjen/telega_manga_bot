import json
import os

import requests
import asyncio

from selenium.webdriver.common.by import By
from utils import ROOT_DIR

from . import driver, driver_mics

toptoon_s = requests.Session()
toomics_s = requests.Session()


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
        await login_toomics()


async def login_toomics():
    driver_mics.get('https://www.toomics.com/webtoon/toon_list/display/G2')
    with open(ROOT_DIR + '\\temp\\cookies\\cookie_toomics.json', 'w', encoding='utf-8') as f:
        cookies = get_cookie_from_driver(driver_mics, 'toomics.com')
        json.dump(cookies, f)
    with open(ROOT_DIR + '\\temp\\cookies\\cookie_toomics.json', 'r', encoding='utf-8') as f:
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
    with open(ROOT_DIR + '\\temp\\cookies\\cookie_toptoon.json', 'w', encoding='utf-8') as cookie:
        cookies = get_cookie_from_driver(driver, 'toptoon.com')
        json.dump(cookies, cookie)
    with open(ROOT_DIR + '\\temp\\cookies\\cookie_toptoon.json', 'r', encoding='utf-8') as cookie:
        load_to_session(cookie, toptoon_s)