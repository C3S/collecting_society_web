# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import Tdb, Party
from portal_web.views.forms import FormController

from ...services import _
from ...models import (
    TariffCategory,
    Artist,
    Creation,
    CreationDerivative,
    CreationTariffCategory,
    CreationRight,
    Content,
    Instrument,
    CollectingSociety,
)
from .add_creation import (
    AddCreationSchema,
    validate_form,
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
        # shortcuts
        web_user = self.request.web_user
        creation = self.context.creation

        # set appstruct
        self.appstruct = {
            'metadata': {
                'title':  creation.title or '',
                'artist': creation.artist.oid
            },
            'rights': {
                'contributions': [],
            },
            'derivation': {
                'distribution_type': creation.distribution_type,
                'adaption': [],
                'cover': [],
                'remix': [],
            },
            'content': {
                'audio': [],
                'sheet': [],
            },
            'lyrics': {
                'lyrics': creation.lyrics,
            },
            'areas': {},
        }

        # rights
        _contributions = {}
        for right in creation.rights:

            # rightsholder
            rightsholder = right.rightsholder
            rightsholder_editable = Party.is_foreign_editable(
                web_user, rightsholder)
            email = ''
            if rightsholder_editable:
                email = getattr(rightsholder, 'email', '')
            if rightsholder.oid not in _contributions:
                _contributions[rightsholder.oid] = {
                    'mode': 'edit',
                    'rights': [],
                    'rightsholder': [{
                        'mode': rightsholder_editable and 'edit' or 'add',
                        'oid': rightsholder.oid,
                        'name': rightsholder.name,
                        'email': email,
                    }]
                }

            # contributions
            _contributions[rightsholder.oid]['rights'].append({
                'mode': 'edit',
                'oid': right.oid,
                'contribution': f"{right.type_of_right}-{right.contribution}",
                'instruments': [
                    instrument.oid
                    for instrument in right.instruments
                ],
                'collecting_society':
                    getattr(right.collecting_society, 'oid', None),
            })

        self.appstruct['rights']['contributions'] = list(
            _contributions.values())

        # derivation
        for original in creation.original_relations:
            original_creation = original.original_creation
            original_creation_editable = Creation.is_foreign_editable(
                web_user, original_creation)
            self.appstruct['derivation'][creation.distribution_type].append({
                'mode': original_creation_editable and 'edit' or 'add',
                'oid': original_creation.oid,
                'code': original_creation.code,
                'titlefield': original_creation.title,
                'artist': original_creation.artist.name,
            })

        # content
        for content in creation.content:
            self.appstruct['content'][content.category].append({
                'mode': 'add',
                'oid': content.oid,
                'code': content.code,
                'name': content.name,
            })

        # areas
        for area in creation.tariff_categories:
            collecting_society = area.collecting_society.oid
            self.appstruct['areas'][area.category.code] = collecting_society

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_creation(self):

        # --- shortcuts -------------------------------------------------------

        # shortcuts: objects
        web_user = self.request.web_user
        party = self.request.party
        creation = self.context.creation

        # shortcuts: appstruct
        _metadata = self.appstruct['metadata']
        _contributions = self.appstruct['rights']['contributions']
        _derivation = self.appstruct['derivation']
        _contents = [
            *self.appstruct['content'].get('audio', []),
            *self.appstruct['content'].get('sheet', []),
        ]
        _lyrics = self.appstruct['lyrics']['lyrics']
        _areas = self.appstruct['areas']

        # --- metadata --------------------------------------------------------

        # artist
        artist = creation.artist
        if artist.oid != _metadata['artist']:
            artist = Artist.search_by_oid(_metadata['artist'])
            if not artist or artist not in Artist.search_by_party(party):
                # TODO: add proper validator
                raise Exception()

        # title
        title = _metadata['title']

        # --- rights ----------------------------------------------------------

        # contributions
        rights = []
        for _contribution in _contributions:
            _rightsholder = _contribution['rightsholder'][0]
            rightsholder, = Party.search_rightsholder(
                ('oid', '=', _rightsholder['oid']), web_user=web_user)

            # rightsholder: add
            if _rightsholder['mode'] == "add":
                if not rightsholder:
                    continue

            # rightsholder: create
            elif _rightsholder['mode'] == "create":
                rightsholder = Party.create_foreign(
                    party=web_user.party,
                    name=_rightsholder['name'],
                    email=_rightsholder['email'],
                )

            # rightsholder: edit
            elif _rightsholder['mode'] == "edit":
                if not Party.is_foreign_editable(web_user, rightsholder):
                    continue
                rightsholder.name = _rightsholder['name']
                for contact in rightsholder.contact_mechanisms:
                    if contact.type == 'email':
                        contact.value = _rightsholder['email']
                        contact.save()
                rightsholder.save()

            # rightsholder: delete
            if rightsholder.oid != _rightsholder['oid']:
                # TODO: check and delete orphan
                pass

            # rights
            for _right in _contribution['rights']:
                _right_type, _contribution = _right['contribution'].split('-')
                collecting_society = CollectingSociety.search_by_oid(
                    _right['collecting_society'])
                instruments = Instrument.search_by_oids(_right["instruments"])

                # right: add
                if _right['mode'] == "add":
                    continue

                # right: create
                elif _right['mode'] == "create":
                    if _right['oid'] != "IGNORED":
                        continue
                    right, = CreationRight.create([{
                        'rightsobject': creation,
                        'rightsholder': rightsholder,
                        'type_of_right': _right_type,
                        'contribution': _contribution,
                        'collecting_society': collecting_society,
                        'instruments': [('add', instruments)],
                    }])

                # right: edit
                elif _right['mode'] == "edit":

                    # find corresponding right db entry
                    right = False
                    for item in creation.rights:
                        if item.oid == _right['oid']:
                            right = item
                            break
                    if not right:
                        continue

                    # right: edit
                    right.rightsholder = rightsholder
                    right.type_of_right = _right_type
                    right.contribution = _contribution
                    right.collecting_society = collecting_society
                    right.instruments = instruments
                    right.save()

                rights.append(right)

        # rights: delete
        # TODO: delete orphaned rightsholder
        new_oids = {right.oid for right in rights}
        CreationRight.delete([
            right
            for right in creation.rights
            if right.oid not in new_oids
        ])

        # --- derivation ------------------------------------------------------

        # original relations
        original_relations = []
        distribution_type = _derivation['distribution_type']
        for _original in _derivation.get(distribution_type, []):
            if _original['oid'] == creation.oid:
                # TODO: add validator
                continue

            # original creation: add
            if _original['mode'] == 'add':
                original = Creation.search_by_oid(_original['oid'])
                if not original:
                    continue
                # TODO: check permission (commited or foreign editable)

            # original creation: create
            elif _original['mode'] == 'create':
                original = Creation.create_foreign(
                    party=party,
                    artist_name=_original['artist'],
                    title=_original['titlefield'],
                )

            # original creation: edit
            elif _original['mode'] == 'edit':
                original = Creation.search_by_oid(_original['oid'])
                if not Creation.is_foreign_editable(web_user, original):
                    continue
                original.title = _original['titlefield']
                original.artist.name = _original['artist']
                original.artist.save()
                original.save()

            # find corresponding right db entry
            original_relation = False
            for item in creation.original_relations:
                if item.original_creation.oid == _original['oid']:
                    original_relation = item
                    break

            # original relation: create
            if not original_relation:
                original_relation, = CreationDerivative.create([{
                    'original_creation': original,
                    'derivative_creation': creation,
                }])

            # original relation: edit
            else:
                original_relation.original_creation = original

            original_relations.append(original_relation)

        # original relations: delete
        new_oids = {relation.oid for relation in original_relations}
        CreationDerivative.delete([
            relation for relation in creation.original_relations
            if relation.oid not in new_oids
        ])

        # --- content ---------------------------------------------------------

        # content
        contents = []
        for _content in _contents:
            content = Content.search_by_oid(_content['oid'])
            if not content:
                continue
            if not content.permits(web_user, 'edit_content'):
                continue
            contents.append(content)

        # --- lyrics ----------------------------------------------------------

        # lyrics
        lyrics = _lyrics

        # --- areas -----------------------------------------------------------

        # tariff categories
        tariff_categories = []
        for _category, _collecting_society in _areas.items():
            if not _collecting_society:
                continue
            collecting_society = CollectingSociety.search_by_oid(
                _collecting_society)
            if not collecting_society:
                continue

            # find corresponding right db entry
            tariff_category = False
            for item in creation.tariff_categories:
                if item.category.code == _category:
                    tariff_category = item
                    break

            # tariff category: create
            if not tariff_category:
                category = TariffCategory.search_by_code(_category)
                if not category:
                    continue
                tariff_category, = CreationTariffCategory.create([{
                    'creation': creation,
                    'category': category,
                    'collecting_society': collecting_society,
                }])

            # tariff category: edit
            else:
                tariff_category.collecting_society = collecting_society

            tariff_categories.append(tariff_category)

        # tariff categories: delete
        new_oids = {category.oid for category in tariff_categories}
        CreationTariffCategory.delete([
            category for category in creation.tariff_categories
            if category.oid not in new_oids
        ])

        # --- creation --------------------------------------------------------

        creation.artist = artist
        creation.title = title
        creation.lyrics = lyrics
        creation.rights = rights
        creation.distribution_type = distribution_type
        creation.original_relations = original_relations
        creation.content = contents
        creation.tariff_categories = tariff_categories
        creation.save()

        # --- feedback --------------------------------------------------------

        # user feedback
        log.info("creation edit successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _("Creation edited: ${crct} (${crco})",
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
        schema=AddCreationSchema(validator=validate_form).bind(
            request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
