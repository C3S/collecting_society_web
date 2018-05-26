# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
import logging

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController
from ...services import _
from ...models import Artist
from ...resources import ArtistResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class SearchArtistMember(FormController):
    """
    form controller for searching members to add to group artists
    """

    def controller(self):

        self.form = search_artists_form(self.request)
        if self.submitted() and self.validate():
            self.search_artists()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=True)
    def search_artists(self):
        self.context.search = self.appstruct['name']


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

def search_artists_form(request):
    return deform.Form(
        schema=SearchArtistsSchema().bind(request=request),
        buttons=[
            deform.Button('search', _(u"Search artist"))
        ]
    )
