# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import Tdb, Party, Address
from ...models import LocationSpace, LocationSpaceCategory
from .add_location import AddLocationSchema
from portal_web.views.forms import FormController
from ...services import _

log = logging.getLogger(__name__)


class EditLocation(FormController):
    """
    form controller for editing locations
    """

    def controller(self):
        self.form = edit_location_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_location()
        else:
            self.edit_location()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_location(self):
        location = self.context.location

        # set appstruct
        self.appstruct = {
            'general': {
                'name': location.name,
                'category': location.category.id,
                'public': location.public,
                'latitude': location.latitude,
                'longitude': location.longitude,
            },
            'contact': {
                'contact_name': location.party.name or '',
                'contact_first_name': location.party.firstname or '',
                'website': location.party.website or '',
                'email': location.party.email or '',
                'fax': location.party.fax or ''
            },
            'spaces': {
                'spaces': []
            }
        }
        if location.party.addresses:
            if location.party.addresses[0].country:
                country_id = location.party.addresses[0].country.id
            else:
                country_id = ''

            self.appstruct['address'] = {
                'address_name': location.party.addresses[0].name or '',
                'street': location.party.addresses[0].street or '',
                'zip': location.party.addresses[0].zip or '',
                'city': location.party.addresses[0].city or '',
                'country': country_id
                # TODO: subdivision
            }

        # location spaces
        for ls_record in location.spaces:
            if ls_record.confirmed_size:         # the UI looks a bit different
                size = ls_record.confirmed_size  # from the data model here for
                size_estimated = False           # having an estimated checkbox
            else:                                # rather than two size entries
                size = ls_record.estimated_size
                size_estimated = True
            self.appstruct['spaces']['spaces'].append(
            {
                'mode': "edit",
                'oid': ls_record.oid,
                'name': ls_record.name,
                'category': ls_record.category.id,
                'size': size,
                'size_estimated': size_estimated
            })

        # render
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_location(self):
        web_user = self.request.web_user
        location_record = self.context.location

        # generate vlist
        location_vlist = {
            'id': location_record.id,
            'name': self.appstruct['general']['name'],
            'category': self.appstruct['general']['category'],
            # 'party': self.appstruct['general']['party'],
            'public': self.appstruct['general']['public'],
            'latitude': self.appstruct['general']['latitude'],
            'longitude': self.appstruct['general']['longitude']
            # TODO: spaces
        }

        # location spaces
        spaces_create = []
        spaces_delete = list(location_record.spaces)
        spaces = self.appstruct['spaces']['spaces']
        if spaces:
            for space in spaces:
                # does the space category exist in the database?
                lsc_record = LocationSpaceCategory.search_by_code(
                    space['category'])
                if not lsc_record:
                    continue

                if space['mode'] == "create":
                    # append space
                    if space['size_estimated']:
                        indicator_field = 'estimated_size'
                    else:
                        indicator_field = 'confirmed_size'
                    spaces_create.append({
                        'name': space['name'],
                        'category': lsc_record.id,
                        indicator_field: space['size']
                    })

                if space['mode'] == "edit":
                    ls_record = LocationSpace.search_by_oid(space['oid'])
                    if not ls_record:
                        continue
                    if ls_record in spaces_delete:
                        spaces_delete.remove(ls_record)
                    # update the location space
                    if space['size_estimated']:
                        ls_record.estimated_size = space['size']
                        ls_record.confirmed_size = None
                    else:
                        ls_record.estimated_size = None
                        ls_record.confirmed_size = space['size']
                    ls_record.name = space['name']
                    ls_record.category = lsc_record.id
                    ls_record.save()              

        # agglomerated append and delete actions for location spaces
        location_vlist['spaces'] = []
        if spaces_create:
            location_vlist['spaces'].append(('create', spaces_create))
        if spaces_delete:
            location_vlist['spaces'].append(('delete', spaces_delete))

        # write the location record to database
        location_record.write([location_record], location_vlist)

        # also write associated party and address records
        party_record = Party.search_by_id(location_record.party.id)
        if party_record:
            party_vlist = {
                'name': self.appstruct['contact']['contact_name'],
                'firstname': self.appstruct['contact']['contact_first_name'],
                # 'website': self.appstruct['contact']['website'],
                # 'email': self.appstruct['contact']['email'],
                # 'fax': self.appstruct['contact']['fax'],
                # TODO: find out how these undocumented ContactMechanisms work
            }
            party_record.write([party_record], party_vlist)

            address_vlist = {
                'name': self.appstruct['address']['address_name'],
                'street': self.appstruct['address']['street'],
                'zip': self.appstruct['address']['zip'],
                'city': self.appstruct['address']['city'],
                'country': self.appstruct['address']['country']
                # 'subsection': self.appstruct['address']['subsection']
                # TODO: country and subsection
            }
            address_record = Address.search_by_party(location_record.party.id)
            if address_record:
                address_record.write([address_record], address_vlist)
            else:  # no address before and now non-empty strings in address?
                for index, value in address_vlist:
                    if value:  # create new address record
                        address_vlist["party"] = party_record[0].id
                        Address.create([address_vlist])
                        break

            # TODO: check ownership or write pemissions here!

            # user feedback
            log.info("edit location successful for %s: %s" % (web_user,
                     location_record))
            self.request.session.flash(
                _(u"Location edited:  ${name}",
                  mapping={'name': location_record.name}),
                'main-alert-success'
            )
        else:
            # user feedback
            log.info("edit location unsuccessful for %s: %s" % (web_user,
                     location_record))
            self.request.session.flash(
                _(u"Location ${name} edited changes couldn't be stored",
                  mapping={'name': location_record.name}),
                'main-alert-warning'
            )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_location_form(request):
    return deform.Form(
        schema=AddLocationSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
