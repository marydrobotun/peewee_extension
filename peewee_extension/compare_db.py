# -*- coding: utf-8 -*-
"""console tool, compares database with python models"""
from peewee_extension.migration import from_db
from peewee_extension.utils import CompareDbConfigurator


def main():
    configurator = CompareDbConfigurator()
    configurator.run()
    source_graph = from_db.get_graph(configurator.get_target())
    target_graph = from_db.get_graph(configurator.get_source())
    diff_graph = source_graph.get_diff(other=target_graph)
    print(diff_graph.as_sql())


if __name__ == '__main__':
    main()
