# -*- coding: utf-8 -*-
import unittest

from peewee_extension.migration.from_py import get_graph
from peewee_extension.migration.graph import ColumnNode, DbNode, TableNode
from playhouse.reflection import (
    AutoField, BigIntegerField, BlobField, CharField, DateField,
    DateTimeField, DecimalField, DoubleField,
    FixedCharField, FloatField, IntegerField, SmallIntegerField,
    TextField, TimeField,
)


class FromPyTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_graph(self):
        res = get_graph(module_name='tests.models.first')
        tables = ['table1', 'table2']
        columns1 = [
            'date_time_field', 'char_field', 'big_integer_field', 'blob_field', 'date_field',
            'decimal_field', 'double_field', 'fixed_char_field', 'float_field', 'integer_field',
            'small_integer_field', 'text_field', 'time_field', 'id',
        ]
        columns2 = ['date_time_field', 'id']

        self.assertIsInstance(res, DbNode)

        self.assertEqual(len(res.tables), 2)

        for tab in tables:
            self.assertIsInstance(res.tables[tab], TableNode)

        table1 = res.tables['table1']
        self.assertEqual(len(table1.columns), len(columns1))
        table2 = res.tables['table2']
        self.assertEqual(len(table2.columns), len(columns2))

        for col in columns1:
            self.assertIsInstance(table1.columns[col], ColumnNode)
        for col in columns2:
            self.assertIsInstance(table2.columns[col], ColumnNode)

        self.assertEqual(
            table1.columns['date_time_field'].refl_column.field_class, DateTimeField,
        )
        self.assertEqual(
            table1.columns['char_field'].refl_column.field_class, CharField,
        )
        self.assertEqual(
            table1.columns['big_integer_field'].refl_column.field_class, BigIntegerField,
        )
        self.assertEqual(
            table1.columns['blob_field'].refl_column.field_class, BlobField,
        )
        self.assertEqual(table1.columns['date_field'].refl_column.field_class, DateField)
        self.assertEqual(table1.columns['decimal_field'].refl_column.field_class, DecimalField)
        self.assertEqual(table1.columns['double_field'].refl_column.field_class, DoubleField)
        self.assertEqual(table1.columns['fixed_char_field'].refl_column.field_class, FixedCharField)
        self.assertEqual(table1.columns['float_field'].refl_column.field_class, FloatField)
        self.assertEqual(table1.columns['integer_field'].refl_column.field_class, IntegerField)
        self.assertEqual(
            table1.columns['small_integer_field'].refl_column.field_class, SmallIntegerField,
        )
        self.assertEqual(table1.columns['text_field'].refl_column.field_class, TextField)
        self.assertEqual(table1.columns['time_field'].refl_column.field_class, TimeField)
        self.assertEqual(table1.columns['id'].refl_column.field_class, AutoField)

        self.assertEqual(table2.columns['date_time_field'].refl_column.field_class, DateTimeField)
        self.assertEqual(table2.columns['id'].refl_column.field_class, AutoField)

        self.assertEqual(table1.columns['date_time_field'].refl_column.nullable, True)
        self.assertEqual(table1.columns['char_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['big_integer_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['blob_field'].refl_column.nullable, True)
        self.assertEqual(table1.columns['date_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['decimal_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['double_field'].refl_column.nullable, True)
        self.assertEqual(table1.columns['fixed_char_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['float_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['integer_field'].refl_column.nullable, True)
        self.assertEqual(table1.columns['small_integer_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['text_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['time_field'].refl_column.nullable, False)
        self.assertEqual(table1.columns['id'].refl_column.nullable, False)

        self.assertEqual(table2.columns['date_time_field'].refl_column.nullable, False)
        self.assertEqual(table2.columns['id'].refl_column.nullable, False)

        self.assertEqual(
            table1.columns['char_field'].refl_column.extra_parameters['max_length'], 63,
        )
        self.assertEqual(
            table1.columns['fixed_char_field'].refl_column.extra_parameters['max_length'], 2,
        )


if __name__ == '__main__':
    unittest.main()
