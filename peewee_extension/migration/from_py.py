# -*- coding: utf-8 -*-
import importlib

from peewee import CompositeKey, Field, ForeignKeyField, ForeignKeyMetadata
from peewee_extension.migration import graph
from playhouse.reflection import Column


def get_graph(module_name: str):
    try:
        module = importlib.import_module(module_name)
    except ImportError as exception:
        print('Failure in improting', module_name)
        raise Exception(exception)

    tables = {}
    columns = {}
    if hasattr(module, 'ABSTRACT_MODELS'):
        abstract_models = module.ABSTRACT_MODELS
    else:
        abstract_models = []

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if not isinstance(attr, type):
            continue
        if not hasattr(attr, '_meta'):
            continue
        if attr in abstract_models:
            continue
        if not attr.__module__ == module_name:  # is this ok??
            continue
        if not hasattr(attr._meta, 'table_name'):
            continue
        if len(attr._meta.columns.keys()) < 2:
            continue
        table_name = getattr(attr._meta, 'table_name')
        if table_name == 'pe_migrations':
            continue
        indexes = getattr(attr._meta, 'indexes')
        # if indexes:
        #   print(indexes)
        primary_key = getattr(attr._meta, 'primary_key')
        # print(primary_key, table_name)
        if not (isinstance(primary_key, Field) or isinstance(primary_key, CompositeKey)):
            primary_key = None
            primary_key = graph.PrimaryKeyNode(primary_key)
        if isinstance(primary_key, CompositeKey):
            primary_key = graph.PrimaryKeyNode(list(primary_key.field_names))
        if isinstance(primary_key, Field):
            temp = [primary_key.column_name.lower()]
            primary_key = graph.PrimaryKeyNode(temp)
        # indexes.append(attr.id)
        indexes_list = []
        for index in indexes:
            curr_index_list = []
            for field_name in index[0]:
                curr_index_list.append(getattr(attr, field_name).column_name)
            # print(curr_index_list)
            # print(list(index[0]))
            curr_index = graph.IndexNode(curr_index_list, unique=index[1])
            indexes_list.append(curr_index)
        # for i in indexes_list:
        #    print(i.indexes, i.unique, i.mode)
        if table_name == 'basemodel':
            continue
        model = attr.__name__
        columns = {}
        has_foreign_keys = False
        for table_attr_name in dir(attr):
            foreign_key_meta = None
            table_attr = getattr(attr, table_attr_name)
            if not isinstance(table_attr, Field):
                continue
            if isinstance(table_attr, CompositeKey):
                continue
            if table_attr.column_name not in attr._meta.columns:
                continue
            if table_attr.index or table_attr.unique:
                indexes_list.append(graph.IndexNode([table_attr.column_name], table_attr.unique))
            is_primary_key = table_attr.primary_key
            if hasattr(table_attr, 'max_length'):
                extra = {}

                extra['max_length'] = table_attr.max_length
                refl_column = Column(
                    name=table_attr.column_name,
                    column_name=table_attr.column_name,
                    default=table_attr.default,
                    nullable=table_attr.null,
                    raw_column_type=table_attr.field_type,
                    field_class=type(table_attr),
                    extra_parameters=extra,
                    index=table_attr.index,
                    unique=table_attr.unique,
                    primary_key=is_primary_key,
                )
            else:
                refl_column = Column(
                    name=table_attr.column_name,
                    nullable=table_attr.null,
                    column_name=table_attr.column_name,
                    default=table_attr.default,
                    raw_column_type=table_attr.field_type,
                    field_class=type(table_attr),
                    index=table_attr.index,
                    unique=table_attr.unique,
                    primary_key=is_primary_key,
                )
            if isinstance(table_attr, ForeignKeyField):
                model_names = {
                    table_name: attr_name,
                    table_attr.rel_model._meta.table_name: table_attr.rel_model.__name__,
                }
                has_foreign_keys = True
                foreign_key_meta = ForeignKeyMetadata(
                    column=table_attr_name,
                    dest_table=table_attr.rel_model._meta.table_name,
                    dest_column=table_attr.rel_field.column_name, table=table_name,

                )

                refl_column.set_foreign_key(foreign_key=foreign_key_meta, model_names=model_names)

            if hasattr(table_attr, 'values'):
                refl_column.extra_parameters = {'values': getattr(table_attr, 'values')}
            columns[table_attr.column_name] = graph.ColumnNode(
                table_attr.column_name,
                refl_column=refl_column,

            )

        tables[table_name] = graph.TableNode(
            name=table_name, primary_key=primary_key, columns=columns, model=model,
            indexes=indexes_list, has_foreign_keys=has_foreign_keys,
        )

        tables[table_name].get_model()

        # print(tables[table_name].indexes)
    db2 = graph.DbNode(tables)

    # db2.get_foreign_keys_graph()
    return db2
