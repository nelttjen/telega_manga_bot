import os

import requests

token_api = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
translation_api = 'https://translate.api.cloud.yandex.net/translate/v2/translate'


def get_translate_token(user_token):
    return requests.post(token_api,
                         json={'yandexPassportOauthToken': user_token}).json()['iamToken']


def make_translations(texts: list, from_lang='ko', to_lang='ru'):
    token = get_translate_token(os.getenv('YA_TOKEN'))

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
    resp = requests.post(translation_api,
                         json=data, headers=headers)
    return resp.json()['translations']
