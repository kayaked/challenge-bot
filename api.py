from bottle import route, run, response, Bottle
import json
from pymongo import MongoClient

client = MongoClient()
db = client['Discord']

app = Bottle()

@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'

@app.route('/list')
def clist():
    challenge_list = list(db.levels.find({'placement': {'$lte': 50}}))
    for lvl in challenge_list:
        lvl['_id'] = str(lvl['_id'])
    response.content_type = 'application/json'
    return json.dumps(challenge_list)

@app.route('/legacy')
def llist():
    legacy_list = list(db.levels.find({'placement': {'$gt': 50}}))
    for lvl in legacy_list:
        lvl['_id'] = str(lvl['_id'])
    response.content_type = 'application/json'
    return json.dumps(legacy_list)

app.run(host='0.0.0.0', port=443, debug=True, server='gunicorn', keyfile='key.pem', certfile='cert.pem')
