from flask import Flask, request, make_response
import json
import uuid
import sys
import csv
import os.path
import io
import threading
from decouple import config

app = Flask(__name__)
db_dir: os.path = config("DB_PATH")
active_task = {}


def get_collection(task_id):
    return os.path.join(db_dir, str(task_id) + ".json")


@app.route("/status/<task_id>")
def status(task_id):
    task_path = get_collection(task_id)
    if not os.path.exists(task_path):
        return make_response(json.dumps({"error": "Id not found"}), 404)

    with open(task_path) as f:
        return f.read()


@app.route('/')
def valid():
    return "Service running"


def do_work1(uploaded_file):
    # do stuff with inputs
    row_num = 0
    col_num = 0
    for row in uploaded_file:
        row_num += 1
        col_num = max(col_num, row.count())
    return {"row_num": row_num, "col_num": col_num}


def do_work2(uploaded_file, work1_result):
    missing_line = []
    row_type = []
    row_count = 0
    for row in uploaded_file:
        if row.count() != work1_result["col_num"]:
            missing_line.append(row_count)
        elif row_count > 0:
            for value in row:
                if value.isnumeric() and '.' in value:
                    row_type.append("float")
                elif value.isnumeric():
                    row_type.append("int")
                else:
                    row_type.append("string")
        row_count += 1

    return {"missing value in line": missing_line, "type": row_type}


def do_work3(uploaded_file, work2_result):
    result = work2_result["type"]
    for (i, t) in enumerate(work2_result["type"]):
        if t == "string":
            result[i] = 0
        else:
            result[i] = {"mean": 0, "median": 0, "min": sys.float_info.max, "max": sys.float_info.min}

    rowcount = 0
    for row in uploaded_file:
        colnum = 0
        rowcount += 1
        for value in row:
            if work2_result["type"][colnum] == "string":
                result[colnum] += len(value.split())
            else:
                result[colnum]["mean"] += value
                result[colnum]["min"] = min(value, result[colnum]["min"])
                result[colnum]["max"] = max(value, result[colnum]["max"])
            colnum += 1

    for (i, t) in enumerate(work2_result["type"]):
        if t != "string":
            result[i]["mean"] = result[i]["mean"] / rowcount


def get_unique_id():
    new_id = uuid.uuid4()
    while os.path.exists(get_collection(new_id)):
        new_id = uuid.uuid4()
    return str(new_id)


@app.route("/process_values", methods=['POST'])
def process_values():
    stream = io.BytesIO()
    request.files['input'].save(stream)

    new_id = get_unique_id()
    task_file = get_collection(new_id)
    value = {"input": str(stream.getvalue()), "id": new_id}
    with open(task_file, 'x') as f:
        json.dump(value, f)

    def threaded_process():
        csv_input = csv.reader(stream, delimiter=',')

        with open(task_file, 'w') as f:
            work1_result = do_work1(csv_input)
            value["do_work1"] = work1_result
            json.dump(value, f)

            work2_result = do_work2(csv_input, work1_result)
            value["do_work2"] = work2_result
            f.seek(0)
            json.dump(value, f)

            work3_result = do_work3(csv_input, work2_result)
            value["do_work3"] = work3_result
            f.seek(0)
            json.dump(value, f)

            value["finished"] = True
            f.seek(0)
            json.dump(value, f)

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
