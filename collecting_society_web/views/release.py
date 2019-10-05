# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.models import Tdb
from portal_web.views import ViewBase

from ..models import Release
from ..services import _
from .forms import (
    AddRelease,
    EditRelease
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ReleasesResource')
class ReleasesViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/release/list.pt',
        permission='list_releases')
    def list(self):
        return {}

    @view_config(
        name='add',
        renderer='../templates/release/add.pt',
        permission='add_release')
    def add(self):
        self.register_form(AddRelease)
        return self.process_forms()


@view_defaults(
    context='..resources.ReleaseResource')
class ReleaseViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/release/show.pt',
        permission='view_release')
    def show(self):
        return {}

    @view_config(
        name='edit',
        renderer='../templates/release/edit.pt',
        permission='edit_release')
    def edit(self):
        self.register_form(EditRelease)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False),
        permission='delete_release')
    def delete(self):
        title = self.context.release.title
        Release.delete([self.context.release])
        log.info("release delete successful for %s: %s (%s)" % (
            self.request.web_user, title, self.context.code
        ))
        self.request.session.flash(
            _(u"Release deleted:  ${reti} (${reco})",
              mapping={'reti': title,
                       'reco': self.context.code}),
            'main-alert-success'
        )
        return self.redirect('..')
