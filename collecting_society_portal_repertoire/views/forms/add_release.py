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
from ...models import (
    Artist,
    Creation,
    License,
    Release
)
from ...resources import ReleaseResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddRelease(FormController):
    """
    form controller for creation of creations
    """

    def controller(self):

        self.form = add_release_form(self.request)

        if self.submitted() and self.validate():
            self.save_release()

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def save_release(self):
        party = WebUser.current_party(self.request)

        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )

        _release = {
            'party': party,
            'title': self.appstruct['metadata']['title']
        }
        if self.appstruct['metadata']['isrc_code']:
            _release['isrc_code'] = self.appstruct['metadata']['isrc_code']
        if self.appstruct['metadata']['label']:
            _release['label'] = self.appstruct['metadata']['label']
        if self.appstruct['metadata']['ean_upc_code']:
            _release['ean_upc_code'] = self.appstruct['metadata'][
                'ean_upc_code']

        Release.create([_release])

        self.redirect(ReleaseResource, 'list')

# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------


# --- Fields ------------------------------------------------------------------

class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class IsrcCodeField(colander.SchemaNode):
    oid = "isrc_code"
    schema_type = colander.String
    missing = ""


class LabelField(colander.SchemaNode):
    oid = "label"
    schema_type = colander.String
    missing = ""


class EanUpcCodeField(colander.SchemaNode):
    oid = "ean_upc_code"
    schema_type = colander.String
    missing = ""


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    title = TitleField(
        title=_(u"Title")
    )
    isrc_code = IsrcCodeField(
        title=_(u"ISRC Code")
    )
    label = LabelField(
        title=_(u"Label")
    )
    ean_upc_code = EanUpcCodeField(
        title=_(u"EAN UPC Code")
    )


class Metadata2Schema(colander.Schema):
    pass


class Metadata3Schema(colander.Schema):
    pass


class AddReleaseSchema(colander.Schema):
    title = _(u"Add Release")
    metadata = MetadataSchema(
        title=_(u"Metadata")
    )
    metadata2 = Metadata2Schema(
        title=_(u"Metadata2")
    )
    metadata3 = Metadata3Schema(
        title=_(u"Metadata3")
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


def add_release_form(request):
    return deform.Form(
        renderer=zpt_renderer_tabs,
        schema=AddReleaseSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
