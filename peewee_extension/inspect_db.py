# -*- coding: utf-8 -*-

import configargparse
from playhouse.db_url import connect
from playhouse.reflection import (
    Introspector, UnknownField,
)

from peewee_extension.core import MxMySQLMetadata
from peewee_extension.utils import get_db_name

HEADER = """\
from peewee import (
    BigAutoField, AutoField, Model, DatabaseProxy, DeferredForeignKey, ForeignKeyField, CompositeKey,
    BooleanField, CharField, DateTimeField,
    IntegerField, SmallIntegerField, TextField, FixedCharField, DateField,
    DoubleField, BigIntegerField, TimeField, DecimalField, FloatField,
)

from peewee_extension.core import (
    UnsignedIntegerField, TinyIntegerField, UnsignedTinyIntegerField, UnsignedSmallIntegerField,
    UnsignedBigIntegerField, MediumIntegerField, UnsignedMediumIntegerField, UnsignedDoubleField,
    UnsignedDecimalField, LongTextField, MediumTextField, LongBlobField, EnumField,
)

db = DatabaseProxy()
"""

BASE_MODEL = """\
class BaseModel(Model):
    class Meta:
        database = db
"""

UNKNOWN_FIELD = """\
class UnknownField(object):
    def __init__(column, *_, **__): pass
"""


def make_introspector(db_url, schema=None):
    db = connect(db_url)
    meta = MxMySQLMetadata(db)
    return Introspector(metadata=meta, schema=schema)


def print_models(introspector, db_name=None, tables=None, preserve_order=False,
                 include_views=False, ignore_unknown=False, snake_case=True, lower_case=False):
    """
    Взято из pwiz - http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#pwiz
    :param introspector:
    :param tables:
    :param preserve_order:
    :param include_views:
    :param ignore_unknown:
    :param snake_case:
    :return:
    """

    database = introspector.introspect(table_names=tables,
                                       include_views=include_views,
                                       snake_case=snake_case)
    print(HEADER)
    if not ignore_unknown:
        print(UNKNOWN_FIELD)
    if db_name is not None:
        print('db_name = \'', db_name, '\'\n', sep='')
    print(BASE_MODEL)

    def _print_table(table, seen, accum=None):
        accum = accum or []
        foreign_keys = database.foreign_keys[table]
        for foreign_key in foreign_keys:
            dest = foreign_key.dest_table

            # In the event the destination table has already been pushed
            # for printing, then we have a reference cycle.
            if dest in accum and table not in accum:
                print('# Possible reference cycle: %s' % dest)

            # If this is not a column-referential foreign key, and we have
            # not already processed the destination table, do so now.
            if dest not in seen and dest not in accum:
                seen.add(dest)
                if dest != table:
                    _print_table(dest, seen, accum + [table])

        print('class %s(BaseModel):' % database.model_names[table])
        columns = database.columns[table].items()
        if not preserve_order:
            columns = sorted(columns)
        primary_keys = database.primary_keys[table]
        for name, column in columns:
            skip = all([
                name in primary_keys,
                name == 'id',
                len(primary_keys) == 1,
                column.field_class in introspector.pk_classes])
            if skip:
                continue
            if column.primary_key and len(primary_keys) > 1:
                # If we have a CompositeKey, then we do not want to explicitly
                # mark the columns as being primary keys.
                column.primary_key = False

            is_unknown = column.field_class is UnknownField
            if is_unknown and ignore_unknown:
                disp = '%s - %s' % (column.name, column.raw_column_type or '?')
                print('    # %s' % disp)
            else:
                column.default = None  # зануляем что бы не было constraints=[SQL("DEFAULT 35")]
                if lower_case:
                    # иначе пишет column_name='DECIMALS' в кваргах поля
                    column.column_name = column.column_name.lower()
                print('    %s' % column.get_field())

        print('')
        print('    class Meta:')
        print('        table_name = \'%s\'' % table)
        #print(database.indexes[table])
        multi_column_indexes = database.multi_column_indexes(table)
        if len(primary_keys) > 1:
            #print(primary_keys)
            #pk_field_names = primary_keys
            #for c in pk_field_names:
             #   c = c.lower()
            #pk_field_names = [field.name for col, field in columns
             #   if col in primary_keys]
            #print(columns)
            pk_field_names_2=[]
            for key in primary_keys:
                for col, field in columns:
                    #print('COL', col, 'FIELD', field)
                    if col == key:
                        pk_field_names_2.append(field.name)
                        #pk_field_names.reverse()
            print(pk_field_names_2)
        else:
            pk_field_names_2 = False
        #print(database.multi_column_indexes(table))
        if multi_column_indexes:
            print('        indexes = (')
            for fields, unique in sorted(multi_column_indexes):
                #fields_sorted = sorted(fields)
                if (not pk_field_names_2 or fields != pk_field_names_2) or unique == False:
                    #print(fields, pk_field_names_2)
                    print('            ((%s), %s),' % (
                    ', '.join("'%s'" % field for field in fields),
                    unique,
                ))

                    #print(pk_field_names, fields)
            print('        )')

        if introspector.schema:
            print('        schema = \'%s\'' % introspector.schema)
        if len(primary_keys) > 1:
            pk_field_names = sorted(
                field.name for col, field in columns
                if col in primary_keys)
            pk_field_names.reverse()
            pk_list = ', '.join("'%s'" % pk for pk in pk_field_names)

            print('        primary_key = CompositeKey(%s)' % pk_list)
        elif not primary_keys:
            print('        primary_key = False')
        print('')
        print('')

        seen.add(table)

    seen = set()
    for table in sorted(database.model_names.keys()):
        if table not in seen:
            if not tables or table in tables:
                _print_table(table, seen)


def main():
    configurator = configargparse.ArgParser()
    configurator.add_argument(
        '-c', '--config', default='config.yml', required=False, is_config_file=True,
        help='config file path',
    )
    configurator.add_argument(
        '-d', '--db_url', required=True, help='db_url to connect to',
    )
    options = configurator.parse_known_args()
    db_name = get_db_name(options[0].db_url)
    introspector = make_introspector(options[0].db_url)
    print_models(introspector, db_name=db_name, preserve_order=True)


if __name__ == '__main__':
    main()
