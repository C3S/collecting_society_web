# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import colander
import deform

from collecting_society_portal.models import (
    Tdb,
    Party,
    WebUser
)
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)

from ...services import _
from ...models import Artist
from .datatables import ArtistSequence

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddArtist(FormController):
    """
    form controller for creation of artists
    """

    def controller(self):
        self.form = add_artist_form(self.request)
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
            'group': self.appstruct['metadata']['group'],
            'party': party,
            'entity_creator': party,
            'entity_origin': 'direct',
            'claim_state': 'claimed',
            'name': self.appstruct['metadata']['name'],
            'description': self.appstruct['metadata']['description'] or '',
        }
        if self.appstruct['metadata']['picture']:
            with open(self.appstruct['metadata']['picture']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = self.appstruct['metadata']['picture']['mimetype']
            _artist['picture_data'] = picture_data
            _artist['picture_data_mime_type'] = mimetype

        # set members
        if self.appstruct['metadata']['group']:
            members_add = []
            members_create = []
            for member in self.appstruct['members']['members']:

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

            # append directives
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
                _(u"Artist could not be added: ") + _artist['name'],
                'main-alert-danger'
            )
            self.redirect()
            return
        artist = artists[0]
        log.info("artist add successful for %s: %s" % (email, artist))
        self.request.session.flash(
            _(u"Artist added: ") + artist.name + " (" + artist.code + ")",
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

class MetadataSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    group = GroupField(title=_(u"Group"))
    name = NameField(title=_(u"Name"))
    description = DescriptionField(title=_(u"Description"))
    picture = PictureField(title=_(u"Picture"))


class MembersSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    members = ArtistSequence(title="")


class AddArtistSchema(colander.Schema):
    title = _(u"Add Artist")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    metadata = MetadataSchema(title=_(u"Metadata"))
    members = MembersSchema(title=_(u"Members"))


# --- Forms -------------------------------------------------------------------

def add_artist_form(request):
    return deform.Form(
        schema=AddArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
