# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden

from portal_web.models import Tdb
from portal_web.views.forms import FormController

from .datatables import CreationSequence
from ...services import _
from ...resources import DeclarationsResource
from ...models import (
    ArtistPlaylist,
    ArtistPlaylistItem,
    Creation,
)

log = logging.getLogger(__name__)


class FinalizeDeclarationLive(FormController):
    """
    form controller for finalization of declarations
    """

    def controller(self):
        self.form = live_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.finalize_declaration()
        else:
            self.load_declaration()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def load_declaration(self):
        # shortcuts
        web_user = self.request.web_user
        declaration = self.context.declaration
        event = declaration.context
        performances = event.performances

        # set appstruct
        self.appstruct['playlists'] = {}
        for performance in performances:
            self.appstruct['playlists'][performance.oid] = []
            if not performance.playlist or not performance.playlist.items:
                continue
            for item in performance.playlist.items:
                creation = item.creation
                self.appstruct['playlists'][performance.oid].append({
                    'mode':
                        Creation.is_foreign_editable(web_user, creation)
                        and 'edit' or 'add',
                    'oid': item.oid,
                    'artist': creation.artist.name,
                    'code': creation.code,
                    'titlefield': creation.title,
                })

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def finalize_declaration(self):
        # tryton models
        __ArtistPlaylist = ArtistPlaylist.get()
        __ArtistPlaylistItem = ArtistPlaylistItem.get()

        # shortcuts: objects
        web_user = self.request.web_user
        declaration = self.context.declaration
        utilisation = declaration.utilisations[0]
        event = declaration.context
        performances = event.performances

        # shortcuts: appstruct
        _playlists = self.appstruct['playlists']

        # sanity check: action
        if not self.submitted('save') and not self.submitted('finalize'):
            raise HTTPBadRequest

        # sanity check: performance oids in request same as in db
        request_oids = set(_playlists.keys())
        db_oids = {performance.oid for performance in performances}
        if not request_oids == db_oids:
            raise HTTPBadRequest

        # playlists
        for _performance_oid, _playlist in _playlists.items():
            # find corresponding performance db entry
            performance = False
            for item in performances:
                if item.oid == _performance_oid:
                    performance = item
                    break

            # playlist: get
            playlist = performance.playlist

            # playlist: create
            if not playlist:
                performance, = performance.browse([performance.id])
                performance.playlist = __ArtistPlaylist(
                    artist=performance.artist,
                    public=False,
                    entity_origin='direct',
                    entity_creator=web_user.party
                )
                performance.save()
                playlist = performance.playlist

            # playlist items: save
            playlist_items = []
            for index, _playlist_item in enumerate(_playlist):
                # find corresponding playlist item db entry
                playlist_item = False
                for item in playlist.items:
                    if item.oid == _playlist_item['oid']:
                        playlist_item = item
                        break

                # playlist item: add
                creation_code = _playlist_item['code']
                if playlist_item:

                    # creation: edit
                    if _playlist_item['mode'] == 'edit':
                        creation = Creation.search_by_code(creation_code)
                        if not Creation.is_foreign_editable(
                                web_user, creation):
                            raise HTTPForbidden
                        creation.title = _playlist_item['titlefield']
                        creation.artist.name = _playlist_item['artist']
                        creation.artist.save()
                        creation.save()

                    # playlist item: add
                    playlist_items.append(item)

                # playlist item: create
                else:

                    # creation: add
                    if _playlist_item['mode'] == 'add':
                        creation = Creation.search_by_code(creation_code)
                        if not creation:
                            raise HTTPBadRequest

                    # creation: create
                    elif _playlist_item['mode'] == 'create':
                        creation = Creation.create_foreign(
                            party=web_user.party,
                            artist_name=_playlist_item['artist'],
                            title=_playlist_item['titlefield'],
                        )

                    # playlist item: create
                    playlist_item = __ArtistPlaylistItem(
                        playlist=playlist,
                        creation=creation,
                        position=index,
                        entity_origin='direct',
                        entity_creator=web_user.party
                    )
                    playlist_items.append(playlist_item)

            # playlist items: position
            for index, playlist_item in enumerate(playlist_items):
                playlist_item.position = index
                playlist_item.save()

            # playlist items: delete
            _request_oids = [_item['oid'] for _item in _playlist]
            playlist_items_to_delete = [
                item for item in playlist.items
                if item.oid not in _request_oids
            ]
            ArtistPlaylistItem.delete(playlist_items_to_delete)

            # playlist: save
            playlist, = playlist.browse([playlist.id])  # refresh needed
            playlist.items = playlist_items
            playlist.save()

        # action: finalize
        if self.submitted('finalize'):
            utilisation.state = 'finalized'
            utilisation.save()

            # user feedback
            log.info("declaration finalize successful for %s: %s" % (
                web_user, declaration))
            self.request.session.flash(
                _(u"Declaration finalized."),
                'main-alert-success'
            )

        # action: save
        else:
            # user feedback
            log.info("declaration save successful for %s: %s" % (
                web_user, declaration))
            self.request.session.flash(
                _(u"Declaration saved."),
                'main-alert-success'
            )

        # redirect
        self.redirect(DeclarationsResource, declaration.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

@colander.deferred
def deferred_playlist_schema_node(node, kw):
    schema = colander.SchemaNode(
        colander.Mapping(),
        title=_("Playlists"),
        oid="playlists",
        name="playlists",
        widget=deform.widget.MappingWidget(template='navs/mapping'),
        description=_("Please add the playlists for the performances.")
    )
    performances = kw['request'].context.declaration.context.performances
    for performance in performances:
        schema.add(
            CreationSequence(
                title=performance.artist.name,
                oid=performance.oid,
                name=performance.oid,
                orderable=1,
                pin_active=True
            ).bind(request=kw['request']),
        )
    return schema


# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

class LiveSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    playlists = deferred_playlist_schema_node


# --- Forms -------------------------------------------------------------------

def live_form(request):
    return deform.Form(
        schema=LiveSchema().bind(request=request),
        buttons=[
            deform.Button('save', _("Save")),
            deform.Button('finalize', _("Finalize")),
        ]
    )
