# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CreationRightsholderInstrument(Tdb):
    """
    Model wrapper for Tryton model object 'creation.rightsholder'
    """
    __name__ = 'creation.rightsholder-instrument'

    @classmethod
    def search_by_crightsholder_and_instrument(cls,
                                               crightsholder_id,
                                               instrument_id):
        """
        Searches creation.rightsholder-instrument

        Args:
          crightsholder_id (int): creation-rightsholder.id
          instrument_id (int): instrument.id

        Returns:
          list: creations.rightsholder
          None: if no match is found
        """
        result = cls.get().search([
            ('rightsholder', '=', crightsholder_id),
            ('instrument', '=', instrument_id)
            ])
        return result or None