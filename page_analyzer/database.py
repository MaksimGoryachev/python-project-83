import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import flash

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
TIMEOUT = 15
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app1.log"),
        logging.StreamHandler()
    ]
)


def get_connection():
    """Создает и возвращает новое соединение с базой данных."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        flash(f"Ошибка подключения к базе данных: {e}", 'danger')
        return None


def create_url_check(url_id: int):
    """Создает запись в таблице url_checks."""
    query_check = 'SELECT name FROM urls WHERE id = %s LIMIT 1'
    query_insert = (
        'INSERT INTO url_checks'
        '(url_id, status_code, h1, title, description, created_at)'
        'VALUES (%s, %s, %s, %s, %s, %s)'
    )
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_check, (url_id,))
                result = cursor.fetchone()
                if not result:
                    flash('Произошла ошибка при проверке', 'danger')
                    logging.info('Не удалось получить данные по ID')
                    return None

                name = result[0]
                resp = get_response(name)  # type: ignore
                if resp is None:
                    flash('Произошла ошибка при проверке', 'danger')
                    logging.info('На запрос не получен ответ: RequestException')
                    return None

                status_code = resp.status_code
                if status_code != 200:
                    flash('Произошла ошибка при проверке', 'danger')
                    logging.info('Код статуса не равен 200')
                    return None

                h1, title, description = get_tag_content(resp)
                params = (url_id,
                          status_code,
                          h1,
                          title,
                          description,
                          datetime.now().date())
                cursor.execute(query_insert, params)
                flash('Страница успешно проверена', 'success')
                conn.commit()

    except psycopg2.Error as e:
        flash('Произошла ошибка при проверке', 'danger')
        logging.info('Произошла ошибка при проверке "%s"', e)
        return None


def get_scheme_hostname(valid_url):
    """Возвращает схему и хост из валидного URL."""
    parsed_url = urlparse(valid_url)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'


def create_new_url(url_to_save: str) -> int | None:
    """Создает новую запись в таблице urls и возвращает её ID."""
    created_at = datetime.now().date()
    name = get_scheme_hostname(url_to_save)

    query_check = 'SELECT id FROM urls WHERE name = %s LIMIT 1'
    query_insert = ('INSERT INTO urls (name, created_at) '
                    'VALUES (%s, %s) RETURNING id')

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_check, (name,))
                existing_url = cursor.fetchone()
                if existing_url:
                    flash('Страница уже существует', 'info')
                    return existing_url[0]

                cursor.execute(query_insert, (name, created_at))
                new_url_id = cursor.fetchone()
                conn.commit()
                if new_url_id:
                    flash('Страница успешно добавлена', 'success')
                    return new_url_id[0]
    except psycopg2.Error as e:
        flash(f'Ошибка при добавлении страницы: {e}', 'danger')
        logging.error('Ошибка при добавлении страницы: "%s"', e)
        return None


def get_one_url(url_id):
    """Возвращает данные по указанной странице."""
    query = (
        'SELECT * FROM urls WHERE id = %s'
    )
    url_data = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (url_id,))
                row = cursor.fetchone()
                if row is not None:
                    url_data = {
                        'id': row[0],
                        'name': row[1],
                        'created_at': row[2]
                    }
        return url_data
    except psycopg2.Error as e:
        flash(f'Ошибка при получении данных страницы: {e}', 'danger')
        return None


def get_all_urls() -> list:
    """Возвращает список всех добавленных страниц."""
    query = """
    SELECT DISTINCT ON (urls.id) urls.id, urls.name,
    MAX(url_checks.created_at), url_checks.status_code
    FROM urls
    LEFT JOIN url_checks ON urls.id = url_checks.url_id
    GROUP BY urls.id, url_checks.status_code, url_checks.created_at
    ORDER BY urls.id DESC, url_checks.created_at DESC;
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    urls = [
                        {
                            'id': row[0],
                            'name': row[1],
                            'last_check_date': row[2] or '',
                            'last_status_code': row[3] or ''
                        }
                        for row in rows
                    ]
                    return urls
        return None
    except psycopg2.Error as e:
        flash(f'Ошибка при получении страниц: {e}', 'danger')
        return None


def get_data_checks(url_id):
    """Возвращает список всех проверок для указанной страницы."""
    checks_query = (
        'SELECT * FROM url_checks '
        'WHERE url_id = %s ORDER BY id DESC'
    )
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(checks_query, (url_id,))
            data = cursor.fetchall()
            if data:
                checks_data = [
                    {
                        'id': row[0],
                        'status_code': row[2],
                        'h1': row[3],
                        'title': row[4],
                        'description': row[5],
                        'created_at': row[6]
                    }
                    for row in data
                ]
                return checks_data
        return None
    except psycopg2.Error as e:
        flash(f'Ошибка при получении данных: {e}', 'dander')
        return None


def get_response(url):
    """Отправляем запрос на сайт и получаем ответ."""
    try:
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=False)
        response.raise_for_status()
    except requests.RequestException as req_err:
        logging.info('Ошибка при выполнении запроса к сайту: %s', req_err)
        return None

    logging.info('Ответ от сайта получен')
    return response


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
