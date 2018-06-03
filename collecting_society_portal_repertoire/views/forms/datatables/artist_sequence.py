import colander
import deform


# --- Fields ------------------------------------------------------------------

@colander.deferred
def artists_sequence_widget(node, kw):
    request = kw.get('request')
    settings = request.registry.settings
    return deform.widget.SequenceWidget(
        template='datatables/artist_sequence',
        item_template='datatables/artist_sequence_item',
        category='structural',
        api=''.join([
            settings['api.datatables.url'], '/',
            settings['api.datatables.version']
        ])
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class EmailField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.Email()
    missing = ""


class KeyField(colander.SchemaNode):
    oid = "key"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


# --- Schemas -----------------------------------------------------------------

class ArtistSchema(colander.Schema):
    mode = ModeField()
    name = NameField()
    code = CodeField()
    email = EmailField()
    key = KeyField()
    title = ""


class ArtistSequence(colander.SequenceSchema):
    artist = ArtistSchema()
    widget = artists_sequence_widget
