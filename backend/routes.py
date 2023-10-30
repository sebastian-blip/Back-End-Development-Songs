from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def healt():
    return jsonify(dict(status="OK")), 200


@app.route("/count", methods=["GET"])
def count():
    count = db.songs.count_documents({})
    return jsonify(dict(count=count)), 200


@app.route("/song", methods=["GET"])
def get_songs():
    songs = db.songs.find({})
    songs = list(songs)
    if not songs:
        return json_util.dumps(songs), 404
    songs = {'songs': songs}
    return json_util.dumps(songs), 200

@app.route("/song/<int:id>", methods=["GET"])
def get_songs_by_id(id):
    songs = db.songs.find({'id': id})
    if not songs:
        return json_util.dumps(songs), 404
    return json_util.dumps(songs[0]), 200

@app.route("/song", methods=["POST"])
def create_song():

    song = request.json

    if not song:
        return {"message": "Invalid input parameter"}, 422
    
    existing_song = db.songs.find_one({"id": song["id"]})
    if existing_song:
        return {
            "Message": f"song with id {song['id']} already present"
            }, 302
    try:
        data = db.songs.insert_one(song)
        inserted_id = str(data.inserted_id)
        print(data)
    
    except NameError:
        return {"message": "data not defined"}, 500

    return jsonify({'inserted id':inserted_id}), 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):

    song = request.json

    if not song:
        return {"message": "Invalid input parameter"}, 422

    existing_song = db.songs.find_one({"id": id})
    if existing_song:
        filter = {"id": id}
        update = {"$set": song}
        result = db.songs.update_one(filter, update)
        if result.modified_count > 0:
           updated_document = db.songs.find_one(filter)
           return json_util.dumps(updated_document), 200
        else:
            return {"message":"song found, but nothing updated"}, 200
    
    return {"message": "song not found"}, 404


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):


    filter = {"id": id}
    result = db.song.delete_one(filter)
    if result.deleted_count > 0:
        return {}, 204
    else:
        return {"message": "song not found"}, 404