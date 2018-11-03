# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController

from ...services import _
from ...models import (
    Artist,
    Creation,
    Track,
    License,
    Label
)
from .add_release import AddReleaseSchema

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditRelease(FormController):
    """
    form controller for edit release
    """

    def controller(self):
        self.form = edit_release_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_release()
        else:
            self.edit_release()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_release(self):
        release = self.context.release

        # set appstruct
        self.appstruct = {
            'metadata': {
                'release_type':
                    release.type,
                'release_title':
                    release.title or '',
                'genres':
                    [unicode(genre.id) for genre in release.genres],
                'styles':
                    [unicode(style.id) for style in release.styles],
                'warning':
                    release.warning or '',
            },
            'tracks': {
                'tracks': []
            },
            'production': {
                'isrc_code':
                    release.isrc_code or '',
                'copyright_date':
                    release.copyright_date or '',
                'production_date':
                    release.production_date or '',
            },
            'distribution': {
                'label_catalog_number':
                    release.label_catalog_number or '',
                'ean_upc_code':
                    release.ean_upc_code or '',
                'release_date':
                    release.release_date or '',
                'release_cancellation_date':
                    release.release_cancellation_date or '',
                'online_release_date':
                    release.online_release_date or '',
                'online_cancellation_date':
                    release.online_cancellation_date or '',
                'distribution_territory':
                    release.distribution_territory or '',
            },
        }

        # artist release: artist
        if release.type == 'artist':
            self.appstruct['metadata']['artist'] = release.artists[0].oid

        # split release: split_artists
        if release.type == 'split':
            self.appstruct['metadata']['split_artists'] = []
            for artist in release.artists:
                self.appstruct['metadata']['split_artists'].append({
                    'mode': "add",
                    'oid': artist.oid,
                    'name': artist.name,
                    'code': artist.code or '',
                    'description': artist.description or '',
                })

        # tracks
        tracks = sorted(release.tracks, key=lambda t: t.track_number)
        log.debug(tracks)
        for track in tracks:
            creation_mode = "add"
            if Creation.is_foreign_track(
                    self.request, release, track.creation):
                creation_mode = "edit"
            self.appstruct['tracks']['tracks'].append({
                'mode': "edit",
                'oid': track.oid,
                'track_title': track.title,
                'license': track.license.oid,
                # 'medium_number': track.medium_number,
                # 'track_number': track.track_number,
                'track': [{
                    'mode': creation_mode,
                    'oid': track.creation.oid,
                    'code': track.creation.code,
                    'titlefield': track.creation.title,
                    'artist': track.creation.artist.name
                }]
            })

        # set label
        if release.label:
            mode = 'add'
            if self.request.party == release.label.entity_creator:
                mode = 'edit'
            self.appstruct['distribution']['label'] = [{
                'mode': mode,
                'oid': release.label.oid,
                'name': release.label.name,
                'gvl_code': release.label.gvl_code or '',
            }]

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_release(self):
        appstruct = self.appstruct
        web_user = self.request.web_user
        party = self.request.party
        release = self.context.release

        # generate vlist
        _release = {
            'type':
                appstruct['metadata']['release_type'],
            'tracks':
                None,  # TODO: tracks (also in edit_release)
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
            artist = Artist.search_by_oid(appstruct['metadata']['artist'])
            if artist and artist.permits(web_user, 'edit_artist'):
                _add = [artist.id]
                _remove = [ra.id for ra in release.artists]
                if set(_add) != set(_remove):
                    _release['artists'] = [
                        ['add', [artist.id]],
                        ['remove', _remove]]

        # split realease: split_artists
        if appstruct['metadata']['release_type'] == 'split':
            _add = []
            _remove = [ra.id for ra in release.artists]
            for _artist in appstruct['metadata']['split_artists']:
                artist = Artist.search_by_oid(_artist['oid'])
                if artist:
                    _add.append(artist.id)
                    if artist.id in _remove:
                        _remove.remove(artist.id)
            _release['artists'] = [['add', _add], ['remove', _remove]]

        # split realease: compilation
        if appstruct['metadata']['release_type'] == 'compilation':
            _remove = [ra.id for ra in release.artists]
            _release['artists'] = [['remove', _remove]]

        # tracks
        _tracks = appstruct['tracks']['tracks']
        if _tracks:
            tracks_create = []
            tracks_delete = list(release.tracks)
            for track_number, _track in enumerate(_tracks):
                _creation = _track['track'][0]
                license = License.search_by_oid(_track['license'])
                if not license:
                    continue

                # create track
                if _track['mode'] == "create":
                    # create creation
                    if _creation['mode'] == "create":
                        artist = Artist.create([{
                            'name': _creation['artist'],
                            'entity_origin': 'indirect',
                            'entity_creator': party.id
                            }])[0]
                        if not artist:
                            continue
                        creation = Creation.create([{
                            'title': _creation['titlefield'],
                            'artist': artist.id,
                            'entity_origin': 'indirect',
                            'entity_creator': party.id
                            }])[0]
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
                        'medium_number': 0,  # TODO
                        'track_number': track_number + 1,
                        'license': license.id
                        })

                # edit track
                if _track['mode'] == "edit":
                    track = Track.search_by_oid(_track['oid'])
                    if not track:
                        continue
                    if track in tracks_delete:
                        tracks_delete.remove(track)
                    # create creation
                    if _creation['mode'] == "create":
                        artist = Artist.create([{
                            'name': _creation['artist'],
                            'entity_origin': 'indirect',
                            'entity_creator': party.id
                            }])[0]
                        if not artist:
                            continue
                        creation = Creation.create([{
                            'title': _creation['titlefield'],
                            'artist': artist.id,
                            'entity_origin': 'indirect',
                            'entity_creator': party.id
                            }])[0]
                        if not creation:
                            continue
                    # add creation
                    else:
                        creation = Creation.search_by_oid(_creation['oid'])
                        if not creation:
                            continue
                        # edit creation
                        if _creation['mode'] == "edit":
                            creation.artist.name = _creation['artist']
                            creation.artist.save()
                            creation.title = _creation['titlefield']
                            creation.save()
                    # update track
                    track.creation = creation.id
                    track.license = license.id
                    track.title = _track['track_title']
                    track.medium_number = 0  # TODO
                    track.track_number = track_number + 1
                    track.save()

            # append actions
            _release['tracks'] = []
            if tracks_create:
                _release['tracks'].append(('create', tracks_create))
            if tracks_delete:
                _release['tracks'].append(('delete', tracks_delete))

        # label
        _label = next(iter(appstruct['distribution']['label']), None)
        if not _label:
            release.label_name = None
            release.label = None
            release.save()
        else:
            if _label['mode'] == "add":
                label = Label.search_by_oid(_label['oid'])
                if label:
                    release.label = label.id
                    release.save()
            if _label['mode'] == "create":
                label = Label.create([{
                    'name': _label['name'],
                    'entity_creator': party,
                    'entity_origin': 'indirect'
                    }])[0]
                release.label = label.id
                release.save()
            if _label['mode'] == "edit":
                if party == release.label.entity_creator:
                    release.label.name = _label['name']
                    release.label.save()

        # picture
        if appstruct['metadata']['picture']:
            with open(appstruct['metadata']['picture']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = appstruct['metadata']['picture']['mimetype']
            _release['picture_data'] = picture_data
            _release['picture_data_mime_type'] = mimetype

        # remove empty fields
        for index, value in _release.items():
            if not value:
                del _release[index]

        # update release
        release.write([release], _release)

        # user feedback
        log.info("edit release successful for %s: %s" % (web_user, release))
        self.request.session.flash(
            _(u"Release edited: ") + release.title + " (" + release.code + ")",
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

def edit_release_form(request):
    return deform.Form(
        schema=AddReleaseSchema(
            title=_(u"Edit Release")
        ).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
