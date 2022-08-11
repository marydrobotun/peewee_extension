# -*- coding: utf-8 -*-
"""модуль для создания скрипта миграции"""
import datetime
from pathlib import Path

import peewee
import peewee_extension.migration.graph
from jinja2 import Template


def get_additional_fields_used(fields: list):
    additional_fields_used = []
    for field in fields:
        if not hasattr(peewee, field) and field not in additional_fields_used:
            additional_fields_used.append(field)
    additional_fields_used = ', '.join(additional_fields_used)
    return additional_fields_used


def get_peewee_fields_used(fields: list):
    peewee_fields_used = []
    for field in fields:
        if hasattr(peewee, field) and field not in peewee_fields_used:
            peewee_fields_used.append(field)
    peewee_fields_used = ', '.join(peewee_fields_used)
    return peewee_fields_used


def get_models_order(diff_graph):
    pass


seen = set()


def get_models_right_order(
        diff_graph: peewee_extension.migration.graph.DbNode,
        table_name, right_order, accum=None,
):

    accum = accum or []
    foreign_keys_columns = diff_graph.tables[table_name].get_foreign_key_columns()
    for foreign_key_column in foreign_keys_columns:
        column = diff_graph.tables[table_name].columns[foreign_key_column].refl_column
        dest = column.foreign_key.dest_table

        # In the event the destination table has already been pushed
        # for printing, then we have a reference cycle.
        if dest in accum and table_name not in accum:
            print('# Possible reference cycle: %s' % dest)

        # If this is not a column-referential foreign key, and we have
        # not already processed the destination table, do so now.
        if dest not in seen and dest not in accum:
            seen.add(dest)
            if dest != table_name:
                get_models_right_order(diff_graph, dest, right_order, accum + [table_name])

    right_order.append(table_name)
    seen.add(table_name)


def make(
        diff_graph: peewee_extension.migration.graph.DbNode,
        models_file: str, main_temp=None, model_temp=None, empty_temp=None,
) -> str:
    """ генерирует скрипт в строковом формате по разностному графу
    с использованием готовых темплэйтов"""
    if not diff_graph:
        empty_temp = Path(__file__).parent / 'templates' / 'empty_migration.j2'
        with open(empty_temp, 'r') as file_handle:
            script = file_handle.read()
        return script

    if main_temp is None:
        main_temp = Path(__file__).parent / 'templates' / 'migration_template.j2'
    if model_temp is None:
        model_temp = Path(__file__).parent / 'templates' / 'table_model_template.j2'
    query = diff_graph.as_pycode()
    reversed_query = diff_graph.as_pycode_reversed()
    tables_to_add = diff_graph.get_tables_mode_add()
    tables_to_delete = diff_graph.get_tables_mode_delete()
    tables_to_print = {}
    for table in tables_to_delete:
        tables_to_print[table] = diff_graph.tables[table].model
        foreign_keys_columns = diff_graph.tables[table].get_foreign_key_columns()
        for foreign_key_column in foreign_keys_columns:
            column = diff_graph.tables[table].columns[foreign_key_column].refl_column
            dest = column.foreign_key.dest_table
            if dest not in tables_to_print:
                tables_to_print[dest] = column.get_field_parameters()['model']

    for table in tables_to_add:
        tables_to_print[table] = diff_graph.tables[table].model
        foreign_keys_columns = diff_graph.tables[table].get_foreign_key_columns()
        for foreign_key_column in foreign_keys_columns:
            column = diff_graph.tables[table].columns[foreign_key_column].refl_column
            dest = column.foreign_key.dest_table
            if dest not in tables_to_print:
                tables_to_print[dest] = column.get_field_parameters()['model']
    fields = diff_graph.get_fields_names()
    models_description = ''
    models_names_for_deleting = []
    right_order = []
    for table in tables_to_print.keys():
        if table not in seen:
            get_models_right_order(diff_graph, table, right_order)
    models_names_for_adding = []
    for table in right_order:
        if table in tables_to_delete:
            models_names_for_deleting.append(diff_graph.tables[table].model)
            models_description += diff_graph.tables[table].get_model()
        elif table in tables_to_add:
            models_names_for_adding.append(diff_graph.tables[table].model)
            models_description += diff_graph.tables[table].get_model()
        else:
            models_description += diff_graph.tables[table].get_model()

    with open(main_temp, 'r') as file_handle:
        script = file_handle.read()
    script = Template(script)
    model_init = ''
    for table in tables_to_add:
        model_init = model_init + table + '._meta.database = db\n'
    models_names_for_deleting = ', '.join(models_names_for_deleting)
    models_names_for_adding = ', '.join(models_names_for_adding)
    data = {
        'peewee_fields': get_peewee_fields_used(fields),
        'core_fields': get_additional_fields_used(fields),
        'migrations': query,
        'reversed_migrations': reversed_query,
        'tables_to_delete': models_names_for_deleting,
        'tables_to_add': models_names_for_adding,
        'fields': fields,
        'model_init': model_init,
        'models_to_delete': models_description,
        'models_file': models_file,
    }
    script = script.render(data)
    script = script + '\n'
    return script


def write_in_file(migrations_path: str, db_name: str, script: str, migration_name: str = None):
    """ записывает скрипт в файл с названием вида ГГГГММДДччммсс_имябд_затронутыетаблицы"""
    if migration_name:
        filepath = str(migrations_path) + '/' + migration_name + '.py'
    else:
        date_time = datetime.datetime.now()
        date_time = date_time.strftime('%Y%m%d%H%M%S')
        filepath = str(migrations_path) + '/' + date_time + '_' + db_name
        filepath = filepath + '.py'
    with open(filepath, 'w') as file_handle:
        file_handle.write(script)
    return filepath
