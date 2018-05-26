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
from ..resources import ArtistResource
from .forms import (
    AddArtist,
    EditArtist,
    SearchArtistMember,
    CreateArtistMember,
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.ArtistResource',
    permission='read')
class ArtistViews(ViewBase):

    @view_config(
        name='')
    def root(self):
        return self.redirect(ArtistResource, 'list')

    @view_config(
        name='list',
        renderer='../templates/artist/list.pt',
        decorator=Tdb.transaction(readonly=True))
    def list(self):
        web_user = WebUser.current_web_user(self.request)
        _party_id = web_user.party.id
        return {
            'artists': Artist.search_solo_artists_by_party(_party_id)
        }

    @view_config(
        name='show',
        renderer='../templates/artist/show.pt',
        decorator=Tdb.transaction(readonly=True))
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
        decorator=Tdb.transaction(readonly=False))
    def add(self):
        self.register_form(AddArtist)
        return self.process_forms()

    @view_config(
        name='edit',
        renderer='../templates/artist/edit.pt',
        decorator=Tdb.transaction(readonly=False))
    def edit(self):
        self.register_form(EditArtist)
        return self.process_forms()

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False))
    def delete(self):
        email = self.request.unauthenticated_userid

        _code = self.request.subpath[0]
        if _code is None:
            self.request.session.flash(
                _(u"Could not delete artist - code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')

        artist = Artist.search_by_code(_code)
        if artist is None:
            self.request.session.flash(
                _(u"Could not delete artist - artist not found"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')

        _name = artist.name
        Artist.delete([artist])
        log.info("artist delete successful for %s: %s (%s)" % (
            email, _name, _code
        ))
        self.request.session.flash(
            _(u"Artist deleted: ") + _name + ' (' + _code + ')',
            'main-alert-success'
        )
        return self.redirect(ArtistResource, 'list')

    @view_config(
        name='addmember',
        renderer='../templates/artist/add_member.pt',
        decorator=Tdb.transaction(readonly=False))
    def addmember(self):
        # get group
        _group_code = self.request.subpath[0]
        if not _group_code:
            return self.redirect(ArtistResource, 'list')
        self.context.group = Artist.search_by_code(self.request.subpath[0])
        # register forms
        self.register_form(SearchArtistMember)
        self.register_form(CreateArtistMember)
        # return response
        return self.process_forms()

    @view_config(
        name='removemember',
        decorator=Tdb.transaction(readonly=False))
    def removemember(self):
        _group_code = self.request.subpath[0]
        if _group_code is None:
            self.request.session.flash(
                _(u"Could not remove member artist - group code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')
        _member_code = self.request.subpath[1]
        if _member_code is None:
            self.request.session.flash(
                _(u"Could not remove member artist - member code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')
        group = Artist.search_by_code(_group_code)
        if not group:
            self.request.session.flash(
                _(u"Could not remove member artist - group artist not found"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')
        member = Artist.search_by_code(_member_code)
        if not member:
            self.request.session.flash(
                _(u"Could not remove member artist - member artist not found"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')
        if not member.id in group.solo_artists:
            self.request.session.flash(
                _(u"Could not remove member artist - artist is not a member"),
                'main-alert-warning'
            )
            return self.redirect(ArtistResource, 'list')

        group.solo_artists = [('remove', member.id)]
        group.save()

        log.info("member artist successful added to %s: %s" % (group, member))
        self.request.session.flash(
            _(u"Artist member added: ") + member.name + " (" + member.code + ")",
            'main-alert-success'
        )
        
        return self.redirect(ArtistResource, 'show', _group)

