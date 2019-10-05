# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Track(Tdb):
    """
    Model wrapper for Tryton model object 'artist'
    """

    __name__ = 'release.track'

    @classmethod
    def search_all(cls):
        """
        Fetches all Tracks

        Returns:
          list: tracks
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, track_id):
        """
        Searches a track by track id

        Args:
          track_id (int): track.id

        Returns:
          obj: track
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', track_id)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid):
        """
        Searches a track by oid (public api id)

        Args:
          oid (int): track.oid

        Returns:
          obj: track
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def delete(cls, tracks):
        """
        Deletes track

        Args:
          tracks (list): tracks::

            [artist1, artist2, ...]

        Returns:
          ?
        """
        return cls.get().delete(tracks)

    @classmethod
    def create(cls, vlist):
        """
        Creates tracks

        Args:
          vlist (list): list of dicts with attributes to create tracks

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created tracks
          None: if no object was created
        """
        log.debug('create tracks:\n{}'.format(vlist))
        for values in vlist:
            if 'release' not in values:
                raise KeyError('release is missing')
            if 'creation' not in values:
                raise KeyError('creation is missing')
            if 'title' not in values:
                raise KeyError('title is missing')
        result = cls.get().create(vlist)
        return result or None
