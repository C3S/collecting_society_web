# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController

from ...services import _
from ...models import (
    CollectingSociety,
    TariffCategory,
    Artist,
    Creation,
    CreationContribution,
    CreationDerivative,
    CreationTariffCategory,
    CreationRole,
    Content
)
from .add_creation import (
    AddCreationSchema,
    validate_content
)

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditCreation(FormController):
    """
    form controller for edit creation
    """

    def controller(self):
        self.form = edit_creation_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_creation()
        else:
            self.edit_creation()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_creation(self):
        creation = self.context.creation
        web_user = self.request.web_user

        # set appstruct
        self.appstruct = {
            'metadata': {
                'title':  creation.title or '',
                'artist': creation.artist.id,
                'tariff_categories': []
            },
            'lyrics': {
                'lyrics': creation.lyrics
            }
        }

        # tariff categories
        if creation.tariff_categories:
            for ctc in creation.tariff_categories:
                self.appstruct['metadata']['tariff_categories'].append({
                    'mode': 'edit',
                    'oid': ctc.oid,
                    'category': ctc.category.oid,
                    'collecting_society': ctc.collecting_society.oid
                    })

        # contributions
        if creation.contributions:
            _contributions = []
            for contribution in creation.contributions:
                artist_mode = 'add'
                artist_email = ''
                if Artist.is_foreign_contributor(
                        self.request, contribution, contribution.artist):
                    artist_mode = 'edit'
                    artist_email = contribution.artist.party.email
                role_oid = ''
                if contribution.roles:
                    role_oid = contribution.roles[0].oid
                cs_name = ''
                if contribution.collecting_society:
                    cs_name = contribution.collecting_society.name
                nrs_name = ''
                if contribution.neighbouring_rights_society:
                    nrs_name = contribution.neighbouring_rights_society.oid
                _contributions.append({
                    'mode': 'edit',
                    'oid': contribution.oid,
                    'contribution_type': contribution.type,
                    'performance': contribution.performance or '',
                    'role': role_oid,
                    'collecting_society': cs_name,
                    'neighbouring_rights_society': nrs_name,
                    'artist': [{
                        'mode': artist_mode,
                        'oid': contribution.artist.oid,
                        'name': contribution.artist.name,
                        'code': contribution.artist.code,
                        'description': contribution.artist.description or '',
                        'email': artist_email
                    }]
                })
            self.appstruct['contributions'] = {
                'contributions': _contributions
            }

        # original works, this creation is derived from
        if creation.original_relations:
            _originals = []
            for original_relation in creation.original_relations:
                original_mode = "add"
                if (
                    Creation.is_foreign_creation(
                        web_user,
                        original_relation.original_creation
                    )
                ):
                    original_mode = "edit"
                _originals.append({
                        'mode': 'edit',
                        'oid': original_relation.oid,
                        'type': original_relation.allocation_type,
                        'original': [{
                            'mode': original_mode,
                            'code': original_relation.original_creation.
                                code,
                            'oid': original_relation.original_creation.
                                oid,
                            'titlefield': original_relation.
                                original_creation.title,
                            'artist': original_relation.original_creation.
                                artist.name
                        }]
                    })
            self.appstruct['originals'] = {
                'originals': _originals
            }

        # content files that are assigned to the creation
        if creation.content:
            _contentfiles = []
            for contentfile in creation.content:
                _contentfiles.append(
                    {
                        'mode': 'add',
                        'oid': contentfile.oid,
                        'code': contentfile.code,
                        'name': contentfile.name,
                        'category': contentfile.category
                    }
                )
            self.appstruct['content'] = {
                'content': _contentfiles
            }

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_creation(self):
        a = self.appstruct
        web_user = self.request.web_user
        party = self.request.party
        creation = self.context.creation

        # (working) title
        if a['metadata']['title']:
            creation.title = a['metadata']['title']

        # artist
        if a['metadata']['artist']:
            creation.artist = a['metadata']['artist']

        # lyrics
        if a['lyrics']['lyrics']:
            creation.lyrics = a['lyrics']['lyrics']

        # contributions
        _contributions = self.appstruct['contributions']['contributions']
        if _contributions:
            for _contribution in _contributions:
                _artist = _contribution['artist'][0]
                _cs = _contribution['collecting_society']
                _nrs = _contribution['neighbouring_rights_society']
                _type = _contribution['contribution_type']
                _role = _contribution['role']

                # create contribution
                if _contribution['mode'] == "create":

                    # create artist
                    if _artist['mode'] == "create":
                        artist = Artist.create_foreign(
                            party, _artist['name'], _artist['email'],
                            group=False)
                        if not artist:
                            continue

                    # add artist
                    else:
                        artist = Artist.search_by_oid(_artist['oid'])
                        if not artist:
                            continue

                    # prepare contribution
                    create = {
                        'creation': creation.id,
                        'artist': artist.id,
                        'type': _contribution['contribution_type']
                    }
                    # type: text
                    if _type == 'text' and _cs:
                        cs = CollectingSociety.search_by_oid(_cs)
                        if not cs:
                            continue
                        create['collecting_society'] = cs.id
                    # type: composition
                    if _type == 'composition' and _role:
                        role = CreationRole.search_by_oid(_role)
                        if not role:
                            continue
                        create['roles'] = [('add', [role.id])]
                    # type: performance
                    if _type == 'performance':
                        create['performance'] = _contribution['performance']
                        if _role:
                            role = CreationRole.search_by_oid(_role)
                            if not role:
                                continue
                            create['roles'] = [('add', [role.id])]
                        if _nrs:
                            nrs = CollectingSociety.search_by_oid(_nrs)
                            if not nrs:
                                continue
                            create['neighbouring_rights_society'] = nrs.id
                    # append contribution
                    CreationContribution.create([create])

                # create contribution
                if _contribution['mode'] == "edit":
                    contribution = CreationContribution.search_by_oid(
                        _contribution['oid'])
                    if not contribution or not contribution.creation.permits(
                            web_user, 'edit_creation'):
                        continue

                    # create artist
                    if _artist['mode'] == "create":
                        artist = Artist.create_foreign(
                            party, _artist['name'], _artist['email'],
                            group=False)
                        if not artist:
                            continue

                    # add artist
                    else:
                        artist = Artist.search_by_oid(_artist['oid'])
                        if not artist:
                            continue

                        # edit artist
                        if _artist['mode'] == "edit":
                            if not Artist.is_foreign_contributor(
                                    self.request, contribution,
                                    contribution.artist):
                                continue
                            artist.name = _artist['name']
                            has_email = False
                            if artist.party.contact_mechanisms:
                                for contact in artist.party.contact_mechanisms:
                                    if contact.type == 'email':
                                        has_email = True
                                        contact.email = _artist['email']
                                        contact.save()
                            if not has_email:
                                # TODO: find out, how to create a new contact
                                # mechanism without user validation error
                                log.debug("warning: email not created (TODO)")
                            artist.save()

                    contribution.roles = []
                    contribution.performance = None
                    contribution.collecting_society = None
                    contribution.neighbouring_rights_society = None
                    contribution.type = _contribution['contribution_type']
                    # type: text
                    if _type == 'text' and _cs:
                        cs = CollectingSociety.search_by_oid(_cs)
                        if not cs:
                            continue
                        contribution.collecting_society = cs.id
                    # type: composition
                    if _type == 'composition' and _role:
                        role = CreationRole.search_by_oid(_role)
                        if not role:
                            continue
                        contribution.roles = [role.id]
                    # type: performance
                    if _type == 'performance':
                        contribution.performance = _contribution['performance']
                        if _role:
                            role = CreationRole.search_by_oid(_role)
                            if not role:
                                continue
                            contribution.roles = [role.id]
                        if _nrs:
                            nrs = CollectingSociety.search_by_oid(_nrs)
                            if not nrs:
                                continue
                            contribution.neighbouring_rights_society = nrs.id
                    contribution.save()

        # look for removed originals
        # originals = CreationDerivative.search_originals_of_creation_by_id(
        #    creation.id)
        originals = creation.original_relations
        oids_to_preserve = []
        for a_original in a['originals']['originals']:
            # sanity: already in list? then it must be a dupe: only add once
            if a_original['oid'] not in oids_to_preserve:
                oids_to_preserve.append(a_original['oid'])
        if originals:
            for original in originals:  # loop through database
                # original from db table no longer in appstruct?
                if original.oid not in oids_to_preserve:
                    CreationDerivative.delete([original])  # remove it from db

        # add new derivative-original relations or perform edits there
        # relations can be of allocation type 'adaption', 'cover', or 'remix'
        # (objects starting with a_ relate to form data provided by appstruct)
        for a_original_relation in a['originals']['originals']:
            a_original = a_original_relation['original'][0]

            # sanity checks
            if a_original['code'] == creation.code:  # original of self?
                self.request.session.flash(
                    _(u"Warning: A Creation cannot be the original of it self."
                      " If you do an adaption of a creation, you need to "
                      "create a new creation in order to be able to refer to "
                      "it as an original."),
                    'main-alert-warning'
                )

            # new derivative-original relation to create?
            if a_original_relation['mode'] == 'create':

                # create foreign creation
                if a_original['mode'] == 'create':
                    original = Creation.create_foreign(
                        party,
                        a_original['artist'],
                        a_original['titlefield']
                    )
                    if not original:
                        continue
                else:  # add creation
                    original = Creation.search_by_oid(a_original['oid'])
                    if not original:
                        # TODO: Userfeedback
                        continue
                _original = {
                    'original_creation': original.id,
                    'derivative_creation': creation.id,
                    'allocation_type': a_original_relation['type']
                }
                CreationDerivative.create([_original])

            # allocation_type of derivative-original relation has been changed?
            if a_original_relation['mode'] == 'edit':

                # find the derivative-original relation in the database and
                # change the allocation_type, e.g. from 'remix' to 'cover'
                existing_original_relation = CreationDerivative.search_by_oid(
                        a_original_relation['oid'])
                if not existing_original_relation:
                    continue
                existing_original_relation.allocation_type = (
                    a_original_relation['type'])

                # create foreign creation
                if a_original['mode'] == "create":
                    original = Creation.create_foreign(
                        party,
                        a_original['artist'],
                        a_original['titlefield']
                    )
                    if not original:
                        continue
                else:  # add (including edit) foreign creation
                    original = Creation.search_by_oid(a_original['oid'])
                    if not original:
                        continue
                    # edit foreign creation
                    if a_original['mode'] == "edit":
                        # form data of foreign original changed?
                        # if (original.artist.name != a_original['artist'] or
                        #         original.title != a_original['titlefield']):
                        if not original.permits(web_user, 'edit_creation'):
                            self.request.session.flash(
                                _(
                                    u"Warning: You don't have permissions "
                                    "to edit the original. Changes won't "
                                    "take effekt."
                                ),
                                'main-alert-warning'
                            )
                            continue
                        original.artist.name = a_original['artist']
                        original.artist.save()
                        original.title = a_original['titlefield']
                        original.save()

                # save derivative-original relation
                existing_original_relation.original_creation = original
                existing_original_relation.save()

        # creation tariff categories
        _ctcs = a['metadata']['tariff_categories']
        if _ctcs:
            for _ctc in _ctcs:
                if _ctc['mode'] == "add":
                    continue
                tariff_category = TariffCategory.search_by_oid(
                    _ctc['category'])
                if not tariff_category:
                    continue
                collecting_society = CollectingSociety.search_by_oid(
                    _ctc['collecting_society'])
                if not collecting_society:
                    continue

                # create creation tariff categories
                if _ctc['mode'] == "create":
                    # TODO: check, if category is already assigned
                    # (function in model)
                    CreationTariffCategory.create([{
                        'creation': creation.id,
                        'category': tariff_category.id,
                        'collecting_society': collecting_society.id
                    }])

                # edit creation tariff categories
                if _ctc['mode'] == "edit":
                    ctc = CreationTariffCategory.search_by_oid(_ctc['oid'])
                    if not ctc:
                        continue
                    ctc.category = tariff_category.id
                    ctc.collecting_society = collecting_society.id
                    ctc.save()

        # content
        contents_to_add = []
        for content_item in self.appstruct['content']['content']:
            content = Content.search_by_oid(content_item['oid'])
            if content:
                # content = Content.search_by_code(content_item['code'])
                # sanity checks
                # TODO: maybe something like this:
                # # is not the webusers content and wasn't there before?
                # if web_user.party != content.entity_creator:  # skip it!
                #     if content not in creation.content:
                #         self.request.session.flash(
                #             _(u"Content couldn't be added: ") + content.title,
                #             'main-alert-warning'
                #         )
                #         continue
                # Alex: better: content.permits(web_user, 'edit_content')
                contents_to_add.append(content)
        creation.content = contents_to_add

        # update creation
        creation.save()

        # user feedback
        log.info("creation edit successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation edited: ") + creation.title +
            " ("+creation.code+")", 'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(
            validator=validate_content).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
