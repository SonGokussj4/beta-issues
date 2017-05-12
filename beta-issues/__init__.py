from flask import Flask, render_template, flash
from content_management import content

TOPIC_DICT = content()

app = Flask(__name__)
# app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'totalysecretkey'

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
    return render_template('login.html')


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
