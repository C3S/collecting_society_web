# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.creative

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Release(Tdb):
    """
    Model wrapper for Tryton model object 'creation'
    """

    __name__ = 'release'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls, active=True):
        """
        Fetches all Releases

        Args:
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: releases
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_party(cls, party_id, active=True):
        """
        Searches releases by party id

        Args:
          party_id (int): party.party.id

        Returns:
          list: releases of web_user
          None: if no match is found
        """
        return cls.get().search([
            [
                'OR',
                ('party', '=', party_id),
                ('creations.creation.artist.party', '=', party_id)
            ],
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_id(cls, uid, active=True):
        """
        Searches releases by id

        Args:
          uid (int): release id

        Returns:
          list: releases of web_user
          None: if no match is found
        """
        releases = cls.get().search([
            ('id', '=', uid),
            ('active', 'in', (True, active))
        ])
        if not releases:
            return None
        return releases[0]

    @classmethod
    @Tdb.transaction(readonly=False)
    def delete(cls, release):
        """
        Deletes release

        Args:
          release (list): realeases::

            [release1, release2, ...]

        Returns:
          ?
        """
        return cls.get().delete(release)

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates Releases

        Args:
          vlist (list): list of dicts with attributes to create releases::

            [
                {
                    ...2DO
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created releases
          None: if no object was created
        """
        log.debug('create release:\n{}'.format(vlist))
        # for values in vlist:
        #     if 'title' not in values:
        #         raise KeyError('title is missing')
        #     if 'artist' not in values:
        #         raise KeyError('artist is missing')
        result = cls.get().create(vlist)
        return result or None
