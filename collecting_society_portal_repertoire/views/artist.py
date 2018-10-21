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
from ..models import (
    Artist,
    Creation
)
from ..services import _
from ..resources import (
    ArtistResource,
    EditArtistResource
)
from .forms import (
    AddArtist,
    EditArtist
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ArtistResource')
class ArtistViews(ViewBase):

    @view_config(
        name='',
        permission='artist_root')
    def root(self):
        return self.redirect(ArtistResource, 'list')

    @view_config(
        name='list',
        renderer='../templates/artist/list.pt',
        permission='list_aritsts')
    def list(self):
        web_user = WebUser.current_web_user(self.request)
        _party_id = web_user.party.id
        return {
            'artists': Artist.search_solo_artists_by_party(_party_id)
        }

    @view_config(
        name='show',
        renderer='../templates/artist/show.pt',
        permission='show_artist')
    def show(self):
        artist_code = self.request.subpath[-1]
        _artist = Artist.search_by_code(artist_code)
        if _artist is None:
            return None
        _creations = Creation.search_by_artist(_artist.id)
        _contributions = Creation.search_by_contributions_of_artist(_artist.id)
        return {
            'artist': _artist,
            'creations': _creations,
            'contributions': _contributions
        }

    @view_config(
        name='add',
        renderer='../templates/artist/add.pt',
        permission='add_artist')
    def add(self):
        self.register_form(AddArtist)
        return self.process_forms()

    @view_config(
        name='',
        context=EditArtistResource,
        renderer='../templates/artist/edit.pt',
        permission='edit_artist')
    def edit(self):
        self.register_form(EditArtist)
        return self.process_forms({
            'artist': self.context.artist
        })

    @view_config(
        name='delete',
        permission='delete_artist')
    def delete(self):
        email = self.request.unauthenticated_userid

        code = self.request.subpath[0]
        if code is None:
            self.request.session.flash(
                _(u"Could not delete artist - code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')

        artist = Artist.search_by_code(code)
        if artist is None:
            self.request.session.flash(
                _(u"Could not delete artist - artist not found"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')

        name = artist.name
        Artist.delete([artist])
        log.info("artist delete successful for %s: %s (%s)" % (
            email, name, code
        ))
        self.request.session.flash(
            _(u"Artist deleted: ") + name + ' (' + code + ')',
            'main-alert-success'
        )
        return self.redirect(ArtistResource, 'list')
