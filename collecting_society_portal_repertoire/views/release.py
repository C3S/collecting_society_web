# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.creative

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
from ..models import (
    Artist,
    Creation,
    Release
)
from ..services import _
from ..resources import ReleaseResource
from .forms import AddRelease

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ReleaseResource',
    permission='read')
class ReleaseViews(ViewBase):

    @view_config(
        name='')
    def root(self):
        return self.redirect(ReleaseResource, 'list')

    @view_config(
        name='list',
        renderer='../templates/release/list.pt',
        decorator=Tdb.transaction(readonly=True))
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
        name='add',
        renderer='../templates/release/add.pt',
        decorator=Tdb.transaction(readonly=False))
    def add(self):
        self.register_form(AddRelease)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False))
    def delete(self):
        email = self.request.unauthenticated_userid

        _id = self.request.subpath[0]
        if _id is None:
            self.request.session.flash(
                _(u"Could not delete release - id is missing"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')

        release = Release.search_by_id(_id)
        if release is None:
            self.request.session.flash(
                _(u"Could not delete release - artist not found"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')

        _title, _code = release.title, str(release.id)
        Release.delete([release])
        log.info("release delete successful for %s: %s (%s)" % (
            email, _title, _code
        ))
        self.request.session.flash(
            _(u"Artist deleted: ") + _title + ' (' + _code + ')',
            'main-alert-success'
        )
        return self.redirect(ReleaseResource, 'list')
