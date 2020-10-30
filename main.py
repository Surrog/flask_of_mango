from flask import Flask, request
import pymongo
import subprocess
import uuid
import asyncio
import time

app = Flask(__name__)
mongoC: pymongo.MongoClient
request_db: pymongo.collection
active_task = {}


@app.route("/status/<task_id>")
def status(task_id):
    print(task_id)
    print(request_db)

    collection = request_db.get_collection(str(task_id))
    print(collection)
    cursor = collection.find({})
    print(cursor)
    result = []
    for doc in cursor:
        result.append(str(doc))

    return str(result)


@app.route('/')
def valid():
    return "Service running"


async def do_work1(uploaded_file):
    # do stuff with inputs
    time.sleep(1)
    return {"x": 42, "y": 50}


async def do_work2(uploaded_file, work1_result):
    # do stuff with inputs
    return {"starwars": "mandalorian", "did some cool stuff": "yes"}


@app.route("/process_values", methods=['POST'])
def process_values():
    uploaded_file = request.files['file']
    new_id = uuid.uuid4()
    while request_db.get_collection(new_id) is not None:
        new_id = uuid.uuid4()
    collection = request_db.create_collection(new_id)
    collection.insert_many({"finished": False})

    async def process(task_id, task_collection):
        work1_result = await do_work1(uploaded_file)
        task_collection.insert_one({"function": "do_work1", "result": work1_result})
        work2_result = await do_work2(uploaded_file, work1_result)
        task_collection.insert_one({"function": "do_work2", "result": work2_result})
        task_collection.replace_one({"finished": False}, {"finished": True})
        active_task.pop(task_id)

    active_task[str(new_id)] = asyncio.create_task(process(new_id, collection))
    return str(new_id)


@app.before_first_request
def before_first_request():
    global mongoC
    global request_db
    subprocess.run("mongod")  # make sure that the service is running before creating mongo client
    mongoC = pymongo.MongoClient()
    request_db = mongoC["requests"]


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
