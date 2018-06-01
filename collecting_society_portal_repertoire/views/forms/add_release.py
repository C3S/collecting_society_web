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
    Genre,
    Label,
    License,
    Party,
    Release
)
from ...resources import ReleaseResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddRelease(FormController):
    """
    form controller for add release
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

        release = {
            'entity_origin': "direct",
            'entity_creator': WebUser.current_web_user(self.request).party,
            'title': self.appstruct['general']['title']
        }  
        # general tab
        tab = 'general'
        def get_formdata(value):    # a little embedded helper function
            if self.appstruct[tab][value]:
                release[value] = self.appstruct[tab][value]
        get_formdata('number_mediums')
        get_formdata('ean_upc_code')
        get_formdata('isrc_code')
        get_formdata('warning')
        if self.appstruct['general']['picture']:
            with open(self.appstruct['general']['picture']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = self.appstruct['general']['picture']['mimetype']
            release['picture_data'] = picture_data
            release['picture_data_mime_type'] = mimetype
        # production tab
        tab = 'production'
        get_formdata('copyright_date')
        get_formdata('production_date')
        get_formdata('producer')
        # distribution tab
        tab = 'distribution'
        if self.appstruct['distribution']['label']:
            label = Label.search_by_gvl_code(
                self.appstruct['distribution']['label'])
            if label:
                release['label'] = label
        get_formdata('label_catalog_number')
        get_formdata('release_date')
        get_formdata('release_cancellation_date')
        get_formdata('online_release_date')
        get_formdata('online_cancellation_date')
        get_formdata('distribution_territory')
        get_formdata('neighbouring_rights_society')        
        # genres tab
        if self.appstruct['genres']['genres']:
            release['genres'] = [(
                'add', list(self.appstruct['genres']['genres']))]

        Release.create([release])

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
    validator = colander.All(
                    colander.Length(min=12, max=13
                    # TODO: find out why this is not working (old colander version?):
                    # ,
                    # min_err=_('at least 12 digits for a valid UPC barcode, 13 for an EAN code.'),
                    # max_err=_('maximum of 13 digits for an EAN code (12 for a UPC).'
                    ),
                    #colander.ContainsOnly(
                    #    '0123456789', 
                    #    err_msg=_('may only contain digits') <- why no custom err_msg?!?
                    #)
                    colander.Regex('^[0-9]*$', msg=_('may only contain digits'))
                )
    missing = ""


class IsrcCodeField(colander.SchemaNode):
    oid = "isrc_code"
    schema_type = colander.String
    validator = colander.Regex('^[a-zA-Z][a-zA-Z][a-zA-Z0-9][a-zA-Z0-9][a-z'
                               'A-Z0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*$',
                               msg=_('Please enter a valid international '
                                     'standard recording code, for example: '
                                     'DEA123456789'
                                    )
                              )
    missing = ""


class WarningField(colander.SchemaNode):
    oid = "warning"
    schema_type = colander.String
    missing = ""


class PictureField(colander.SchemaNode):
    oid = "picture"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget
    missing = ""

# -- Production Tab --


@colander.deferred
def party_select_widget(node, kw):
    parties = Party.search_all()
    label_options = [
        (party.code, party.name) for party in parties
    ]
    widget = deform.widget.Select2Widget(values=label_options)
    return widget
    
    
class CopyrightDateField(colander.SchemaNode):
    oid = "copyright_date"
    schema_type = colander.Date
    missing = ""


class CopyrightOwnerField(colander.SchemaNode):
    oid = "get_copyright_owners"
    schema_type = colander.String
    #widget = party_select_widget <- no paries any more?
    widget=deform.widget.TextInputWidget(readonly=True)
    missing=colander.null
    # displaying a read-only function field, assembled from the repective
    # copyright owners of the release creations


class ProductionDateField(colander.SchemaNode):
    oid = "production_date"
    schema_type = colander.Date
    missing = ""


class ProducerField(colander.SchemaNode):
    oid = "producer"
    schema_type = colander.String
    #widget = party_select_widget <-- too complicated, too many implications
    missing = "" 


# -- Distribution tab --


@colander.deferred
def labels_select_widget(node, kw):
    labels = Label.search_all()
    label_options = [
        (label.gvl_code, 'LC' + label.gvl_code + ' - ' + label.name) for label in labels
    ]
    widget = deform.widget.Select2Widget(values=label_options)
    return widget


class LabelField(colander.SchemaNode):
    oid = "label"
    schema_type = colander.String
    widget = labels_select_widget
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
    oid = "release_cancellation_date"
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


class NeighbouringRightsSocietyField(colander.SchemaNode):
    oid = "neighbouring_rights_society"
    schema_type = colander.String
    missing = ""


# -- Genres tab --


@colander.deferred
def deferred_checkbox_widget(node, kw):
    genres = Genre.search_all()
    genre_options = [(genre.id, unicode(genre.name)) for genre in genres]
    widget = deform.widget.CheckboxChoiceWidget(values=genre_options)
    return widget


class GenreCheckboxField(colander.SchemaNode):
    oid = "genres"
    schema_type = colander.Set
    widget = deferred_checkbox_widget
    validator = colander.Length(min=1)
    #    , min_err=_(u'Please choose at least one genre for this release'))
    missing = ""
    

# --- Schemas -----------------------------------------------------------------

class GeneralSchema(colander.Schema):
    title = TitleField(title=_(u"Title"))
    number_mediums = NumberOfMediumsField(title=_(u"Number of Mediums"))
    ean_upc_code = EanUpcCodeField(title=_(u"EAN or UPC Code"))
    isrc_code = IsrcCodeField(title=_(u"ISRC Code"))
    warning = WarningField(title=_(u"Warning"))
    picture = PictureField(title=_(u"Picture"))


class ProductionSchema(colander.Schema):
    copyright_date = CopyrightDateField(title=_(u"Copyright Date"))
    copyright_owner = CopyrightOwnerField(title=_(u"Copyright Owner(s)"))
    production_date = ProductionDateField(title=_(u"Production Date"))
    producer = ProducerField(title=_(u"Producer"))


class DistributionSchema(colander.Schema):
    label = LabelField(
        title=_(u"Label")
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
    neighbouring_rights_society = NeighbouringRightsSocietyField(
        title=_(u"Neighbouring Rights Society"))


class GenresSchema(colander.Schema):    
    genres = GenreCheckboxField(title=_(u"Genres"))


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
    genres = GenresSchema(
        title=_(u"Genres")
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
