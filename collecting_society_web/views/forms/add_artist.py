# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import (
    Tdb,
    Party,
    WebUser
)
from portal_web.views.forms import (
    FormController,
    deferred_file_upload_widget
)

from ...services import (_, picture_processing)
from ...models import Artist, ArtistIdentifierSpace
from .datatables import ArtistSequence

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddArtist(FormController):
    """
    form controller for creation of artists
    """

    def controller(self):
        self.form = add_artist_form(self.request)
        self.render()
        if self.submitted() and self.validate():
            self.create_artist()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_artist(self):
        email = self.request.unauthenticated_userid
        party = WebUser.current_party(self.request)

        # generate vlist
        _artist = {
            'group': self.appstruct['group'],
            'party': party,
            'entity_creator': party,
            'entity_origin': 'direct',
            'claim_state': 'claimed',
            'name': self.appstruct['name'],
            'identifiers': [(
                'create',
                [{
                    'space': ArtistIdentifierSpace.search_by_name('IPN'),
                    'id_code': self.appstruct['ipn_code']
                }]
            )],
            'description': self.appstruct['description'] or '',
        }

        # picture
        if self.appstruct['picture']:
            err, p, t, m = picture_processing(self.appstruct['picture']['fp'])
            if not err:
                _artist['picture_data'] = p
                _artist['picture_thumbnail_data'] = t
                _artist['picture_data_mime_type'] = m
            else:
                self.request.session.flash(err, 'main-alert-warning')

        # members
        if self.appstruct['group']:
            members_add = []
            members_create = []
            for member in self.appstruct['members']:

                # add existing artists
                if member['mode'] == "add":
                    member_artist = Artist.search_by_oid(member['oid'])
                    # sanity checks
                    if not member_artist:
                        continue
                    if member_artist.group:
                        continue
                    # append artist id
                    members_add.append(member_artist.id)

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
                    # append member data
                    members_create.append({
                        'group': False,
                        'description': "",
                        'party': member_party.id,
                        'entity_creator': party.id,
                        'entity_origin': 'indirect',
                        'claim_state': 'unclaimed',
                        'name': member['name']
                    })

            # append actions
            _artist['solo_artists'] = []
            if members_create:
                _artist['solo_artists'].append(('create', members_create))
            if members_add:
                _artist['solo_artists'].append(('add', members_add))

        # create artist
        artists = Artist.create([_artist])

        # user feedback
        if not artists:
            log.info("artist add failed for %s: %s" % (email, _artist))
            self.request.session.flash(
                _("Artist could not be added: ${arna}",
                  mapping={'arna':  _artist['name']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        artist = artists[0]
        log.info("artist add successful for %s: %s" % (email, artist))
        artists = Artist.search_by_party(party)
        is_first_artist = False
        if artists and len(artists) == 1:
            is_first_artist = True
        if is_first_artist:
            self.request.session.flash(
                _("Congratulations! You created your first artist "
                  "'${arna}' (${arco}). Now go back to the dashboard and "
                  "see what's next.",
                  mapping={'arna': artist.name, 'arco': artist.code}),
                'main-alert-success'
            )
        else:
            self.request.session.flash(
                _("Artist added:  ${arna} (${arco})",
                  mapping={'arna': artist.name, 'arco': artist.code}),
                'main-alert-success'
            )

        # redirect
        self.redirect(artist.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class GroupField(colander.SchemaNode):
    oid = "group"
    schema_type = colander.Boolean
    widget = deform.widget.CheckboxWidget()


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


class IpnCodeField(colander.SchemaNode):
    oid = "ipn_code"
    schema_type = colander.String
    missing = ""


class DescriptionField(colander.SchemaNode):
    oid = "description"
    schema_type = colander.String
    widget = deform.widget.TextAreaWidget()
    missing = ""


class PictureField(colander.SchemaNode):
    oid = "picture"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget
    missing = ""


# --- Schemas -----------------------------------------------------------------

class AddArtistSchema(colander.Schema):
    group = GroupField(title=_("Group"))
    # title = _(u"Add Artist")
    name = NameField(title=_("Name"))
    ipn_code = IpnCodeField(title=_("International Performer Number"))
    description = DescriptionField(title=_("Description"))
    picture = PictureField(title=_("Picture"))
    members = ArtistSequence(title=_("Members"))


# --- Forms -------------------------------------------------------------------

def add_artist_form(request):
    return deform.Form(
        schema=AddArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
