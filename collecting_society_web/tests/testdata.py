# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from portal_web.models import Tdb, WebUser, Party, WebUserRole


class TestDataCollectingSociety():
    """
    Mix-in class for portal with helper functions to create test data.
    """

    @classmethod
    @Tdb.transaction(readonly=False)
    def createLocationCategory(cls, name, code, description):
        lcat, = Tdb.pool().get('location.category').create([{
            'name': name,
            'code': code,
            'description': description
        }])
        cls.data.append(lcat)
        return lcat

    @classmethod
    @Tdb.transaction(readonly=False)
    def createLocation(cls, name, category, party, entity_creator):
        location, = Tdb.pool().get('location').create([{
            'name': name,
            'category': category,
            'party': party.id,
            'entity_creator': entity_creator.id
        }])
        cls.data.append(location)
        return location
