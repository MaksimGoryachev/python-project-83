import os
import logging
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages
)
import validators
from page_analyzer.database import (
    get_all_urls,
    create_url_check,
    get_data_checks,
    create_new_url,
    get_one_url,
)


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL1')

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
    if url_data is None:
        return 'Страница не найдена!', 404
    messages = get_flashed_messages(with_categories=True)
    checks_url = get_data_checks(url_id)
    return render_template(
        'url.html',
        checks_url=checks_url,
        url=url_data,
        messages=messages
    )


@app.post('/urls')
def add_url():
    """Добавление новой страницы."""
    url_from_request = request.form.get('url', '')
    errors = validate(url_from_request)
    url_id = create_new_url(url_from_request) if not errors else 0

    if errors:
        return render_template(
            'base.html',
            url_from_request=url_from_request,
            errors=errors
        ), 422

    if url_id is None:
        errors.append('Ошибка сохранения в базу')
        return render_template(
            'base.html',
            url_from_request=url_from_request,
            errors=errors
        ), 422

    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_url_id', url_id=url_id))


@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    """Проверка статуса страницы."""
    create_url_check(url_id)
    return redirect(url_for('get_url_id', url_id=url_id))


def validate(url_from_request: str) -> list:
    """Валидация URL."""
    result = []
    if not url_from_request:
        result.append('URL обязателен')
    elif len(url_from_request) > 255:
        result.append('URL не должен быть длиннее 255 символов')
    elif not validators.url(url_from_request):
        result.append('Некорректный URL')
    return result


if __name__ == '__main__':
    app.run(debug=True)  # debug=True  на время отладки
