from bottle import route, run, response
import json
from pymongo import MongoClient

client = MongoClient()
db = client['Discord']

@route('/list')
async def clist():
    challenge_list = list(db.levels.find({'placement': {'$lte': 50}}))
    response.content_type = 'application/json'
    return json.dumps(challenge_list)

@route('/legacy')
async def llist():
    legacy_list = list(db.levels.find({'placement': {'$gt': 50}}))
    response.content_type = 'application/json'
    return json.dumps(legacy_list)

run(host='0.0.0.0', port=80, debug=True)
