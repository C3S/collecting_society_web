# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from portal_web.tests.base import UnitTestBase
from portal_web.models import Tdb
from portal_web.tests.testdata import TestDataPortal
from ...models import Event
from ..testdata import TestDataCollectingSociety


class TestEvent(UnitTestBase, TestDataPortal, TestDataCollectingSociety):

    @classmethod
    def setUpClass(cls):
        """
        Initializes the database connection and creats test data.
        """
        #import ptvsd; ptvsd.enable_attach(address=("0.0.0.0", 51004), redirect_output=True); ptvsd.wait_for_attach(); ptvsd.break_into_debugger()
        super(TestEvent, cls).setUpClass()
        Tdb.init()
        test_party = cls.createParty(
            name='James Last',
            firstname='James',
            lastname='Last'
        )
        # test_webuser = cls.createWebUser(
        #     email='james@last.test',
        #     password='rightpassword'
        # )
        lcat_nichtclub = cls.createLocationCategory(
            code='N',
            name="Nightclub",
            description="Where people go to dance at nighttimes"
        )
        cls.test_location = cls.createLocation(
            name="Batcave",
            category=lcat_nichtclub,
            party=test_party
        )

    @Tdb.transaction()
    def test_can_write_and_read_a_record(self):
        """
        Can write a record?
        """
        #import ptvsd; ptvsd.enable_attach(address=("0.0.0.0", 51004), redirect_output=True); ptvsd.wait_for_attach(); ptvsd.break_into_debugger()        
        eventdata = {
            'name': "Monty Pythons Flying Circus",
            'description': "Comedy",
            'location': self.test_location.id
        }
        event, = Event.create([eventdata])
        assert event
        self.data.append(event)

        event_in_database = Event.search_by_id(event.id)
        assert event_in_database.description == "Comedy"

        #event_in_database.Delete()
