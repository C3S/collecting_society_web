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

class CreateArtistMember(FormController):
    """
    form controller for creating members to add to group artists
    """

    def controller(self):
        self.form = create_artist_form(self.request)
        # if search name given, save into session and render it
        if getattr(self.context, 'search_string', False):
            self.data['name'] = self.context.search_string
            self.render({'name': self.data['name']})
        # if no search term given
        else:
            # hide form
            self.response = {}
            # or process it, if submitted
            if self.submitted() and self.validate(data=True):
                self.create_artist()
        # return response
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_artist(self):
        self.request.session.flash(
            _(u"Artist theoretically added!"),
            'main-alert-success'
        )
        self.redirect(ArtistResource, 'show', self.context.group.code)

        # email = self.request.unauthenticated_userid
        # party = WebUser.current_party(self.request)

        # log.debug(
        #     (
        #         "self.appstruct: %s\n"
        #     ) % (
        #         self.appstruct
        #     )
        # )

        # _artist = {
        #     'group': self.appstruct['metadata']['group'],
        #     'party': party,
        #     'entity_creator': party,
        #     'name': self.appstruct['metadata']['name'],
        #     'description': self.appstruct['metadata']['description'] or '',
        # }
        # if self.appstruct['metadata']['picture']:
        #     with open(self.appstruct['metadata']['picture']['fp'].name,
        #               mode='rb') as picfile:
        #         picture_data = picfile.read()
        #     mimetype = self.appstruct['metadata']['picture']['mimetype']
        #     _artist['picture_data'] = picture_data
        #     _artist['picture_data_mime_type'] = mimetype

        # artists = Artist.create([_artist])

        # if not artists:
        #     log.info("artist add failed for %s: %s" % (email, _artist))
        #     self.request.session.flash(
        #         _(u"Artist could not be added: ") + _artist['name'],
        #         'main-alert-danger'
        #     )
        #     self.redirect(ArtistResource, 'list')
        #     return
        # artist = artists[0]

        # log.info("artist add successful for %s: %s" % (email, artist))
        # self.request.session.flash(
        #     _(u"Artist added: ") + artist.name + " (" + artist.code + ")",
        #     'main-alert-success'
        # )

        # self.redirect(ArtistResource, 'show', artist.code)


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    validator = colander.Email()


# --- Schemas -----------------------------------------------------------------

class CreateArtistSchema(colander.Schema):
    name = NameField(
        title=_(u"Name"),
        widget=deform.widget.TextInputWidget(readonly=True)
    )
    email = EmailField(
        title=_(u"Email")
    )


# --- Forms -------------------------------------------------------------------

def create_artist_form(request):
    return deform.Form(
        schema=CreateArtistSchema().bind(request=request),
        buttons=[
            deform.Button('create', _(u"Create new artist"))
        ]
    )
