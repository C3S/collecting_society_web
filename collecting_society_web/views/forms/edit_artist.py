# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import Tdb
from portal_web.views.forms import FormController
from ...services import (_, picture_processing)
from ...models import Artist
from .add_artist import AddArtistSchema

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditArtist(FormController):
    """
    form controller for edit of artists
    """

    def controller(self):
        self.form = edit_artist_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_artist()
        else:
            self.edit_artist()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_artist(self):
        # shortcuts
        artist = self.context.artist

        # set appstruct
        self.appstruct = {
            'group': artist.group,
            'name': artist.name,
            'ipn_code': artist.get_id_code('IPN') or '',
            'description': artist.description or ''
        }

        # members
        if artist.group:
            _members = []
            for member in artist.solo_artists:
                mode = "add"
                email = ""
                if Artist.is_foreign_editable(self.request.web_user, member):
                    mode = "edit"
                    email = member.party.email
                _members.append({
                    'mode': mode,
                    'oid': member.oid,
                    'name': member.name,
                    'code': member.code,
                    'description': member.description or '',
                    'email': email
                })
            self.appstruct['members'] = _members

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_artist(self):

        # --- shortcuts -------------------------------------------------------

        # shortcuts: objects
        web_user = self.request.web_user
        party = web_user.party
        artist = self.context.artist

        # shortcuts: appstruct
        _group = self.appstruct['group']
        _name = self.appstruct['name']
        _ipn_code = self.appstruct['ipn_code']
        _description = self.appstruct['description'] or ''
        _picture = self.appstruct['picture']
        _members = self.appstruct['members']

        # --- ids -------------------------------------------------------------

        # ipn code
        artist.set_id_code('IPN', _ipn_code)

        # --- group -----------------------------------------------------------

        # group
        if artist.group != _group:
            # if group status has changed
            if artist.group:
                # remove solo artists from current group artist
                artist.solo_artists = []
            else:
                # remove current solo artist from group artists
                artist.group_artists = []

        # --- picture ---------------------------------------------------------

        # picture
        if _picture:
            error, picture, thumb, mime = picture_processing(_picture['fp'])
            if error:
                self.request.session.flash(error, 'main-alert-warning')
            else:
                artist.picture_data = picture
                artist.picture_thumbnail_data = thumb
                artist.picture_data_mime_type = mime

        # --- members ---------------------------------------------------------

        # members
        members = []
        if _group:
            for _member in _members:

                # member: add
                if _member['mode'] == "add":
                    member = Artist.search_by_oid(_member['oid'])
                    if not member or member.group:
                        continue
                    members.append(member)

                # member: create
                elif _member['mode'] == "create":
                    member = Artist.create_foreign(
                        party, _member['name'], _member['email'])
                    members.append(member)

                # member: edit
                elif _member['mode'] == "edit":
                    member = Artist.search_by_oid(member['oid'])
                    if not Artist.is_foreign_editable(web_user, member):
                        continue
                    member.name = _member['name']
                    member.party.name = _member['name']
                    for contact in member.party.contact_mechanisms:
                        if contact.type == 'email':
                            contact.value = _member['email']
                            contact.save()
                    member.party.save()
                    member.save()
                    members.append(member)

        # --- artist ----------------------------------------------------------

        # artist
        artist.group = _group
        artist.name = _name
        artist.description = _description
        artist.solo_artists = members
        artist.save()

        # user feedback
        log.info("edit artist successful for %s: %s" % (web_user, artist))
        self.request.session.flash(
            _("Artist edited: ${name} (${code})",
              mapping={'name': artist.name, 'code': artist.code}),
            'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_artist_form(request):
    return deform.Form(
        schema=AddArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
