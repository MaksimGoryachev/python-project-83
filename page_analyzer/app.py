import logging
import os

import validators
from dotenv import load_dotenv
from flask import (Flask, abort, flash, get_flashed_messages, redirect,
                   render_template, request, url_for)

from page_analyzer.database import (create_new_url, create_url_check,
                                    get_all_urls, get_data_checks, get_one_url)

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)


@app.route('/')
def index():
    """Возвращает главную страницу."""
    return render_template('base.html')


@app.get('/urls')
def get_urls():
    """Возвращает страницу со списком всех сайтов."""
    urls = get_all_urls()
    return render_template('urls.html', urls=urls)


@app.get('/urls/<int:url_id>')
def get_url_id(url_id):
    """Возвращает страницу с полной информацией."""
    url_data = get_one_url(url_id)
    try:
        if url_data is None:
            abort(404)
        checks_url = get_data_checks(url_id)
        return render_template(
            'url.html',
            checks_url=checks_url,
            url=url_data
        )
    except Exception as e:
        logging.exception('Произошла ошибка при получении данных URL: "%s"', e)
        abort(500)


@app.post('/urls')
def add_url():
    """Добавление новой страницы."""
    url_from_request = request.form.get('url', '')
    errors = validate(url_from_request)

    if errors:
        return render_template(
            'base.html',
            url_from_request=url_from_request
        ), 422
    url_id = create_new_url(url_from_request)

    if url_id is None:
        flash('Ошибка сохранения в базу', 'danger')
        return render_template(
            'base.html',
            url_from_request=url_from_request,
        ), 422
    return redirect(url_for('get_url_id', url_id=url_id), 302)


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    """Проверка статуса страницы."""
    create_url_check(url_id)
    return redirect(url_for('get_url_id', url_id=url_id))


@app.errorhandler(404)
def page_not_found(error):
    """Обработчик ошибки 404."""
    logging.exception(error)
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Обработчик ошибки 500."""
    logging.exception(error)
    return render_template('500.html'), 500


def validate(url_from_request: str) -> list:
    """Валидация URL."""
    if len(url_from_request) > 255:
        flash('URL превышает 255 символов', 'danger')
    elif not validators.url(url_from_request):
        flash('Некорректный URL', 'danger')
    return get_flashed_messages(category_filter='danger')


if __name__ == '__main__':
    app.run()
