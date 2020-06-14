# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByOid,
    MixinSearchAll
)

log = logging.getLogger(__name__)


class Location(Tdb, MixinSearchById, MixinSearchByOid, MixinSearchAll):
    """
    Model wrapper for Tryton model object 'location'
    """
    __name__ = 'location'

    @classmethod
    def create(cls, vlist):
        """
        Creates location

        Args:
          vlist (list): list of dicts with attributes to create publisher::

            [
                {
                    'name': str (required)
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created location
          None: if no object was created
        """
        log.debug('create location:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
            if 'longitude' not in values or 'latitude' not in values:
                raise KeyError('Full latitude/longitude geoinfo is necessary')
        result = cls.get().create(vlist)
        return result or None
