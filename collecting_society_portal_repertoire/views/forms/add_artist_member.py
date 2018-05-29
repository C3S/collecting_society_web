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
        # hide add form, if no search string is given
        if not getattr(self.context, 'search_string', False):
            return {}
        # add form
        self.form = add_artists_form(self.request)
        # search artists
        self.search_artists(self.context.search_string)
        # return response
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=True)
    def search_artists(self, search_string):
        artists = Artist.search_fulltext(search_string)
        self.response.update({'artists': artists})


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


# --- Schemas -----------------------------------------------------------------

class SearchArtistsSchema(colander.Schema):
    name = NameField(
        title=_(u"Name")
    )


# --- Forms -------------------------------------------------------------------

def add_artists_form(request):
    return deform.Form(
        schema=SearchArtistsSchema().bind(request=request),
        buttons=[
            deform.Button('search', _(u"Search artist"))
        ]
    )
