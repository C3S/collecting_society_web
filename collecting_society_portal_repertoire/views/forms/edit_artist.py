# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
from pkg_resources import resource_filename
import logging

from pyramid.threadlocal import get_current_request
from pyramid.i18n import get_localizer

from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)
from ...services import _
from ...models import Artist
from ...resources import ArtistResource
from .add_artist_solo import add_artist_solo_form
from .add_artist_group import add_artist_group_form

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditArtist(FormController):
    """
    form controller for edit of artists
    """

    def controller(self):

        # get artist
        code = self.request.subpath[0]
        artist = Artist.search_by_code(code)
        if not artist:
            self.request.session.flash(
                _(u"Could not edit artist - artist not found"),
                'main-alert-warning'
            )
            self.redirect(ArtistResource, 'list')
            return self.response

        # choose form
        if artist.group:
            self.form = add_artist_group_form(
                self.request, title=_(u"Edit Group Artist"))
        else:
            self.form = add_artist_solo_form(
                self.request, title=_(u"Edit Solo Artist"))

        # process form
        if self.submitted() and self.validate():
            self.edit_artist(artist)
        else: 
            self.appstruct['metadata'] = {
                'name': artist.name,
                'description': artist.description
                # 'picture': {
                #     '': _artist.picture_data,
                #     'mimetype': _artist.picture_data_mime_type
                # }
            }
            if artist.group:
                self.appstruct['members'] = {'members': []}
                for solo_artist in artist.solo_artists:
                    self.appstruct['members']['members'].append(solo_artist.id)
            self.render(self.appstruct)

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def edit_artist(self, artist):
        email = self.request.unauthenticated_userid
        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )

        if artist.name != self.appstruct['metadata']['name']:
            artist.name = self.appstruct['metadata']['name']
        if artist.description != self.appstruct['metadata']['description']:
            artist.description = self.appstruct['metadata']['description']
        if artist.group:
            artist.solo_artists = self.appstruct['members']['members']   
        artist.save()

        log.info("edit add successful for %s: %s" % (email, artist))
        self.request.session.flash(
            _(u"Artist edited: ") + artist.name + " (" + artist.code + ")",
            'main-alert-success'
        )

        self.redirect(ArtistResource, 'show/' + artist.code)

# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------
