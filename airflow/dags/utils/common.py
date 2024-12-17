import concurrent.futures
import re
import multiprocessing
from time import time
from random import randint, seed
from dateutil import parser


def get_chunks(arr, chunk_size):
    if chunk_size <= 0:
        raise ValueError("Invalid chunk size")

    result = []
    length = len(arr)

    for i in range(0, length, chunk_size):
        result.append(arr[i : i + chunk_size])

    return result


def execute_multithreading_functions(functions, timeout=300):
    try:
        results = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for function in functions:
                results.append(executor.submit(function["fn"], **function["args"]))

        return [result.result(timeout=timeout) for result in results]

    except TimeoutError:
        raise Exception("Function execution timed out")
    except Exception as e:
        raise Exception(f"Error executing multithreading functions: {e}")


def execute_multiprocessing_functions(functions):
    try:
        max_threads = 30
        with multiprocessing.Pool(processes=max_threads) as pool:
            results = [
                pool.apply_async(func=function["fn"], kwds=function["args"])
                for function in functions
            ]
            return [result.get() for result in results]
    except Exception as e:
        raise Exception(f"Error executing multiprocessing functions: {e}")


def camel_to_snake(camel_case):
    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", camel_case).lower()
    return snake_case


def normalize_timestamp_by_interval(timestamp, interval):
    return (timestamp // interval) * interval


def snake_to_camel(snake_case):
    words = snake_case.split("_")
    camel_case = words[0].lower() + "".join(word.title() for word in words[1:])
    return camel_case


def random(min, max, repetition=0):
    seed(time() + repetition)
    return randint(min, max)


def check_list_include_string(check_string, list_string):
    check_string_lower = check_string.lower()
    list_string_lower = [s.lower() for s in list_string]

    return any(string in check_string_lower for string in list_string_lower)


def convert_datetime_to_timestamp(time_str):
    dt = parser.parse(time_str)
    timestamp = int(dt.timestamp())
    return timestamp
