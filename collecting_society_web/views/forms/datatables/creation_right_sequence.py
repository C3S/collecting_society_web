# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _
from ....models import CreationRight, Instrument, CollectingSociety

log = logging.getLogger(__name__)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    return value


# --- Options -----------------------------------------------------------------

right_options = [
    ('copyright', _('Copyright')),
    ('ancillary', _('Ancillary Copyright'))
]

contribution_options = [
    ('lyrics', 'Lyrics'),
    ('composition', 'Composition'),
    ('instrument', 'Instrument'),
    ('production', 'Production'),
    ('mixing', 'Mixing'),
    ('mastering', 'Mastering'),
]


# --- Validators --------------------------------------------------------------

def validate_multifield(node, values):  # multifield validator
    """Check plausibility between fields"""

    # check if contributions match rights
    ctbr = values["contribution"]
    tor = values["type_of_right"]
    ctbr_list = CreationRight.get_contributions_by_type_of_right(tor)
    if (ctbr not in ctbr_list):
        raise colander.Invalid(
            node, _(u"Contribution type '${c}' does not apply to ${r}.",
                    mapping={'c': ctbr, 'r': tor}))

    # check if collecting society represets the selected type of right
    sel_cs_oid = values["collecting_society"]
    if tor == 'copyright':
        cs_list = [tc.oid for tc in CollectingSociety.search(
            [("represents_copyright", "=", True)]
        )]
    else:  # if tor == 'ancillary copyright':
        cs_list = [tc.oid for tc in CollectingSociety.search(
            [("represents_ancillary_copyright", "=", True)]
        )]
    if sel_cs_oid and sel_cs_oid not in cs_list:
        sel_cs = CollectingSociety.search_by_oid(sel_cs_oid)
        sel_cs_name = sel_cs.name
        if not sel_cs_name:
            sel_cs_name = "Selected collecting society"
        raise colander.Invalid(
            node, _(u"${c} does not represent ${r}.",
                    mapping={'c': sel_cs_name, 'r': tor}))


# --- Widgets -----------------------------------------------------------------


@colander.deferred
def deferred_instrument_widget(node, kw):
    instruments = Instrument.search_all()
    inst_options = [
        (inst.oid, unicode(inst.name)) for inst in instruments]  # noqa: F821
    widget = deform.widget.Select2Widget(values=inst_options, multiple=True)
    return widget


@colander.deferred
def collecting_society_widget(node, kw):
    # TODO: switch between neighboring and copyright societies according to
    # type_of_right
    collecting_societies = CollectingSociety.search([])
    values = [('', '')] + [(tc.oid, tc.name) for tc in collecting_societies]
    return deform.widget.Select2Widget(values=values, placeholder=_("None"))


# --- Fields ------------------------------------------------------------------


@colander.deferred
def creation_right_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/creation_right_sequence',
        item_template='datatables/creation_right_sequence_item'
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['create', 'edit'])


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.uuid,
        colander.Regex(r'^IGNORED\Z', '')
    )


class TypeOfRightField(colander.SchemaNode):
    oid = "type_of_right"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=right_options, multiple=False)


class ContributionField(colander.SchemaNode):
    oid = "contribution"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(
        values=contribution_options, multiple=False)


class InstrumentsField(colander.SchemaNode):
    oid = "instruments"
    schema_type = colander.Set
    widget = deferred_instrument_widget


class CollectingSocietyField(colander.SchemaNode):
    oid = "collecting_society"
    schema_type = colander.String
    widget = collecting_society_widget
    validator = colander.uuid
    missing = ""

# --- Schemas -----------------------------------------------------------------


class CreationRightSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    type_of_right = TypeOfRightField()
    contribution = ContributionField()
    instruments = InstrumentsField()
    collecting_society = CollectingSocietyField()
    title = ""


class CreationRightSequence(DatatableSequence):
    creation_right_sequence = CreationRightSchema(
        validator=validate_multifield)
    widget = creation_right_sequence_widget
    actions = ['create', 'edit']
