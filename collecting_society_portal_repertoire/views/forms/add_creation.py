# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import colander
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController
from ...services import _
from ...models import (
    Artist,
    Creation,
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
        web_user = self.request.web_user
        party = self.request.party

        # generate vlist
        _creation = {
            'title': self.appstruct['metadata']['title'],
            'artist': self.appstruct['metadata']['artist'],
            'entity_creator': party,
            'releases': self.appstruct['metadata']['releases'],
        }

        # releases
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

        # contributions
        # if self.appstruct['contributions']['contributions']:
        #     _creation['contributions'] = []
        #     for contribution in self.appstruct[
        #             'contributions']['contributions']:
        #         _creation['contributions'].append(
        #             (
        #                 'create',
        #                 [{
        #                     'type': contribution['type'],
        #                     'artist': contribution['artist']
        #                 }]
        #             )
        #         )

        # derivation
        # if self.appstruct['relations']['original_creations']:
        #     _creation['original_relations'] = []
        #     for original_creation in self.appstruct[
        #             'relations']['original_creations']:
        #         _creation['original_relations'].append(
        #             (
        #                 'create',
        #                 [{
        #                     'original_creation': original_creation['creation'],
        #                     'allocation_type': original_creation['type']
        #                 }]
        #             )
        #         )

        # content
        if self.appstruct['content']['content']:
            _creation['content'] = []
            for content_listenty in self.appstruct['content']['content']:
                content = Content.search_by_code(content_listenty['code'])
                if content:
                    _creation['content'].append(
                        (
                            'add',
                            [content.id],
                            [content.name],
                            [content.category]
                        )
                    )

        # create creation
        creations = Creation.create([_creation])

        # user feedback
        if not creations:
            log.info("creation add failed for %s: %s" % (web_user, _creation))
            self.request.session.flash(
                _(u"Creation could not be added: ") + _creation['title'],
                'main-alert-danger'
            )
            self.redirect()
            return
        creation = creations[0]
        log.info("creation add successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation added: ") + creation.title
            + " (" + creation.code + ")", 'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

def validate_content(node, values, **kwargs):  # multifield validator
    """Check if content is already assigned to another creation"""

    # Content.search_by_id()
    request = node.bindings["request"]
    contents = values["content"]["content"]
    if contents == [] or None:
        return
        # raise colander.Invalid(node, _(
        #     u"Please assign a uploaded file to this creation"))
    audio_count = 0
    sheet_count = 0
    edit_creation_code = getattr(request.context, 'code', None)
    for content_listenty in contents:
        c = Content.search_by_code(content_listenty['code'])
        if c.creation:  # selected content is already assigned some creation
            crco = c.creation.code  # creation code of content_listenty
            if (edit_creation_code is None or  # either in Add Creation or
                    edit_creation_code != crco):    # in Edit Creation and code
                raise colander.Invalid(    # doesn't fit the creation?
                    node, _(u"Content file ${coco} is "
                            "already assigned to creation ${crco}.",
                            mapping={'coco': c.code, 'crco': crco}))
        if c.category == 'audio':
            audio_count = audio_count + 1
        if c.category == 'sheet':
            sheet_count = sheet_count + 1
    if audio_count > 1 or sheet_count > 1:
        raise colander.Invalid(node, _(u"Only one uploaded content file "
                                       "for each file type (audio and sheet "
                                       "music)."))


# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

@colander.deferred
def current_artists_select_widget(node, kw):
    request = kw.get('request')
    artists = Artist.current_editable(request)
    artist_options = [(artist.id, artist.name) for artist in artists]
    widget = deform.widget.Select2Widget(values=artist_options)
    return widget


@colander.deferred
def releases_select_widget(node, kw):
    request = kw.get('request')
    releases = Release.current_editable(request)
    releases_options = [
        (int(release.id), release.title) for release in releases]
    widget = deform.widget.Select2Widget(
        values=releases_options, multiple=True
    )
    return widget


@colander.deferred
def content_select_widget(node, kw):
    request = kw.get('request')
    contents = Content.search_orphans(request.party.id, 'audio')
    content_options = []
    if contents:
        content_options = [(content.id, content.name) for content in contents]
    widget = deform.widget.Select2Widget(values=content_options)
    return widget


# --- Fields ------------------------------------------------------------------

class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.Integer
    widget = current_artists_select_widget


class ReleasesField(colander.SchemaNode):
    oid = "releases"
    schema_type = colander.List
    widget = releases_select_widget


class CollectingSocietyField(colander.SchemaNode):
    oid = "collecting-society"
    schema_type = colander.String
    missing = ""


class ContentField(colander.SchemaNode):
    oid = "content"
    schema_type = colander.String
    widget = content_select_widget
    missing = ""


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    title = _(u"Add metadata")
    widget = deform.widget.MappingWidget(template='navs/mapping')
    working_title = TitleField(name='title', title=_(u"Working Title"))
    artist = ArtistField(title=_(u"Featured Artist"))
    releases = ReleasesField(title=_(u"Release"))
    collecting_society = CollectingSocietyField()


class OriginalsSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    originals = OriginalSequence(title="")


class ContentSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    content = ContentSequence(actions=['add'])


class AddCreationSchema(colander.Schema):
    title = _(u"Add Creation")
    widget = deform.widget.FormWidget(template='navs/form', navstyle='pills')
    metadata = MetadataSchema(title=_(u"Metadata"))
    originals = OriginalsSchema(title=_(u"Derivation"))
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
