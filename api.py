from quart import Quart
import json
from motor import motor_asyncio
client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

app = Quart(__name__)

@app.route('/list')
async def clist():
    #challenge_list = await db.levels.find({'placement': {'$lte': 50}}).to_list(length=50)
    return {}

@app.route('/legacy')
async def llist():
    #legacy_list = await db.levels.find({'placement': {'$gt': 50}}).to_list(length=50)
    return {}

app.run(debug=True, port=80)
