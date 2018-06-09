# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform


# --- Fields ------------------------------------------------------------------

@colander.deferred
def labels_sequence_widget(node, kw):
    request = kw.get('request')
    settings = request.registry.settings
    return deform.widget.SequenceWidget(
        template='datatables/label_sequence',
        item_template='datatables/label_sequence_item',
        category='structural',
        api=''.join([
            settings['api.datatables.url'], '/',
            settings['api.datatables.version']
        ])
    )


class GvlCodeField(colander.SchemaNode):
    oid = "gvl_code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


# --- Schemas -----------------------------------------------------------------

class LabelSchema(colander.Schema):
    name = NameField()
    gvl_code = GvlCodeField()
    title = ""


class LabelSequence(colander.SequenceSchema):
    label = LabelSchema()
    widget = labels_sequence_widget
