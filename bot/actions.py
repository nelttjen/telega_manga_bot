import datetime
import inspect

import pyquery as pq

from data import db_session
from data import __all_models as models
from login.session import toptoon_s, toomics_s, login_topton_manual, login_toomics_manual
from utils import ROOT_DIR
from utils.bot_utils import get_clear_number
from utils.translator import make_translations

from bot.bot import send_admins

count_toptoon = 0
count_toomics = 0


async def fetch_toptoon():
    global count_toptoon
    if count_toptoon > 3:
        return {'success': False}
    session = db_session.create_session()
    m_resp = toptoon_s.get('https://toptoon.com/latest').text
    html = pq.PyQuery(m_resp)
    with open(ROOT_DIR + '\\temp\\toptoon.html', 'w', encoding='utf-8') as f:
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
    with open(ROOT_DIR + '\\temp\\toomics.html', 'w', encoding='utf-8') as f:
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
                    rus_tags = make_translations([ko_tags, ])[0]['text'] \
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
#toomics

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