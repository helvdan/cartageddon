import logging

from hooks.base import BasePipelineHook
from schema import SCHEMAS

logger = logging.getLogger("HOOK.SSH")


class SchemaValidationError(Exception):
    pass


class CheckPyarrowSchema(BasePipelineHook):

    def run_before(self, ctx) -> None:
        for oc_table_name, schema in SCHEMAS.items():
            if not schema.metadata:
                raise SchemaValidationError(f"No metadata for table {oc_table_name}")

            if b'pg_name' not in schema.metadata:
                raise SchemaValidationError(f"Missing pg_name in table metadata {oc_table_name}")


if __name__ == '__main__':
    check_schema = CheckPyarrowSchema()
    check_schema.run_before(None)
