# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import (
    Tdb,
    Party,
    WebUser
)
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
                if Artist.is_foreign_member(self.request, artist, member):
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
        appstruct = self.appstruct
        artist = self.context.artist
        email = self.request.unauthenticated_userid
        party = WebUser.current_party(self.request)

        # group
        if artist.group != appstruct['group']:
            # if group status has changed
            if artist.group:
                # remove solo artists from current group artist
                artist.solo_artists = []
            else:
                # remove current solo artist from group artists
                artist.group_artists = []
            artist.group = appstruct['group']

        # name
        if artist.name != appstruct['name']:
            artist.name = appstruct['name']

        # description
        if artist.description != appstruct['description']:
            artist.description = appstruct['description']

        # picture
        if self.appstruct['picture']:
            err, p, t, m = picture_processing(self.appstruct['picture']['fp'])
            if not err:
                artist.picture_data = p
                artist.picture_thumbnail_data = t
                artist.picture_data_mime_type = m
            else:
                self.request.session.flash(err, 'main-alert-warning')

        # members
        if artist.group:
            members_current = list(artist.solo_artists)
            members_future = []
            members_remove = members_current
            members_add = []
            members_create = []
            for member in appstruct['members']:

                # add existing artists
                if member['mode'] == "add":
                    member_artist = Artist.search_by_oid(member['oid'])
                    # sanity checks
                    if not member_artist:
                        continue
                    if member_artist.group:
                        continue
                    members_future.append(member_artist)
                    if member_artist in members_current:
                        members_remove.remove(member_artist)
                        continue
                    # append artist id
                    members_add.append(member_artist)

                # create new artists
                if member['mode'] == "create":
                    # create new party
                    member_party = Party.create([{
                        'name': member['name'],
                        'contact_mechanisms': [(
                            'create',
                            [{
                                'type': 'email',
                                'value': member['email']
                            }]
                        )]
                    }])
                    member_party = member_party[0]
                    # create vlist
                    members_create.append({
                        'group': False,
                        'description': "",
                        'party': member_party.id,
                        'entity_creator': party.id,
                        'entity_origin': 'indirect',
                        'claim_state': 'unclaimed',
                        'name': member['name']
                    })

                # edit created artists
                if member['mode'] == "edit":
                    member_artist = Artist.search_by_code(member['code'])
                    member_party = member_artist.party
                    # sanity checks
                    if not member_artist:
                        continue
                    # security checks
                    if not Artist.is_foreign_member(
                            self.request, artist, member_artist):
                        continue
                    # edit artist
                    member_artist.name = member['name']
                    has_email = False
                    if member_party.contact_mechanisms:
                        for contact in member_party.contact_mechanisms:
                            if contact.type == 'email':
                                has_email = True
                                contact.email = member['email']
                                contact.save()
                    if not has_email:
                        # TODO: find out, how to create a new contact mechanism
                        # without triggering a user validation error on email
                        log.debug("warning: member email not created (TODO)")
                    member_artist.save()
                    members_future.append(member_artist)

            # create new artists
            if members_create:
                members_created = Artist.create(members_create)
                members_future += members_created

            # add new member list
            artist.solo_artists = members_future

        artist.set_id_code('IPN', appstruct['ipn_code'])

        # update artist
        artist.save()

        # user feedback
        log.info("edit artist successful for %s: %s" % (email, artist))
        self.request.session.flash(
            _("Artist edited: ${arna} (${arco})",
              mapping={'arna': artist.name, 'arco': artist.code}),
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
