from flask import Flask, request, make_response
import json
import uuid
import csv
import io
import concurrent.futures
from decouple import config
import pymongo
import work
import asyncio

app = Flask(__name__)
mongo_host: str = config("DB_HOST", default="")
thread_pool = concurrent.futures.ThreadPoolExecutor(int(config("EXECUTOR_THREAD", 5)))
pymongoC: pymongo.MongoClient
request_db: pymongo.mongo_client.database.Database
active_task = {}


def get_collection(task_id: str) -> pymongo.collection.Collection:
    return request_db[task_id]


def collection_exist(task_id: str) -> bool:
    return request_db[task_id].estimated_document_count() > 0


def build_result_from_collection(collection: pymongo.collection.Collection) -> dict:
    result = {}
    for entry in collection.find():
        for (key, val) in entry.items():
            result[key] = val
    if "_id" in result:
        del result["_id"]
    return result


def dump_collection(task_id: str) -> str:
    return json.dumps(build_result_from_collection(request_db[task_id]))


@app.route("/status/<task_id>")
def status(task_id: str) -> str:
    if not collection_exist(task_id):
        return make_response(json.dumps({"error": "Id not found"}), 404)
    return dump_collection(task_id)


@app.route('/')
def valid() -> str:
    return "Service running"


def get_unique_id() -> str:
    new_id = str(uuid.uuid4())
    while collection_exist(new_id):
        new_id = str(uuid.uuid4())
    return new_id


@app.route("/process_values", methods=['POST'])
def process_values() -> str:
    stream = io.BytesIO()
    request.files['input'].save(stream)

    new_id: str = get_unique_id()
    task = get_collection(new_id)
    task.insert_many([{"input": str(stream.getvalue())}, {"id": new_id}])
    result = {"input": str(stream.getvalue()), "id": new_id}

    def threaded_process():
        asyncio.run(work.process(stream, task, result), debug=True)
        print("async done")
        active_task.pop(result["id"])

    active_task[new_id] = thread_pool.submit(threaded_process)
    return new_id


def restart_unfinished_process():
    for entry in request_db.list_collection_names():
        collection = request_db[str(entry)]
        result = build_result_from_collection(collection)
        if "input" not in result or "id" not in result:
            request_db.drop_collection(collection)
            continue
        if ("finished" not in result or result["finished"] is False) and result["id"] not in active_task:
            def threaded_process():
                input_stream = io.StringIO(result["input"])
                asyncio.run(work.process(input_stream, entry, result))
                active_task.pop(result["id"])

            active_task[result["id"]] = thread_pool.submit(threaded_process)


@app.before_first_request
def before_first_request():
    global request_db
    global pymongoC
    pymongoC = pymongo.MongoClient(host=mongo_host)
    request_db = pymongoC["request"]
    restart_unfinished_process()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
