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


class ArtistModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class ArtistNameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class ArtistCodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class ArtistEmailField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.Email()
    missing = ""


class ArtistKeyField(colander.SchemaNode):
    oid = "key"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class ArtistsField(colander.SchemaNode):
    oid = "members"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


# --- Schemas -----------------------------------------------------------------

class ArtistSchema(colander.Schema):
    mode = ArtistModeField()
    name = ArtistNameField()
    code = ArtistCodeField()
    email = ArtistEmailField()
    key = ArtistKeyField()
    title = ""


class ArtistSequence(colander.SequenceSchema):
    artist = ArtistSchema()
    widget = deform.widget.SequenceWidget(
        template='datatables/sequence',
        item_template='datatables/sequence_item',
        category='structural'
    )


class MetadataSchema(colander.Schema):
    group = GroupField(
        title=_(u"Group")
    )
    name = NameField(
        title=_(u"Name")
    )
    description = DescriptionField(
        title=_(u"Description")
    )
    picture = PictureField(
        title=_(u"Picture")
    )


class AddArtistSchema(colander.Schema):
    title = _(u"Add Artist")
    metadata = MetadataSchema(
        title=_(u"Metadata")
    )
    members = ArtistSequence(
        title=_(u"Members"),
        missing=""
    )


# --- Forms -------------------------------------------------------------------

# custom template
def translator(term):
    return get_localizer(get_current_request()).translate(term)


zpt_renderer_tabs = deform.ZPTRendererFactory([
    resource_filename('collecting_society_portal', 'templates/deform/tabs'),
    resource_filename('collecting_society_portal', 'templates/deform'),
    resource_filename('deform', 'templates')
], translator=translator)


def add_artist_form(request):
    return deform.Form(
        renderer=zpt_renderer_tabs,
        schema=AddArtistSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
