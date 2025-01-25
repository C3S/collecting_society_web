# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform
from pyramid.httpexceptions import HTTPBadRequest

from portal_web.models import Tdb, Country, Party
from portal_web.views.forms import FormController
from portal_web.views.forms.deform.money_input import MoneyInputField

from ...services import _
from ...resources import DeclarationsResource
from ...models import (
    Artist,
    Event,
    Declaration,
    DistributionPlan,
    Location,
    LocationCategory,
    Tariff,
    TariffAdjustmentCategory,
    TariffCategory,
    TariffRelevance,
    TariffRelevanceCategory,
)
from .datatables import (
    LocationSequence,
    PerformanceSequence,
    TariffAdjustmentSequence,
)

log = logging.getLogger(__name__)


class AddDeclarationLive(FormController):
    """
    form controller for creation of declarations with tariff live
    """

    def controller(self):
        self.form = live_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.create_declaration()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_declaration(self):
        web_user = self.request.web_user

        # appstruct shortcuts
        _event = self.appstruct['event']
        _location = _event['location'][0]
        _estimation = self.appstruct['estimation']
        _utilisation = self.appstruct['utilisation']
        _adjustments = _utilisation['adjustments']

        # prepare: tariff
        tariff_category_code = self.request.view_name
        tariff_category_codes = [
            tariff_category.code
            for tariff_category in TariffCategory.search_all()
        ]
        if tariff_category_code not in tariff_category_codes:
            raise HTTPBadRequest()
        tariff = Tariff.search_latest_by_category_code(self.request.view_name)
        if not tariff:
            raise HTTPBadRequest()

        # prepare: period
        if tariff.category.code in ['L']:
            period = 'onetime'
        else:
            period = self.appstruct['utilisation']['period']

        # prepare: adjustments
        adjustments_vlist = []
        for adjustment in _adjustments:
            if adjustment['mode'] != 'create':
                continue
            category = TariffAdjustmentCategory.search_by_code(
                adjustment['category'], tariff.category.code)
            adjustments_vlist.append({
                'category': category,
                'value': category.value_default,
            })

        # prepare: performances
        _performances = []
        for performance in _event['performances']:
            if performance['mode'] != 'create':
                continue

            # artist
            _artist = performance['artist'][0]
            if _artist['mode'] == 'add':
                artist = Artist.search_by_code(_artist['code'])
            elif _artist['mode'] == 'create':
                # party
                artist_party_vlist = {
                    'name': _artist['name'],
                    'contact_mechanisms': [(
                        'create',
                        [{
                            'type': 'email',
                            'value': _artist['email'],
                        }]
                    )]
                }
                artist_party, = Party.create([artist_party_vlist])
                # artist
                artist_vlist = {
                    'name': _artist['name'],
                    'description': "",
                    'group': False,
                    'party': artist_party,
                    'entity_creator': web_user.party,
                    'entity_origin': 'indirect',
                    'claim_state': 'unclaimed',
                }
                artist, = Artist.create([artist_vlist])

            # performance
            _performances.append({
                'start': performance['start'],
                'end': performance['end'],
                'artist': artist,
            })

        # prepare: others
        distribution_plan = DistributionPlan.search_latest()
        location_category = LocationCategory.search_by_code(
            _location['category'])
        country = Country.search_by_code(_location['country'])
        tariff_relevance_category = TariffRelevanceCategory.search_by_oid(
            _utilisation['relevance'])

        # create location
        if _location['mode'] == 'add':
            location = Location.search_by_oid(_location['oid'])
        elif _location['mode'] == 'create':
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

        # create event
        event_vlist = {
            'name': _event['name'],
            'description': _event['description'],
            'location': location,
            'performances': [('create', _performances)],
            'estimated_start': _estimation['start'],
            'estimated_end': _estimation['end'],
            'estimated_attendants': _estimation['attendants'],
            'estimated_max_attendants': _estimation['max_attendants'],
            'estimated_max_admission': _estimation['max_admission'],
            'estimated_turnover_tickets': _estimation['turnover_tickets'],
            'estimated_turnover_benefit': _estimation['turnover_benefit'],
            'estimated_expenses_musicians': _estimation['expenses_musicians'],
            'estimated_expenses_production':
                _estimation['expenses_production'],
        }
        event, = Event.create([event_vlist])

        # create tariff relevance
        tariff_relevance_vlist = {
            'category': tariff_relevance_category,
            'value': tariff_relevance_category.value_default,
        }
        tariff_relevance, = TariffRelevance.create([tariff_relevance_vlist])

        # create declaration
        declaration_vlist = {
            'licensee': web_user.party,
            'state': 'submitted',
            'tariff': tariff,
            'period': period,
            'context': event,
            'utilisations': [('create', [{
                'licensee': web_user.party,
                'state': 'estimated',
                'tariff': tariff,
                'distribution_plan': distribution_plan,
                'context': event,
                'estimated_relevance': tariff_relevance,
                'estimated_adjustments': [('create', adjustments_vlist)]
            }])]
        }
        declaration = Declaration.create([declaration_vlist])

        # user feedback
        if not declaration:
            log.info("declaration add failed for %s: %s" % (
                web_user, declaration_vlist))
            self.request.session.flash(
                _(u"Declaration could not be added."),
                'main-alert-danger'
            )
            self.redirect(DeclarationsResource)
            return
        declaration = declaration[0]
        log.info("declaration add successful for %s: %s" % (
            web_user, declaration))
        self.request.session.flash(
            _(u"Declaration added."),
            'main-alert-success'
        )

        # redirect
        self.redirect(DeclarationsResource, declaration.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

period_options = (
    ('monthly', _('Monthly')),
    ('quarterly', _('Quarterly')),
    ('yearly', _('Yearly')),
)


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def current_tariff_relevance_category_select_widget(node, kw):
    tariff_category = None
    tariff_categories = TariffCategory.search_all()
    for category in tariff_categories:
        if category.code == kw['request'].view_name:
            tariff_category = category
            break
    values = []
    if tariff_category:
        values = [(category.oid,
                   f"{category.name} ({category.value_default})")
                  for category in tariff_category.relevance_categories]
    widget = deform.widget.SelectWidget(values=values)
    return widget


# --- Fields ------------------------------------------------------------------

@colander.deferred
def deferred_period_missing(node, kw):
    tariff_category_code = kw['request'].view_name
    if tariff_category_code in ['L']:
        return ""
    return colander.required


# --- Utilisation

class PeriodField(colander.SchemaNode):
    oid = "period"
    schema_type = colander.String
    widget = deform.widget.SelectWidget(values=period_options)
    missing = deferred_period_missing


class RelevanceField(colander.SchemaNode):
    oid = "relevance"
    schema_type = colander.String
    widget = current_tariff_relevance_category_select_widget


# --- EventIndicators

class EventStartField(colander.SchemaNode):
    oid = "start"
    schema_type = colander.DateTime


class EventEndField(colander.SchemaNode):
    oid = "end"
    schema_type = colander.DateTime


class EventAttendantsField(colander.SchemaNode):
    oid = "attendants"
    schema_type = colander.Integer


class EventMaxAttendantsField(colander.SchemaNode):
    oid = "max_attendants"
    schema_type = colander.Integer


class EventMaxAdmissionField(MoneyInputField):
    oid = "max_admission"


class EventTurnoverTicketsField(MoneyInputField):
    oid = "turnover_tickets"


class EventTurnoverBenefitField(MoneyInputField):
    oid = "turnover_benefit"


class EventExpensesMusiciansField(MoneyInputField):
    oid = "expenses_musicians"


class EventExpensesProductionField(MoneyInputField):
    oid = "expenses_production"


# --- Event

class EventNameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


class EventDescriptionField(colander.SchemaNode):
    oid = "description"
    schema_type = colander.String
    widget = deform.widget.TextAreaWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class UtilisationOnetimeSchema(colander.Schema):
    title = _("Adjustments")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    relevance = RelevanceField()
    adjustments = TariffAdjustmentSequence(title=_("Adjustments"))


class UtilisationPeriodSchema(colander.Schema):
    title = _("Adjustments")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    relevance = RelevanceField()
    period = PeriodField()
    adjustments = TariffAdjustmentSequence(title=_("Adjustments"))


class EventIndicatorsSchema(colander.Schema):
    title = _("Estimation")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    start = EventStartField()
    end = EventEndField()
    attendants = EventAttendantsField()
    max_attendants = EventMaxAttendantsField()
    max_admission = EventMaxAdmissionField()
    turnover_tickets = EventTurnoverTicketsField()
    turnover_benefit = EventTurnoverBenefitField()
    expenses_musicians = EventExpensesMusiciansField()
    expenses_production = EventExpensesProductionField()


class EventSchema(colander.Schema):
    title = _("Event")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    name = EventNameField()
    description = EventDescriptionField()
    location = LocationSequence(title=_("Location"), min_len=1, max_len=1)
    performances = PerformanceSequence(title=_("Performances"), min_len=1)


class LiveSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    event = EventSchema()
    estimation = EventIndicatorsSchema()
    utilisation = UtilisationOnetimeSchema()


# --- Forms -------------------------------------------------------------------

def live_form(request):
    return deform.Form(
        schema=LiveSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _("Submit")),
        ]
    )
