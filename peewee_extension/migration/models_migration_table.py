# -*- coding: utf-8 -*-
from peewee import (
    BooleanField, CharField, DatabaseProxy,
    DateTimeField, Model,
)

db = DatabaseProxy()


class Migration(Model):
    name = CharField(max_length=255)
    is_applied = BooleanField(default=False)
    created_at = DateTimeField()
    applied_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'pe_migrations'
