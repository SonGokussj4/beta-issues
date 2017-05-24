import os
import sys
from flask import Flask, render_template, flash, request, url_for, redirect, session, abort, Markup
from werkzeug.utils import secure_filename
from functools import wraps
from wtforms import Form, TextField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
import datetime
import gc
from .models import Issues, User
from .database import db
from sqlalchemy import func

# User scripts
sys.path.append(os.path.abspath(os.path.join(os.path.curdir, 'static', 'scripts')))
from beta_pdf_miner import get_issues_list

app = Flask(__name__)
app.config.from_object(__name__)  # load config from this file, flaskr.py
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'mydb.db'),
    SCHEMA=os.path.join(app.root_path, 'schema.sql'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'upload'),
    SQLALCHEMY_DATABASE_URI='sqlite:///database.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
))

db.init_app(app)
with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))
    return wrap


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


@app.route('/issue_status/')
def issue_status():
    resolved = Issues.query.filter_by(evektor=True, resolved=True).all()
    unresolved = Issues.query.filter_by(evektor=True, resolved=False).all()
    issues = {'resolved': resolved, 'unresolved': unresolved}
    today = datetime.datetime.today().strftime('%Y-%m-%d')

    return render_template('issue_status.html', today=today, issues=issues)


@app.route('/add_issue/', methods=['GET', 'POST'])
def add_issue():
    if not session.get('logged_in'):
        abort(401)

    issue = request.form.get('issue').strip()
    description = request.form.get('description')
    date_issued = request.form.get('date_issued').strip()
    author = request.form.get('author').strip()
    details = request.form.get('details')

    issue_found = Issues.query.filter_by(issue=issue).all()
    # Issue not in DB, add it
    if len(issue_found) == 0:
        print("DEBUG", "len(issue_found) == 0", "issue_found", issue_found)
        issue_add = Issues(
            issue=issue,
            evektor=True,
            description=description,
            date_issued=date_issued,
            author=author,
            details=details,
        )
        db.session.add(issue_add)
    # Issue found in DB
    else:
        print("DEBUG", "ELSE", "issue_found", issue_found)
        q = Issues.query.filter_by(issue=issue, resolved=True).one_or_none()
        # Issue is already tagged as RESOLVED, update other attributes
        if q:
            msg = Markup("<p><strong>This issue is already resolved!</strong></p>"
                         "<p>Version: {}</p>"
                         "<p>Date resolved: {}</p>".format(q.version, q.date_resolved))
            flash(msg, 'success')
            Issues.query.filter_by(issue=issue).update(dict(
                evektor=True,
                description=description,
                date_issued=date_issued,
                author=author,
                details=details,
            ))
        # Issue is UNRESOLVED, user tries to add existing issue
        else:
            flash("Issue <{}> already exists...".format(issue), 'danger')
            return redirect(url_for('issue_status'))
    db.session.commit()

    flash('New issue was successfully added into database.', 'success')
    return redirect(url_for('issue_status'))


@app.route('/edit_issue/', methods=['GET', 'POST'])
def edit_issue():
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST' and request.form.get('submit') == 'details':
        sys.exit()

    orig_issue = request.form.get('orig_issue')

    res = Issues.query.filter_by(issue=orig_issue).all()
    if len(res) == 0:
        flash("This issue was not found in database... Weird...", 'danger')
        return redirect(url_for('issue_status'))

    Issues.query.filter_by(issue=orig_issue).update(dict(
        issue=request.form.get('issue'),
        description=request.form.get('description'),
        date_issued=request.form.get('date_issued'),
        author=request.form.get('author'),
        details=request.form.get('details'),
    ))

    db.session.commit()
    flash("Issue: [{}] was modified successfully.".format(request.form.get('issue')), 'success')
    return redirect(url_for('issue_status'))


@app.route('/upload_release_changes/')
@login_required
def upload_release_changes():
    data = db.session.query(Issues.version, func.count('issue')).group_by('version').all()
    data = [(version, count) for (version, count) in data if version is not None]  # [('None', 1), ('ANSA v...')]
    versions = sorted(data, reverse=True)  # [('META v17.0.1', '46'), ('ANSA v17.1.0', '86'), ...]
    resolved_db = Issues.query.filter_by(resolved=True).all()  # return all issues with attr resolved = True
    return render_template('upload_release_changes.html', resolved_db=resolved_db, versions=versions)


@app.route('/upload_release_changes/', methods=['GET', 'POST'])
def upload_changes():
    file_list = request.files.getlist('UploadFiles')

    if file_list[0].filename == '':
        flash('No file(s) selected', 'warning')
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
            flash("Can't recognize this file: {}. I has to have ANSA or META in it's name...".format(
                filename), 'danger')
            return redirect(request.url)
        os.remove(filepath)

    # Iterate over found issues in PDF
    count = 0
    for issue_tuple in issues:
        issue, version = issue_tuple

        issue_in_db = Issues.query.filter_by(issue=issue).all()
        # Not in DB: add name, version, date resolved, resolved
        if len(issue_in_db) == 0:
            # flash("ADDING Issue: [{}]".format(issue))
            issue_add = Issues(
                issue=issue,
                version=version,
                date_resolved=datetime.datetime.today().strftime('%Y-%m-%d'),
                resolved=True,
            )
            db.session.add(issue_add)
            count += 1
        # In DB
        else:
            issue_resolved = Issues.query.filter_by(issue=issue, resolved=True).all()
            # Already uploaded from PDF, not unresolved issue, ignore
            if len(issue_resolved) == 1:
                pass
            # Not uploaded from PDF, update version, date resolved, resolved to True
            else:
                q = Issues.query.filter_by(issue=issue)
                subq = q.with_entities(Issues.issue, Issues.description).one()
                issue_num, description = subq
                msg = Markup("<p><strong>Our issue resolved!</strong></p>"
                             "<p>Issue: {}</p>"
                             "<p>Description: {}</p>".format(issue_num, description))
                flash(msg, 'success')
                Issues.query.filter_by(issue=issue).update(dict(
                    version=version,
                    date_resolved=datetime.datetime.today().strftime('%Y-%m-%d'),
                    resolved=True,
                ))
                count += 1
    db.session.commit()

    msg = Markup("<p>{} resolved issues found in selected document(s).</p>"
                 "<p><strong>{}</strong> new issues added to database.</p>".format(len(issues), count))
    flash(msg, 'success')
    return redirect(url_for('upload_release_changes'))


@app.route('/login/', methods=['GET', 'POST'])  # /?variable=this (post)
def login():
    error = None
    try:
        if request.method == 'POST':
            form_username = request.form.get('username')
            form_password = request.form.get('password')

            q = User.query.filter_by(username=form_username).one_or_none()

            if q and sha256_crypt.verify(form_password, q.password):
                session['logged_in'] = True
                session['username'] = q.username
                flash("Your are now logged in", 'success')
                return redirect(url_for('issue_status'))
            else:
                error = "Invalid credentials, try again."

        return render_template('login.html', error=error)

    except Exception as e:
        error = "Invalid credentials, try again."
        flash(e)
        return render_template('login.html', error=error)


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm', message="Passwords must match.")])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and the Privacy notice.',
                              [validators.Required()])


@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))
            flash("{}, {}, {}".format(username, email, password))
            # q = User.query.filter_by(username=username).all()
            # if len(q) != 0:
            #     flash("That username is already taken, please choose another", 'danger')
            #     return render_template('register.html', form=form)

            # user_add = User(username=username, password=password, email=email)
            # db.session.add(user_add)
            # db.session.commit()

            # flash("Thanks for registering.", 'success')

            # session['logged_in'] = True
            # session['username'] = username

            # return redirect(url_for('issue_status'))

        return render_template('register.html', form=form)

    except Exception as e:
        return("Erra: {}".format(e))


@app.route('/logout/')
@login_required
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.", "info")
    gc.collect()
    return redirect(url_for('issue_status'))


@app.route('/issue_status/', methods=['GET', 'POST'])
def issue_modify():
    issue = request.form.get('remove_issue')
    q = Issues.query.filter_by(issue=issue).one()
    if q.resolved:
        Issues.query.filter_by(issue=issue).update(dict(
            evektor=False,
            description=None,
            details=None,
            author=None,
            date_issued=None,
        ))
    else:
        db.session.delete(q)
    db.session.commit()
    flash("Issue: [{}] deleted.".format(q.issue), 'danger')
    return redirect(url_for('issue_status'))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
