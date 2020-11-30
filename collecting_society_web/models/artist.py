# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    Party,
    MixinWebuser
)

log = logging.getLogger(__name__)


class Artist(Tdb, MixinWebuser):
    """
    Model wrapper for Tryton model object 'artist'
    """

    __name__ = 'artist'

    @classmethod
    def is_foreign_member(cls, request, group, member):
        """
        Checks if the member is a foreign object and still editable by the
        current webuser.

        Checks, if the member
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          group (obj): Group of the member in the current context
          member (obj): Member to check.

        Returns:
          true: if member is editable.
          false: otherwise.
        """
        # sanity checks
        if member not in group.solo_artists:
            return False
        # 1) is a foreign object
        if member.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if member.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        if not group.permits(request.web_user, 'edit_artist'):
            return False
        # 4) TODO: was not part of a distribution yet
        return True

    @classmethod
    def is_foreign_contributor(cls, request, contribution, artist):
        """
        Checks if the artist is a foreign object and still editable by the
        current webuser.

        Checks, if the member
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          contribution (obj): Contribution of the artist
          artist (obj): Artist to check.

        Returns:
          true: if member is editable.
          false: otherwise.
        """
        # sanity checks
        if artist != contribution.artist:
            return False
        # 1) is a foreign object
        if artist.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if artist.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        if not contribution.creation.permits(
                request.web_user, 'edit_creation'):
            return False
        # 4) TODO: was not part of a distribution yet
        return True
    
    @classmethod
    def is_foreign_rightsholder(cls, request, right, artist):
        """
        Checks if the artist is a foreign object and still editable by the
        current webuser.

        Checks, if the member
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          right (obj): Right object.
          artist (obj): Artist to check.

        Returns:
          true: if member is editable.
          false: otherwise.
        """
        # sanity checks
        if artist != right.rightsholder:
            return False
        # 1) is a foreign object
        if artist.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if artist.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        permission = ""
        if right.__class__.__name__ == "CreationRight":
            permission = "edit_creation"
        if right.__class__.__name__ == "ReleaseRight":
            permission = "edit_release"
        if not permission:
            return False
        if not right.rightsobject.permits(
                request.web_user, permission):
            return False
        # 4) TODO: was not part of a distribution yet
        return True

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches artists by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of artists
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_count(cls, domain, escape=False, active=True):
        """
        Counts artists by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of artists
        """
        # prepare query
        if escape:
            domain = cls.escape(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search_count(domain)
        return result

    @classmethod
    def search_all(cls, active=True):
        """
        Fetches all Artists

        Returns:
          list: artist
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
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
    def search_by_id(cls, artist_id, active=True):
        """
        Searches an artist by artist id

        .. note::

          We don't want our internal ids to be exposed to the world.
          So better use ``search_by_oid()``.

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
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches an artist by oid (public api id)

        Args:
          oid (int): artist.oid

        Returns:
          obj: artist
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
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
    def search_by_name(cls, artist_name, active=True):
        """
        Searches artists by artist name

        Args:
          artist_name (str): artist.name

        Returns:
          obj: list of artists
        """
        result = cls.get().search([
            ('name', '=', artist_name),
            ('active', 'in', (True, active))
        ])
        return result

    @classmethod
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
    def search_fulltext(cls, search_string, active=True):
        """
        Searches artists by fulltext search of
        - code
        - name
        - description

        Args:
          search_string (str): string to search for

        Returns:
          obj: list of artists
        """
        # escape operands
        search_string.replace('_', '\\_')
        search_string.replace('%', '\\_')
        # wrap search string
        search_string = "%" + search_string + "%"
        # search
        result = cls.get().search([
            [
                'OR',
                ('code', 'ilike', search_string),
                ('name', 'ilike', search_string),
                ('description', 'ilike', search_string)
            ],
            ('active', 'in', (True, active))
        ])
        return result

    @classmethod
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

    @classmethod
    def create_foreign(cls, party, name, email, group=False):
        """
        Creates foreign Artist

        Args:
            party: the Party that wants to create the foreign objects
            name: the artist name of the foreign artist object
            email: the artist email of the foreign artist object

        Returns:
            Artist object: the artist that has been created
            None: if no object was created
        """
        assert(name)
        assert(email)
        artist_party = Party.create([{
            'name': name,
            'contact_mechanisms': [(
                'create', [{
                    'type': 'email',
                    'value': email
                    }]
                )]
            }])
        artist = Artist.create([{
            'group': group,
            'name': name,
            'party': artist_party.id,
            'entity_creator': party.id,
            'entity_origin': 'indirect',
            'claim_state': 'unclaimed',
            }])
        if not artist:
            return None
        return artist[0]
