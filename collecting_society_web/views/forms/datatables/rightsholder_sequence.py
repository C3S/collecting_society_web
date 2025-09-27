# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from portal_web.models import Party

log = logging.getLogger(__name__)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    # email required for create/edit
    if value['mode'] != "add" and value['email'] == "IGNORED":
        value['email'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def rightsholder_sequence_widget(node, kw):
    request = kw.get('request')
    web_user = request.web_user
    # get initial source data
    domain = []
    rightsholders = Party.search_rightsholder(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')],
        web_user=web_user)
    source_data = [{
        'name': rightsholder.name,
        'oid': rightsholder.oid,
    } for rightsholder in rightsholders]
    # get statistics
    total_domain = []
    total = Party.search_count_rightsholder(total_domain, web_user=web_user)
    # return widget
    return DatatableSequenceWidget(
        request=request,
        template='datatables/rightsholder_sequence',
        source_data=source_data,
        source_data_total=total
    )


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


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.Email(),
        colander.Regex(r'^IGNORED\Z', '')
    )


# --- Schemas -----------------------------------------------------------------

class RightsholderSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    email = EmailField()
    preparer = [prepare_required]
    title = ""


class RightsholderSequence(DatatableSequence):
    rightsholder_sequence = RightsholderSchema()
    widget = rightsholder_sequence_widget


class RightsholderIndividual(RightsholderSequence):
    min_len = 1
    max_len = 1
