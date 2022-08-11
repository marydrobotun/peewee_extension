# -*- coding: utf-8 -*-
"""module to build a graph out of a database"""
from peewee import ForeignKeyField
from peewee_extension.core import MxMySQLMetadata
from peewee_extension.migration import graph
from playhouse.db_url import connect
from playhouse.reflection import Introspector, UnknownField


def make_introspector(db_url, schema=None) -> Introspector:
    """function that connects to a database and gets all the metainformation from it"""
    database = connect(db_url)
    meta = MxMySQLMetadata(database)
    return Introspector(metadata=meta, schema=schema)


def get_primary_key_from_indexes(indexes: list) -> list:
    """function to get a list of columns that are marked as
    primary keys out of indexes from introspector"""
    for index in indexes:
        if index.name == 'PRIMARY':
            columns = []
            for column in index.columns:
                columns.append(column.lower())
            return columns
    return None


def get_graph(db_url, tables=None) -> graph.DbNode:
    """function connects to a database, makes introspection and then builds
    a database graph (look graph.py) out of introspector
    returns object of type DbNode (look graph.py)"""
    introspector = make_introspector(db_url)
    database = introspector.introspect(table_names=tables)
    seen = set()
    tabs = {}
    for table in sorted(database.model_names.keys()):
        has_foreign_keys = False
        if table == 'pe_migrations':
            continue
        if table not in seen:
            if not tables or table in tables:
                cols = {}

                columns = database.columns[table].items()

                indexes = []
                #  print(table)
                for index in database.indexes[table]:

                    #  print('         ', index.name, index)
                    if index.name != 'PRIMARY':
                        curr_index = graph.IndexNode(index.columns, index.unique)
                        indexes.append(curr_index)
                primary_key = get_primary_key_from_indexes(database.indexes[table])
                primary_key = graph.PrimaryKeyNode(primary_key)
                for name, column in columns:
                    curr = graph.ColumnNode(
                        name=name,
                        refl_column=column,

                    )
                    if column.field_class == UnknownField:
                        continue
                    if column.field_class == ForeignKeyField:
                        has_foreign_keys = True

                    cols[name] = curr

                curr = graph.TableNode(
                    table, primary_key=primary_key, columns=cols, indexes=indexes,
                    model=database.model_names[table], has_foreign_keys=has_foreign_keys
                )
                #print(curr.name, curr.primary_key.columns)
                tabs[curr.name] = curr
    db1 = graph.DbNode(tabs)

    return db1
