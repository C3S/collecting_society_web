# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CreationRightInstrument(Tdb):
    """
    Model wrapper for Tryton model object 'creation.right'
    """
    __name__ = 'creation.right-instrument'

    @classmethod
    def search_by_right_and_instrument(cls, right_id, instrument_id):
        """
        Searches creation.right-instrument

        Args:
          right_id (int): creation-right.id
          instrument_id (int): instrument.id

        Returns:
          list: creations.right
          None: if no match is found
        """
        result = cls.get().search([
            ('right', '=', right_id),
            ('instrument', '=', instrument_id)
            ])
        return result or None
