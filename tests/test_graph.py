# -*- coding: utf-8 -*-
import unittest

from peewee_extension.migration.graph import DbNode
from tests.models import model_for_test_graph_1, model_for_test_graph_2


class GraphTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_diff(self):
        diff_graph = model_for_test_graph_1.db_1.get_diff(model_for_test_graph_2.db_2)
        self.assertIsInstance(diff_graph, DbNode)
        self.assertEqual(len(diff_graph.tables.keys()), 3)

        self.assertEqual('table_1' in diff_graph.tables.keys(), True)
        self.assertEqual('table_to_drop' in diff_graph.tables.keys(), True)
        self.assertEqual('table_to_add' in diff_graph.tables.keys(), True)
        self.assertEqual('table_static' in diff_graph.tables.keys(), False)

        self.assertEqual(diff_graph.tables['table_1'].mode, 3)
        self.assertEqual(diff_graph.tables['table_to_drop'].mode, 2)
        self.assertEqual(diff_graph.tables['table_to_add'].mode, 1)

        self.assertEqual(len(diff_graph.tables['table_1'].columns.keys()), 4)

        self.assertEqual('column_to_modify' in diff_graph.tables['table_1'].columns.keys(), True)
        self.assertEqual('column_to_add' in diff_graph.tables['table_1'].columns.keys(), True)
        self.assertEqual('column_renamed' in diff_graph.tables['table_1'].columns.keys(), True)
        self.assertEqual('column_to_delete' in diff_graph.tables['table_1'].columns.keys(), True)
        self.assertEqual('column_static' in diff_graph.tables['table_1'].columns.keys(), False)

        self.assertEqual(diff_graph.tables['table_1'].columns['column_to_modify'].mode, 3)
        self.assertEqual(diff_graph.tables['table_1'].columns['column_to_add'].mode, 1)
        self.assertEqual(diff_graph.tables['table_1'].columns['column_to_delete'].mode, 2)
        self.assertEqual(diff_graph.tables['table_1'].columns['column_renamed'].mode, 4)

        self.assertEqual(
            diff_graph.tables['table_1'].columns['column_to_add'].refl_column.raw_column_type,
            'tinyint',
        )
        self.assertEqual(diff_graph.tables['table_1'].columns['column_renamed'].refl_column, None)
        column_to_modify = diff_graph.tables['table_1'].columns['column_to_modify'].refl_column
        self.assertEqual(column_to_modify.raw_column_type, 'varchar')
        self.assertEqual(column_to_modify.extra_parameters['max_length'], 61)


if __name__ == '__main__':
    unittest.main()
