# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Release(Tdb):
    """
    Model wrapper for Tryton model object 'release'
    """

    __name__ = 'release'

    @classmethod
    def current_viewable(cls, request):
        """
        Searches releases, which the current web user is allowed to view.

        Args:
          party_id (int): party.party.id

        Returns:
          list: viewable releases of current web_user
          None: if no match is found
        """
        return cls.search_viewable_by_web_user(request.web_user.id)

    @classmethod
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
    def search_by_code(cls, release_code, active=True):
        """
        Searches an release by release code

        Args:
          release_code (string): release.code

        Returns:
          obj: release
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', release_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_party(cls, party_id, active=True):
        """
        Searches releases by party id

        Args:
          party_id (int): party.party.id

        Returns:
          list: releases of web_user
                and of releases the web user has creations on
          None: if no match is found
        """
        return cls.get().search([
            [
                'OR',
                ('entity_creator', '=', party_id),
                ('tracks.creation.artist.party', '=', party_id)
            ],
            ('active', 'in', (True, active))
        ])

    @classmethod
    def search_viewable_by_web_user(cls, web_user_id, active=True):
        """
        Searches releases, which the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable releases of web_user, empty if none were found
        """
        return cls.get().search([
            [
                'OR',
                [
                    ('acl.web_user', '=', web_user_id),
                    ('acl.roles.permissions.code', '=', 'view_release')
                ], [
                    ('artists.artist.acl.web_user', '=', web_user_id),
                    ('artists.artist.acl.roles.permissions.code',
                        '=', 'view_artist_releases'),
                ]
            ]
        ])

    @classmethod
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
