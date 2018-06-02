# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
import logging

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

        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )

        _artist = {
            'group': self.appstruct['metadata']['group'],
            'party': party,
            'entity_creator': party,
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

        artists = Artist.create([_artist])

        if not artists:
            log.info("artist add failed for %s: %s" % (email, _artist))
            self.request.session.flash(
                _(u"Artist could not be added: ") + _artist['name'],
                'main-alert-danger'
            )
            self.redirect(ArtistResource, 'list')
            return
        artist = artists[0]

        log.info("artist add successful for %s: %s" % (email, artist))
        self.request.session.flash(
            _(u"Artist added: ") + artist.name + " (" + artist.code + ")",
            'main-alert-success'
        )

        self.redirect(ArtistResource, 'show', artist.code)


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
    widget = deform.widget.MappingWidget(template='tabs/mapping')
    group = GroupField(title=_(u"Group"))
    name = NameField(title=_(u"Name"))
    description = DescriptionField(title=_(u"Description"))
    picture = PictureField(title=_(u"Picture"))


class AddArtistSchema(colander.Schema):
    title = _(u"Add Artist")
    widget = deform.widget.FormWidget(template='tabs/form')
    metadata = MetadataSchema(title=_(u"Metadata"))
    members = ArtistSequence(title=_(u"Members"), missing="")


# --- Forms -------------------------------------------------------------------

def add_artist_form(request):
    return deform.Form(
        schema=AddArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
