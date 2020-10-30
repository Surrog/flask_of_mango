from flask import Flask, request, make_response
import json
import uuid
import asyncio
import time
import csv
import os.path
import io
import threading

app = Flask(__name__)
db_dir: os.path = "/home/appuser/db/requests"
active_task = {}


@app.route("/status/<task_id>")
def status(task_id):
    task_path = os.path.join(db_dir, task_id + ".json")
    if not os.path.exists(task_path):
        return make_response(json.dumps({"error": "Id not found"}), 404)

    with open(task_path) as f:
        return f.read()


@app.route('/')
def valid():
    return "Service running"


def do_work1(uploaded_file):
    # do stuff with inputs
    time.sleep(1)
    return {"x": 42, "y": 50}


def do_work2(uploaded_file, work1_result):
    # do stuff with inputs
    return {"starwars": "mandalorian", "did some cool stuff": "yes"}


def get_unique_id():
    new_id = uuid.uuid4()
    while os.path.exists(os.path.join(db_dir, str(new_id))):
        new_id = uuid.uuid4()
    return str(new_id)


@app.route("/process_values", methods=['POST'])
def process_values():
    stream = io.BytesIO()
    request.files['input'].save(stream)
    csv_input = csv.reader(stream)

    new_id = get_unique_id()
    task_file = os.path.join(db_dir, new_id + ".json")
    value = {"input": str(stream.getvalue()), "id": new_id}
    with open(os.path.join(task_file), 'x') as f:
        json.dump(value, f)

    def threaded_process():
        with open(task_file, 'w') as f:
            work1_result = do_work1(csv_input)
            value["do_work1"] = work1_result
            json.dump(value, f)
            f.seek(0)

            work2_result = do_work2(csv_input, work1_result)
            value["do_work2"] = work2_result
            json.dump(value, f)
            f.seek(0)

            value["finished"] = True
            json.dump(value, f)
            f.seek(0)

        active_task.pop(new_id)

    active_task[new_id] = threading.Thread(target=threaded_process)
    active_task[new_id].start()
    return new_id


@app.before_first_request
def before_first_request():
    # connect to db to a real db on a real world
    if not os.path.exists(db_dir):
        os.mkdir(db_dir)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
