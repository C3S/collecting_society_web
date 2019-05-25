# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from collecting_society_portal.models import (
    Tdb,
    WebUser
)

log = logging.getLogger(__name__)


class Content(Tdb):
    """
    Model wrapper for Tryton model object 'web.user'.
    """

    __name__ = 'content'

    @classmethod
    def current_viewable(cls, request):
        """
        Searches content, which the current web_user is allowed to view.

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: viewable content of web_user
          None: if no match is found
        """
        return cls.search_viewable_by_web_user(request.web_user.id)

    @classmethod
    def current_orphans(cls, request, category='all'):
        """
        Searches orphan content in category of current web user.

        Args:
            request (pyramid.request.Request): Current request.
            category (str): optional - Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        party = WebUser.current_web_user(request).party
        return cls.search_orphans(party.id, category)

    @classmethod
    def current_rejects(cls, request, reason, category='all'):
        """
        Searches rejected content
        (optionally in category) of current web user.

        Args:
            request (pyramid.request.Request): Current request.
            reason (str): Reason for rejected content.
            category (str): optional - Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        party = WebUser.current_web_user(request).party
        return cls.search_rejects(party.id, reason, category)

    @classmethod
    def current_uncommits(cls, request, category='all'):
        """
        Searches uncommited content
        (optionally in category) of current web user.

        Args:
            request (pyramid.request.Request): Current request.
            category (str): optional - Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        party = WebUser.current_web_user(request).party
        return cls.search_uncommits(party.id, category)

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches content entries by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of content entries
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
        Counts content entries by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of content entries
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
    def search_all(cls):
        """
        Gets all content.

        Returns:
            list (obj[content]): List of content.
            None: if no match is found.
        """
        return cls.get().search([('active', '=', True)])

    @classmethod
    def search_by_id(cls, uid):
        """
        Searches a content by id.

        Args:
            uid (string): Id of the content.

        Returns:
            obj (content): Content.
            None: If no match is found.
        """
        if uid is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('id', '=', uid)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a content by oid (public api id)

        Args:
          oid (int): content.oid

        Returns:
          obj: content
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
    def search_by_code(cls, content_code, active=True):
        """
        Searches a content by content code

        Args:
          content_code (int): content.code

        Returns:
          obj: content
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', content_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a content by name.

        Args:
            name (str): Name of the content.

        Returns:
            list (content): List of content.
        """
        if name is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('name', '=', name)
        ])
        return result

    @classmethod
    def search_by_uuid(cls, uuid):
        """
        Searches a content by uuid.

        Args:
            uuid (str): Uuid of the content.

        Returns:
            obj (content): Content.
            None: If no match is found.
        """
        if uuid is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('uuid', '=', uuid)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_archive(cls, archive):
        """
        Searches a content by archive.

        Args:
            archive (int): Id of the archive.

        Returns:
            list (content): List of content.
        """
        if archive is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('archive', '=', archive)
        ])
        return result

    @classmethod
    def search_by_party(cls, party_id):
        """
        Searches a content by party id.

        Args:
            party_id (int): Id of the party.

        Returns:
            list (content): List of content.
        """
        if party_id is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('entity_creator', '=', party_id)
        ])
        return result

    @classmethod
    def search_by_web_user(cls, web_user_id):
        """
        Searches a content by web user id.

        Args:
            web_user_id (int): Id of the user.

        Returns:
            list (content): List of content.
        """
        if web_user_id is None:
            return None
        web_user = WebUser.search_by_id(web_user_id)
        if web_user is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('entity_creator', '=', web_user.party.id)
        ])
        return result

    @classmethod
    def search_by_creation(cls, creation_id):
        """
        Searches a content by creation id.

        Args:
            creation_id (int): Id of the creation.

        Returns:
            obj (content): Content.
            None: If no match is found.
        """
        if creation_id is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('creation', '=', creation_id)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_creation_and_category(cls, creation_id, category):
        """
        Searches a content by creation id and content category.

        Args:
            creation_id (int): Id of the creation.
            category (strint): e.g. 'audio' oder 'sheet'

        Returns:
            obj (content): Content.
            None: If no match is found.
        """
        if creation_id is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('creation', '=', creation_id),
            ('category', '=', category)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_extension(cls, extension):
        """
        Searches a content by extension.

        Args:
            extension (str): Extension of the content.

        Returns:
            list (content): List of content.
        """
        if extension is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('extension', '=', extension)
        ])
        return result

    @classmethod
    def search_by_mime_type(cls, mime_type):
        """
        Searches a content by mime type.

        Args:
            mime_type (str): Mime type of the content.

        Returns:
            list (content): List of content.
        """
        if mime_type is None:
            return None
        result = cls.get().search([
            ('active', '=', True),
            ('mime_type', '=', mime_type)
        ])
        return result

    @classmethod
    def search_viewable_by_web_user(cls, web_user_id, active=True):
        """
        Searches artists, which the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable artists of web_user, empty if none were found
        """
        return cls.get().search([
            [
                'OR',
                [
                    ('acl.web_user', '=', web_user_id),
                    ('acl.roles.permissions.code', '=', 'view_content')
                ], [
                    ('creation.artist.acl.web_user', '=', web_user_id),
                    ('creation.artist.acl.roles.permissions.code',
                        '=', 'view_artist_content'),
                ]
            ]
        ])

    @classmethod
    def search_unprocessed(cls, party_id, category):
        """
        Searches unprocessed content in category of web user.

        Args:
            cls (pyramid.request.Request): Current request.
            party_id (int): Res user id.
            category (str): Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        if party_id is None:
            return None
        search_clause = [
            ('active', '=', True),
            ('entity_creator', '=', party_id),
            ('creation', '=', None),
            ('processing_state', '!=', 'rejected'),
            ('processing_state', '!=', 'dropped'),
            ('processing_state', '!=', 'archived')
        ]
        if category is not 'all':
            search_clause.append(
                ('category', '=', category)
            )
        result = cls.get().search(search_clause)
        return result or None

    @classmethod
    def search_orphans(cls, party_id, category):
        """
        Searches orphan content in category of web user.

        Args:
            cls (pyramid.request.Request): Current request.
            party_id (int): Res user id.
            category (str): Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        if party_id is None:
            return None
        search_clause = [
            ('active', '=', True),
            ('entity_creator', '=', party_id),
            ('creation', '=', None),
            [
                'OR',
                ('processing_state', '=', 'archived'),
                ('processing_state', '=', 'dropped')
            ]
        ]
        if category is not 'all':
            search_clause.append(
                ('category', '=', category)
            )
        result = cls.get().search(search_clause)
        return result or None

    @classmethod
    def search_rejects(cls, party_id, reason, category):
        """
        Searches duplicate content of current user.

        Args:
            cls (pyramid.request.Request): Current request.
            party_id (int): Res user id.
            reason (str): Reason for rejected content.
            category (str): Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        search_clause = [
                ('active', '=', True),
                ('entity_creator', '=', party_id),
                ('processing_state', '=', 'rejected')
            ]
        if reason is 'dupl':
            search_clause.append(
                ('duplicate_of', '!=', None)
            )
        if reason is 'ferror':
            search_clause.append(
                ('rejection_reason', '=', 'format_error')
            )
        if reason is 'lossyc':
            search_clause.append(
                ('rejection_reason', '=', 'lossy_compression')
            )
        if category is not 'all':
            search_clause.append(
                ('category', '=', category)
            )
        result = cls.get().search(search_clause)
        return result or None

    @classmethod
    def search_uncommits(cls, party_id, category):
        """
        Searches uncommited content of current user.

        Args:
            cls (pyramid.request.Request): Current request.
            party_id (int): Res user id.
            category (str): Category of content.

        Returns:
            list (content): List of content.
            None: If no match is found.
        """
        search_clause = [
                ('active', '=', True),
                ('entity_creator', '=', party_id),
                ('commit_state', '=', 'uncommited'),
                ('processing_state', '!=', 'rejected')
            ]
        if category is not 'all':
            search_clause.append(
                ('category', '=', category)
            )
        result = cls.get().search(search_clause)
        return result or None

    @classmethod
    def delete(cls, content):
        """
        Deletes content

        Args:
          content (list): contents::

            [content1, content2, ...]

        Returns:
          ?
        """
        return cls.get().delete(content)

    @classmethod
    def create(cls, vlist):
        """
        Creates content.

        Args:
            vlist (list): List of dictionaries with attributes of a content.
                [
                    {
                        'active': bool,
                        'uuid': str (required),
                        'name': str (required),
                        'size': int,
                        'path': str,
                        'preview_path': str,
                        'mime_type': str,
                        'mediation': bool,
                        'duplicate_of': int,
                        'duplicates': list,
                        'entity_origin': str (required),
                        'entity_creator': str (required),
                        'user_committed_state': bool,
                        'fingerprintlogs': list,
                        'checksums': list,
                        'archive': int,
                        'category': str (required),
                        'creation': int,
                        'processing_state': str,
                        'processing_hostname': str,
                        'rejection_reason': str,
                        'length': float,
                        'channels': int,
                        'sample_rate': int,
                        'sample_width': int
                    },
                    {
                        ...
                    }
                ]

        Returns:
            list (obj[content]): List of created content.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
        """
        for values in vlist:
            if 'processing_state' not in values:
                raise KeyError('processing_state is missing')
            if 'name' not in values:
                raise KeyError('name is missing')
            if 'uuid' not in values:
                raise KeyError('uuid is missing')
            if 'entity_origin' not in values:
                raise KeyError('entity_origin is missing')
            if 'entity_creator' not in values:
                raise KeyError('entity_creator is missing')
            if 'category' not in values:
                raise KeyError('category is missing')
        log.debug('create content:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None
