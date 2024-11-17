import os
# from urllib.parse import urlparse
import psycopg2
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    # request,
    # redirect,
    # url_for,
)

# from validators.url import url

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# conn = psycopg2.connect(DATABASE_URL)

try:
    conn = psycopg2.connect(DATABASE_URL)
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")


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


if __name__ == '__main__':
    app.run(debug=True)  # debug=True  на время отладки
