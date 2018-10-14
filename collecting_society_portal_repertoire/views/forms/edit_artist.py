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
from ...resources import ArtistResource
from .datatables import ArtistSequence

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

    @Tdb.transaction(readonly=True)
    def edit_artist(self):
        artist = self.context.artist

        # set appstruct
        self.appstruct = {
            'metadata': {
                'group': artist.group,
                'name': artist.name,
                'description': artist.description or ''
            }
        }
        if artist.group:
            _members = []
            for member in artist.solo_artists:
                mode = "add"
                email = ""
                if Artist.is_editable(self.request, member):
                    mode = "edit"
                    email = member.party.email
                _members.append({
                    'mode': mode,
                    'name': member.name,
                    'code': member.code,
                    'description': member.description or '',
                    'email': email
                })
            self.appstruct['members'] = {
                'members': _members
            }

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_artist(self):
        artist = self.context.artist
        email = self.request.unauthenticated_userid
        party = WebUser.current_party(self.request)

        # group
        if artist.group != self.appstruct['metadata']['group']:
            # if group status has changed
            if artist.group:
                # remove solo artists from current group artist
                artist.solo_artists = []
            else:
                # remove current solo artist from group artists
                artist.group_artists = []
            artist.group = self.appstruct['metadata']['group']

        # name
        if artist.name != self.appstruct['metadata']['name']:
            artist.name = self.appstruct['metadata']['name']

        # description
        if artist.description != self.appstruct['metadata']['description']:
            artist.description = self.appstruct['metadata']['description']

        # picture
        if self.appstruct['metadata']['picture_delete']:
            artist.picture_data = None
            artist.picture_data_mime_type = None
        elif self.appstruct['metadata']['picture_change']:
            with open(self.appstruct['metadata']['picture_change']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = self.appstruct['metadata']['picture_change']['mimetype']
            artist.picture_data = picture_data
            artist.picture_data_mime_type = mimetype

        # members
        if artist.group:
            members_current = list(artist.solo_artists)
            members_future = []
            members_remove = members_current
            members_add = []
            members_create = []
            for member in self.appstruct['members']['members']:

                # add existing artists
                if member['mode'] == "add":
                    member_artist = Artist.search_by_code(member['code'])
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
                        'name': member['name']
                    })

                # edit created artists
                if member['mode'] == "edit":
                    member_artist = Artist.search_by_code(member['code'])
                    # sanity checks
                    if not member_artist:
                        continue
                    if not Artist.is_editable(self.request, member_artist):
                        continue
                    member_artist.name = member['name']
                    for mechanism in member_artist.party.contact_mechanisms:
                        if mechanism.type == 'email':
                            mechanism.email = member['email']
                            mechanism.save()
                    member_artist.save()
                    members_future.append(member_artist)

            # create new artists
            if members_create:
                members_created = Artist.create(members_create)
                members_future += members_created

            # add new member list
            artist.solo_artists = members_future

        # update artist
        artist.save()

        # user feedback
        log.info("edit artist successful for %s: %s" % (email, artist))
        self.request.session.flash(
            _(u"Artist edited: ") + artist.name + " (" + artist.code + ")",
            'main-alert-success'
        )

        # redirect
        self.redirect(ArtistResource, 'show', artist.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

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


class PictureChangeField(colander.SchemaNode):
    oid = "picture-change"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget
    missing = ""


class PictureDeleteField(colander.SchemaNode):
    oid = "picture-delete"
    schema_type = colander.Boolean
    widget = deform.widget.CheckboxWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    group = GroupField(title=_(u"Group"))
    name = NameField(title=_(u"Name"))
    description = DescriptionField(title=_(u"Description"))
    picture_delete = PictureDeleteField(title=_(u"Delete Picture"))
    picture_change = PictureChangeField(title=_(u"Change Picture"))


class MembersSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    members = ArtistSequence(title="")


class EditArtistSchema(colander.Schema):
    title = _(u"Edit Artist")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    metadata = MetadataSchema(title=_(u"Metadata"))
    members = MembersSchema(title=_(u"Members"))


# --- Forms -------------------------------------------------------------------

def edit_artist_form(request):
    return deform.Form(
        schema=EditArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
