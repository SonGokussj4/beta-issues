import os
from flask import Flask, render_template, flash, request, url_for, redirect
from content_management import content

from dbconnect import connection

TOPIC_DICT = content()

app = Flask(__name__)
app.config.from_object(__name__)  # load config from this file, flaskr.py
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'mydb.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route('/dashboard/')
def dashboard():
    # flash("Welcome to dashboard")
    return render_template('dashboard.html', TOPIC_DICT=TOPIC_DICT)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e)


@app.route('/login/', methods=['GET', 'POST'])  # /?variable=this (post)
def login():
    error = None
    try:
        if request.method == 'POST':
            attempted_username = request.form.get('username')
            attempted_password = request.form.get('password')

            flash(attempted_username)
            flash(attempted_password)

            if attempted_username == 'admin' and attempted_password == 'password':
                flash("CORRECT LOGIN")
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid credentials. Try Again."

        return render_template('login.html', error=error)

    except Exception as error:
        flash(error)  # TODO: remove, debugging purposes
        return render_template('login.html', error=error)


@app.route('/register/', methods=['GET', 'POST'])  # /?variable=this (post)
def register_page():
    try:
        c, conn = connection()
        return("Okay")
    except Exception as e:
        return(str(e))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
