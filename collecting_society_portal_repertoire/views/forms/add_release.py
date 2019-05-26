# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import colander
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)
from ...services import (_, picture_processing)
from ...models import (
    Artist,
    Creation,
    Release,
    License,
    Genre,
    Style,
    Label,
    Publisher
)
from .datatables import (
    ArtistSequence,
    TrackSequence,
    LabelSequence,
    PublisherSequence
)

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddRelease(FormController):
    """
    form controller for add release
    """

    def controller(self):
        self.form = add_release_form(self.request)
        self.render()
        if self.submitted() and self.validate():
            self.create_release()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def create_release(self):
        appstruct = self.appstruct
        web_user = self.request.web_user
        party = self.request.party

        # generate vlist
        _release = {
            'entity_origin':
                "direct",
            'entity_creator':
                party,
            'type':
                appstruct['metadata']['release_type'],
            'title':
                appstruct['metadata']['release_title'],
            'genres':
                [('add', map(int, appstruct['metadata']['genres']))],
            'styles':
                [('add', map(int, appstruct['metadata']['styles']))],
            'warning':
                appstruct['metadata']['warning'],
            'isrc_code':
                appstruct['production']['isrc_code'],
            'copyright_date':
                appstruct['production']['copyright_date'],
            'production_date':
                appstruct['production']['production_date'],
            'label_catalog_number':
                appstruct['distribution']['label_catalog_number'],
            'ean_upc_code':
                appstruct['distribution']['ean_upc_code'],
            'release_date':
                appstruct['distribution']['release_date'],
            'release_cancellation_date':
                appstruct['distribution']['release_cancellation_date'],
            'online_release_date':
                appstruct['distribution']['online_release_date'],
            'online_cancellation_date':
                appstruct['distribution']['online_cancellation_date'],
            'distribution_territory':
                appstruct['distribution']['distribution_territory'],
        }

        # artist realease: artist
        if appstruct['metadata']['release_type'] == 'artist':
            oid = appstruct['metadata']['artist']
            artist = Artist.search_by_oid(oid)
            if artist and artist.permits(web_user, 'edit_artist'):
                _release['artists'] = [('add', [artist.id])]

        # split realease: split_artists
        if appstruct['metadata']['release_type'] == 'split_release':
            _add_artists = []
            for _artist in appstruct['metadata']['artists']:
                artist = Artist.search_by_oid(artist['oid'])
                if artist:
                    _add_artists.append(artist.id)
            _release['artists'] = [('add', _add_artists)]

        # tracks
        tracks_create = []
        for _medium in appstruct['tracks']['media']:
            for track_number, _track in enumerate(_medium):
                _creation = _track['track'][0]
                license = License.search_by_oid(_track['license'])
                if not license:
                    continue

                # create track
                if _track['mode'] == "create":
                    # create creation
                    if _creation['mode'] == "create":
                        creation = Creation.create_foreign(
                            party,
                            _creation['artist'],
                            _creation['titlefield']
                        )
                        if not creation:
                            continue
                    # add creation
                    else:
                        creation = Creation.search_by_oid(_creation['oid'])
                        if not creation:
                            continue
                    # append track
                    tracks_create.append({
                        'creation': creation.id,
                        'title': _track['track_title'],
                        'medium_number': _medium,
                        'track_number': track_number + 1,
                        'license': license.id
                        })

        # append actions
        _release['tracks'] = []
        if tracks_create:
            _release['tracks'].append(('create', tracks_create))

        # publisher
        _publisher = next(iter(appstruct['production']['publisher']), None)
        if _publisher:
            if _publisher['mode'] == "add":
                publisher = Publisher.search_by_oid(_publisher['oid'])
                if publisher:
                    _release['publisher'] = publisher.id
            if _publisher['mode'] == "create":
                _release['label_name'] = _publisher['name']

        # label
        _label = next(iter(appstruct['distribution']['label']), None)
        if _label:
            if _label['mode'] == "add":
                label = Label.search_by_oid(_label['oid'])
                if label:
                    _release['label'] = label.id
            if _label['mode'] == "create":
                _release['label_name'] = _label['name']

        # picture
        if self.appstruct['metadata']['picture']:
            err, p, t, m = picture_processing(
                self.appstruct['metadata']['picture']['fp'])
            if not err:
                _release['picture_data'] = p
                _release['picture_thumbnail_data'] = t
                _release['picture_data_mime_type'] = m
            else:
                self.request.session.flash(err, 'main-alert-warning')

        # remove empty fields
        for index, value in _release.items():
            if not value:
                del _release[index]

        # create release
        release = Release.create([_release])

        # user feedback
        if not release:
            log.info("release add failed for %s: %s" % (web_user, _release))
            self.request.session.flash(
                _(u"Release could not be added: ${reti}",
                  mapping={'reti': _release['title']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        release = release[0]
        log.info("release add successful for %s: %s" % (web_user, release))
        self.request.session.flash(
            _(u"Release added:  ${reti} (${reco})",
              mapping={'reti': release.title,
                       'reco': release.code}),
            'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

release_type_options = (
    ('artist', _('Artist Release')),
    ('split', _('Split Release')),
    ('compilation', _('Compilation')),
)


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def current_artists_select_widget(node, kw):
    request = kw.get('request')
    artists = Artist.current_editable(request)
    artist_options = [(artist.oid, artist.name) for artist in artists]
    widget = deform.widget.Select2Widget(values=artist_options)
    return widget


@colander.deferred
def deferred_genre_widget(node, kw):
    genres = Genre.search_all()
    genre_options = [(genre.id, unicode(genre.name)) for genre in genres]
    widget = deform.widget.Select2Widget(values=genre_options, multiple=True)
    return widget


@colander.deferred
def deferred_style_widget(node, kw):
    styles = Style.search_all()
    style_options = [(style.id, unicode(style.name)) for style in styles]
    widget = deform.widget.Select2Widget(values=style_options, multiple=True)
    return widget


# --- Fields ------------------------------------------------------------------

@colander.deferred
def deferred_artist_missing(node, kw):
    params = kw['request'].params
    release_type = params.get("release_type")
    if not release_type or release_type == 'artist':
        return colander.required
    return ""


@colander.deferred
def deferred_split_artists_missing(node, kw):
    params = kw['request'].params
    release_type = params.get("release_type")
    if not release_type or release_type == 'split':
        return colander.required
    return ""


# -- Metadata tab --

class ReleaseTypeField(colander.SchemaNode):
    oid = "type"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=release_type_options)


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.String
    validator = colander.uuid
    widget = current_artists_select_widget
    missing = deferred_artist_missing


class SplitArtistSequence(ArtistSequence):
    min_len = 1
    missing = deferred_split_artists_missing


class ReleaseTitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String


class GenreCheckboxField(colander.SchemaNode):
    oid = "genres"
    schema_type = colander.Set
    widget = deferred_genre_widget
    validator = colander.Length(min=1)


class StyleCheckboxField(colander.SchemaNode):
    oid = "styles"
    schema_type = colander.Set
    widget = deferred_style_widget
    validator = colander.Length(min=1)


class WarningField(colander.SchemaNode):
    oid = "warning"
    schema_type = colander.String
    missing = ""


class PictureField(colander.SchemaNode):
    oid = "picture"
    schema_type = deform.FileData
    widget = deferred_file_upload_widget
    missing = ""


# -- Production Tab --

class CopyrightDateField(colander.SchemaNode):
    oid = "copyright_date"
    schema_type = colander.Date
    missing = ""


# class CopyrightOwnerField(colander.SchemaNode):
#     oid = "get_copyright_owners"
#     schema_type = colander.String
#     # widget = party_select_widget <- no paries any more?
#     widget = deform.widget.TextInputWidget(readonly=True)
#     missing = colander.null
#     # displaying a read-only function field, assembled from the repective
#     # copyright owners of the release creations


class ProductionDateField(colander.SchemaNode):
    oid = "production_date"
    schema_type = colander.Date
    missing = ""


# -- Distribution tab --

class LabelCatalogNumberField(colander.SchemaNode):
    oid = "label_catalog_number"
    schema_type = colander.String
    missing = ""


class EanUpcCodeField(colander.SchemaNode):
    oid = "ean_upc_code"
    schema_type = colander.String
    validator = colander.All(
        # TODO: find out why this is not working (old colander version?):
        # min_err=_('at least 12 digits for a valid UPC barcode,
        #           '13 for an EAN code.'),
        # max_err=_('maximum of 13 digits for an EAN code (12 for a UPC).'
        colander.Length(min=12, max=13),
        # colander.ContainsOnly(
        #     '0123456789',
        #     err_msg=_('may only contain digits') <- why no custom err_msg?!?
        # )
        colander.Regex('^[0-9]*$', msg=_('May only contain digits'))
    )
    missing = ""


class IsrcCodeField(colander.SchemaNode):
    oid = "isrc_code"
    schema_type = colander.String
    validator = colander.Regex('^[a-zA-Z][a-zA-Z][a-zA-Z0-9][a-zA-Z0-9][a-z'
                               'A-Z0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*$',
                               msg=_('Please enter a valid international '
                                     'standard recording code, for example: '
                                     'DEA123456789'))
    missing = ""


class ReleaseDateField(colander.SchemaNode):
    oid = "release_date"
    schema_type = colander.Date
    missing = ""


class ReleaseCancellationDateField(colander.SchemaNode):
    oid = "release_cancellation_date"
    schema_type = colander.Date
    missing = ""


class OnlineReleaseDateField(colander.SchemaNode):
    oid = "online_release_date"
    schema_type = colander.Date
    missing = ""


class OnlineReleaseCancellationDateField(colander.SchemaNode):
    oid = "online_cancellation_date"
    schema_type = colander.Date
    missing = ""


class DistributionTerritoryField(colander.SchemaNode):
    oid = "distribution_territory"
    schema_type = colander.String
    missing = ""


# --- Schemas -----------------------------------------------------------------

class MetadataSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    release_type = ReleaseTypeField(title=_(u"Release Type"))
    artist = ArtistField(title=_(u"Artist"))
    split_artists = SplitArtistSequence(
        title=_(u"Split Artists"), actions=['add'])
    release_title = ReleaseTitleField(title=_(u"Title"))
    genres = GenreCheckboxField(title=_(u"Genres"))
    styles = StyleCheckboxField(title=_(u"Styles"))
    warning = WarningField(title=_(u"Warning"))
    picture = PictureField(title=_(u"Picture"))


class MediaSequence(colander.SequenceSchema):
    title = ""
    description = _(u"Please add a medium, then add some tracks.")
    track_sequence = TrackSequence(title=_(u"Medium"), min_len=1,
                                   language_overrides={
                                       "custom": {"create": _(u"Add Track")}
                                   })


class TracksSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    media = MediaSequence(actions=['create', 'edit'])


class ProductionSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    publisher = PublisherSequence(title=_(u"Publisher"), max_len=1)
    isrc_code = IsrcCodeField(title=_(u"ISRC Code"))
    copyright_date = CopyrightDateField(title=_(u"Copyright Date"))
    # copyright_owner = CopyrightOwnerField(title=_(u"Copyright Owner(s)"))
    production_date = ProductionDateField(title=_(u"Production Date"))


class DistributionSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    label = LabelSequence(title=_(u"Label"), max_len=1)
    label_catalog_number = LabelCatalogNumberField(
        title=_(u"Label Catalog Number of Release"))
    ean_upc_code = EanUpcCodeField(title=_(u"EAN or UPC Code"))
    release_date = ReleaseDateField(title=_(u"Release Date"))
    release_cancellation_date = ReleaseCancellationDateField(
        title=_(u"Release Cancellation Date"))
    online_release_date = OnlineReleaseDateField(
        title=_(u"Online Release Date"))
    online_cancellation_date = OnlineReleaseCancellationDateField(
        title=_(u"Online Release Cancellation Date"))
    distribution_territory = DistributionTerritoryField(
        title=_(u"Distribution Territory"))


class AddReleaseSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    metadata = MetadataSchema(title=_(u"Metadata"))
    production = ProductionSchema(title=_(u"Production"))
    distribution = DistributionSchema(title=_(u"Distribution"))
    tracks = TracksSchema(title=_(u"Tracks"))


# --- Forms -------------------------------------------------------------------

def add_release_form(request):
    return deform.Form(
        schema=AddReleaseSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
