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

class AddArtistMember(FormController):
    """
    form controller for adding members to group artists
    """

    __stage__ = "search"

    def controller(self):
        self.group = Artist.search_by_code(self.request.subpath[0])

        # search artists in database
        if self.stage == "search":
            self.stage_search()

        # create new artists
        if self.stage == "create":
            self.stage_create()

        log.debug(
            (
                "self.response: %s\n"
            ) % (
                self.response
            )
        )

        self.response.update({
            'group': self.group
        })
        return self.response

    # --- Stages --------------------------------------------------------------

    def stage_search(self):
        self.stage = "search"
        self.form = search_artists_form(self.request)
        if self.submitted("search_artists") and self.validate():
            self.form = search_artists_form(self.request, True)
            self.render(self.appstruct)
            self.search_artists()
        if self.submitted("stage_create"):
            self.stage_create()

    def stage_create(self):
        self.stage = "create"
        self.form = create_artist_form(self.request)
        self.render(self.appstruct)
        # self.render(self.data)
        if self.submitted("stage_search"):
            self.stage_search()
        if self.submitted("create_artist") and self.validate():
            self.create_artist()

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def search_artists(self):
        self.data.update(self.appstruct.copy())

    @Tdb.transaction(readonly=False)
    def create_artist(self):
        self.request.session.flash(
            _(u"Artist theoretically added!"),
            'main-alert-success'
        )
        self.redirect(ArtistResource, 'show', self.group.code)

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

class SearchArtistsSchema(colander.Schema):
    name = NameField(
        title=_(u"Name")
    )


class CreateArtistSchema(colander.Schema):
    name = NameField(
        title=_(u"Name")
    )
    email = EmailField(
        title=_(u"Email")
    )


# --- Forms -------------------------------------------------------------------

def search_artists_form(request, create_button=False):
    buttons = [
        deform.Button('search_artists', _(u"Search"))
    ]
    if create_button:
        buttons.append(deform.Button('stage_create', _(u"Create new artist")))
    return deform.Form(
        schema=SearchArtistsSchema().bind(request=request),
        buttons=buttons
    )


def create_artist_form(request):
    return deform.Form(
        schema=CreateArtistSchema().bind(request=request),
        buttons=[
            deform.Button('create_artist', _(u"Create")),
            deform.Button('stage_search', _(u"Back to Search"))
        ]
    )
