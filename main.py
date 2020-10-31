from flask import Flask, request, make_response
import json
import uuid
import sys
import csv
import os.path
import io
import threading
import copy
from decouple import config

app = Flask(__name__)
db_dir: os.path = config("DB_PATH", default="/home/appuser/db")
active_task = {}


def get_collection(task_id) -> os.path:
    return os.path.join(db_dir, str(task_id) + ".json")


@app.route("/status/<task_id>")
def status(task_id) -> str:
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
        col_num = max(col_num, len(row))
    return {"row_num": row_num, "col_num": col_num}


def is_float(value) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def do_work2(uploaded_file, work1_result):
    missing_line = []
    row_type = []
    row_count = 0
    for row in uploaded_file:
        if len(row) != work1_result["col_num"]:
            missing_line.append(row_count)
        elif row_count > 0 and len(row_type) == 0:
            for value in row:
                if value.isnumeric():
                    row_type.append("int")
                elif is_float(value):
                    row_type.append("float")
                else:
                    row_type.append("string")
        row_count += 1

    return {"missing value in line": missing_line, "type": row_type}


def do_work3(uploaded_file, work2_result):
    result = copy.deepcopy(work2_result["type"])
    for (i, t) in enumerate(work2_result["type"]):
        if t == "string":
            result[i] = 0
        else:
            result[i] = {
                "mean": 0,
                "min": float(sys.float_info.max),
                "max": float(sys.float_info.min)
            }

    rowcount = 0
    for row in uploaded_file:
        for (colnum, value) in enumerate(row):
            if rowcount > 0:
                if work2_result["type"][colnum] == "string":
                    result[colnum] += len(value.split())
                else:
                    result[colnum]["mean"] = float(result[colnum]["mean"]) + float(value)
                    result[colnum]["min"] = min(float(value), float(result[colnum]["min"]))
                    result[colnum]["max"] = max(float(value), float(result[colnum]["max"]))
        rowcount += 1

    if rowcount > 0:
        for (i, t) in enumerate(work2_result["type"]):
            if t != "string":
                result[i]["mean"] = result[i]["mean"] / (rowcount - 1)
    return result


def get_unique_id() -> str:
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
        stream.seek(0)
        strStream = io.TextIOWrapper(stream, encoding='utf-8')
        csv_input = csv.reader(strStream, delimiter=',')

        with open(task_file, 'w') as f:
            work1_result = do_work1(csv_input)
            value["do_work1"] = work1_result
            json.dump(value, f)

            strStream.seek(0)
            work2_result = do_work2(csv_input, work1_result)
            value["do_work2"] = work2_result
            f.seek(0)
            json.dump(value, f)

            strStream.seek(0)
            work3_result = do_work3(csv_input, work2_result)
            value["do_work3"] = work3_result
            f.seek(0)
            json.dump(value, f)

            strStream.seek(0)
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
