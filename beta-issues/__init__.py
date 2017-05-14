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


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))
    return wrap


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db(cursor=False):
    """Opens a new database connection of there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    if cursor:
        c = g.sqlite_db.cursor()
        return c, g.sqlite_db
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e)


@app.route('/')
@app.route('/index/')
def homepage():
    return render_template('main.html')


@app.route('/help/')
def help_page():
    return render_template('help.html')


@app.route('/dashboard/')
def dashboard():
    db = get_db()
    cur = db.cursor()
    issues = cur.execute("SELECT * FROM issues").fetchall()
    resolved, unresolved = [], []
    for row in issues:
        idx, issue, description = row
        found = cur.execute("SELECT * FROM resolvedIssues WHERE issue = ?", [issue]).fetchall()
        if len(found) > 0:
            resolved.append(row)
        else:
            unresolved.append(row)
    return render_template('dashboard.html', TOPIC_DICT=TOPIC_DICT, resolved=resolved, unresolved=unresolved)


@app.route('/issue_status/')
def issue_status():
    cur, db = get_db(cursor=True)
    issues = cur.execute("SELECT * FROM issues").fetchall()
    resolved, unresolved = [], []

    for row in issues:
        idx, issue, description = row
        found = cur.execute("SELECT * FROM resolvedIssues WHERE issue = ?", [issue]).fetchall()
        if len(found) > 0:
            resolved.append(row)
        else:
            unresolved.append(row)
    return render_template('issue_status.html', resolved=resolved, unresolved=unresolved)


@app.route('/issue_add_new/')
@login_required
def issue_add_new():
    return render_template('issue_add_new.html')


@app.route('/add_issue/', methods=['GET', 'POST'])
def add_issue():
    if not session.get('logged_in'):
        abort(401)

    cur, db = get_db(cursor=True)
    cur.execute("SELECT * FROM issues WHERE issue = ?", [request.form.get('issue')])

    existing = cur.fetchall()
    if len(existing) > 0:
        flash("This issue already exists...")
        return redirect(url_for('issue_add_new'))

    cur.execute("INSERT INTO issues (issue, description) VALUES (?, ?)",
                (request.form.get('issue'), request.form.get('description')))
    db.commit()

    flash('New issue was successfully posted')
    return redirect(url_for('issue_add_new'))


@app.route('/upload_release_changes/')
@login_required
def upload_release_changes():
    cur, db = get_db(cursor=True)
    data = cur.execute("SELECT * FROM resolvedIssues")
    issues = len(data.fetchall())
    return render_template('upload_release_changes.html', resolved_issues_in_db=issues)


@app.route('/upload_release_changes/', methods=['GET', 'POST'])
def load_changes():
    file_list = request.files.getlist('UploadFiles')

    if file_list[0].filename == '':
        flash('No file(s) selected')
        return redirect(url_for('upload_release_changes'))

    issues = []
    for file in file_list:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config.get('UPLOAD_FOLDER'), filename)
        file.save(filepath)

        if 'ansa' in filename.lower():
            issues.extend(get_issues_list(filepath, 'Ansa'))
        elif 'meta' in filename.lower():
            issues.extend(get_issues_list(filepath, 'Meta'))
        else:
            flash("Can't recognize this file: {}. I has to have ANSA or META in it's name...".format(filename))
            return redirect(request.url)

        os.remove(filepath)

    cur, db = get_db(cursor=True)
    count = 0
    for issue in issues:
        found = cur.execute("SELECT EXISTS(SELECT 1 FROM resolvedIssues WHERE issue = ? LIMIT 1)", [issue]).fetchone()[0]
        if found == 0:  # not in the list for now
            unresolved = cur.execute("SELECT * FROM issues where issue = ?", [issue]).fetchall()
            if len(unresolved) > 0:
                flash("Our issue resolved: {} - {}".format(unresolved[0][1], unresolved[0][2]))
            cur.execute("INSERT OR IGNORE INTO resolvedIssues (issue) VALUES (?)", [issue])
            count += 1
    db.commit()
    gc.collect()

    flash('{} new resolved issues added to database.'.format(count))
    return redirect(url_for('upload_release_changes'))


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
                return redirect(url_for('issue_status'))
            else:
                error = "Invalid credentials, try again."
        gc.collect()
        return render_template('login.html', error=error)

    except Exception as e:
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

                return redirect(url_for('issue_status'))

        return render_template('register.html', form=form)

    except Exception as e:
        return("Erra: {}".format(e))


@app.route('/logout/')
@login_required
def logout():
    session.pop('logged_in', None)
    # session.clear()
    flash("You have been logged out.", "info")
    gc.collect()
    return redirect(url_for('issue_status'))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
