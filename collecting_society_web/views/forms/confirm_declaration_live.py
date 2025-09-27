# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden

from portal_web.models import Tdb, Country
from portal_web.services import utc_to_timezone
from portal_web.views.forms import FormController

from ...services import _
from ...resources import DeclarationsResource
from ...models import (
    Artist,
    EventPerformance,
    EventIndicators,
    Location,
    LocationCategory,
    TariffAdjustmentCategory,
    TariffRelevance,
    TariffRelevanceCategory,
    UtilisationIndicators,
)
from .add_declaration_live import (
    EventSchema,
    EventIndicatorsSchema,
    UtilisationOnetimeSchema,
)

log = logging.getLogger(__name__)


class ConfirmDeclarationLive(FormController):
    """
    form controller for confirmation of declarations
    """

    def controller(self):
        self.form = live_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.confirm_declaration()
        else:
            self.load_declaration()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def load_declaration(self):
        # shortcuts
        web_user = self.request.web_user
        declaration = self.context.declaration
        event = declaration.context
        location = event.location
        performances = event.performances
        estimation = event.estimated_indicators
        relevance = declaration.utilisations[0].estimated_relevance
        adjustments = declaration.utilisations[0].estimated_adjustments

        # set appstruct
        self.appstruct = {
            'event': {
                'name': event.name,
                'description': event.description,
                'location': [{
                    'mode':
                        Location.is_foreign_editable(web_user, location)
                        and 'edit' or 'add',
                    'oid': location.oid,
                    'name': location.name,
                    'category': location.category.code,
                    'street': location.street,
                    'postal_code': location.postal_code,
                    'city': location.city,
                    'country': location.country.code,
                }],
                'performances': [],
            },
            'confirmation': {
                'start': utc_to_timezone(self.request, estimation.start),
                'end': utc_to_timezone(self.request, estimation.end),
                'attendants': estimation.attendants,
                'max_attendants': estimation.max_attendants,
                'max_admission': estimation.max_admission,
                'turnover_tickets': estimation.turnover_tickets,
                'turnover_benefit': estimation.turnover_benefit,
                'expenses_musicians': estimation.expenses_musicians,
                'expenses_production': estimation.expenses_production,
            },
            'utilisation': {
                'relevance': relevance.category.oid,
                'adjustments': [{
                    'mode': 'add',
                    'oid': adjustment.oid,
                    'category': adjustment.category.code,
                    'status': adjustment.status,
                    'value': adjustment.value,
                } for adjustment in adjustments],
            },
        }

        # performances
        for performance in performances:
            # performance
            _performance = {
                'mode': 'edit',
                'oid': performance.oid,
                'start': utc_to_timezone(self.request, performance.start),
                'end': utc_to_timezone(self.request, performance.end),
            }
            # artist
            editable = Artist.is_foreign_editable(web_user, performance.artist)
            email = ''
            if editable:
                email = getattr(performance.artist.party, 'email', '')
            _performance['artist'] = [{
                'mode': editable and 'edit' or 'add',
                'oid': performance.artist.oid,
                'code': performance.artist.code,
                'name': performance.artist.name,
                'email': email,
            }]
            self.appstruct['event']['performances'].append(_performance)

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def confirm_declaration(self):
        # shortcuts: objects
        web_user = self.request.web_user
        declaration = self.context.declaration
        utilisation = declaration.utilisations[0]
        relevance = utilisation.estimated_relevance
        event = declaration.context
        location = event.location

        # shortcuts: appstruct
        _event = self.appstruct['event']
        _location = _event['location'][0]
        _confirm = self.appstruct['confirmation']
        _utilisation = self.appstruct['utilisation']
        _adjustments = _utilisation['adjustments']

        # --- event -----------------------------------------------------------

        # location: add
        if _location['mode'] == 'add':
            if location.oid != _location['oid']:
                location = Location.search_by_oid(_location['oid'])

        # location: edit
        elif _location['mode'] == 'edit':
            if Location.is_foreign_editable(web_user, location):
                location.name = _location['name']
                if location.category.oid != _location['oid']:
                    location.category = LocationCategory.search_by_code(
                        _location['category'])
                location.street = _location['street']
                location.postal_code = _location['postal_code']
                location.city = _location['city']
                if location.country.code != _location['country']:
                    location.country = Country.search_by_code(
                        _location['country'])
                location.save()

        # location: create
        # TODO: delete orphaned location on delete and create new?
        elif _location['mode'] == 'create':
            location_category = LocationCategory.search_by_code(
                _location['category'])
            country = Country.search_by_code(_location['country'])
            location_vlist = {
                'name': _location['name'],
                'category': location_category,
                'public': False,
                'street': _location['street'],
                'postal_code': _location['postal_code'],
                'city': _location['city'],
                'country': country,
                'entity_origin': 'indirect',
                'entity_creator': web_user.party,
            }
            location, = Location.create([location_vlist])

        # performances: edit, create
        performances = []
        for _performance in _event['performances']:
            # find corresponding performance db entry
            performance = False
            for item in event.performances:
                if item.oid == _performance['oid']:
                    performance = item
                    break

            # artist: add
            artist = performance and performance.artist or False
            _artist = _performance['artist'][0]
            if _artist['mode'] == 'add':
                if not artist or artist.oid != _artist['oid']:
                    artist = Artist.search_by_oid(_artist['oid'])

            # artist: edit
            elif _artist['mode'] == 'edit':
                if not artist:
                    raise HTTPBadRequest()
                if not Artist.is_foreign_editable(web_user, artist):
                    raise HTTPForbidden()
                artist.party.name = _artist['name']
                artist.party.save()
                email = artist.party.contact_mechanism_get('email')
                email.value = _artist['email']
                email.save()
                artist.name = _artist['name']
                artist.save()

            # artist: create
            elif _artist['mode'] == 'create':
                artist = Artist.create_foreign(
                    party=web_user.party,
                    name=_artist['name'],
                    email=_artist['email'],
                )

            # performance: edit
            if _performance['mode'] == 'edit':
                if not performance:
                    raise HTTPBadRequest()
                performance.start = _performance['start']
                performance.end = _performance['end']
                performance.artist = artist

            # performance: create
            elif _performance['mode'] == 'create':
                performance, = EventPerformance.create([{
                    'event': event,
                    'start': _performance['start'],
                    'end': _performance['end'],
                    'artist': artist,
                }])

            performances.append(performance)

        # performances: delete
        # TODO: delete orphaned performance artist?
        new_oids = {perf['oid'] for perf in _event['performances']}
        EventPerformance.delete([
            performance
            for performance in event.performances
            if performance.oid not in new_oids
        ])

        # event: confirmed indicators
        event_confirmed_indicators_vlist = {
            'start': _confirm['start'],
            'end': _confirm['end'],
            'attendants': _confirm['attendants'],
            'max_attendants': _confirm['max_attendants'],
            'max_admission': _confirm['max_admission'],
            'turnover_tickets': _confirm['turnover_tickets'],
            'turnover_benefit': _confirm['turnover_benefit'],
            'expenses_musicians': _confirm['expenses_musicians'],
            'expenses_production': _confirm['expenses_production'],
        }
        event_confirmed_indicators, = EventIndicators.create(
            [event_confirmed_indicators_vlist])

        # event
        event, = event.browse([event.id])  # refresh needed
        event.name = _event['name']
        event.description = _event['description']
        event.location = location
        event.performances = performances
        event.confirmed_indicators = event_confirmed_indicators
        event.save()

        # --- utilisation -----------------------------------------------------

        # utilisation: relevance
        relevance_category = relevance.category
        if relevance_category.oid == _utilisation['relevance']:
            # no category change
            relevance_value = relevance.value
            relevance_deviation = relevance.deviation
            relevance_deviation_reason = relevance.deviation_reason
        else:
            # category change
            relevance_category = TariffRelevanceCategory.search_by_oid(
                _utilisation['relevance'])
            relevance_value = relevance_category.value_default
            relevance_deviation = False
            relevance_deviation_reason = ''
        relevance_vlist = {
            'category': relevance_category,
            'value': relevance_value,
            'deviation': relevance_deviation,
            'deviation_reason': relevance_deviation_reason,
        }
        relevance, = TariffRelevance.create([relevance_vlist])

        # utilisation: adjustments
        adjustments_vlist = []
        for _adjustment in _adjustments:
            adjustment = False
            for item in utilisation.estimated_adjustments:
                if item.oid == _adjustment['oid']:
                    adjustment = item
                    break
            if adjustment:
                # existing adjustment
                adjustment_category = adjustment.category
                adjustment_status = adjustment.status
                adjustment_value = adjustment.value
                adjustment_deviation = adjustment.deviation
                adjustment_deviation_reason = adjustment.deviation_reason
            else:
                # new adjustment
                adjustment_category = TariffAdjustmentCategory.search_by_code(
                    _adjustment['category'], utilisation.tariff.category.code)
                adjustment_status = 'on_approval'
                adjustment_value = adjustment_category.value_default
                adjustment_deviation = False
                adjustment_deviation_reason = ''
            adjustments_vlist.append({
                'category': adjustment_category,
                'status': adjustment_status,
                'value': adjustment_value,
                'deviation': adjustment_deviation,
                'deviation_reason': adjustment_deviation_reason,
            })

        # utilisation: confirmed indicators
        utilisation_confirmed_indicators_vlist = {
            'relevance': relevance,
            'adjustments': [('create', adjustments_vlist)],
        }
        utilisation_confirmed_indicators, = UtilisationIndicators.create(
            [utilisation_confirmed_indicators_vlist])

        # utilisation
        utilisation, = utilisation.browse([utilisation.id])  # refresh needed
        utilisation.state = 'confirmed'
        utilisation.confirmed_indicators = utilisation_confirmed_indicators
        utilisation.save()

        # --- processing ------------------------------------------------------

        # user feedback
        log.info("declaration confirm successful for %s: %s" % (
            web_user, declaration))
        self.request.session.flash(
            _(u"Declaration confirmed."),
            'main-alert-success'
        )

        # redirect
        self.redirect(DeclarationsResource, declaration.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

class LiveSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    event = EventSchema()
    confirmation = EventIndicatorsSchema(title=_("Confirmation"))
    utilisation = UtilisationOnetimeSchema()


# --- Forms -------------------------------------------------------------------

def live_form(request):
    return deform.Form(
        schema=LiveSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _("Confirm")),
        ]
    )
