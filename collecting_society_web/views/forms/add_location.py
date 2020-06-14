# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import Tdb, Party, Address
from portal_web.views.forms import FormController

from ...services import _
from ...models import Location, LocationCategory

log = logging.getLogger(__name__)


class AddLocation(FormController):
    """
    form controller for creation of locations
    """

    def controller(self):
        self.form = add_location_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.create_location()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_location(self):
        web_user = self.request.web_user

        # generate vlist
        location = {
            'name': self.appstruct['general']['name'],
            'category': self.appstruct['general']['category'],
            # 'party': self.appstruct['party'],
            'public': self.appstruct['general']['public'],
            'latitude': self.appstruct['general']['latitude'],
            'longitude': self.appstruct['general']['longitude'],
            # 'spaces': self.appstruct['spaces']
        }

        party = {
            'name': self.appstruct['contact']['contact_name'],
            'first_name': self.appstruct['contact']['contact_first_name'],
            'website': self.appstruct['contact']['website'],
            'email': self.appstruct['contact']['email'],
            'fax': self.appstruct['contact']['fax'],
            # 'web_user': web_user,
            # member_c3s
            # member_c3s_token
            # artists
            # default_solo_artist
            # firstname
            # lastname
            # birthdate
            # repertoire_terms_accepted
            # oid
            # identifiers
            # legal_person
            'common_public_interest': 'no'
        }  

        address = {
            'name': self.appstruct['address']['address_name'],
            'street': self.appstruct['address']['street'],
            'streetbis': self.appstruct['address']['streetbis'],
            'zip': self.appstruct['address']['zip'],
            'city': self.appstruct['address']['city'],
            'country': self.appstruct['address']['country']
            # TODO: subsection
        }

        # remove empty fields
        for tab in [location, party, address]:
            for index, value in tab.items():
                if not value:
                    del tab[index]

        # create location
        if "name" not in party:
            party["name"] = self.appstruct['general']['name']
        party_record = Party.create([party])
        if party_record:
            location["party"] = party_record[0].id  # party is a required field
            if address != []:
                address["party"] = party_record[0].id
                if "name" not in address:
                    address["name"] = self.appstruct['general']['name']
                # address_record =
                Address.create([address])
        location_record = Location.create([location])

        # user feedback
        if not location_record:
            # TODO: delete party_record if location_record wasn't added
            log.info("location add failed for %s: %s" % (web_user,
                     location))
            self.request.session.flash(
                _(u"Location could not be added: ${name}",
                  mapping={'name': location['name']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        location_record = location_record[0]
        log.info("location add successful for %s: %s" % (web_user,
                 location_record))
        self.request.session.flash(
            _(u"Location '${name}' added. ",
              mapping={'name': location_record.name}),
            'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------


@colander.deferred
def deferred_category_widget(node, kw):
    cats = LocationCategory.search_all()
    cat_options = [(cat.id, unicode(cat.name)) for cat in cats]
    widget = deform.widget.Select2Widget(values=cat_options, multiple=False)
    return widget

# --- Fields ------------------------------------------------------------------

# -- General tab --


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = deferred_category_widget


class PublicField(colander.SchemaNode):
    oid = "public"
    schema_type = colander.Boolean
    missing = ""


class LatitudeField(colander.SchemaNode):
    oid = "latitude"
    schema_type = colander.Float
    validator = colander.Range(min=-90, max=90)


class LongitudeField(colander.SchemaNode):
    oid = "longitude"
    schema_type = colander.Float
    validator = colander.Range(min=-90, max=90)


# -- Contact info tab --


class ContactNameField(colander.SchemaNode):
    oid = "contact_name"
    schema_type = colander.String
    missing = ""


class ContactFirstNameField(colander.SchemaNode):
    oid = "contact_first_name"
    schema_type = colander.String
    missing = ""


class WebsiteField(colander.SchemaNode):
    oid = "website"
    schema_type = colander.String
    missing = ""


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    missing = ""


class FaxField(colander.SchemaNode):
    oid = "fax"
    schema_type = colander.String
    missing = ""


# -- Address tab --


class AddressNameField(colander.SchemaNode):
    oid = "address_name"
    schema_type = colander.String
    missing = ""


class StreetNameField(colander.SchemaNode):
    oid = "street"
    schema_type = colander.String
    missing = ""


class StreetBisNameField(colander.SchemaNode):
    oid = "streetbis"
    schema_type = colander.String
    missing = ""


class ZipField(colander.SchemaNode):
    oid = "zip"
    schema_type = colander.String
    missing = ""


class CityField(colander.SchemaNode):
    oid = "city"
    schema_type = colander.String
    missing = ""


class CountryField(colander.SchemaNode):
    oid = "country"
    schema_type = colander.String
    missing = ""


# --- Schemas -----------------------------------------------------------------


class GeneralSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    name = NameField(title=_(u"Name"))
    category = CategoryField(title=_(u"Category"))
    public = PublicField(title=_(u"Public"))
    latitude = LatitudeField(title=_(u"Latitude"))
    longitude = LongitudeField(title=_(u"Longitude"))


class ContactSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    contact_name = ContactNameField(title=_(u"Contact person name"))
    contact_first_name = ContactNameField(title=_(u"Contact person first name"))
    website = WebsiteField(title=_(u"Website"))
    email = EmailField(title=_(u"Email"))
    fax = FaxField(title=_(u"Fax"))


class AddressSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    address_name = AddressNameField(title=_(u"Name (doorbell)"))
    street = StreetNameField(title=_(u"Street"))
    streetbis = StreetBisNameField(title=_(u"Street (bis)"))
    zip = ZipField(title=_(u"Zip"))
    city = CityField(title=_(u"City"))
    country = CountryField(title=_(u"Country"))
    # subdivision


class AddLocationSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    general = GeneralSchema(title=_(u"General"))
    contact = ContactSchema(title=_(u"Contact information"))
    address = AddressSchema(title=_(u"Business address"))


# --- Forms -------------------------------------------------------------------

def add_location_form(request):
    return deform.Form(
        schema=AddLocationSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
