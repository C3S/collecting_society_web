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
from ..models import Creation
from ..services import _
from ..resources import CreationResource
from .forms import AddCreation

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.CreationResource',
    permission='read')
class CreationViews(ViewBase):

    @view_config(
        name='')
    def root(self):
        return self.redirect(CreationResource, 'list')

    @view_config(
        name='list',
        renderer='../templates/creation/list.pt',
        decorator=Tdb.transaction(readonly=True))
    def list(self):
        web_user = WebUser.current_web_user(self.request)
        _creations = sorted(
            Creation.search_by_party(web_user.party.id),
            key=lambda creation: creation.artist.name
        )
        return {'creations': _creations}

    @view_config(
        name='show',
        renderer='../templates/creation/show.pt',
        decorator=Tdb.transaction(readonly=True))
    def show(self):
        artist_id = self.request.subpath[-1]
        _creation = Creation.search_by_id(artist_id)
        _contributions = sorted(
            _creation.contributions,
            key=lambda contribution: contribution.type
        )
        return {
            'creation': _creation,
            'contributions': _contributions
        }

    @view_config(
        name='add',
        renderer='../templates/creation/add.pt',
        decorator=Tdb.transaction(readonly=False))
    def add(self):
        self.register_form(AddCreation)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False))
    def delete(self):
        email = self.request.unauthenticated_userid

        _id = self.request.subpath[0]
        if _id is None:
            self.request.session.flash(
                _(u"Could not delete creation - id is missing"),
                'main-alert-warning'
            )
            return self.redirect(CreationResource, 'list')

        creation = Creation.search_by_id(_id)
        if creation is None:
            self.request.session.flash(
                _(u"Could not delete creation - creation not found"),
                'main-alert-warning'
            )
            return self.redirect(CreationResource, 'list')

        _title = creation.title
        _artist = creation.artist.name
        _code = creation.code

        creation.active = False
        creation.save()
        log.info("creation delete successful for %s (%s): %s (%s)" % (
            email, _title, _artist, _code
        ))
        self.request.session.flash(
            _(u"Creation deleted: ") + _title + ' (' + _code + ')',
            'main-alert-success'
        )
        return self.redirect(CreationResource, 'list')
