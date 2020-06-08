# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import Tdb, Party
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
            'name': self.appstruct['name'],
            'category': self.appstruct['category'],
            # 'party': self.appstruct['party'],
            'public': self.appstruct['public'],
            'latitude': self.appstruct['latitude'],
            'longitude': self.appstruct['longitude'],
            # 'spaces': self.appstruct['spaces']
        }

        party = {
            'name': self.appstruct['name'],
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

        # remove empty fields
        for index, value in location.items():
            if not value:
                del location[index]

        # create location
        party_record = Party.create([party])
        if party_record:
            location["party"] = party_record[0].id  # party is a required field
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


class LatitudeField(colander.SchemaNode):
    oid = "latitude"
    schema_type = colander.Float


class LongitudeField(colander.SchemaNode):
    oid = "longitude"
    schema_type = colander.Float


# --- Schemas -----------------------------------------------------------------

class AddLocationSchema(colander.Schema):
    name = NameField(title=_(u"Name"))
    category = CategoryField(title=_(u"Category"))
    public = PublicField(title=_(u"Public"))
    latitude = LatitudeField(title=_(u"Latitude"))
    longitude = LongitudeField(title=_(u"Longitude"))
    # styles = StyleCheckboxField(title=_(u"Styles"))


# --- Forms -------------------------------------------------------------------

def add_location_form(request):
    return deform.Form(
        schema=AddLocationSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
