
import sys
import copy


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