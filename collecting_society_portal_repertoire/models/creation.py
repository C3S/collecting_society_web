# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Creation(Tdb):
    """
    Model wrapper for Tryton model object 'creation'
    """

    __name__ = 'creation'

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
          oid (int): creation.oid

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
