# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb, MixinSearchById

log = logging.getLogger(__name__)


class Event(Tdb, MixinSearchById):
    """
    Model wrapper for Tryton model object 'event'
    """
    __name__ = 'event'

    @classmethod
    def create(cls, vlist):
        """
        Creates event

        Args:
          vlist (list): list of dicts with attributes to create event::

            [
                {
                    'name': str (required)
                    'entity_creator': int (required)
                    'location': int (required)
                    'description': str
                    'performances': [int]
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created event
          None: if no object was created
        """
        log.debug('create event:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
            if 'location' not in values:
                raise KeyError('entity_creator is missing')
        result = cls.get().create(vlist)
        return result or None
