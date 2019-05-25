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
                'artist': creation.artist.id
            },
            'areas': {
            },
            'lyrics': {
                'lyrics': creation.lyrics
            }
        }

        # tariff categories
        tcats = TariffCategory.search_all()
        for tcat in tcats:
            for creation_tcat in creation.tariff_categories:
                if creation_tcat.category.oid == tcat.oid:
                    collecting_soc_oid = creation_tcat.collecting_society.oid
                    self.appstruct['areas'][
                        'tariff_category_'+tcat.code] = collecting_soc_oid
                    break

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
            a_derivation = { 'adaption': [], 'cover':[], 'remix':[] }
            for original_relation in creation.original_relations:
                original_mode = "add"
                if (
                    Creation.is_foreign_original(
                        self.request,
                        creation,
                        original_relation.original_creation
                    )
                ):
                    original_mode = "edit"
                a_derivation[original_relation.allocation_type].append({
                    'mode': original_mode,
                    'code': original_relation.original_creation.
                        code,
                    'oid': original_relation.original_creation.
                        oid,
                    'titlefield': original_relation.
                        original_creation.title,
                    'artist': original_relation.original_creation.
                        artist.name
                })
                
            self.appstruct['derivation'] = {
                'adaption': a_derivation['adaption'],
                'cover': a_derivation['cover'],
                'remix': a_derivation['remix']
            }

        # content files that are assigned to the creation
        if creation.content:
            self.appstruct['content'] = {}            
            _contentfiles = {}
            for contentfile in creation.content:
                if contentfile.category not in _contentfiles:
                    _contentfiles[contentfile.category] = []
                _contentfiles[contentfile.category].append(
                    {
                        'mode': 'add',
                        'oid': contentfile.oid,
                        'code': contentfile.code,
                        'name': contentfile.name
                    }
                )
            for contenttype in _contentfiles.keys():
                self.appstruct['content'][contenttype] = \
                    _contentfiles[contenttype]

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
                    # look for dupes
                    # dupe_found = False
                    # for item in _contributions:
                    #     if (item['artist'][0].id == create['artist'].id and
                    #         item['role'] == create['role']):
                    #         dupe_found = True
                    #         break                    
                    # append contribution
                    #if not dupe_found:
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
        for derivation_type in [ 'adaption', 'cover', 'remix' ]:
            for a_derivation in a['derivation'][derivation_type]:
                # sanity: already in list? then it must be a dupe: only add once
                if a_derivation['oid'] not in oids_to_preserve:
                    oids_to_preserve.append(a_derivation['oid'])
        if originals:
            for original in originals:  # loop through database
                # original from db table no longer in appstruct?
                if original.oid not in oids_to_preserve:
                    CreationDerivative.delete([original])  # remove it from db

        # add new derivative-original relations or perform edits there
        # relations can be of allocation type 'adaption', 'cover', or 'remix'
        # (objects starting with a_ relate to form data provided by appstruct)
        for derivation_type in ['adaption', 'cover', 'remix']:
            for a_derivation in a['derivation'][derivation_type]:

                # sanity checks
                if a_derivation['code'] == creation.code:  # original of self?
                    self.request.session.flash(
                        _(u"Warning: A Creation cannot be the original of it self."
                          " If you do an adaption of a creation, you need to "
                          "create a new creation in order to be able to refer to "
                          "it as an original."),
                        'main-alert-warning'
                    )
                else:
                    # create foreign creation
                    if a_derivation['mode'] == 'create':
                        original = Creation.create_foreign(
                            party,
                            a_derivation['artist'],
                            a_derivation['titlefield']
                        )
                        if not original:
                            continue
                    else:  # add creation
                        original = Creation.search_by_oid(a_derivation['oid'])
                        if not original:
                            # TODO: Userfeedback
                            continue
                    a_original = {
                        'original_creation': original.id,
                        'derivative_creation': creation.id,
                        'allocation_type': derivation_type
                    }
                    CreationDerivative.create([a_original])

        # areas of exploitation / tariff categories / collecting societies 
        ctcs_to_delete = []  # collect necessary operations in list
        ctcs_to_add = []     # to minimize number of tryton calls
        tcats = TariffCategory.search_all()
        for tcat in tcats: # for each tariff category
            collecting_soc_oid_new = a['areas']['tariff_category_'+tcat.code]
            # find changes in previously stored collecting societies of creation
            ctc_oid_old = None
            for creation_tcat in creation.tariff_categories:
                if creation_tcat.category.oid == tcat.oid:
                    ctc_oid_old = creation_tcat.oid
                    break
            # collecting society association deleted for this tariff category?
            if not collecting_soc_oid_new and ctc_oid_old:
                ctc_to_delete = CreationTariffCategory.search_by_oid(ctc_oid_old)
                if ctc_to_delete:
                    ctcs_to_delete.append(ctc_to_delete)
            # new collecting society association for this tariff category?
            if collecting_soc_oid_new and not ctc_oid_old:
                collecting_society = CollectingSociety.search_by_oid(collecting_soc_oid_new)
                if collecting_society:
                    ctcs_to_add.append({
                            'creation': creation.id,
                            'category': tcat.id,
                            'collecting_society': collecting_society.id
                        })
            # collecting society association changed for this tariff category?
            if (collecting_soc_oid_new and ctc_oid_old
                    and creation_tcat.collecting_society.oid != collecting_soc_oid_new):
                ctc_to_change = CreationTariffCategory.search_by_oid(ctc_oid_old)
                collecting_society = CollectingSociety.search_by_oid(collecting_soc_oid_new)
                if ctc_to_change and collecting_society:
                    ctc_to_change.collecting_society = collecting_society
                    ctc_to_change.save()
        if ctcs_to_delete:
            CreationTariffCategory.delete(ctcs_to_delete)
        if ctcs_to_add:
            CreationTariffCategory.create(ctcs_to_add)

        # content
        contents_to_add = []
        for contenttype in self.appstruct['content'].keys():
            if self.appstruct['content'][contenttype]:
                content_new = self.appstruct['content'][contenttype][0]
                content_to_add = Content.search_by_oid(content_new['oid'])
                if not content_to_add:
                    continue
                if not content_to_add.permits(web_user, 'edit_content'):
                    continue
                contents_to_add.append(content_to_add)
        creation.content = contents_to_add

        # update creation
        creation.save()

        # user feedback
        log.info("creation edit successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation edited: ${crct} (${crco})",
              mapping={'crct': creation.title,
                       'crco': creation.code}),
            'main-alert-success'
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
