# -*- coding: utf-8 -*-
from peewee_extension.migration import from_db, from_py, script


class MigrationGenerator:

    def __init__(
            self, db_url: str, models: str, make_empty_migration: bool = False,
    ):
        self.db_url = db_url
        self.models = models
        self.make_empty_migration = make_empty_migration
        self.script: str = ''

    def get_db_url(self):
        return self.db_url

    def get_models(self):
        return self.models

    def get_db_name(self) -> str:
        """function to get database name out of db_url"""
        temp = self.db_url.split('/')
        return temp[-1]

    def get_script_name(self):
        pass  # sdelat

    def generate(self, only_tables: list = None):
        source_graph = from_db.get_graph(self.db_url)
        target_graph = from_py.get_graph(self.models)
        if self.make_empty_migration:
            diff_graph = None
        else:
            diff_graph = source_graph.get_diff(other=target_graph, only_tables=only_tables)
        self.script = script.make(
            diff_graph, self.models,
            #  'peewee_extension/migration/templates/migration_template.j2',
            #  'peewee_extension/migration/templates/table_model_template.j2',
        )

    def write_in_file(self, migrations_path, migration_name: str = None):
        db_name = self.get_db_name()
        filename = script.write_in_file(
            migrations_path, db_name, self.script, migration_name,
        )
        return filename
