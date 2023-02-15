# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from . import Artist

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Creation(Tdb):
    """
    Model wrapper for Tryton model object 'creation'
    """

    __name__ = 'creation'

    @classmethod
    def is_foreign_original(cls, request, derivative, original):
        """
        Checks if the original is a foreign object and still editable by the
        current webuser.

        Checks, if the original
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          derivative (obj): Derived creation.
          original (obj): Original creation.

        Returns:
          true: if orignal is foreign and editable.
          false: otherwise.
        """
        # sanity checks
        log.debug(derivative.original_relations)
        if original.id not in [r.id for r in derivative.original_relations]:
            return False
        # 1) is a foreign object
        if original.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if original.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        if not derivative.permits(request.web_user, 'edit_creation'):
            return False
        # 4) TODO: was not part of a distribution yet
        return True

    @classmethod
    def is_foreign_track(cls, web_user, release, creation):
        """
        Checks if the track is a foreign object and still editable by the
        current webuser.

        Checks, if the creation
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          release (obj): Release of track.
          creation (obj): Track creation of release.

        Returns:
          true: if orignal is foreign and editable.
          false: otherwise.
        """
        # sanity check: is it part of the release?
        included = False
        for release_track in release.tracks:
            if creation == release_track.creation:
                included = True
        if not included:
            return False

        return Creation.is_foreign_creation(web_user, creation)

    @classmethod
    def is_foreign_creation(cls, web_user, creation):
        """
        Checks if the creation is a foreign object and still editable by the
        current webuser.

        Checks, if the creation
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          request (pyramid.request.Request): Current request.
          release (obj): Release of track.
          track (obj): Track creation of release.

        Returns:
          true: if orignal is foreign and editable.
          false: otherwise.
        """
        # sanity checks
        # TODO
        # 1) is a foreign object
        if creation.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if creation.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        if not creation.permits(web_user, 'edit_creation'):
            return False
        # 4) TODO: was not part of a distribution yet
        return True

    @classmethod
    def current_viewable(cls, request):
        """
        Searches creations, which the current web_user is allowed to view.

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: viewable creations of current web_user
          None: if no match is found
        """
        return cls.search_viewable_by_web_user(request.web_user.id)

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches creations by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of creations
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
        Counts creations by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of creations
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
        Fetches all Creations

        Args:
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creation
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    def search_by_id(cls, creation_id, active=True):
        """
        Searches a creation by creation id

        .. note::

          We don't want our internal ids to be exposed to the world.
          So better use ``search_by_oid()``.

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
    def search_by_oid(cls, oid, active=True):
        """
        Searches a creation by oid (public api id)

        Args:
          oid (uuid): creation.oid

        Returns:
          obj: creation
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
    def search_by_code(cls, creation_code, active=True):
        """
        Searches a creation by artist code

        Args:
          creation_code (int): creation.code

        Returns:
          obj: creation
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', creation_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
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
                ('entity_creator', '=', party_id),
                ('artist.party', '=', party_id),
                ('contributions.artist.party', '=', party_id),
                ('contributions.artist.solo_artists.party', '=', party_id),
                ('contributions.artist.group_artists.party', '=', party_id)
            ],
            ('active', 'in', (True, active))
        ])

    @classmethod
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
    def search_by_artistname_and_title(cls, artist_name, title, active=True):
        """
        Searches creations by artist name and title

        Args:
          artist_name (char): artist.name
          title (char): creation.title
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: creations
          None: if no match is found
        """
        result = cls.get().search([
            ('artist.name', '=', artist_name),
            ('title', '=', title),
            ('active', 'in', (True, active))
        ])
        return result or None

    @classmethod
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
    def search_viewable_by_web_user(cls, web_user_id, active=True):
        """
        Searches creations, which the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable creations of web_user, empty if none were found
        """
        return cls.get().search([
            [
                'OR',
                [
                    ('acl.web_user', '=', web_user_id),
                    ('acl.roles.permissions.code', '=', 'view_creations')
                ], [
                    ('artist.acl.web_user', '=', web_user_id),
                    ('artist.acl.roles.permissions.code',
                        '=', 'view_artist_creations'),
                ]
            ]
        ])

    @classmethod
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
            # TODO: if commited, also check if there is at least one valid
            #       title in ReleaseCreation. if not: dashboard warning
            if 'artist' not in values:
                raise KeyError('artist is missing')
        result = cls.get().create(vlist)
        return result or None

    @classmethod
    def create_foreign(cls, party, artist_name, title):
        """
        Creates foreign Artist(!) and Creaion

        Args:
            party: the Party that wants to create the foreign objects
            artist_name: the artist name of the foreign artist object
            title: the original title of the foreign creation object

        Returns:
            Creation object: the creation that has been creation
            None: if no object was created
        """
        artist = Artist.create([{
            'name': artist_name,
            'entity_origin': 'indirect',
            'entity_creator': party.id
            }])
        if not artist:
            return None
        creation = Creation.create([{
            'title': title,
            'artist': artist[0].id,
            'entity_origin': 'indirect',
            'entity_creator': party.id
            }])
        if not creation:
            return None
        return creation[0]
