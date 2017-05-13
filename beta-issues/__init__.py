import os
from static.scripts.beta_pdf_miner import get_issues_list
from flask import Flask, render_template, flash, request, url_for, redirect, session, g, abort
from werkzeug.utils import secure_filename
from content_management import content
from functools import wraps
from wtforms import Form, TextField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
import gc
import sqlite3

TOPIC_DICT = content()

app = Flask(__name__)
app.config.from_object(__name__)  # load config from this file, flaskr.py
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'mydb.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'upload'),
))


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection of there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))
    return wrap


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route('/dashboard/')
def dashboard():
    db = get_db()
    cur = db.cursor()
    issues = cur.execute("SELECT * FROM issues")
    return render_template('dashboard.html', TOPIC_DICT=TOPIC_DICT, issues=issues)


@app.route('/load_changes/', methods=['POST'])
def load_changes():
    # text = request.form.get('text')
    db = get_db()
    cur = db.cursor()

    ANSAfile = request.files.get('AnsaFile')
    filename = secure_filename(ANSAfile.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    ANSAfile.save(filepath)
    ANSA_issues = get_issues_list(filepath, 'Ansa')
    os.remove(filepath)

    METAfile = request.files.get('MetaFile')
    filename = secure_filename(METAfile.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    METAfile.save(filepath)
    META_issues = get_issues_list(filepath, 'Meta')
    os.remove(filepath)

    issues = ANSA_issues + META_issues

    count = 0
    for issue in issues:
        found = cur.execute("SELECT EXISTS(SELECT 1 FROM resolvedIssues WHERE issue=? LIMIT 1)", [issue]).fetchone()[0]
        if found == 0:  # not in the list for now
            cur.execute("INSERT OR IGNORE INTO resolvedIssues (issue) VALUES (?)", [issue])
            count += 1

    db.commit()

    flash('{} new issues resolved.'.format(count))
    return redirect(url_for('dashboard'))


@app.route('/add_issue/', methods=['POST'])
def add_issue():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM issues WHERE issue = ?", [request.form.get('issue')])
    existing = cur.fetchall()
    if len(existing) > 0:
        flash("This issue already exists...")
        return redirect(url_for('dashboard'))

    cur.execute("INSERT INTO issues (issue, description) VALUES (?, ?)",
        (request.form.get('issue'), request.form.get('description')))
    db.commit()

    flash('New issue was successfully posted')
    return redirect(url_for('dashboard'))


@app.route('/login/', methods=['GET', 'POST'])  # /?variable=this (post)
def login():
    error = None
    try:
        db = get_db()
        cur = db.cursor()
        if request.method == 'POST':
            cur.execute("SELECT * FROM users WHERE username = ?",
                (request.form.get('username'), ))

            data = cur.fetchone()
            username, password = data[1], data[2]

            if sha256_crypt.verify(request.form.get('password'), password):
                session['logged_in'] = True
                session['username'] = username

                flash("Your are now logged in")
                return redirect(url_for('dashboard'))

            else:
                error = "Invalid credentials, try again."

        gc.collect()

        return render_template('login.html', error=error)

    except Exception as error:
        error = "Invalid credentials, try again."
        return render_template('login.html', error=error)


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm', message="Passwords must match.")])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and the Privacy notice.',
        [validators.Required()])



@app.route('/register/', methods=['GET', 'POST'])  # /?variable=this (post)
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))
            db = get_db()
            cur = db.execute("""SELECT * FROM users WHERE username = "{}" """.format(username))
            found_users = cur.fetchall()
            if len(found_users) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)
            else:
                db.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (username, password, email))
                db.commit()
                flash("Thanks for registering.")
                gc.collect()  # garbage collection, clear unused cache memory, important

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('dashboard'))

        return render_template('register.html', form=form)

    except Exception as e:
        return("Erra: {}".format(e))


@app.route('/logout/')
@login_required
def logout():
    session.pop('logged_in', None)
    # session.clear()
    flash("You have been logged out.")
    gc.collect()
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
