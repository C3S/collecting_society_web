# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.models import Tdb
from collecting_society_portal.views import ViewBase

from ..services import _
from ..models import Artist
from .forms import (
    AddArtist,
    EditArtist
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ArtistsResource')
class ArtistsViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/artist/list.pt',
        permission='list_artists')
    def list(self):
        return {}

    @view_config(
        name='add',
        renderer='../templates/artist/add.pt',
        permission='add_artist')
    def add(self):
        self.register_form(AddArtist)
        return self.process_forms()


@view_defaults(
    context='..resources.ArtistResource')
class ArtistViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/artist/show.pt',
        permission='view_artist')
    def show(self):
        return {}

    @view_config(
        name='edit',
        renderer='../templates/artist/edit.pt',
        permission='edit_artist')
    def edit(self):
        self.register_form(EditArtist)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False),
        permission='delete_artist')
    def delete(self):
        name = self.context.artist.name
        Artist.delete([self.context.artist])
        log.info("artist delete successful for %s: %s (%s)" % (
            self.request.web_user, name, self.context.code
        ))
        self.request.session.flash(
            _(u"Artist deleted: ") + name + ' (' + self.context.code + ')',
            _(u"Artist deleted: ${arna} (${arco})",
              mapping={'arna': name, 'arco': self.context.code}),
            'main-alert-success'
        )
        return self.redirect('..')
