# -*- coding: utf-8 -*-
import datetime
from collections import defaultdict
from collections.abc import Iterable  # добавила импорт из абс, было предупреждение

from peewee import ColumnBase, Model, SQL
from playhouse.reflection import (
    BigIntegerField, BlobField, CharField, DateField, DateTimeField, DecimalField, DoubleField,
    Field, FixedCharField, FloatField, IntegerField, MySQLMetadata, SmallIntegerField,
    TextField, TimeField, UnknownField, BooleanField
)


class TimedAtTable(Model):
    created_at = DateTimeField(default=datetime.datetime.now, null=True)
    updated_at = DateTimeField(default=datetime.datetime.now, null=True)

    def save(self, force_insert=False, only=None):
        self.updated_at = datetime.datetime.now()
        super(TimedAtTable, self).save(force_insert=force_insert, only=only)


class SystimeTable(Model):
    systime = DateTimeField(column_name='SYSTIME', constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class SortOrderColumn(Model):
    sort_order = IntegerField(default=None)


# TODO сделать MixIn для sort_order:
#      - если не определен -> Брать max(sort_order) + 1 из таблицы


class UnsignedIntegerField(Field):
    field_type = 'INTEGER UNSIGNED'


class TinyIntegerField(IntegerField):
    field_type = 'TINYINT'


class UnsignedTinyIntegerField(IntegerField):
    field_type = 'TINYINT UNSIGNED'


class UnsignedSmallIntegerField(SmallIntegerField):
    field_type = 'SMALLINT UNSIGNED'


class UnsignedBigIntegerField(BigIntegerField):
    field_type = 'BIGINT UNSIGNED'


class MediumIntegerField(IntegerField):
    field_type = 'MEDIUMINT'


class UnsignedMediumIntegerField(MediumIntegerField):
    field_type = 'MEDIUMINT UNSIGNED'


class UnsignedDoubleField(DoubleField):
    field_type = 'DOUBLE UNSIGNED'


class UnsignedDecimalField(DecimalField):
    field_type = 'DECIMAL UNSIGNED'


class LongTextField(TextField):
    field_type = 'LONGTEXT'


class MediumTextField(TextField):
    field_type = 'MEDIUMTEXT'


class LongBlobField(Field):
    field_type = 'LONGBLOB'


class MediumBlobField(Field):
    field_type = 'MEDIUMBLOB'


class TinyTextField(Field):
    field_type = 'TINYTEXT'


class YearField(Field):
    field_type = 'MEDIUMBLOB'


class SetField(Field):
    field_type = 'SET'


class BinaryField(Field):
    field_type = 'BINARY'


class VarBinaryField(Field):
    field_type = 'VARBINARY'


class BitField(Field):
    field_type = 'BIT'


class EnumField(Field):
    # field_type = 'ENUM'
    def __str__(self):
        values = []
        for value in self.values:
            values.append('\'' + value + '\'')
        return 'ENUM({})'.format(', '.join(values))

    @property
    def field_type(self):
        values = []
        for value in self.values:
            values.append('\'' + value + '\'')
        return 'ENUM({})'.format(', '.join(values))

    def __init__(self, values=None, *args, **kwargs):
        if values is None or not isinstance(values, Iterable):
            raise ValueError('EnumField must contain keyword values=<iterable>')
        self.values = values
        super(EnumField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        if value not in self.values:
            raise ValueError(f'EnumField {self.name} has not value {value}')
        return value


class MxMySQLMetadata(MySQLMetadata):
    column_map = {
        'int': IntegerField,
        'tinyint': TinyIntegerField,
        'smallint': SmallIntegerField,
        'mediumint': MediumIntegerField,
        'bigint': BigIntegerField,
        'int unsigned': UnsignedIntegerField,
        'tinyint unsigned': UnsignedTinyIntegerField,
        'smallint unsigned': UnsignedSmallIntegerField,
        'mediumint unsigned': UnsignedMediumIntegerField,
        'bigint unsigned': UnsignedBigIntegerField,
        'bit': BitField,

        'float': FloatField,
        'double': DoubleField,
        'double unsigned': UnsignedDoubleField,
        'decimal': DecimalField,
        'decimal unsigned': UnsignedDecimalField,

        'varchar': CharField,
        'char': FixedCharField,
        'binary': BinaryField,
        'varbinary': VarBinaryField,

        'date': DateField,
        'datetime': DateTimeField,
        'time': TimeField,
        'timestamp': DateTimeField,
        'year': YearField,

        'tinytext': TinyTextField,
        'blob': BlobField,
        'longblob': LongBlobField,
        'mediumblob': MediumBlobField,
        'text': TextField,
        'mediumtext': MediumTextField,
        'longtext': LongTextField,

        'enum': EnumField,
        'set': SetField,
        'bool': BooleanField,

    }

    def get_column_types(self, table, schema=None):
        """
        Переопределенный метод для получения ПОЛНОЙ информации из БД
        :param table:
        :param schema:
        :return:
        """
        column_types = {}
        extra_params = defaultdict(dict)

        sql = 'SELECT * FROM information_schema.columns WHERE table_schema = %s AND table_name = %s'
        cursor = self.database.execute_sql(sql, [self.database.database, table])
        names = [d[0].lower() for d in cursor.description]
        result = [{name: val for name, val in zip(names, row)} for row in cursor]
        for descr in result:
            name = descr['column_name']
            data_type = descr['data_type']
            raw_type = descr['column_type']  # column_type - raw MySQL column type
            # (like varchar(32))
            if 'unsigned' in raw_type:
                data_type += ' unsigned'
            column_types[name] = self.column_map.get(data_type, UnknownField)
            if data_type in ('char', 'varchar'):
                extra_params[name]['max_length'] = descr['character_maximum_length']
            comment = descr['column_comment']
            if comment:
                extra_params[name]['verbose_name'] = f"'{comment}'"
            default = descr['column_default']
            if default:
                extra_params[name]['default'] = default if default.isdigit() else f"'{default}'"
            if 'decimal' in data_type:
                extra_params[name]['max_digits'] = descr['numeric_scale']
                extra_params[name]['decimal_places'] = descr['numeric_precision']
            if data_type == 'enum':
                # 'enum(\'common\',\'manual\',\'asts\',\'ekbd\',\'calc\',\'stock_dep\')'
                extra_params[name]['values'] = raw_type.replace('enum', '')
        return column_types, extra_params


ColumnBase.is_true = lambda self: self == True  # noqa E712
ColumnBase.is_false = lambda self: self == False  # noqa E712
