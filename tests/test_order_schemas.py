import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal

import pyarrow as pa
import pyarrow.parquet as pq

from common import RunTimeContext
from schema import OpenCartSchema
from stages.join.join_tables import JoinTablesStage
from stages.normalize.normalize_values import NormalizeValuesStage
from stages.normalize.rules import get_callback


class OrderSchemasTests(unittest.TestCase):
    def setUp(self):
        self.schema = OpenCartSchema(single_language=True)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.context = RunTimeContext(work_dir=self.temp_dir.name)

    def normalize(self, table_name, rows):
        from stages.extract.extract import ExtractTableStage

        artifact = ExtractTableStage(self.schema, self.context).create_artifact(table_name)
        arrow_schema = self.schema.get_pyarrow_schema(table_name)
        data = [tuple(row[name] for name in arrow_schema.names) for row in rows]
        artifact.save(iter([data]), arrow_schema.names)
        return NormalizeValuesStage(self.schema, self.context).run({table_name: artifact})[table_name]

    def test_single_language_does_not_change_other_schema_instances(self):
        self.assertNotIn('language_id', self.schema['oc_order_status'].names)
        self.assertIn('language_id', OpenCartSchema()['oc_order_status'].names)
        self.assertNotIn('oc_currency', self.schema.oc_tables)
        for table_name in self.schema.oc_tables:
            if table_name.startswith('oc_order'):
                self.assertNotIn('language_id', self.schema[table_name].names)
                self.assertFalse(any(name.startswith('currency_') for name in self.schema[table_name].names))

    def test_join_keeps_orders_without_simple_fields_and_maps_primary_key(self):
        order_schema = self.schema.get_pyarrow_schema('oc_order')
        first_order = {
            field.name: '' if pa.types.is_string(field.type) else 0
            for field in order_schema
        }
        first_order.update(order_id=101, firstname='Иван')
        second_order = dict(first_order, order_id=102)
        orders = self.normalize('oc_order', [first_order, second_order])
        simple_fields = self.normalize('oc_order_simple_fields', [{
            'order_id': 101,
            'metadata': '{"entrance": "2"}',
            'patronymic': 'Иванович',
            'upload': 'order_uploads/example.pdf',
            'example': None,
            'deliverytime': '10:00–14:00',
            'deliverydate': '2026-11-13',
            'bic': '012345678',
            'settlement_account': '01234567890123456789',
        }])

        result = JoinTablesStage(self.schema, self.context).run({
            'oc_order': orders, 'oc_order_simple_fields': simple_fields,
        })
        self.assertEqual(set(result), {'oc_order'})
        joined = pq.read_table(result['oc_order'].path)
        rows = {row['order_id']: row for row in joined.to_pylist()}
        self.assertEqual(set(rows), {101, 102})
        self.assertEqual(rows[101]['deliverydate'], date(2026, 11, 13))
        self.assertEqual(rows[101]['metadata'], '{"entrance": "2"}')
        self.assertEqual(rows[101]['settlement_account'], '01234567890123456789')
        self.assertIsNone(rows[102]['deliverydate'])
        self.assertIsNone(rows[102]['metadata'])

        columns = self.schema.get_pg_columns(joined.column_names, 'oc_order', 'oc_order_simple_fields')
        self.assertEqual(columns[0], '"id"')
        self.assertEqual(len(columns), len(joined.column_names))
        self.assertEqual(columns.count('"id"'), 1)
        self.assertIn('"patronymic"', columns)

    def test_money_keeps_four_decimal_places(self):
        artifact = self.normalize('oc_order_product', [{
            'order_product_id': 201, 'order_id': 101, 'product_id': 1,
            'name': 'Товар', 'model': 'SKU', 'quantity': 2,
            'price': Decimal('12345678901.1234'),
            'total': Decimal('24691357802.2468'),
            'tax': Decimal('0.0001'), 'reward': 0,
        }])
        row = pq.read_table(artifact.path).to_pylist()[0]
        self.assertEqual(row['price'], Decimal('12345678901.1234'))
        self.assertEqual(row['total'], Decimal('24691357802.2468'))
        self.assertEqual(row['tax'], Decimal('0.0001'))

        artifact = self.normalize('oc_order_total', [{
            'order_total_id': 301, 'order_id': 101, 'code': 'coupon',
            'title': 'Скидка', 'value': Decimal('-10.1234'), 'sort_order': 1,
        }])
        self.assertEqual(pq.read_table(artifact.path)['value'][0].as_py(), Decimal('-10.1234'))

    def test_history_notify_is_boolean(self):
        rows = [{
            'order_history_id': index + 1, 'order_id': 101,
            'order_status_id': 1, 'notify': notify, 'comment': '',
            'date_added': datetime(2026, 11, 13, 10, 0),
        } for index, notify in enumerate((0, 1))]
        artifact = self.normalize('oc_order_history', rows)
        self.assertEqual(pq.read_table(artifact.path)['notify'].to_pylist(), [False, True])

    def test_optional_delivery_date_and_json(self):
        schema = self.schema['oc_order_simple_fields']
        callback = get_callback(self.schema, 'oc_order_simple_fields', schema.names.index('deliverydate'))
        for value in (None, '', '  ', '0000-00-00'):
            with self.subTest(value=value):
                self.assertIsNone(callback(value))
        for value in ('2026-11-13', date(2026, 11, 13), datetime(2026, 11, 13, 10, 0)):
            self.assertEqual(callback(value), date(2026, 11, 13))
        with self.assertRaises(ValueError):
            callback('invalid-date')

        callback = get_callback(self.schema, 'oc_order_simple_fields', schema.names.index('metadata'))
        self.assertIsNone(callback(''))
        self.assertIsNone(callback(None))
        self.assertEqual(callback('{"entrance": "2"}'), '{"entrance": "2"}')


if __name__ == '__main__':
    unittest.main()
