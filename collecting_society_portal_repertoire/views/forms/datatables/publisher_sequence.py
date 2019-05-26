# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....models import Publisher


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
def publisher_sequence_widget(node, kw):
    # get initial source data
    source_data = []
    domain = []
    publishers = Publisher.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')])
    for publisher in publishers:
        source_data.append({
            'oid': publisher.oid,
            'name': publisher.name})
    # get statistics
    total_domain = []
    total = Publisher.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/publisher_sequence',
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


# --- Schemas -----------------------------------------------------------------

class PublisherSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    preparer = [prepare_required]
    title = ""


class PublisherSequence(DatatableSequence):
    publisher_sequence = PublisherSchema()
    widget = publisher_sequence_widget
