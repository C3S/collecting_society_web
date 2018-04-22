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
            self.form = edit_artist_group_form(self.request)
        else:
            self.form = edit_artist_solo_form(self.request)

        # process form
        if self.submitted() and self.validate():
            self.edit_artist(artist)
        else: 
            self.appstruct['metadata'] = {
                'name': artist.name,
                'description': artist.description
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

@colander.deferred
def solo_artists_select_widget(node, kw):
    solo_artists = Artist.search_all_solo_artists()
    solo_artist_options = [(artist.id, artist.name) for artist in solo_artists]
    widget = deform.widget.Select2Widget(values=solo_artist_options)
    return widget


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


class MembersField(colander.SchemaNode):
    oid = "members"
    schema_type = colander.String
    widget = solo_artists_select_widget


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    name = NameField(
        title=_(u"Name")
    )
    description = DescriptionField(
        title=_(u"Description")
    )
    picture_delete = PictureDeleteField(
        title=_(u"Delete Picture")
    )
    picture_change = PictureChangeField(
        title=_(u"Change Picture")
    )


class MembersSequence(colander.SequenceSchema):
    member = MembersField(
        title=""
    )


class MembersSchema(colander.Schema):
    members = MembersSequence(
        title=_(u"Members")
    )


class EditArtistGroupSchema(colander.Schema):
    title = _(u"Edit Group Artist")
    metadata = MetadataSchema(
        title=_(u"Metadata")
    )
    members = MembersSchema(
        title=_(u"Members")
    )

class EditArtistSoloSchema(colander.Schema):
    title = _(u"Edit Solo Artist")
    metadata = MetadataSchema(
        title=_(u"Metadata")
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


def edit_artist_group_form(request):
    return deform.Form(
        renderer=zpt_renderer_tabs,
        schema=EditArtistGroupSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )

def edit_artist_solo_form(request):
    return deform.Form(
        renderer=zpt_renderer_tabs,
        schema=EditArtistSoloSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )

