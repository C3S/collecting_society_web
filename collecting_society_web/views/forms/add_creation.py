# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from itertools import combinations
import logging
import colander
import deform

from portal_web.models import (
    Tdb,
    WebUser,
    Party,
)
from portal_web.views.forms import FormController
from ...services import _
from ...models import (
    TariffCategory,
    Artist,
    Creation,
    Content,
    Instrument,
    CollectingSociety,
)
from .datatables import (
    ContentSequence,
    CreationSequence,
    CreationContributionSequence,
)
from .datatables.creation_right_sequence import get_contribution_label

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddCreation(FormController):
    """
    form controller for add creation
    """

    def controller(self):
        self.form = add_creation_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.create_creation()
        else:
            self.init_creation()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def init_creation(self):
        """
        initializes form with default values
        """
        # set appstruct
        self.appstruct = {
            'metadata': {},
            'content': {}
        }

        # add metadata from content uuid, provided by upload form
        content = getattr(self.context, 'content', False)
        if content:
            self.appstruct['metadata']['title'] = content.metadata_title
            meta_artist = Artist.search_by_name(content.metadata_artist)
            if meta_artist:
                self.appstruct['metadata']['artist'] = meta_artist[0].id
            self.appstruct['content']['audio'] = [{
                'mode': "add",
                'oid': content.oid,
                'category': content.category,
                'code': content.code,
                'name': content.name,
                'preview': bool(content.preview_path),
            }]

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def create_creation(self):

        # --- shortcuts -------------------------------------------------------

        # shortcuts: objects
        web_user = self.request.web_user
        party = self.request.party

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

        # artist: prepare
        artist = Artist.search_by_oid(_metadata['artist'])
        if not artist or artist not in Artist.search_by_party(party):
            # TODO: add proper validator
            raise Exception()

        # --- rights ----------------------------------------------------------

        # rights
        rights_vlist = {'create': []}
        for _contribution in _contributions:
            _rightsholder = _contribution['rightsholder'][0]

            # rightsholder: add
            if _rightsholder['mode'] == "add":
                rightsholder, = Party.search_rightsholder(
                    ('oid', '=', _rightsholder['oid']), web_user=web_user)
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
                continue

            # rights: prepare
            for _right in _contribution['rights']:

                # right: add, edit
                if _right['mode'] != "create":
                    continue

                # right: create
                _right_type, _contribution = _right['contribution'].split('-')
                rights_vlist['create'].append({
                    'rightsholder': rightsholder,
                    'type_of_right': _right_type,
                    'contribution': _contribution,
                    'collecting_society': CollectingSociety.search_by_oid(
                        _right['collecting_society']),
                    'instruments': [(
                        'add', Instrument.search_by_oids(_right["instruments"])
                    )],
                })

        # --- derivation ------------------------------------------------------

        # original relations
        original_relations_vlist = {'create': []}
        distribution_type = _derivation['distribution_type']
        for _original in _derivation.get(distribution_type, []):

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
                continue

            # original relations: prepare
            original_relations_vlist['create'].append({
                'original_creation': original,
            })

        # --- content ---------------------------------------------------------

        # content: prepare
        content_vlist = {'add': []}
        for _content in _contents:
            content = Content.search_by_oid(_content['oid'])
            if not content:
                continue
            if not content.permits(web_user, 'edit_content'):
                continue
            content_vlist['add'].append(content)

        # --- lyrics ----------------------------------------------------------

        # lyrics
        lyrics = _lyrics

        # --- areas -----------------------------------------------------------

        # tariff categories: prepare
        tariff_categories_vlist = {'create': []}
        for _category, _collecting_society in _areas.items():
            if not _collecting_society:
                continue
            collecting_society = CollectingSociety.search_by_oid(
                _collecting_society)
            if not _collecting_society:
                continue
            tariff_category = TariffCategory.search_by_code(_category)
            if not tariff_category:
                continue
            tariff_categories_vlist['create'].append({
                'category': tariff_category,
                'collecting_society': collecting_society,
            })

        # --- creation --------------------------------------------------------

        # creation: create
        creation_vlist = {
            'title': _metadata['title'],
            'artist': artist,
            'lyrics': lyrics,
            'entity_creator': party,
            'rights': list(rights_vlist.items()),
            'distribution_type': distribution_type,
            'original_relations': list(original_relations_vlist.items()),
            'content': list(content_vlist.items()),
            'tariff_categories': list(tariff_categories_vlist.items()),
        }
        creations = Creation.create([creation_vlist])

        # --- feedback --------------------------------------------------------

        # user feedback: error
        if not creations:
            log.info(
                "creation add failed for %s: %s"
                % (web_user, creation_vlist))
            self.request.session.flash(
                _("Creation could not be added: ${creation}",
                  mapping={'creation': creation_vlist['title']}),
                'main-alert-danger')
            self.redirect()
            return
        creation = creations[0]

        # user feedback: success
        log.info(
            "creation add successful for %s: %s"
            % (web_user, creation))
        self.request.session.flash(
            _("Creation added:  ${title} (${code})",
              mapping={'title': creation.title,
                       'code': creation.code}),
            'main-alert-success')

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

def validate_form(node, values, **kwargs):
    request = node.bindings["request"]

    # content
    edit_creation_code = getattr(request.context, 'code', None)
    _contents = [
        *values['content'].get('sheet', []),
        *values['content'].get('audios', []),
    ]
    for _content in _contents:
        content = Content.search_by_code(_content['code'])

        # content: not found
        if not content:
            raise colander.Invalid(
                node, _("Content file ${code} not found.",
                        mapping={'code': content.code}))

        # content: already assigned
        if content.creation:
            if content.creation.code == edit_creation_code:
                continue
            raise colander.Invalid(
                node, _("Content file ${content_code} is "
                        "already assigned to creation ${creation_code}.",
                        mapping={'content_code': content.code,
                                 'creation_code': content.creation.code}))

    # rights: duplicate rightsholders
    for a, b in combinations(values['rights']['contributions'], 2):
        if a['rightsholder'][0]['oid'] == b['rightsholder'][0]['oid']:
            raise colander.Invalid(
                node, _("Multiple entries for the same rightsholder '${name}'."
                        "Please have a single unique rightsholder to assign "
                        "all the applying rights to.",
                        mapping={'name': a['rightsholder'][0]["name"]}))

    # rights: duplicate contributions
    for _contribution in values['rights']['contributions']:
        for a, b in combinations(_contribution['rights'], 2):
            if a['contribution'] == b['contribution']:
                contribution = get_contribution_label(a['contribution'])
                rightsholder = _contribution['rightsholder'][0]["name"]
                raise colander.Invalid(
                    node, _("Multiple entries for the same contribtion "
                            "'${contribution}' for rightsholder '${name}'. "
                            "Please have a single unique contribution for "
                            "every rightsholder.",
                            mapping={'contribution': contribution,
                                     'name': rightsholder}))


# --- Options -----------------------------------------------------------------

distribution_type_options = [
    ('original', _('Original')),
    ('adaption', _('Adaption')),
    ('cover', _('Cover')),
    ('remix', _('Remix')),
]


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def current_artists_select_widget(node, kw):
    request = kw.get('request')
    web_user = WebUser.current_web_user(request)
    artists = Artist.search_by_party(web_user.party.id)
    artist_options = [(artist.oid, artist.name) for artist in artists]
    widget = deform.widget.Select2Widget(values=artist_options)
    return widget


@colander.deferred
def deferred_areas_schema_node(node, kw):
    schema = colander.SchemaNode(
        colander.Mapping(),
        title=_("Areas"),
        oid="areas",
        name="areas",
        widget=deform.widget.MappingWidget(template='navs/mapping'),
        description=_("Assign areas of exploitation the C3S "
                      "will cover for this song. In case you are "
                      "also a member of another collecting society, "
                      "that handles different areas, "
                      "please assign those areas to it, too. "
                      "Changes made will take effect on the beginning "
                      "of the next accounting period.")
    )
    values = [('', '')] + [
        (tc.oid, tc.name) for tc in CollectingSociety.search(
            [("represents_copyright", "=", True)])]
    for tcat in TariffCategory.search_all():
        schema.add(
            colander.SchemaNode(
                colander.String(),
                title=_(tcat.name),
                oid=tcat.code,
                name=tcat.code,
                missing="",
                widget=deform.widget.Select2Widget(
                    values=values,
                    placeholder=_("None")
                )
            )
        )
    return schema


@colander.deferred
def deferred_derivation_missing(node, kw):
    derivation_type = kw['request'].params.get('derivation_type')
    if node.name == derivation_type:
        return colander.required
    return colander.drop


# --- Fields ------------------------------------------------------------------


class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.String
    widget = current_artists_select_widget
    validator = colander.uuid


class LyricsField(colander.SchemaNode):
    oid = "lyrics"
    schema_type = colander.String
    widget = deform.widget.TextAreaWidget(css_class='cs-mono', rows=15)
    missing = ""


class DistributionTypeField(colander.SchemaNode):
    oid = "distribution_type"
    schema_type = colander.String
    widget = deform.widget.SelectWidget(values=distribution_type_options)


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    title = _("Metadata")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    working_title = TitleField(name='title', title=_("Title"))
    artist = ArtistField(title=_("Artist"))


class RightsSchema(colander.Schema):
    title = _("Rights")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    contributions = CreationContributionSequence(title="", min_len=1)


class DerivationSchema(colander.Schema):
    title = _("Derivation")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    distribution_type = DistributionTypeField(title=_("Derivation"))
    adaption = CreationSequence(title=_('Original'), min_len=1, max_len=1,
                                missing=deferred_derivation_missing)
    cover = CreationSequence(title=_('Original'), min_len=1, max_len=1,
                             missing=deferred_derivation_missing)
    remix = CreationSequence(title=_('Original(s)'), min_len=1,
                             missing=deferred_derivation_missing)


class ContentSchema(colander.Schema):
    title = _("Files")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    audio = ContentSequence(title=_("Audio Files"), actions=['add'],
                            max_len=1, category='audio')
    sheet = ContentSequence(title=_("Sheet Music Files"),
                            actions=['add'], max_len=1, category='sheet')


class LyricsSchema(colander.Schema):
    title = _("Lyrics")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    lyrics = LyricsField(title=_("Lyrics"))


class AddCreationSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    metadata = MetadataSchema()
    rights = RightsSchema()
    derivation = DerivationSchema()
    content = ContentSchema()
    lyrics = LyricsSchema()
    areas = deferred_areas_schema_node


# --- Forms -------------------------------------------------------------------

def add_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(validator=validate_form).bind(
            request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
