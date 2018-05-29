# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Artist(Tdb):
    """
    Model wrapper for Tryton model object 'artist'
    """

    __name__ = 'artist'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls, active=True):
        """
        Fetches all Artists

        Returns:
          list: artist
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all_solo_artists(cls, active=True):
        """
        Fetches all solo artists

        Args:
          active (bool): only active artists?

        Returns:
          list: all solo artists
          None: if no match is found
        """
        return cls.get().search([
            ('group', '=', False),
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_party(cls, party_id, active=True):
        """
        Searches artists by party id

        Args:
          party_id (int): party.party.id

        Returns:
          list: artists of web_user
          None: if no match is found
        """
        return cls.get().search([
            [
                'OR',
                ('party', '=', party_id),
                ('solo_artists.party', '=', party_id)
            ],
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_solo_artists_by_party(cls, party_id, active=True):
        """
        Searches solo artists by party id

        Args:
          party_id (int): party.party.id

        Returns:
          list: solo artists of web_user
          None: if no match is found
        """
        return cls.get().search([
            ('party', '=', party_id),
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_group_artists_by_party(cls, party_id, active=True):
        """
        Searches group artists by party id

        Args:
          party_id (int): party.party.id

        Returns:
          list: group artists of web_user
          None: if no match is found
        """
        return cls.get().search([
            ('solo_artists.party', '=', party_id),
            ('active', 'in', (True, active))
        ])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_id(cls, artist_id, active=True):
        """
        Searches an artist by artist id

        Args:
          artist_id (int): artist.id

        Returns:
          obj: artist
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', artist_id),
            ('active', 'in', (True, active))
        ])
        return result[0] or None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_code(cls, artist_code, active=True):
        """
        Searches an artist by artist code

        Args:
          artist_code (int): artist.code

        Returns:
          obj: artist
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', artist_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    @Tdb.transaction(readonly=False)
    def delete(cls, artist):
        """
        Deletes artist

        Args:
          artist (list): artists::

            [artist1, artist2, ...]

        Returns:
          ?
        """
        return cls.get().delete(artist)

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates artists

        Args:
          vlist (list): list of dicts with attributes to create artists::

            [
                {
                    'party': party.party (required)
                    'group': bool (required)
                    'name': str (required),
                    'description': str,
                    'picture_data': Binary,
                    'picture_data_mime_type': str
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created artists
          None: if no object was created
        """
        log.debug('create artists:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
        result = cls.get().create(vlist)
        return result or None
