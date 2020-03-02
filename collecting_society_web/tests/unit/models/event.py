# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from portal_web.tests.base import UnitTestBase
from portal_web.models import Tdb
from portal_web.tests.testdata import TestDataPortal
from ....models import Event
from ...testdata import TestDataCollectingSociety


class TestEvent(UnitTestBase, TestDataPortal, TestDataCollectingSociety):

    @classmethod
    def setUpClass(cls):
        """
        Initializes the database connection and creats test data.
        """
        super(TestEvent, cls).setUpClass()
        Tdb.init()
        test_party = cls.createParty(name='Gargoyle Club in Soho, London')
        lcat_nichtclub = cls.createLocationCategory(
            code='N',
            name="Nightclub",
            description="Where people go to dance at nighttime"
        )
        cls.test_location = cls.createLocation(
            name="Gargoyle Club (upstairs)",
            category=lcat_nichtclub,
            party=test_party
        )

    @Tdb.transaction()
    def test_can_write_a_record(self):
        """
        Can write a record?
        """
        description = "A famous Gothic party"
        eventdata = {
            'name': "The Batcave",
            'description': description,
            'location': self.test_location.id
        }
        event, = Event.create([eventdata])
        assert event
        self.data.append(event)

        event_in_database = Event.search_by_id(event.id)
        assert event_in_database.description == description
