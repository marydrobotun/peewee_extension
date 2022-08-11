# -*- coding: utf-8 -*-
from peewee import AutoField, IntegerField
from peewee_extension.core import EnumField
from playhouse.reflection import Column, UnknownField


def get_key(my_dict, wanted_value):
    """function that returns an appropriate key for given value in given dict"""
    for key, value in my_dict.items():
        if wanted_value == value:
            return key


class Node:
    pass


MODE_NONE = 0
MODE_ADD = 1
MODE_DELETE = 2
MODE_MODIFY = 3
MODE_RENAME = 4
MODE_STUB = 5


class PrimaryKeyNode(Node):
    def __init__(self, columns: list, mode=None):
        self.columns = columns
        self.mode = mode

    def are_equal(self, other) -> bool:  # magic method
        """function that takes two values of primary_key and returns True if they are equal
        False otherwise"""
        if self.columns is not None and other.columns is not None:
            self.columns.sort()
            other.columns.sort()
            for i in range(min(len(self.columns), len(other.columns))):
                if self.columns[i] != other.columns[i]:
                    return False
            if len(self.columns) != len(other.columns):
                return False
            return True
        if self.columns is None and other.columns is None:
            return True
        return False

    def get_columns(self) -> list:
        return self.columns


class IndexNode(Node):
    def __init__(self, indexes: list, unique=False, mode=None):
        self.indexes = indexes
        self.unique = unique
        self.mode = mode

    def is_equal(self, other):
        if len(self.indexes) != len(other.indexes):
            return False
        for i in range(len(self.indexes)):
            if self.indexes[i] != other.indexes[i]:
                return False
        if not self.unique == other.unique:
            return False

        return True

    def get_columns(self):
        return self.indexes

    def as_pycode(self, table):
        columns = '('
        for index in self.indexes:
            columns = columns + '\'' + index + '\'' + ', '
        columns = columns[:-1]
        columns = columns + ')'
        if self.mode == MODE_ADD:
            code = f'        migrator.add_index(\'{table}\', {columns}, {self.unique}),\n'
            return code
        if self.mode == MODE_DELETE:
            code = f'        migrator.drop_index(\'{table}\', {columns}, {self.unique}),\n'
            return code

    def as_pycode_reversed(self, table):
        columns = '('
        for index in self.indexes:
            columns = columns + '\'' + index + '\'' + ', '
        columns = columns[:-1]
        columns = columns + ')'
        if self.mode == MODE_ADD:
            code = f'        migrator.drop_index(\'{table}\', {columns}, {self.unique}),\n'
            return code
        if self.mode == MODE_DELETE:
            code = f'        migrator.add_index(\'{table}\', {columns}, {self.unique}),\n'
            return code


class ColumnNode(Node):
    def __init__(self, name: str, refl_column: Column, mode=None, other=None):
        self.name = name
        self.refl_column = refl_column
        self.mode = mode
        self.other = other

    def get_name(self):
        return self.name

    def get_sql_type(self):
        if self.refl_column.field_class == EnumField:
            values = []
            if type(self.refl_column.get_field_parameters()['values']) == str:
                enum_values = self.refl_column.get_field_parameters()['values']
                converted_values_to_list = enum_values[1:-1].split(',')
            else:
                converted_values_to_list = []
                for value in self.refl_column.get_field_parameters()['values']:
                    converted_values_to_list.append('\'' + value + '\'')
            for value in converted_values_to_list:
                values.append(value)
            sql_type = 'ENUM({})'.format(', '.join(values))
            return sql_type
        if self.refl_column.field_class.field_type == 'AUTO':
            return 'INT'
        return self.refl_column.field_class.field_type

    def get_null(self):
        return self.refl_column.nullable

    def get_field_name(self):
        return self.refl_column.field_class.__name__

    def get_field(self):
        return self.refl_column.field_class

    def get_max_length(self):
        self_extra = self.refl_column.extra_parameters
        if self_extra:
            if 'max_length' in self_extra:
                return self_extra['max_length']
        return None

    def get_full_sql_type(self) -> str:
        sql_type = str(self.get_sql_type())

        if self.get_max_length() is not None:
            sql_type = sql_type + '(' + str(self.get_max_length()) + ')'
        if not self.get_null():
            sql_type = sql_type + ' NOT NULL'
        return sql_type

    def is_max_length_equal(self, other) -> bool:
        """function that takes two values of column_node and returns True if their max_length's
        are equal
        False otherwise"""
        self_max = self.get_max_length()
        other_max = other.get_max_length()
        if self_max == other_max:
            return True
        return False

    def is_equal(self, other) -> bool:
        """function that takes two values of column_node and returns True if they are equal
        False otherwise"""
        self_type = self.get_sql_type()
        other_type = other.get_sql_type()
        self_null = self.get_null()
        other_null = other.get_null()
        if self_type != other_type or self_null != other_null:
            return False
        if not self.is_max_length_equal(other):
            return False
        return True

    def get_diff(self, mode: int, other=None):
        curr = ColumnNode(name=None, refl_column=None, mode=mode)
        if mode == MODE_MODIFY:
            if not self.is_equal(other):
                curr.refl_column = other.refl_column
                curr.name = other.name
        if mode in (MODE_DELETE, MODE_ADD):
            curr.name = self.name
            curr.refl_column = self.refl_column
        if mode == MODE_RENAME:
            curr.name = other.name
            curr.other = self.name
        if curr.name is None:
            return None
        return curr

    def as_sql(self, table):
        if self.mode == MODE_NONE:
            return ''  # такого в принципе не может быть но пусть
        if self.mode == MODE_DELETE:
            return f'ALTER TABLE `{table}` DROP COLUMN `{self.name}`;\n'
        if self.mode == MODE_RENAME:
            return f'ALTER TABLE `{table}` RENAME COLUMN `{self.other}` to `{self.name}`;\n'
        sql_type = self.get_full_sql_type()
        if self.mode == MODE_ADD:
            return f'ALTER TABLE `{table}` ADD COLUMN `{self.name}` {sql_type};\n'
        if self.mode == MODE_MODIFY:
            return f'ALTER TABLE `{table}` MODIFY COLUMN `{self.name}` {sql_type};\n'
        return ''

    def as_pycode(self, table) -> str:
        if self.mode == MODE_NONE:
            return ''  # такого в принципе не может быть но пусть
        if self.mode == MODE_DELETE:
            return f'        migrator.drop_column(\"{table}\", \"{self.name}\"),\n'
        if self.mode == MODE_ADD:
            field = self.refl_column.get_field()
            field = field[len(self.name) + 3:]
            return f'        migrator.add_column(\"{table}\", \"{self.name}\", {field}),\n'
        if self.mode == MODE_MODIFY:
            field = self.refl_column.get_field()
            field = field[len(self.name) + 3:]
            return f'        migrator.alter_column_type(\"{table}\", \"{self.name}\", {field}),\n'
        if self.mode == MODE_RENAME:
            return f'        migrator.rename_column(\"{table}\", \"{self.name}\", \"{self.other}\"),\n' # noqa E501
        return ''

    def as_pycode_reversed(self, table) -> str:
        if self.mode == MODE_NONE:
            return ''
        if self.mode == MODE_DELETE:

            field = self.refl_column.get_field()
            field = field[len(self.name) + 3:]
            return f'        migrator.add_column(\"{table}\", \"{self.name}\", {field}),\n'
        if self.mode == MODE_ADD:
            return f'        migrator.drop_column(\"{table}\", \"{self.name}\"),\n'
        if self.mode == MODE_MODIFY:
            field = self.refl_column.get_field()
            field = field[len(self.name) + 3:]
            return f'        migrator.alter_column_type(\"{table}\", \"{self.name}\", {field}),\n'
        if self.mode == MODE_RENAME:
            return f'        migrator.rename_column(\"{table}\", \"{self.other}\", \"{self.name}\"),\n' # noqa E501
        return ''


class TableNode(Node):
    def __init__(
            self, name: str, primary_key=None,
            columns=None, mode=None, model=None, indexes=None, has_foreign_keys=False,
    ):
        self.name = name
        self.columns = columns
        self.mode = mode
        self.model = model
        self.indexes = indexes
        self.primary_key = primary_key
        self.has_foreign_keys = has_foreign_keys

    def get_foreign_key_columns(self):
        columns_foreign_keys = []
        for column_name, column in self.columns.items():
            if column.refl_column.is_foreign_key():
                columns_foreign_keys.append(column_name)
        return columns_foreign_keys

    def get_foreign_key_refl_columns(self):
        columns_foreign_keys = []
        for column_name, column in self.columns.items():
            if column.refl_column.is_foreign_key():
                columns_foreign_keys.append(column.refl_column)
        return columns_foreign_keys

    def get_model(self, ignore_unknown=False, lower_case=False):

        pk_classes = [AutoField, IntegerField]
        if self.model:
            name = self.model
        else:
            name = self.name
        model_description = ''

        if self.mode == MODE_ADD:
            model_description += '#  MODE_ADD\n'
        if self.mode == MODE_DELETE:
            model_description += '#  MODE_DELETE\n'
        model_description += 'class %s(BaseModel):\n' % name
        columns = self.columns.items()
        primary_keys = self.primary_key.columns
        for name, column in columns:
            skip = all([
                name in primary_keys,
                name == 'id',
                len(primary_keys) == 1,
                column.refl_column.field_class in pk_classes]) # noqa S101
            if skip:
                continue
            if column.refl_column.primary_key and len(primary_keys) > 1:
                # If we have a CompositeKey, then we do not want to explicitly
                # mark the columns as being primary keys.
                column.refl_column.primary_key = False

            is_unknown = column.refl_column.field_class is UnknownField
            if is_unknown and ignore_unknown:
                disp = '%s - %s' % (column.name, column.raw_column_type or '?')
                model_description += '    # %s\n' % disp
            else:
                column.default = None  # зануляем что бы не было constraints=[SQL("DEFAULT 35")]
                if lower_case:
                    # иначе пишет column_name='DECIMALS' в кваргах поля
                    column.column_name = column.column_name.lower()
                model_description += '    %s\n' % column.refl_column.get_field()

        model_description += '\n    class Meta:\n'
        model_description += '        table_name = \'%s\'\n' % self.name

        if len(primary_keys) > 1:
            pk_field_names_2 = []
            for key in primary_keys:
                for column_name, column in columns:
                    if column_name == key:
                        pk_field_names_2.append(column.refl_column.name)

        else:
            pk_field_names_2 = False

        if self.indexes:
            index_declarating = '        indexes = ('
            multi_column_indexes = False
            for index in self.indexes:
                if len(index.indexes) > 1:
                    multi_column_indexes = True
                    # print(fields, pk_field_names_2)
                    index_declarating += '((%s), %s),\n        ' % (
                        ', '.join("'%s'" % field for field in index.indexes),
                        index.unique,
                    )
                # print(pk_field_names, fields)
            index_declarating += '        )\n'
            if multi_column_indexes:
                model_description += index_declarating

        if len(primary_keys) > 1:
            pk_field_names = sorted(
                field.name for col, field in columns # noqa S101
                if col in primary_keys
            )
            pk_field_names.reverse()
            pk_list = ', '.join("'%s'" % pk for pk in pk_field_names)

            model_description += '        primary_key = CompositeKey(%s)\n' % pk_list
        elif not primary_keys:
            model_description += '        primary_key = False\n'
        model_description += '\n\n'
        return model_description

    def get_columns(self):
        pass

    def as_sql(self):
        if self.mode == MODE_DELETE:
            return f'DROP TABLE `{self.name}`;\n'

        if self.mode == MODE_ADD:
            query = 'CREATE TABLE `' + str(self.name) + '` (\n'
            column_names = []
            for column in self.columns.values():
                column_def = '`' + column.get_name() + '` ' + str(column.get_full_sql_type())
                column_names.append(column_def)
            query = query + ',\n'.join(column_names)
            query = query + ');\n'
            return query
        code = ''
        for column in self.columns.values():
            code = code + column.as_sql(self.name)
        return code

    def get_fields_names(self) -> list:
        """method for a diff_graph to get all the field's types that
        need to be added or modified this method is useful for
        script generating because it is needed to import all of this
        field types from peewee to make an appropriate migration"""
        fields = []
        for column in self.columns.values():
            fields.append(column.get_field_name())

        if (self.mode in [MODE_ADD, MODE_DELETE]) and len(self.primary_key.columns) > 1:
            fields.append('CompositeKey')
        return fields

    def get_diff(self, other=None):
        cols = {}
        not_seen_self = set()
        not_seen_other = set()
        if other is None:

            return TableNode(
                self.name,
                columns=self.columns,
                indexes=self.indexes,
                model=self.model, mode=MODE_DELETE,
                primary_key=self.primary_key,
                has_foreign_keys=self.has_foreign_keys,
            )
        if self.columns is None:
            return TableNode(
                name=other.name,
                columns=other.columns,
                indexes=self.indexes,
                mode=MODE_ADD,
                model=other.model,
                primary_key=other.primary_key,
                has_foreign_keys=other.has_foreign_keys,
            )

        indexes = []
        for index_self in self.indexes:
            for index_other in other.indexes:
                if index_self.is_equal(index_other):
                    break
            else:
                curr = IndexNode(index_self.indexes, index_self.unique, mode=MODE_DELETE)
                indexes.append(curr)
        for index_other in other.indexes:
            for index_self in self.indexes:
                if index_other.is_equal(index_self):
                    break
            else:

                curr = IndexNode(index_other.indexes, index_other.unique, mode=MODE_ADD)
                indexes.append(curr)

        for column_name, column in self.columns.items():
            if column_name in other.columns.keys():  # одинаковые имена
                curr = column.get_diff(other=other.columns[column_name], mode=MODE_MODIFY)
                if curr is not None:
                    cols[column_name] = curr
            else:
                not_seen_self.add(column_name)  # те которых нет в дб 2

        for column_name in other.columns.keys():
            if column_name not in self.columns.keys():
                not_seen_other.add(column_name)  # те которых нет в дб 1

        rename_self = set()
        rename_other = set()
        for column_name_self in not_seen_self:  # колонки из дб1, не нашедшие пару в дб2, удаляем
            for column_name_other in not_seen_other:
                if (
                        self.columns[column_name_self].is_equal(other.columns[column_name_other])
                        and column_name_other not in rename_other
                ):
                    curr = self.columns[column_name_self].get_diff(
                        other=other.columns[column_name_other],
                        mode=MODE_RENAME,
                    )
                    cols[column_name_other] = curr
                    rename_self.add(column_name_self)
                    rename_other.add(column_name_other)
                    break

        for column_name_self in not_seen_self - rename_self:
            curr = self.columns[column_name_self].get_diff(mode=MODE_DELETE)
            cols[column_name_self] = curr

        for column_name_other in not_seen_other - rename_other:  # из дб2 не нашедшие пару добавляем
            curr = other.columns[column_name_other].get_diff(mode=MODE_ADD)
            cols[column_name_other] = curr

        if not self.primary_key.are_equal(other.primary_key):
            print('WARNING primary keys for table', self.name, 'were changed')
            print(self.primary_key.columns, '   |   ', other.primary_key.columns)

        if len(cols) != 0 or len(indexes) != 0:
            return TableNode(self.name, columns=cols, indexes=indexes, mode=MODE_MODIFY)
        return None

    def as_pycode(self) -> str:
        if self.mode == MODE_DELETE:
            return ''

        if self.mode == MODE_ADD:
            return ''
        code = ''

        for column in self.columns.values():
            code = code + column.as_pycode(self.name)

        if self.indexes:
            for index in self.indexes:
                if len(index.indexes) > 1 or index.indexes[0] not in self.columns.keys():
                    code = code + index.as_pycode(self.name)
        return code

    def as_pycode_reversed(self) -> str:
        if self.mode == MODE_DELETE:
            return ''

        if self.mode == MODE_ADD:
            return ''
        code = ''

        for column in self.columns.values():
            code = code + column.as_pycode_reversed(self.name)

        if self.indexes:
            for index in self.indexes:
                if len(index.indexes) > 1 or index.indexes[0] not in self.columns.keys():
                    code = code + index.as_pycode_reversed(self.name)
        return code


class DbNode(Node):
    def __init__(self, tables: dict):
        self.tables = tables

    def get_foreign_keys_graph(self):
        graph = {}
        for table_name, table in self.tables.items():
            graph[table_name] = set()
            if not table.has_foreign_keys:
                continue
            for column_name, column in table.columns.items():
                if column.refl_column.is_foreign_key():
                    graph[table_name].add(column.refl_column.foreign_key.dest_table)

        return graph

    def get_right_order(self):
        graph = self.get_foreign_keys_graph()
        tables_right_order = []

        while len(tables_right_order) != len(self.tables.keys()):
            for table, refs in graph.items():
                if refs.issubset(set(tables_right_order)) and table not in tables_right_order:
                    tables_right_order.append(table)

        return tables_right_order

    def get_diff(self, other, only_tables: list = None):

        tabs = {}
        for table_name, table in self.tables.items():
            if only_tables and table_name not in only_tables:
                continue
            if table_name not in other.tables.keys():
                # MODE_DELETE
                curr = table.get_diff()

            else:
                # MODE_MODIFY
                curr = table.get_diff(other=other.tables[table_name])

            if curr is not None:
                tabs[table_name] = curr
        not_seen = set()
        for table_name in other.tables.keys():
            if only_tables and table_name not in only_tables:
                continue
            if table_name not in self.tables.keys():
                not_seen.add(table_name)
        for table_name in not_seen:
            # MODE_ADD
            curr = TableNode(name=table_name).get_diff(other=other.tables[table_name])

            tabs[table_name] = curr
        tables_add_delete = [
            table for table in tabs.keys() if tabs[table].mode in [MODE_DELETE, MODE_ADD]
        ]
        for table_name in tables_add_delete:
            if tabs[table_name].has_foreign_keys:
                for foreign_key in tabs[table_name].get_foreign_key_refl_columns():
                    dest_table = foreign_key.foreign_key.dest_table
                    dest_column = foreign_key.foreign_key.dest_column
                if dest_table not in tabs.keys() or tabs[dest_table].mode == MODE_MODIFY:
                    if tabs[table_name].mode == MODE_ADD:
                        stub = TableNode(
                            name=dest_table,
                            mode=MODE_STUB,
                            columns={dest_column: other.tables[dest_table].columns[dest_column]},
                            primary_key=other.tables[dest_table].primary_key,
                            model=other.tables[dest_table].model,
                        )
                        tabs[dest_table] = stub
                    elif tabs[table_name].mode == MODE_DELETE:
                        stub = TableNode(
                            name=dest_table,
                            mode=MODE_STUB,
                            columns={dest_column: self.tables[dest_table].columns[dest_column]},
                            primary_key=other.tables[dest_table].primary_key,
                            model=other.tables[dest_table].model,
                        )
                        tabs[dest_table] = stub
        return DbNode(tabs)

    def as_sql(self) -> str:
        query = ''
        for table in self.tables.values():
            query = query + table.as_sql()
        return query

    def as_pycode(self) -> str:
        """method for a diff_graph to get peewee commands for direct migration"""
        query = ''
        for table in self.tables.values():
            query = query + table.as_pycode()
            # print(query)
        return query

    def as_pycode_reversed(self) -> str:
        """method for a diff_graph to get peewee commands for roll_back() migration"""
        query = ''
        for table in self.tables.values():
            query = query + table.as_pycode_reversed()
            # print(query)
        return query

    def get_tables_mode_add(self) -> list:
        """method for a diff_graph to get all the tables's names that need to be added
        this method is useful for script generating"""
        tables_mode_add = []
        for table in self.tables.values():
            if table.mode == MODE_ADD:
                tables_mode_add.append(table.name)
        return tables_mode_add

    def get_tables_mode_delete(self) -> list:
        """method for a diff_graph to get all the table's names that need to be deleted
        this method is useful for script generating because
         to delete a table you need to know it's name"""
        tables_mode_delete = []
        for table in self.tables.values():
            if table.mode == MODE_DELETE:
                tables_mode_delete.append(table.name)
        return tables_mode_delete

    def get_fields_names(self) -> list:
        """method for a diff_graph to get all the fields that need to be modified
        this method is useful for script generating because
         to modify a field you need to import a corresponding peewee.Field"""
        fields = []
        for table in self.tables.values():
            fields = fields + table.get_fields_names()
        return fields

    def get_model(self, table_name, model_name):
        if table_name in self.tables.keys() and not model_name:
            return self.tables[table_name].get_model()
        model_description = 'class %s(BaseModel):\n' % model_name
        model_description += '\n    class Meta:\n'
        model_description += '        table_name = \'%s\'\n' % table_name
        return model_description
