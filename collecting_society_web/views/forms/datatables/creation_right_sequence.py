# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from pyramid.i18n import get_localizer

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _
from ....models import CreationRightsholder, Instrument

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


# --- Widgets -----------------------------------------------------------------


@colander.deferred
def deferred_instrument_widget(node, kw):
    instruments = Instrument.search_all()
    inst_options = [(inst.oid, unicode(inst.name)) for inst in instruments]
    widget = deform.widget.Select2Widget(values=inst_options, multiple=True)
    return widget


# --- Fields ------------------------------------------------------------------


@colander.deferred
def creation_right_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/creation_right_sequence'
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


class RightField(colander.SchemaNode):
    oid = "right"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=right_options, multiple=False)


class ContributionField(colander.SchemaNode):
    oid = "contribution"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=contribution_options, 
                                         multiple=False)


class InstrumentsField(colander.SchemaNode):
    oid = "instruments"
    schema_type = colander.Set
    widget = deferred_instrument_widget


# --- Schemas -----------------------------------------------------------------

class CreationRightSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    right = RightField()
    contribution = ContributionField()
    instruments = InstrumentsField()
    title = ""


class CreationRightSequence(DatatableSequence):
    creation_right_sequence = CreationRightSchema()
    widget = creation_right_sequence_widget
    actions = ['create', 'edit']
