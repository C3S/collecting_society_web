# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import pytest

from portal_web.models import Tdb
from ....models import Event


@pytest.fixture(scope='class')
def location(create_party, create_location_category, create_location):
    party = create_party(name='Gargoyle Club in Soho, London')
    location_category = create_location_category(
        code='N',
        name="Nightclub",
        description="Where people go to dance at nighttime",
    )
    location = create_location(
        name="Gargoyle Club (upstairs)",
        category=location_category,
        party=party,
        entity_creator=party,
    )
    return location


class TestEvent:
    """
    Event model test class
    """
    @Tdb.transaction(readonly=False)
    def test_can_write_a_record(self, tryton, location):
        """
        Can write a record?
        """
        eventdata = {
            'name': "The Batcave",
            'description': "A famous Gothic party",
            'location': location.id,
        }
        event, = Event.create([eventdata])
        assert event

        event_in_database = Event.search_by_id(event.id)
        assert event_in_database.description == eventdata['description']

        event.delete([event])
