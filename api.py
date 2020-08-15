from bottle import route, run, response, Bottle
import json
from pymongo import MongoClient

client = MongoClient()
db = client['Discord']

app = Bottle()

@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

@app.route('/list')
def clist():
    challenge_list = list(db.levels.find({'placement': {'$lte': 50}}))
    for lvl in challenge_list:
        lvl['_id'] = str(lvl['_id'])
    challenge_list = sorted(challenge_list, key=lambda i: i['placement'])
    response.content_type = 'application/json'
    return json.dumps(challenge_list)

@app.route('/legacy')
def llist():
    legacy_list = list(db.levels.find({'placement': {'$gt': 50}}))
    for lvl in legacy_list:
        lvl['_id'] = str(lvl['_id'])
    legacy_list = sorted(legacy_list, key=lambda i: i['placement'])
    response.content_type = 'application/json'
    return json.dumps(legacy_list)

@app.route('/level/<placement>')
def level(placement):
    try:
        pl = int(placement)
    except:
        return json.dumps({'error': 'dumbfuck'})
    level = db.levels.find_one({'placement': pl})
    records = list(db.records.find({'challenge': level['name']}))
    level['victors'] = [record for record in records if record['player'] != level['verifier']]
    return json.dumps(level)

app.run(host='0.0.0.0', port=443, debug=True, server='gunicorn', keyfile='key.pem', certfile='cert.pem')
