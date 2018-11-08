# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.models import Tdb
from collecting_society_portal.views import ViewBase

from ..models import Creation
from ..services import _
from .forms import (
    AddCreation,
    EditCreation
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.CreationsResource')
class CreationsViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/creation/list.pt',
        permission='list_creations')
    def list(self):
        return {}

    @view_config(
        name='add',
        renderer='../templates/creation/add.pt',
        permission='add_creation')
    def add(self):
        self.register_form(AddCreation)
        return self.process_forms()


@view_defaults(
    context='..resources.CreationResource')
class CreationViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/creation/show.pt',
        permission='view_creation')
    def show(self):
        # artist_id = self.request.subpath[-1]
        # _creation = Creation.search_by_id(artist_id)
        # _contributions = sorted(
        #     _creation.contributions,
        #     key=lambda contribution: contribution.type
        # )
        return {}

    @view_config(
        name='edit',
        renderer='../templates/creation/edit.pt',
        permission='edit_creation')
    def edit(self):
        self.register_form(EditCreation)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False),
        permission='delete_creation')
    def delete(self):
        title = self.context.creation.title
        artist = self.context.creation.artist.name
        Creation.delete([self.context.creation])
        log.info("creation delete successful for %s (%s): %s (%s)" % (
            self.request.web_user, title, artist, self.context.code
        ))
        self.request.session.flash(
            _(u"Creation deleted: ${crct} (${crco})",
              mapping={'crct': title,
                       'crco': self.context.code}),
            'main-alert-success'
        )
        return self.redirect('..')
