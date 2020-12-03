# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import (
    Tdb,
    WebUser,
    Country
)
from portal_web.views.forms import FormController
from ...services import _
from ...models import (
    CollectingSociety,
    TariffCategory,
    Artist,
    Creation,
    CreationDerivative,
    CreationTariffCategory,
    CreationRight,
    Content,
    Instrument,
    CollectingSociety
)
from .datatables import (
    ContentSequence,
    CreationSequence,
    CreationRightsholderSequence
)

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
        initializes form with arguments passed via url from Content/Uploads
        """

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
                'code': content.code,
                'category': content.category,
                'mode': "add",
                'name': content.name,
                'oid': content.oid
            }]

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def create_creation(self):
        a = self.appstruct
        web_user = self.request.web_user
        party = self.request.party

        # generate vlist
        _creation = {
            'title': a['metadata']['title'],
            'artist': a['metadata']['artist'],
            'lyrics': a['lyrics']['lyrics'],
            'entity_creator': party,
        }

        # content
        _creation['content'] = []
        for content_type in ['audio', 'sheet']:
            if a['content'][content_type]:
                for content_listenty in a['content'][content_type]:
                    content = Content.search_by_code(content_listenty['code'])
                    if not content.permits(web_user, 'edit_content'):
                        continue
                    if content:
                        _creation['content'].append(('add', [content.id]))

        # create creation
        creations = Creation.create([_creation])

        # user feedback
        if not creations:
            log.info("creation add failed for %s: %s" % (web_user, _creation))
            self.request.session.flash(
                _(u"Creation could not be added:  ${crct}",
                  mapping={'crct': _creation['title']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        creation = creations[0]

        # rightsholders

        # rightsholders: merge artists
        # TODO: merge rightsholders_current with same rightsholder subject
        #       within appstruct

        # rightsholders: merge instruments
        # TODO: merge instruments of rights (contribution == instrument)
        #       within appstruct; use one right with oid, if present

        # prohibit duplicate rightsholders
        a_rho_to_remove = []
        for a_rightsholder in a['rightsholders']['rightsholders']:
            for a_rho_to_match in a['rightsholders']['rightsholders']:
                if (a_rightsholder != a_rho_to_match and
                        a_rightsholder not in a_rho_to_remove and
                        a_rho_to_match not in a_rho_to_remove):
                    if (a_rightsholder['subject'][0]['code'] ==
                            a_rho_to_match['subject'][0]['code']):
                        if a_rightsholder['mode'] == 'create':
                            a_rho_to_remove.append(a_rightsholder)
                        else:  # must be the other one that was newly created
                            a_rho_to_remove.append(a_rho_to_match)
                        self.request.session.flash(
                            _(u"Warning: Only one rightsholder entry allowed "
                              "for '${name}'. Entry has been removed.",
                              mapping={
                                  'name': a_rightsholder['subject'][0]['code']
                              }),
                            'main-alert-warning'
                        )
        for a_rho in a_rho_to_remove:
            del a_rho
        # TODO: cover this also in a colander form validator

        # rightsholders: create
        for a_rightsholder in a['rightsholders']['rightsholders']:
            a_subject = a_rightsholder['subject'][0]
            rightsholder_subject = None

            # create rightsholder subject
            if a_subject['mode'] == "create":
                # TODO: foreign subjects
                # rightsholder_subject = ...
                pass
            else:
                rightsholder_subject = Artist.search_by_code(a_subject['code'])

            # check for duplicate rights per rightsholder and merge instruments
            #a_rights_to_remove = []
            #for a_right in a_rightsholder['rights']:
            #    for a_match in a_rightsholder['rights']:
            #        if (a_right != a_match and
            #                a_right not in a_rho_to_remove and
            #                a_match not in a_rho_to_remove):
            #            if (a_right['subject'][0]['code'] ==
            #                    a_match['subject'][0]['code']):
            #                if a_right['mode'] == 'create':
            #                    a_rho_to_remove.append(a_right)
            #                else:  # must be the other one that was newly created
            #                    a_rho_to_remove.append(a_match)
            #                self.request.session.flash(
            #                    _(u"Warning: Only one rightsholder entry allowed "
            #                    "for '${name}'. Entry has been removed.",
            #                    mapping={
            #                        'name': a_rightsholder['subject'][0]['code']
            #                    }),
            #                    'main-alert-warning'
            #                )
            #for a_rho in a_rho_to_remove:
            #    del a_rho
            # TODO: cover this also in a colander form validator                

            for a_right in a_rightsholder['rights']:

                # create right
                if a_right['mode'] == "create":
                    instrument_ids = []
                    if a_right["contribution"] == "instrument":
                        instruments = Instrument.search_by_oids(
                            a_right["instruments"])
                        instrument_ids = [i.id for i in instruments]
                    new_right = {
                        'rightsholder': rightsholder_subject.id,
                        'rightsobject': creation.id,
                        'type_of_right': a_right['type_of_right'],
                        'contribution': a_right['contribution'],
                        'instruments': [('add', instrument_ids)],
                        'country': Country.search_by_code('DE').id
                    }
                    if a_right['collecting_society']:
                        cs_representing = CollectingSociety.search_by_oid(
                            a_right['collecting_society'])
                        new_right['collecting_society'] = cs_representing.id
                    CreationRight.create([new_right])

        # areas of exploitation / tariff categories / collecting societies
        ctcs_to_add = []  # to minimize number of tryton calls
        tcats = TariffCategory.search_all()
        for tcat in tcats:  # for each tariff category
            collecting_soc_oid_new = a['areas']['tariff_category_'+tcat.code]
            # add collecting society association for this tariff category
            if collecting_soc_oid_new:
                collecting_society = CollectingSociety.search_by_oid(
                    collecting_soc_oid_new)
                if collecting_society:
                    ctcs_to_add.append({
                            'creation': creation.id,
                            'category': tcat.id,
                            'collecting_society': collecting_society.id
                        })
        if ctcs_to_add:
            CreationTariffCategory.create(ctcs_to_add)

        # add derivative-original relations
        # (objects starting with a_ relate to form data provided by appstruct)
        for derivation_type in ['adaption', 'cover', 'remix']:
            for a_derivation in a['derivation'][derivation_type]:
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
                _original = {
                    'original_creation': original.id,
                    'derivative_creation': creation.id,
                    'allocation_type': derivation_type
                }
                CreationDerivative.create([_original])

        log.info("creation add successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation added:  ${crct} (${crco})",
              mapping={'crct': creation.title,
                       'crco': creation.code}),
            'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

def validate_content(node, values, **kwargs):  # multifield validator
    """Check if content is already assigned to another creation"""

    # Content.search_by_id()
    request = node.bindings["request"]
    contents = values["content"]["audio"] + values["content"]["sheet"]
    if contents == [] or None:
        return
        # raise colander.Invalid(node, _(
        #     u"Please assign a uploaded file to this creation"))
    edit_creation_code = getattr(request.context, 'code', None)
    for content_listenty in contents:
        c = Content.search_by_code(content_listenty['code'])
        if c.creation:  # selected content is already assigned to some creation
            crco = c.creation.code  # creation code of content_listenty
            if (edit_creation_code is None or  # either in Add Creation or
                    edit_creation_code != crco):    # in Edit Creation and code
                raise colander.Invalid(    # doesn't fit the creation?
                    node, _(u"Content file ${coco} is "
                            "already assigned to creation ${crco}.",
                            mapping={'coco': c.code, 'crco': crco}))

    # look for dupes in contributions
    # contributions = values['contributions']['contributions']
    # reduced_contributions = []
    # for contrib in contributions:
    #     if contrib['mode'] != 'remove':
    #         reduced_contributions.append(
    #             (
    #                 contrib['artist'][0]['code'],
    #                 contrib['contribution_type'],
    #                 contrib['role']
    #             )
    #         )
    # unique_contributions = set(reduced_contributions)
    # if len(reduced_contributions) > len(unique_contributions):
    #     raise colander.Invalid(node, _(u"Duplicate contribution found."))

    # look for duplicate rightsholders
    # a_rightsholders = values['rightsholders']['rightsholders']
    # a_rightsholders.sort(key=lambda x: x['subject'][0]['code'])
    # i = 0
    # while i < len(a_rightsholders):
    #     if (i < len(a_rightsholders)-1 and  # entries with same artist?
    #             a_rightsholders[i]['subject'][0]['code'] ==
    #             a_rightsholders[i+1]['subject'][0]['code']):
    #         raise colander.Invalid(
    #             node, _(u"Duplicate rightsholder entry ${n} (${c}). Please "
    #                     "subsume all right of a specific rightsholder under "
    #                     "a single entry.",
    #                     mapping={'n': a_rightsholders[i]['subject'][0]['name'],
    #                              'c': a_rightsholders[i]['subject'][0]['code']}
    #                     ))

    #     i = i + 1  # move forward if another rightsholder is found

    # check if contributions match rights
    # a_rightsholders = values['rightsholders']['rightsholders']
    # for a_rightsholder in a_rightsholders:
    #     for a_right in a_rightsholder['rights']:
    #         ctbr = a_right["contribution"]
    #         tor = a_right["type_of_right"]
    #         if (ctbr not in CreationRight.get_contributions_by_type_of_right(
    #                 tor)):
    #             raise colander.Invalid(
    #                 node, _(u"Contribution '${c}' does not apply to (${r}).",
    #                         mapping={'c': ctbr, 'r': tor}))

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

@colander.deferred
def current_artists_select_widget(node, kw):
    request = kw.get('request')
    web_user = WebUser.current_web_user(request)
    artists = Artist.search_by_party(web_user.party.id)
    artist_options = [(artist.id, artist.name) for artist in artists]
    widget = deform.widget.Select2Widget(values=artist_options)
    return widget


@colander.deferred
def deferred_areas_schema_node(node, kw):
    schema = colander.SchemaNode(
        colander.Mapping(),
        title=_(u"Areas"),
        oid="areas",
        name="areas",
        widget=deform.widget.MappingWidget(template='navs/mapping'),
        description=_(u"Assign areas of exploitation the C3S "
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
                oid="tariff_category_"+tcat.code,
                name="tariff_category_"+tcat.code,
                missing="",
                widget=deform.widget.Select2Widget(
                    values=values,
                    placeholder=_("None")
                )
            )
        )

    return schema

# --- Fields ------------------------------------------------------------------


class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.Integer
    widget = current_artists_select_widget


class LyricsField(colander.SchemaNode):
    oid = "lyrics"
    schema_type = colander.String
    widget = deform.widget.TextAreaWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    title = _(u"Metadata")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    working_title = TitleField(name='title', title=_(u"Title"))
    artist = ArtistField(title=_(u"Artist"))


class RightsholdersSchema(colander.Schema):
    title = _(u"Rightsholders")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    rightsholders = CreationRightsholderSequence(title="", min_len=1)


class DerivationSchema(colander.Schema):
    title = _(u"Derivation")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    adaption = CreationSequence(title="Adaption of")
    cover = CreationSequence(title="Cover of")
    remix = CreationSequence(title="Remix of")


class ContentSchema(colander.Schema):
    title = _(u"Files")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    audio = ContentSequence(title=_("Audio Files"), actions=['add'],
                            max_len=1, category='audio')
    sheet = ContentSequence(title=_("Sheet Music Files"),
                            actions=['add'], max_len=1, category='sheet')


class LyricsSchema(colander.Schema):
    title = _(u"Lyrics")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    lyrics = LyricsField(title=_(u"Lyrics"))


class AddCreationSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    metadata = MetadataSchema()
    rightsholders = RightsholdersSchema()
    derivation = DerivationSchema()
    content = ContentSchema()
    lyrics = LyricsSchema()
    areas = deferred_areas_schema_node


# --- Forms -------------------------------------------------------------------

def add_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(validator=validate_content).bind(
            request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
