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
from ....models import (
    CollectingSociety,
    CreationRole
)

from . import ArtistSequence
from ....models import Creation

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


# --- Fields ------------------------------------------------------------------

@colander.deferred
def contribution_sequence_widget(node, kw):
    # get initial source data
    source_data = []
    domain = []
    creations = Creation.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('title', 'asc')])
    for creation in creations:
        source_data.append({
            'oid': creation.oid,
            'titlefield': creation.title,
            'artist': creation.artist.name,
            'code': creation.code})
    # get statistics
    total_domain = []
    total = Creation.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/contribution_sequence',
        item_template='datatables/contribution_sequence_item',
        source_data=source_data,
        source_data_total=total
    )


@colander.deferred
def collecting_society_widget(node, kw):
    values = [('', '')] + [
        (tc.oid, tc.name) for tc in CollectingSociety.search(
            [("represents_copyright", "=", True)])]
    return deform.widget.Select2Widget(values=values, placeholder=_("None"))


@colander.deferred
def neighbouring_rights_society_widget(node, kw):
    values = [('', '')] + [
        (tc.oid, tc.name) for tc in CollectingSociety.search(
            [("represents_ancillary_copyright", "=", True)])]
    return deform.widget.Select2Widget(values=values, placeholder=_("None"))


@colander.deferred
def deferred_role_widget(node, kw):
    values = [('', '')] + [(l.oid, l.name) for l in CreationRole.search_all()]
    return deform.widget.Select2Widget(values=values, placeholder=_("None"))


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['add', 'create', 'edit'])


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.uuid,
        colander.Regex(r'^IGNORED\Z', '')
    )


class ContributionTypeField(colander.SchemaNode):
    oid = "contribution_type"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=(
        ('composition', _('Composition')),
        ('performance', _('Performance')),
        ('text', _('Text')),
    ))
    validator = colander.OneOf(
        ['performance', 'composition', 'text'])


class PerformanceField(colander.SchemaNode):
    oid = "performance"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=(
        ('recording', _('Recording')),
        ('producing', _('Producing')),
        ('mastering', _('Mastering')),
        ('mixing', _('Mixing')),
    ))
    validator = colander.OneOf(
        ['recording', 'producing', 'mastering', 'mixing'])
    # missing = ""


class CollectingSocietyField(colander.SchemaNode):
    oid = "collecting_society"
    schema_type = colander.String
    widget = collecting_society_widget
    validator = colander.uuid
    missing = ""


class NeighbouringRightsSocietyField(colander.SchemaNode):
    oid = "neighbouring_rights_society"
    schema_type = colander.String
    widget = neighbouring_rights_society_widget
    validator = colander.uuid
    missing = ""


class RoleField(colander.SchemaNode):
    oid = "role"
    schema_type = colander.String
    validator = colander.uuid
    widget = deferred_role_widget
    missing = ""


# --- Schemas -----------------------------------------------------------------

class ContributionSchema(colander.Schema):
    oid = OidField()
    mode = ModeField()
    artist = ArtistSequence(min_len=1, max_len=1)
    contribution_type = ContributionTypeField()
    performance = PerformanceField()
    role = RoleField()
    collecting_society = CollectingSocietyField()
    neighbouring_rights_society = NeighbouringRightsSocietyField()
    preparer = [prepare_required]
    title = ""


class ContributionSequence(DatatableSequence):
    contribution_sequence = ContributionSchema()
    widget = contribution_sequence_widget
    actions = ['create', 'edit']
