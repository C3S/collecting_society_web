# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.creative

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Creation(Tdb):
    """
    Model wrapper for Tryton model object 'creation'
    """

    __name__ = 'creation'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls, active=True):
        """
        Fetches all Creations

        Args:
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creation
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_party(cls, party_id, active=True):
        """
        Searches creations by party id

        Args:
          party_id (int): party.party.id
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creations of web_user
          None: if no match is found
        """
        return cls.get().search([
            [
                'OR',
                ('artist.party', '=', party_id),
                ('contributions.artist.party', '=', party_id),
                ('contributions.artist.solo_artists.party', '=', party_id),
                ('contributions.artist.group_artists.party', '=', party_id)
            ],
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_id(cls, creation_id, active=True):
        """
        Searches an creation by creation id

        Args:
          creation_id (int): creation.id
          active (bool, optional): active records only? Defaults to True.

        Returns:
          obj: creation
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', creation_id),
            ('active', 'in', (True, active))
        ])
        return result[0] or None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_artist(cls, artist_id, active=True):
        """
        Searches creations by artist id

        Args:
          artist_id (int): artist.id
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creations
          None: if no match is found
        """
        result = cls.get().search([
            ('artist', '=', artist_id),
            ('active', 'in', (True, active))
        ])
        return result or None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_contributions_of_artist(cls, artist_id, active=True):
        """
        Searches creations by contributions of artist id

        Args:
          artist_id (int): artist.id
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creations
          None: if no match is found
        """
        result = cls.get().search([
            ('contributions.artist', '=', artist_id),
            ('active', 'in', (True, active))
        ])
        return result or None

    @classmethod
    @Tdb.transaction(readonly=False)
    def delete(cls, creation):
        """
        Deletes creation

        Args:
          creation (list): creations::

            [creation1, creation2, ...]

        Returns:
          ?
        """
        return cls.get().delete(creation)

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates creations

        Args:
          vlist (list): list of dicts with attributes to create creations::

            [
                {
                    'title': str (required)
                    'artist': int artist.id (required)
                    ...2DO
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created creations
          None: if no object was created
        """
        log.debug('create creation:\n{}'.format(vlist))
        for values in vlist:
            if 'title' not in values:
                raise KeyError('title is missing')
            if 'artist' not in values:
                raise KeyError('artist is missing')
        result = cls.get().create(vlist)
        return result or None
