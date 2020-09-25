# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from trytond.transaction import Transaction
from portal_web.tests.base import UnitTestBase
from portal_web.models import Tdb
from portal_web.tests.testdata import TestDataPortal
from ....models import Location
from ...testdata import TestDataCollectingSociety


class TestLocation(UnitTestBase, TestDataPortal, TestDataCollectingSociety):

    @classmethod
    def setUpClass(cls):
        """
        Initializes the database connection and creats test data.
        """
        #import ptvsd; ptvsd.enable_attach(address=("0.0.0.0", 51004), redirect_output=True); ptvsd.wait_for_attach(); ptvsd.break_into_debugger()
        super(TestLocation, cls).setUpClass()
        Tdb.init()
        cls.test_party = cls.createParty(
            name='Tresor Berlin GmbH',
            firstname='Dietmar',
            lastname='Hegemann'
        )
        cls.lcat_nichtclub = cls.createLocationCategory(
            code='N',
            name="Nightclub",
            description="Where people go to dance at nighttime"
        )

    @Tdb.transaction()
    def test_can_write_a_record(self):
        """
        Can write a record?
        """
        name = "Tresor Berlin"
        locationdata = {
            'name': name,
            'category': self.lcat_nichtclub,
            'party': self.test_party,
            'entity_creator': self.test_party
        }
        location, = Location.create([locationdata])
        assert location
        self.data.append(location)

        location_in_database = Location.search_by_id(location.id)
        assert location_in_database.name == name
