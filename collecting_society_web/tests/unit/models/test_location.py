# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import pytest

from portal_web.models import Tdb
from ....models import Location


@pytest.fixture(scope='class')
def party(create_party):
    """
    Creates a party for location tests.
    """
    party = create_party(
        name='Tresor Berlin GmbH',
        firstname='Dietmar',
        lastname='Hegemann'
    )
    return party


@pytest.fixture(scope='class')
def location_category(create_location_category):
    """
    Creates a location category for location tests.
    """
    location_category = create_location_category(
        code='N',
        name="Nightclub",
        description="Where people go to dance at nighttime"
    )
    return location_category


class TestLocation:
    """
    Location model test class
    """
    @Tdb.transaction()
    def test_can_write_a_record(self, party, location_category):
        """
        Can write a record?
        """
        locationdata = {
            'name': "Tresor Berlin",
            'category': location_category,
            'party': party,
            'entity_creator': party,
        }
        location, = Location.create([locationdata])
        assert location

        location_in_database = Location.search_by_id(location.id)
        assert location_in_database.name == locationdata['name']

        location.delete([location])
