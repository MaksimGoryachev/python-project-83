import os
from urllib.parse import urlparse
import psycopg2
import logging
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    # request,
    # redirect,
    # url_for,
)
import requests
from bs4 import BeautifulSoup
import validators

TIMEOUT = 0.1
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL1')
print(DATABASE_URL)


try:
    conn = psycopg2.connect(DATABASE_URL)
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")

logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщения
    handlers=[
        logging.FileHandler("app.log"),  # Запись в файл
        logging.StreamHandler()  # Вывод в консоль
    ]
)


@app.route('/')
def index():
    """Return the main page."""
    return render_template('base.html')


@app.get('/urls')
def urls():
    return render_template('urls.html')


@app.get('/urls/<int:url_id>')
def url(url_id):
    return render_template('url.html')


def validate(url_from_request: str) -> list:
    result = []
    if not url_from_request:
        result.append('URL обязателен')
    elif len(url_from_request) > 255:
        result.append('URL не должен быть длиннее 255 символов')
    elif not validators.url(url_from_request):
        result.append('Некорректный URL')
    return result


def get_scheme_hostname(valid_url):
    parsed_url = urlparse(valid_url)
    return f'{parsed_url.scheme}:// {parsed_url.netloc}'


def get_response(url):
    try:
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=False)
        response.raise_for_status()
    except requests.RequestException:
        logging.exception('Error when requesting the site')
        raise

    logging.info('The response from the site was received')
    return response


def get_tag_content(response):
    status_code = response.status_code
    soup = BeautifulSoup(response.text, 'html.parser')

    h1_tag = soup.find('h1')
    h1 = h1_tag.text.strip() if h1_tag else ''
    logging.info(f'H1 tag content: "{h1}"')

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''
    logging.info(f'H1 tag content: "{h1}"')

    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'].strip() if description_tag else ''
    logging.info(f'H1 tag content: "{h1}"')

    return status_code, h1, title, description


if __name__ == '__main__':
    app.run(debug=True)  # debug=True  на время отладки
