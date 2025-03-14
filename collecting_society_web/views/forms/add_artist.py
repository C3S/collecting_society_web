# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import Tdb
from portal_web.views.forms import (
    FormController,
    deferred_file_upload_widget
)

from ...services import (_, picture_processing)
from ...models import Artist, ArtistIdentifierSpace
from .datatables import ArtistSequence

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddArtist(FormController):
    """
    form controller for creation of artists
    """

    def controller(self):
        self.form = add_artist_form(self.request)
        self.render()
        if self.submitted() and self.validate():
            self.create_artist()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_artist(self):

        # --- shortcuts -------------------------------------------------------

        # shortcuts: objects
        email = self.request.unauthenticated_userid
        web_user = self.request.web_user
        party = web_user.party

        # shortcuts: appstruct
        _group = self.appstruct['group']
        _name = self.appstruct['name']
        _ipn_code = self.appstruct['ipn_code']
        _description = self.appstruct['description'] or ''
        _picture = self.appstruct['picture']
        _members = self.appstruct['members']

        # --- ids -------------------------------------------------------------

        # ipn code
        cs_identifiers = {'create': []}
        if _ipn_code:
            cs_identifiers['create'].append({
                'space': ArtistIdentifierSpace.search_by_name('IPN'),
                'id_code': _ipn_code,
            })

        # --- picture ---------------------------------------------------------

        # picture
        if _picture:
            picture = {}
            error, picture, thumb, mime = picture_processing(_picture['fp'])
            if not error:
                picture = {
                    'picture_data': picture,
                    'picture_thumbnail_data': thumb,
                    'picture_data_mime_type': mime,
                }
            else:
                self.request.session.flash(error, 'main-alert-warning')

        # --- members ---------------------------------------------------------

        # members
        members_vlist = {'add': []}
        if _group:
            for _member in _members:

                # member: add
                if _member['mode'] == "add":
                    member = Artist.search_by_oid(_member['oid'])
                    if not member or member.group:
                        continue
                    members_vlist['add'].append(member)

                # member: create
                elif _member['mode'] == "create":
                    member = Artist.create_foreign(
                        party, _member['name'], _member['email'])
                    members_vlist['add'].append(member)

                # member: edit
                elif _member['mode'] == "edit":
                    member = Artist.search_by_oid(member['oid'])
                    if not Artist.is_foreign_editable(web_user, member):
                        continue
                    member.name = _member['name']
                    member.party.name = _member['name']
                    for contact in member.party.contact_mechanisms:
                        if contact.type == 'email':
                            contact.value = _member['email']
                            contact.save()
                    member.party.save()
                    member.save()
                    members_vlist['add'].append(member)

        # --- artist ----------------------------------------------------------

        # artist
        artist_vlist = {
            'group': _group,
            'party': party,
            'entity_creator': party,
            'entity_origin': 'direct',
            'claim_state': 'claimed',
            'name': _name,
            'description': _description,
            'cs_identifiers': list(cs_identifiers.items()),
            'solo_artists': list(members_vlist.items()),
            **picture,
        }
        artists = Artist.create([artist_vlist])

        # --- feedback --------------------------------------------------------

        # user feedback: error
        if not artists:
            log.info("artist add failed for %s: %s" % (email, artist_vlist))
            self.request.session.flash(
                _("Artist could not be added: ${artist}",
                  mapping={'artist':  artist_vlist['name']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        artist = artists[0]

        # user feedback: success
        log.info("artist add successful for %s: %s" % (email, artist_vlist))
        artists = Artist.search_by_party(party)
        is_first_artist = False
        if artists and len(artists) == 1:
            is_first_artist = True
        if is_first_artist:
            self.request.session.flash(
                _("Congratulations! You created your first artist "
                  "'${name}' (${code}). Now go back to the dashboard and "
                  "see what's next.",
                  mapping={'name': artist.name, 'code': artist.code}),
                'main-alert-success'
            )
        else:
            self.request.session.flash(
                _("Artist added:  ${name} (${code})",
                  mapping={'name': artist.name, 'code': artist.code}),
                'main-alert-success'
            )

        # redirect
        self.redirect(artist.code)


# --- Validators --------------------------------------------------------------

@colander.deferred
def deferred_validate_form(node, kw):
    request = kw['request']

    def validate_form(node, values, **kwargs):

        # groups should have at least one member
        if values['group'] and len(values['members']) < 1:
            raise colander.Invalid(
                node, _("Group artists should have at least 1 member."))

        # check for email in foreign editable members
        for _member in values['members']:
            if _member['mode'] != 'add':
                continue
            member = Artist.search_by_oid(_member['oid'])
            if Artist.is_foreign_editable(request.web_user, member):
                raise colander.Invalid(
                    node, _("Please add an email address to member ${name}.",
                            mapping={'name': _member['name']}))

    return validate_form


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class GroupField(colander.SchemaNode):
    oid = "group"
    schema_type = colander.Boolean
    widget = deform.widget.CheckboxWidget()


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String


class IpnCodeField(colander.SchemaNode):
    oid = "ipn_code"
    schema_type = colander.String
    missing = ""


class DescriptionField(colander.SchemaNode):
    oid = "description"
    schema_type = colander.String
    widget = deform.widget.TextAreaWidget()
    missing = ""


class PictureField(colander.SchemaNode):
    oid = "picture"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget
    missing = ""


# --- Schemas -----------------------------------------------------------------

class AddArtistSchema(colander.Schema):
    group = GroupField(title=_("Group"))
    name = NameField(title=_("Name"))
    ipn_code = IpnCodeField(title=_("International Performer Number"))
    description = DescriptionField(title=_("Description"))
    picture = PictureField(title=_("Picture"))
    members = ArtistSequence(title=_("Members"))


# --- Forms -------------------------------------------------------------------

def add_artist_form(request):
    return deform.Form(
        schema=AddArtistSchema(validator=deferred_validate_form).bind(
            request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
