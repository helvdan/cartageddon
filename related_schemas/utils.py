import json
from typing import Dict

import pyarrow as pa


def pk_field(name: str) -> pa.Field:
    return pa.field(name, pa.int32(), metadata={"primary_key": "True"})


def create_meta(callback_name: str, default_meta: Dict[str, str] = None, **kwargs) -> dict:
    meta = {
        "nullable": "True",
        "callback": callback_name,
        "args": json.dumps(kwargs)  # Превращаем словарь в плоскую строку '{"gauge": "0000-00-00"}'
    }
    if default_meta:
        meta.update(default_meta)

    return meta
