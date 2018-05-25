source env/bin/activate
export FLASK_APP=beta-issues/__init__.py
export FLASK_DEBUG=1
nohup flask run --host=ar-lamp --port=5080 &

