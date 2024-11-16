import os
import psycopg2
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    # request,
    # redirect,
    # url_for,
)


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


@app.route('/')
def index():
    """Return the main page."""
    return render_template('urls.html')


@app.route('/urls')
def urls():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)  # debug=True  на время отладки
