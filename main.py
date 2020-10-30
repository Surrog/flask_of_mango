import decouple
from flask import Flask, make_response
import pymongo
import subprocess

app = Flask(__name__)
dbClient = None

@app.route("/status/<id>")
def status(id):
    table = dbClient["task"][id]
    if table is None:
        return make_response("page not found", 404)
    return table

@app.before_first_request
def before_first_request():
    global dbClient
    subprocess.run("mongod")
    dbClient = pymongo.MongoClient()
    #setup db

if __name__ == '__main__':
    app.run(debug=True)
    
    
