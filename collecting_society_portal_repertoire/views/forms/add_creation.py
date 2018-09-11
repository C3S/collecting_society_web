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
from ...resources import CreationResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddCreation(FormController):
    """
    form controller for creation of creations
    """

    __stage__ = 'upload_audiofile'  # initial stage

    def controller(self):

        self.form = add_creation_form(self.request)

        if self.submitted() and self.validate():
            self.save_creation()
        else:
            self.init_creation()

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
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

        # contents tab
        if 'uuid' in self.request.GET.keys():
            _content = Content.search_by_uuid(self.request.GET['uuid'])
            if not _content:
                return
            self.appstruct['content']['content'] = [(_content.id,
                                                    _content.name)]
            # TODO: further initialization via content metadata

    @Tdb.transaction(readonly=False)
    def save_creation(self):
        email = self.request.unauthenticated_userid

        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )

        _creation = {
            'artist': self.appstruct['metadata']['artist'],
            'entity_creator': WebUser.current_web_user(self.request).party,
            'releases': self.appstruct['metadata']['releases'],
        }
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
        if self.appstruct['licenses']['licenses']:
            _creation['licenses'] = []
            for license_id in self.appstruct['licenses']['licenses']:
                _creation['licenses'].append(
                    (
                        'create',
                        [{
                            'license': license_id
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
        # TODO: save content relations
        #import rpdb2; rpdb2.start_embedded_debugger("supersecret", fAllowRemote = True)
        #if self.appstruct['content']['content']:
        #    _creation['content'] = []
        #    for content_id in self.appstruct['content']['content']:
        #        _creation['content'].append(
        #            (
        #                'create',
        #                [{
        #                    'content': content_id
        #                }]
        #            )
        #        )

        creations = Creation.create([_creation])
        if not creations:
            log.info("creation add failed for %s: %s" % (email, _creation))
            self.request.session.flash(
                _(u"Creation could not be added: ") + _creation['default_title'],
                'main-alert-danger'
            )
            self.redirect(CreationResource, 'list')
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
            _(u"Creation added: ") + creation.default_title
            + " ("+creation.code+")", 'main-alert-success'
        )
        self.remove()
        self.clean()
        self.redirect(CreationResource, 'list')


# --- Validators --------------------------------------------------------------

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


# --- Fields ------------------------------------------------------------------

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
        (creation.id, creation.default_title +
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
    creation_title = TitleField(name='title', title=_(u"Title"))
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


class CreationRelationSchema(colander.Schema):
    creation = CreationField(title=_(u"Artist"))
    type = RelationTypeField(title=_(u"Type"))


class CreationRelationSequence(colander.SequenceSchema):
    creation = CreationRelationSchema()


class AddCreationRelationsSchema(colander.MappingSchema):
    title = _(u"Add relations to other creations")
    original_creations = CreationRelationSequence(
        title=_(u"Original creations")
    )
    derivative_creations = CreationRelationSequence(
        title=_(u"Derivative creations")
    )


class MetadataSchema(colander.Schema):
    title = _(u"Add metadata")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    creation_title = TitleField(name='title', title=_(u"Title"))
    artist = CurrentArtistField(title=_(u"Featured Artist"))
    releases = ReleasesField(title=_(u"Release"))
    collecting_society = CollectingSocietyField()


class ContributionsSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    contributions = ArtistRelationSequence(title=_(u"Contributions"))


class LicensesSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    licenses = LicensesField(title=_(u"Licenses"))


class RelationsSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    original_creations = CreationRelationSequence(
        title=_(u"Original creations")
    )
    derivative_creations = CreationRelationSequence(
        title=_(u"Derivative creations")
    )


class ContentSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    content = ContentField(title=_(u"Content"))


class AddCreationSchema(colander.Schema):
    title = _(u"Add Solo Artist")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    metadata = MetadataSchema(title=_(u"Metadata"))
    # access = AccessSchema(title=_(u"Access"))
    contributions = ContributionsSchema(title=_(u"Contributions"))
    licenses = LicensesSchema(title=_(u"Licenses"))
    relations = RelationsSchema(title=_(u"Relations"))
    content = ContentSchema(title=_(u"Content"))


# --- Forms -------------------------------------------------------------------

def add_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
