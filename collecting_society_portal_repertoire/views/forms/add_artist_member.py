# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
import logging

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController
from ...services import _
from ...models import Artist

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddArtistMember(FormController):
    """
    form controller for adding existing members to group artists
    """

    def controller(self):
        # add form
        self.form = add_artists_form(self.request)
        if self.submitted() and self.validate():
            self.add_artist()
        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )
        # return response
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def add_artist(self):
        pass

    # @Tdb.transaction(readonly=True)
    # def search_artists(self, search_string):
    #     artists = Artist.search_fulltext(search_string)
    #     self.response.update({'artists': artists})


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

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


# --- Schemas -----------------------------------------------------------------

class ArtistSchema(colander.Schema):
    mode = ModeField()
    name = NameField()
    code = CodeField()
    email = EmailField()
    title = ""


class ArtistSequence(colander.SequenceSchema):
    artist = ArtistSchema()
    widget = deform.widget.SequenceWidget(
        template='datatables/sequence',
        item_template='datatables/sequence_item',
        category='structural'
    )


class AddArtistsSchema(colander.Schema):
    artists = ArtistSequence(title="")


# --- Forms -------------------------------------------------------------------

def add_artists_form(request):
    return deform.Form(
        schema=AddArtistsSchema().bind(request=request)
    )
