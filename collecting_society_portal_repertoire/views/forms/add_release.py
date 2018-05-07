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
            'entity_origin': "direct",
            'entity_creator': WebUser.current_web_user(self.request).party,
            'title': self.appstruct['general']['title']
        }  
        # general tab
        if self.appstruct['general']['isrc_code']:
            _release['number_mediums'] = self.appstruct['general'][
                'number_mediums']
        if self.appstruct['general']['ean_upc_code']:
            _release['ean_upc_code'] = self.appstruct['general'][
                'ean_upc_code']
        if self.appstruct['general']['isrc_code']:
            _release['isrc_code'] = self.appstruct['general']['isrc_code']
        # distribution tab
         # TODO: save label relation here:
        #if self.appstruct['distribution']['label']:    --> Many2One relation!
        #    _release['label'] = self.appstruct['distribution']['label']
        if self.appstruct['distribution']['label']:
            _release['label_catalog_number'] = self.appstruct['distribution']['label_catalog_number']
        if self.appstruct['distribution']['label_catalog_number']:
            _release['label_catalog_number'] = self.appstruct['distribution'][
                'label_catalog_number']
        if self.appstruct['distribution']['release_date']:
            _release['release_date'] = self.appstruct['distribution'][
                'release_date']
        if self.appstruct['distribution']['release_cancellation_date']:
            _release['release_cancellation_date'] = self.appstruct['distribution'][
                'release_cancellation_date']
        if self.appstruct['distribution']['online_release_date']:
            _release['online_release_date'] = self.appstruct['distribution'][
                'online_release_date']
        if self.appstruct['distribution']['online_cancellation_date']:
            _release['online_cancellation_date'] = self.appstruct['distribution'][
                'online_cancellation_date']
        if self.appstruct['distribution']['distribution_territory']:
            _release['distribution_territory'] = self.appstruct['distribution'][
                'distribution_territory']

        Release.create([_release])

        self.redirect(ReleaseResource, 'list')

# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------


# --- Fields ------------------------------------------------------------------

# -- General tab --

class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class NumberOfMediumsField(colander.SchemaNode):
    oid = "number_mediums"
    schema_type = colander.Int
    validator = colander.Range(min=1,
                min_err=_('Release has to include at least one medium.')
    )


class EanUpcCodeField(colander.SchemaNode):
    oid = "ean_upc_code"
    schema_type = colander.String
    missing = ""


class IsrcCodeField(colander.SchemaNode):
    oid = "isrc_code"
    schema_type = colander.String
    missing = ""


# -- Production Tab --

# -- Distribution tab --

class LabelField(colander.SchemaNode):
    oid = "label"
    schema_type = colander.String
    missing = ""


class LabelCatalogNumberField(colander.SchemaNode):
    oid = "label_catalog_number"
    schema_type = colander.String
    missing = ""


class ReleaseDateField(colander.SchemaNode):
    oid = "release_date"
    schema_type = colander.Date
    missing = ""


class ReleaseCancellationDateField(colander.SchemaNode):
    oid = "releas_cancellation_date"
    schema_type = colander.Date
    missing = ""


class OnlineReleaseDateField(colander.SchemaNode):
    oid = "online_release_date"
    schema_type = colander.Date
    missing = ""


class OnlineReleaseCancellationDateField(colander.SchemaNode):
    oid = "online_cancellation_date"
    schema_type = colander.Date
    missing = ""


class DistributionTerritoryField(colander.SchemaNode):
    oid = "distribution_territory"
    schema_type = colander.String
    missing = ""


# -- Tracks tab --


# -- Genres tab --


# -- Neibouring Rights Societies tab --

# --- Schemas -----------------------------------------------------------------

class GeneralSchema(colander.Schema):
    title = TitleField(
        title=_(u"Title")
    )
    number_mediums = NumberOfMediumsField(
        title=_(u"Number of Mediums")
    )
    ean_upc_code = EanUpcCodeField(
        title=_(u"EAN UPC Code")
    )
    isrc_code = IsrcCodeField(
        title=_(u"ISRC Code")
    )
    #picture_data = 
    #picture_data_mime_type = 
    #warning = 


class ProductionSchema(colander.Schema):
    pass


class DistributionSchema(colander.Schema):
    label = LabelField(
        title=_(u"Label [this field is not yet being saved]")
    )
    label_catalog_number = LabelCatalogNumberField(
        title=_(u"Label Catalog Number")
    )
    release_date = ReleaseDateField(title=_(u"Release Date"))
    release_cancellation_date = ReleaseCancellationDateField(
        title=_(u"Release Cancellation Date"))
    online_release_date = OnlineReleaseDateField(
        title=_(u"Online Release Date"))
    online_cancellation_date = OnlineReleaseCancellationDateField(
        title=_(u"Online Release Cancellation Date"))
    distribution_territory = DistributionTerritoryField(
        title=_(u"Distribution Territory"))


class TracksSchema(colander.Schema):
    pass


class GenresSchema(colander.Schema):
    pass


class RightsSocietiesSchema(colander.Schema):
    pass


class AddReleaseSchema(colander.Schema):
    title = _(u"Add Release")
    general = GeneralSchema(
        title=_(u"General")
    )
    production = ProductionSchema(
        title=_(u"Production")
    )
    distribution = DistributionSchema(
        title=_(u"Distribution")
    )
    tracks = TracksSchema(
        title =_(u"Tracks")
    )
    genres = GenresSchema(
        title=_(u"Genres")
    )
    rights_societies = RightsSocietiesSchema(
        title=_(u"Rights Societies")
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
