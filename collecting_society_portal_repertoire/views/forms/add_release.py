# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import colander
import deform

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
    Genre,
    Style,
    Label,
    Party,
    Release
)
from ...resources import ReleaseResource
from .datatables import LabelSequence

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
        # label tab
        tab = 'label'
        if self.appstruct[tab]['label_code']:
            label = Label.search_by_gvl_code(
                        self.appstruct[tab]['label_code'])
            if label:
                release['label'] = label
        get_formdata('label_name')
        get_formdata('label_catalog_number')
        # production tab
        tab = 'production'
        get_formdata('copyright_date')
        get_formdata('production_date')
        get_formdata('producer')
        # distribution tab
        tab = 'distribution'
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
        if self.appstruct['genres']['styles']:
            release['styles'] = [(
                'add', list(self.appstruct['genres']['styles']))]

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
    validator = colander.Range(
        min=1, min_err=_('Release has to include at least one medium.'))


class EanUpcCodeField(colander.SchemaNode):
    oid = "ean_upc_code"
    schema_type = colander.String
    validator = colander.All(
        # TODO: find out why this is not working (old colander version?):
        # min_err=_('at least 12 digits for a valid UPC barcode,
        #           '13 for an EAN code.'),
        # max_err=_('maximum of 13 digits for an EAN code (12 for a UPC).'
        colander.Length(min=12, max=13),
        # colander.ContainsOnly(
        #     '0123456789',
        #     err_msg=_('may only contain digits') <- why no custom err_msg?!?
        # )
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
                                     'DEA123456789'))
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


# -- Label tab --

@colander.deferred
def labels_select_widget(node, kw):
    labels = Label.search_all()
    label_options = [
        (label.gvl_code, 'LC' + label.gvl_code + ' - ' + label.name)
        for label in labels
    ]
    widget = deform.widget.Select2Widget(values=label_options)
    return widget


class LabelCodeField(colander.SchemaNode):
    oid = "label_code"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()
    validator = colander.Regex('^\d{5}$',
                               msg=_('Please enter a valid five-digit '
                                     'GVL code'))


class LabelNameField(colander.SchemaNode):
    oid = "label_name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()
    missing = ""


class LabelCatalogNumberField(colander.SchemaNode):
    oid = "label_catalog_number"
    schema_type = colander.String
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
    # widget = party_select_widget <- no paries any more?
    widget = deform.widget.TextInputWidget(readonly=True)
    missing = colander.null
    # displaying a read-only function field, assembled from the repective
    # copyright owners of the release creations


class ProductionDateField(colander.SchemaNode):
    oid = "production_date"
    schema_type = colander.Date
    missing = ""


class ProducerField(colander.SchemaNode):
    oid = "producer"
    schema_type = colander.String
    # widget = party_select_widget <-- too complicated, too many implications
    missing = ""


# -- Distribution tab --


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

@colander.deferred
def deferred_checkbox_widget_style(node, kw):
    styles = Style.search_all()
    style_options = [(style.id, unicode(style.name)) for style in styles]
    widget = deform.widget.CheckboxChoiceWidget(values=style_options)
    return widget


class GenreCheckboxField(colander.SchemaNode):
    oid = "genres"
    schema_type = colander.Set
    widget = deferred_checkbox_widget
    validator = colander.Length(min=1)
    #    , min_err=_(u'Please choose at least one genre for this release'))
    missing = ""


class StyleCheckboxField(colander.SchemaNode):
    oid = "styles"
    schema_type = colander.Set
    widget = deferred_checkbox_widget_style
    validator = colander.Length(min=1)
    #    , min_err=_(u'Please choose at least one style for this release'))
    missing = ""


# --- Schemas -----------------------------------------------------------------

class GeneralSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    title = TitleField(title=_(u"Title"))
    number_mediums = NumberOfMediumsField(title=_(u"Number of Mediums"))
    ean_upc_code = EanUpcCodeField(title=_(u"EAN or UPC Code"))
    isrc_code = IsrcCodeField(title=_(u"ISRC Code"))
    warning = WarningField(title=_(u"Warning"))
    picture = PictureField(title=_(u"Picture"))


class LabelSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    label_selector = LabelSequence(title=_(u"Select Label"))
    label_code = LabelCodeField(title=_(u"Label Code"))
    label_name = LabelNameField(title=_(u"Label Name"))
    label_catalog_number = LabelCatalogNumberField(
        title=_(u"Label Catalog Number of Release"))


class ProductionSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    copyright_date = CopyrightDateField(title=_(u"Copyright Date"))
    copyright_owner = CopyrightOwnerField(title=_(u"Copyright Owner(s)"))
    production_date = ProductionDateField(title=_(u"Production Date"))
    producer = ProducerField(title=_(u"Producer"))


class DistributionSchema(colander.Schema):
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
    widget = deform.widget.MappingWidget(template='navs/mapping')
    genres = GenreCheckboxField(title=_(u"Genres"))
    styles = StyleCheckboxField(title=_(u"Styles"))


class AddReleaseSchema(colander.Schema):
    title = _(u"Add Release")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    general = GeneralSchema(title=_(u"General"))
    label = LabelSchema(title=_(u"Label"))
    production = ProductionSchema(title=_(u"Production"))
    distribution = DistributionSchema(title=_(u"Distribution"))
    genres = GenresSchema(title=_(u"Genres & Styles"))


# --- Forms -------------------------------------------------------------------

def add_release_form(request):
    return deform.Form(
        schema=AddReleaseSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
