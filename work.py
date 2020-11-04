import io
import sys
import copy
import csv
import pymongo
import asyncio


async def mongo_dump(result: dict, collection: pymongo.collection.Collection, fn, *args, **kwargs) -> dict:
    if fn.__name__ not in result:
        work_result = await fn(*args, **kwargs)
        result[fn.__name__] = work_result
        collection.insert_one({fn.__name__: work_result})
    else:
        work_result = result[fn.__name__]
    return work_result


async def csv_to_array(input_stream) -> []:
    result = []
    input_stream.seek(0)
    str_stream = io.TextIOWrapper(input_stream, encoding='utf-8')
    csv_input = csv.reader(str_stream, delimiter=',')
    for row in csv_input:
        result.append(row)
    return result


async def process(input_stream, collection: pymongo.collection.Collection, result: dict):
    array_input = await csv_to_array(input_stream)

    collection.insert_one({"finished": False})
    result["finished"] = False

    work1_result = await mongo_dump(result, collection, do_work1, array_input)
    work2_result = await mongo_dump(result, collection, do_work2, array_input, work1_result)
    await mongo_dump(result, collection, do_work3, array_input, work2_result)
    collection.replace_one({"finished": False}, {"finished": True})
    result["finished"] = True


async def do_work1(uploaded_file) -> dict:
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


async def do_work2(uploaded_file: [], work1_result: dict) -> dict:
    missing_line = []
    row_type = []

    for (row_count, row) in enumerate(uploaded_file):
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

    return {"missing value in line": missing_line, "type": row_type}


async def do_work3(uploaded_file: [], work2_result: dict) -> dict:
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
