from flask import Flask, request, make_response
import json
import uuid
import csv
import io
import concurrent.futures
from decouple import config
import pymongo
import work

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


def mongo_dump(result: dict, collection: pymongo.collection.Collection, fn, *args, **kwargs):
    if fn.__name__ not in result:
        work_result = fn(*args, **kwargs)
        result[fn.__name__] = work_result
        print(result)
        collection.insert_one({fn.__name__: work_result})
    else:
        work_result = result[fn.__name__]
    return work_result


def csv_to_array(input_stream) -> []:
    result = []
    input_stream.seek(0)
    str_stream = io.TextIOWrapper(input_stream, encoding='utf-8')
    csv_input = csv.reader(str_stream, delimiter=',')
    for row in csv_input:
        result.append(row)
    return result


def process(input_stream, collection: pymongo.collection.Collection, result: dict):
    array_input = csv_to_array(input_stream)

    collection.insert_one({"finished": False})
    result["finished"] = False

    work1_result = mongo_dump(result, collection, work.do_work1, array_input)
    work2_result = mongo_dump(result, collection, work.do_work2, array_input, work1_result)
    mongo_dump(result, collection, work.do_work3, array_input, work2_result)
    collection.replace_one({"finished": False}, {"finished": True})
    result["finished"] = True

    active_task.pop(result["id"])


@app.route("/process_values", methods=['POST'])
def process_values():
    stream = io.BytesIO()
    request.files['input'].save(stream)

    new_id: str = get_unique_id()
    task = get_collection(new_id)
    task.insert_many([{"input": str(stream.getvalue())}, {"id": new_id}])
    result = {"input": str(stream.getvalue()), "id": new_id}

    def threaded_process():
        process(stream, task, result)

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
                process(input_stream, entry, result)

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
