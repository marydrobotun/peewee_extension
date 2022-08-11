# -*- coding: utf-8 -*-
import importlib
import sys
from pathlib import Path

import configargparse

PEEWEE_EXTENSION_CONFIG_STUB = Path(__file__).parent / 'config_stub.yml'


def get_db_name(db_url: str) -> str:
    """function to get database name out of db_url"""
    temp = db_url.split('/')
    return temp[-1]


class Configurator:
    CONFIG_STUB = PEEWEE_EXTENSION_CONFIG_STUB
    required_params = ['db_url', 'models']

    def __init__(self):
        self.params = configargparse.ArgParser(
            config_file_parser_class=configargparse.YAMLConfigFileParser,
            ignore_unknown_config_file_keys=True,
        )
        self.params.add_argument(
            '-c', '--config',
            is_config_file=True,
            help='config file path',
        )
        self.params.add_argument(
            '--write-config-stub', nargs='?', const='config.yml',
            help='make config stub',
        )
        self.additional_params()
        self.options = None

    def is_required(self, field_name: str):
        return field_name in self.required_params

    def add_filepath_param(self):
        self.params.add_argument(
            '-p', '--filepath', required=self.is_required('filepath'),
            help='path where to put migration scripts',
        )

    def add_dburl_param(self):
        self.params.add_argument(
            '-d', '--db_url', required=self.is_required('db_url'),
            help='connect string mysql://user:password@host:port/db',
        )

    def add_models_param(self):
        self.params.add_argument(
            '-m', '--models', required=self.is_required('models'),
            help='models to compare with',
        )

    def additional_params(self):
        self.add_dburl_param()
        self.add_filepath_param()
        self.add_models_param()

    def run(self):
        self.options = self.params.parse_args()
        print(self.params.format_values())
        if self.options.write_config_stub:
            from shutil import copyfile
            copyfile(self.CONFIG_STUB, self.options.write_config_stub)
            print('Config stub wrote to', self.options.write_config_stub)
            sys.exit(0)

    def get_dburl(self):
        return self.options.db_url

    def get_models(self):
        return self.options.models

    def get_filepath(self):
        if not self.options.filepath:
            try:
                models = importlib.import_module(self.get_models())
            except ImportError as err:
                raise Exception('Failed to import models', err)
            filepath = Path(models.__file__).parent / 'pe_migrations'
            filepath.mkdir(exist_ok=True)
            return filepath
        return self.options.filepath

    def get_db_name(self):
        db_url = self.get_db_url()
        temp = db_url.split('/')
        return temp[-1]

    def get_db_url(self):
        return 'user:passwd@localhost/redefine_me'


class CreateMigrationConfigurator(Configurator):

    def additional_params(self):
        super(CreateMigrationConfigurator, self).additional_params()
        self.params.add_argument(
            '-t', '--only_tables', nargs='*',
            help='для фильтрации таблиц, попадающих в миграцию, перечислите через пробел',
        )
        self.params.add_argument(
            '--empty-migration', action='store_true', help='make empty migration',
        )
        self.params.add_argument(
            '--name', help='название для миграции, '
                           'можно не указывать тогда сработает автогенерация',
        )

    def is_empty_migration(self):
        return self.options.empty_migration

    @property
    def migration_name(self):
        return self.options.name

    @property
    def only_tables(self):
        return self.options.only_tables


class MigrateConfigurator(Configurator):

    def additional_params(self):
        super(MigrateConfigurator, self).additional_params()
        self.params.add_argument(
            '--name', help='migration name to apply',
        )
        self.params.add_argument(
            '-y', '--yes', action='store_true',
            help='не спрашивать подтверждения на применение миграций',
        )

    @property
    def ask_user(self):
        return not self.options.yes


class CompareDbConfigurator(Configurator):

    def additional_params(self):
        self.add_dburl_param()
        self.params.add_argument(
            '-s', '--db_url_source', required=True, help='db_url to connect to',
        )

    def get_source(self):
        return self.options.db_url_source

    def get_target(self):
        return self.options.db_url
