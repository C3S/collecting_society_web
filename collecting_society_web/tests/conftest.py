# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Pytest Fixtures
"""

import pytest


@pytest.fixture(scope='class')
def create_location_category(tryton):
    """
    Yields a function to create a location category.
    """
    records = []
    LocationCategory = tryton.pool.get('location.category')

    @staticmethod
    @tryton.transaction(readonly=False)
    def create(**kwargs):
        location_category = LocationCategory(**kwargs)
        location_category.save()
        records.append(location_category)
        return location_category

    yield create

    tryton.delete_records(records)


@pytest.fixture(scope='class')
def create_location(tryton):
    """
    Yields a function to create a location.
    """
    records = []
    Location = tryton.pool.get('location')

    @staticmethod
    @tryton.transaction(readonly=False)
    def create(**kwargs):
        location = Location(**kwargs)
        location.save()
        records.append(location)
        return location

    yield create

    tryton.delete_records(records)
