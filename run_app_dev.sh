#source tacticus/bin/activate
source env/bin/activate
export FLASK_APP=beta-issues/__init__.py
export FLASK_DEBUG=1
flask run --host=localhost --port=5000

