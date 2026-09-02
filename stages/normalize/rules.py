import html as html_lib
import json
from functools import partial
from typing import Callable

from schema import SCHEMAS


def to_html(value):
    return html_lib.unescape(value)


def zero_to_none(value):
    if value == 0:
        return None
    return value


def normalize_date(value):
    if value == "0000-00-00" or value == "0000-00-00 00:00:00":
        return None
    return value


def value_to_none(value, gauge):
    if value == gauge:
        return None
    return value


def int_to_bool(value):
    return bool(value)


TRANSFORM_REGISTRY = {
    "to_html": to_html,
    "zero_to_none": zero_to_none,
    "normalize_date": normalize_date,
    "value_to_none": value_to_none,
    "int_to_bool": int_to_bool,
}


def get_callback(oc_table_name: str, col_num: int) -> Callable:
    field = SCHEMAS[oc_table_name][col_num]
    meta = field.metadata

    if meta and b"callback" in meta:
        callback_name = meta[b"callback"].decode()
        normalize_func = TRANSFORM_REGISTRY[callback_name]
        raw_args = meta.get(b"args", b"{}").decode("utf-8")
        kwargs = json.loads(raw_args)

        return partial(normalize_func, **kwargs)
