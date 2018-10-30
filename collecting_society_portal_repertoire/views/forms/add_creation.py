# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import colander
import deform

from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)
from ...services import _
from ...models import (
    Artist,
    Creation,
    License,
    Content,
    Release
)
from .datatables import (
    ContentSequence,
    OriginalSequence,
)

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddCreation(FormController):
    """
    form controller for add creation
    """

    def controller(self):
        self.form = add_creation_form(self.request)
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
            'contributions': {},
            'licenses': {},
            'relations': {},
            'content': {}
        }
        # add metadata from content uuid, provided by upload form
        content = getattr(self.context, 'content', False)
        if content:
            # self.appstruct['content']['content'] = [(content.id,
            #                                          content.name)]
            self.appstruct['metadata']['title'] = content.metadata_title
            meta_artist = Artist.search_by_name(content.metadata_artist)
            if meta_artist:
                self.appstruct['metadata']['artist'] = meta_artist[0].id

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def create_creation(self):
        email = self.request.unauthenticated_userid
        party = WebUser.current_party(self.request)

        # generate vlist
        _creation = {
            'title': self.appstruct['metadata']['title'],
            'artist': self.appstruct['metadata']['artist'],
            'entity_creator': WebUser.current_web_user(self.request).party,
            'releases': self.appstruct['metadata']['releases'],
        }

        # -------------------------------------------------------
        if self.appstruct['metadata']['releases']:
            _creation['releases'] = []
            for release_id in self.appstruct['metadata']['releases']:
                _creation['releases'].append(
                    (
                        'create',
                        [{
                            'release': release_id,
                            'title': self.appstruct['metadata']['title'],
                            # TODO: manage different titles for releases
                            #       using a datatables control
                            # 'medium_number': TODO: medium_number
                            # 'track_number': TODO: track_number
                            # 'license ': TODO: license
                        }]
                    )
                )
        if self.appstruct['contributions']['contributions']:
            _creation['contributions'] = []
            for contribution in self.appstruct[
                    'contributions']['contributions']:
                _creation['contributions'].append(
                    (
                        'create',
                        [{
                            'type': contribution['type'],
                            'artist': contribution['artist']
                        }]
                    )
                )

        if self.appstruct['relations']['original_creations']:
            _creation['original_relations'] = []
            for original_creation in self.appstruct[
                    'relations']['original_creations']:
                _creation['original_relations'].append(
                    (
                        'create',
                        [{
                            'original_creation': original_creation['creation'],
                            'allocation_type': original_creation['type']
                        }]
                    )
                )

        if self.appstruct['relations']['derivative_creations']:
            _creation['derivative_relations'] = []
            for derivative_creation in self.appstruct[
                    'relations']['derivative_creations']:
                _creation['derivative_relations'].append(
                    (
                        'create',
                        [{
                            'derivative_creation': derivative_creation[
                                'creation'
                            ],
                            'allocation_type': derivative_creation['type']
                        }]
                    )
                )

        if self.appstruct['content']['content']:
            _creation['content'] = []
            for contentlistenty in self.appstruct['content']['content']:
                content = Content.search_by_code(contentlistenty['code'])
                if content:
                    _creation['content'].append(
                        (
                            'add',
                            [content.id]
                        )
                    )

        creations = Creation.create([_creation])
        if not creations:
            log.info("creation add failed for %s: %s" % (email, _creation))
            self.request.session.flash(
                _(u"Creation could not be added: ") + _creation['title'],
                'main-alert-danger'
            )
            self.redirect()
            return
        creation = creations[0]

        # Attachment = Tdb.get('ir.attachment')
        # attachment = Attachment(
        #     type='data',
        #     name=self.appstruct['audiofile']['filename'],
        #     resource=creation,
        #     data=self.appstruct['audiofile']['fp'].read()
        # )
        # attachment.save()
        # self.appstruct['audiofile']['fp'].delete()

        log.info("creation add successful for %s: %s" % (email, creation))
        self.request.session.flash(
            _(u"Creation added: ") + creation.title
            + " ("+creation.code+")", 'main-alert-success'
        )

        self.redirect()


# --- Validators --------------------------------------------------------------

def validate_content(node, values, **kwargs):  # multifield validator
    """Check if content is already assigned to another creation"""

    # Content.search_by_id()
    # request = node.bindings["request"]
    contents = values["content"]["content"]
    if contents == [] or None:
        raise colander.Invalid(node, _(
            u"Please assign a uploaded file to this creation"))
    audio_count = 0
    sheet_count = 0
    for contentlistenty in contents:
        c = Content.search_by_code(contentlistenty['code'])
        if c.creation is not None:
            raise colander.Invalid(node, _(u"Content file ${coco} is already "
                                           "assigned to creation ${crco}.",
                                           mapping={'coco': c.code,
                                                    'crco': c.creation.code}))
        if c.category == 'audio':
            audio_count = audio_count + 1
        if c.category == 'sheet':
            sheet_count = sheet_count + 1
    if audio_count > 1 or sheet_count > 1:
        raise colander.Invalid(node, _(u"Only one uploaded content file "
                                       "for each file type (audio and sheet "
                                       "music)."))


# --- Options -----------------------------------------------------------------

artist_relation_options = (
    ('', _(u"- Select -")),
    ('performance', _(u"Performance")),
    ('composition', _(u"Composition")),
    ('text', _(u"Text"))
)

creation_relation_options = (
    ('', _(u"- Select -")),
    ('adaption', _(u"Adaption")),
    ('cover', _(u"Cover")),
    ('remix', _(u"Remix"))
)


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
def releases_select_widget(node, kw):
    request = kw.get('request')
    web_user = WebUser.current_web_user(request)
    releases = Release.search_by_party(web_user.party.id)
    releases_options = [(int(release.id), release.title) for release in releases]
    widget = deform.widget.Select2Widget(
        values=releases_options, multiple=True
    )
    return widget


@colander.deferred
def solo_artists_select_widget(node, kw):
    solo_artists = Artist.search_all_solo_artists()
    solo_artist_options = [(artist.id, artist.name) for artist in solo_artists]
    widget = deform.widget.Select2Widget(values=solo_artist_options)
    return widget


@colander.deferred
def creations_select_widget(node, kw):
    creations = Creation.search_all()
    creations_options = [
        (creation.id, creation.title +
         ' (' + creation.artist.name + ')')
        for creation in creations
    ]
    widget = deform.widget.Select2Widget(values=creations_options)
    return widget


@colander.deferred
def licenses_select_widget(node, kw):
    licenses = License.search_all()
    licenses_options = [(license.id, license.name) for license in licenses]
    widget = deform.widget.Select2Widget(
        values=licenses_options, multiple=True
    )
    return widget


# --- Fields ------------------------------------------------------------------

@colander.deferred
def content_select_widget(node, kw):
    request = kw.get('request')
    web_user = WebUser.current_web_user(request)
    contents = Content.search_orphans(web_user.party.id, 'audio')
    content_options = []
    if contents:
        content_options = [(content.id, content.name) for content in contents]
    widget = deform.widget.Select2Widget(values=content_options)
    return widget


class AudiofileField(colander.SchemaNode):
    oid = "audiofile"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget


class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class SoloArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.Integer
    widget = solo_artists_select_widget


class CurrentArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.Integer
    widget = current_artists_select_widget


class ReleasesField(colander.SchemaNode):
    oid = "releases"
    schema_type = colander.List
    widget = releases_select_widget


class ContentField(colander.SchemaNode):
    oid = "content"
    schema_type = colander.String
    widget = content_select_widget
    missing = ""


class ContributionTypeField(colander.SchemaNode):
    schema_type = colander.String
    widget = deform.widget.SelectWidget(values=artist_relation_options)


class LicensesField(colander.SchemaNode):
    oid = "licenses"
    schema_type = colander.Set
    widget = licenses_select_widget


class CreationField(colander.SchemaNode):
    oid = "creation"
    schema_type = colander.Integer
    widget = creations_select_widget


class RelationTypeField(colander.SchemaNode):
    schema_type = colander.String
    widget = deform.widget.SelectWidget(values=creation_relation_options)


class CollectingSocietyField(colander.SchemaNode):
    oid = "collecting-society"
    schema_type = colander.String
    missing = ""


class NeighbouringRightsField(colander.SchemaNode):
    oid = "neighbouring-rights"
    schema_type = colander.Bool
    widget = deform.widget.CheckboxWidget()
    missing = ""


class NeighbouringRightsSocietyField(colander.SchemaNode):
    oid = "neighbouring-rights-society"
    schema_type = colander.String
    missing = ""


class LabelNameField(colander.SchemaNode):
    oid = "label-name"
    schema_type = colander.String
    missing = ""


class LabelCodeField(colander.SchemaNode):
    oid = "label-code"
    schema_type = colander.String
    missing = ""


class LabelCatalogNumberField(colander.SchemaNode):
    oid = "label-catalog-number"
    schema_type = colander.Integer
    missing = ""


class LabelUrlField(colander.SchemaNode):
    oid = "label-url"
    schema_type = colander.String
    missing = ""


class EanUpcField(colander.SchemaNode):
    oid = "ean-upc"
    schema_type = colander.Integer
    missing = ""


class IsrcField(colander.SchemaNode):
    oid = "isrc"
    schema_type = colander.String
    missing = ""


class ReleaseDateField(colander.SchemaNode):
    oid = "release-date"
    schema_type = colander.DateTime
    missing = ""


class ReleaseCancellationDateField(colander.SchemaNode):
    oid = "release-cancellation-date"
    schema_type = colander.DateTime
    missing = ""


class OnlineReleaseDateField(colander.SchemaNode):
    oid = "online-release-date"
    schema_type = colander.DateTime
    missing = ""


class OnlineReleaseCancellationDateField(colander.SchemaNode):
    oid = "online-release-cancellation-date"
    schema_type = colander.DateTime
    missing = ""


# --- Schemas -----------------------------------------------------------------

class UploadAudiofileSchema(colander.MappingSchema):
    title = _(u"Upload audiofile")
    audiofile = AudiofileField(title=_(u"Upload Audiofile"))


class AddMetadataSchema(colander.MappingSchema):
    title = _(u"Add metadata")
    working_title = TitleField(name='title', title=_(u"Working Title"))
    artist = CurrentArtistField(title=_(u"Featured Artist"))
    releases = ReleasesField(title=_(u"Releases"))
    collecting_society = CollectingSocietyField()
    neighbouring_rights = NeighbouringRightsField()
    neighbouring_rights_society = NeighbouringRightsSocietyField()
    label_name = LabelNameField()
    label_code = LabelCodeField()
    label_catalog_number = LabelCatalogNumberField()
    label_url = LabelUrlField()
    ean_upc = EanUpcField()
    isrc = IsrcField()
    release_date = ReleaseDateField()
    release_cancellation_date = ReleaseCancellationDateField()
    online_release_date = OnlineReleaseDateField()
    online_release_cancellation_date = OnlineReleaseCancellationDateField()


class ArtistRelationSchema(colander.Schema):
    artist = SoloArtistField(title=_(u"Solo artist"))
    type = ContributionTypeField(title=_(u"Type"))


class ArtistRelationSequence(colander.SequenceSchema):
    contribution = ArtistRelationSchema()


class AddContributionsSchema(colander.MappingSchema):
    title = _(u"Add contributions")
    contributions = ArtistRelationSequence(title=_(u"Contributions"))


class AddLicencesSchema(colander.MappingSchema):
    title = _(u"Add licences")
    licenses = LicensesField(title=_(u"Licenses"))


# class CreationRelationSchema(colander.Schema):
#     creation = CreationField(title=_(u"Artist"))
#     type = RelationTypeField(title=_(u"Type"))


# class CreationRelationSequence(colander.SequenceSchema):
#     creation = CreationRelationSchema()


# class AddCreationRelationsSchema(colander.MappingSchema):
#     title = _(u"Add relations to other creations")
#     original_creations = CreationRelationSequence(
#         title=_(u"Original creations")
#     )
#     derivative_creations = CreationRelationSequence(
#         title=_(u"Derivative creations")
#     )


class MetadataSchema(colander.Schema):
    title = _(u"Add metadata")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    working_title = TitleField(name='title', title=_(u"Working Title"))
    artist = CurrentArtistField(title=_(u"Featured Artist"))
    releases = ReleasesField(title=_(u"Release"))
    collecting_society = CollectingSocietyField()


class ContributionsSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    contributions = ArtistRelationSequence(title=_(u"Contributions"))


class LicensesSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    licenses = LicensesField(title=_(u"Licenses"))


class OriginalsSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    originals = OriginalSequence(title="")


class ContentSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    content = ContentSequence()


class AddCreationSchema(colander.Schema):
    title = _(u"Add Creation")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    metadata = MetadataSchema(title=_(u"Metadata"))
    # access = AccessSchema(title=_(u"Access"))
    contributions = ContributionsSchema(title=_(u"Contributions"))
    licenses = LicensesSchema(title=_(u"Licenses"))
    originals = OriginalsSchema(title=_(u"Relations"))
    content = ContentSchema(title=_(u"Content"))


# --- Forms -------------------------------------------------------------------

def add_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(validator=validate_content).bind(
            request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
