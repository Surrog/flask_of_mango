import decouple
from flask import Flask, make_response
import pymongo
import subprocess

app = Flask(__name__)
db_client = None
db_task = None

@app.route("/status/<id>")
def status(id):
    report = db_task.fin
    if report is None:
        return make_response("page not found", 404)
    return table

@app.route('/')
def valid():
    return "Service running"

@app.before_first_request
def before_first_request():
    global db_client
    global db_task
    subprocess.run("mongod") # make sure that the service is runnin before creating mongo client
    db_client = pymongo.MongoClient()
    db_task = db_client["task"]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    
