# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views import ViewBase
from ..models import Release
from ..services import _
from ..resources import ReleaseResource
from .forms import (
    AddRelease,
    EditRelease
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ReleaseResource')
class ReleaseViews(ViewBase):

    @view_config(
        name='',
        permission='release_root')
    def root(self):
        return self.redirect(ReleaseResource, 'list')

    @view_config(
        name='list',
        renderer='../templates/release/list.pt',
        permission='list_releases')
    def list(self):
        web_user = WebUser.current_web_user(self.request)
        _party_id = web_user.party.id
        releases = Release.search_by_party(_party_id)
        log.debug(
            (
                "releases: %s\n"
            ) % (
                releases
            )
        )
        return {
            'releases': releases
        }

    @view_config(
        name='show',
        renderer='../templates/release/show.pt',
        permission='show_release')
    def show(self):
        release_code = self.request.subpath[-1]
        _release = Release.search_by_code(release_code)
        # _genres = _release.genres
        if _release is None:
            return None
        return {
            'release': _release
        }

    @view_config(
        name='add',
        renderer='../templates/release/add.pt',
        permission='add_release')
    def add(self):
        self.register_form(AddRelease)
        return self.process_forms()

    @view_config(
        name='edit',
        renderer='../templates/release/edit.pt',
        permission='edit_release')
    def edit(self):
        # add record to context
        code = self.request.subpath[-1]
        if code is None:
            self.request.session.flash(
                _(u"Could not edit release - code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')
        release = Release.search_by_code(code)
        if release is None:
            self.request.session.flash(
                _(u"Could not edit release - release not found"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')
        self.context.release = release
        # add form
        self.register_form(EditRelease)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False),
        permission='delete_release')
    def delete(self):
        email = self.request.unauthenticated_userid

        _code = self.request.subpath[0]
        if _code is None:
            self.request.session.flash(
                _(u"Could not delete release - code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')

        release = Release.search_by_code(_code)
        if release is None:
            self.request.session.flash(
                _(u"Could not delete release - release not found"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')

        _title, _code = release.title, str(release.id)
        Release.delete([release])
        log.info("release delete successful for %s: %s (%s)" % (
            email, _title, _code
        ))
        self.request.session.flash(
            _(u"Release deleted: ") + _title + ' (' + _code + ')',
            'main-alert-success'
        )
        return self.redirect(ReleaseResource, 'list')
