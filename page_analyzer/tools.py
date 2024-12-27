import logging
import os
from urllib.parse import urlparse

import psycopg2
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = 15
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection() -> psycopg2.extensions.connection:
    """Создает и возвращает новое соединение с базой данных."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logging.info('Соединение с базой данных успешно установлено')
        return conn
    except psycopg2.OperationalError as e:
        logging.exception('Ошибка при установлении соединения: %s', e)
        return None
    except Exception as e:
        logging.exception('Произошла неожиданная ошибка: %s', e)
        return None


def close_connection(connection: psycopg2.extensions.connection) -> None:
    """Закрывает соединение с базой данных."""
    if connection:
        try:
            connection.close()
            logging.info('Соединение с базой данных закрыто')
        except Exception as e:
            logging.exception('Ошибка при закрытии соединения: %s', e)


def get_tag_content(resp):
    """Получает контент тега H1, заголовка страницы и описания."""
    soup = BeautifulSoup(resp.text, 'html.parser')

    h1_tag = soup.find('h1')
    h1 = h1_tag.text.strip() if h1_tag else ''
    logging.info('Содержимое тега H1: "%s"', h1)

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''
    logging.info('Содержимое тега Title: "%s"', title)

    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'].strip() if description_tag else ''
    logging.info('Содержимое тега Description: "%s"', description)

    return h1, title, description


def validate(url_from_request: str) -> bool:
    """Валидация URL."""
    return len(url_from_request) <= 255 and validators.url(url_from_request)


def get_response(url):
    """Отправляем запрос на сайт и получаем ответ."""
    try:
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=False)
        response.raise_for_status()
    except requests.RequestException as req_err:
        logging.exception('Ошибка при выполнении запроса к сайту: %s', req_err)
        return None

    logging.info('Ответ от сайта получен')
    return response


def get_scheme_hostname(valid_url):
    """Возвращает схему и хост из валидного URL."""
    parsed_url = urlparse(valid_url)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'
