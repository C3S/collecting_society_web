# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb, MixinSearchById

log = logging.getLogger(__name__)


class EventPerformance(Tdb, MixinSearchById):
    """
    Model wrapper for Tryton model object 'event.performance'
    """
    __name__ = 'event.performance'

    @classmethod
    def create(cls, vlist):
        """
        Creates event performances

        Args:
          vlist (list): list of dicts with attributes to create peformances::

            [
                {
                    'start': datetime.datetime (required),
                    'end': datetime.datetime (required),
                    'artist': artist (required),
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created event performances
          None: if no object was created
        """
        log.debug('create event performance:\n{}'.format(vlist))
        for values in vlist:
            if 'start' not in values:
                raise KeyError('start is missing')
            if 'end' not in values:
                raise KeyError('end is missing')
            if 'artist' not in values:
                raise KeyError('artist is missing')
        result = cls.get().create(vlist)
        return result or None

    @classmethod
    def delete(cls, performances):
        """
        Deletes event performances

        Args:
          performances (list): event.performances::

            [performance1, performance2, ...]

        Returns:
          ?
        """
        return cls.get().delete(performances)
