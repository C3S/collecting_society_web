# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import shutil
import logging
import magic
import hashlib
import uuid
from decimal import Decimal
from cgi import FieldStorage
from pydub import AudioSegment

from webob.byterange import ContentRange
from pyramid.response import FileResponse
from pyramid.security import (
    Allow,
    DENY_ALL,
    NO_PERMISSION_REQUIRED
)
from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPForbidden,
    HTTPServiceUnavailable,
    HTTPInternalServerError,
    HTTPNotFound
)
from cornice import Service
from colander import (
    MappingSchema,
    SchemaNode,
    String,
    OneOf,
    Email
)

from collecting_society_portal.models import Tdb, WebUser
from collecting_society_portal_creative.models import Content

from ...services import _
from ...services.lossless_audio_formats import (
    lossless_audio_extensions,
    lossless_audio_mimetypes
)


log = logging.getLogger(__name__)
mime = magic.Magic(mime=True)

_prefix = 'repertoire'


# --- configuration -----------------------------------------------------------

_path_temporary = 'temporary'
_path_complete = 'complete'
_path_preview = 'preview'

_preview_format = 'ogg'
_preview_quality = '0'
_preview_bitrate = '16000'
_preview_fadein = 1000
_preview_fadeout = 1000
_preview_segment_duration = 8000
_preview_segment_crossfade = 2000
_preview_segment_interval = 54000


# --- methods -----------------------------------------------------------------

def get_cors_policy():
    return {
        'origins': os.environ['API_C3SUPLOAD_CORS_ORIGINS'].split(","),
        'credentials': True
    }


def get_cors_headers():
    return ', '.join([
        'Content-Type',
        'Content-Range',
        'Content-Disposition',
        'Content-Description'
    ])


def get_acl(request):
    # no webuser logged in
    if not request.user:
        return [DENY_ALL]
    # webuser logged in
    return [
        (
            Allow,
            request.unauthenticated_userid,
            ('create', 'read', 'update', 'delete')
        ),
        DENY_ALL
    ]


def get_url(url, version, action, content_id):
    if url.endswith('/'):
        url = url[:-1]
    return '/'.join([str(url), str(version), str(action), str(content_id)])


def get_path(request, directory, filename=None):
    base_directory = request.registry.settings['api.c3supload.filepath']
    webuser_directory = str(request.user.id)
    if not filename:
        return os.path.join(base_directory, directory, webuser_directory)
    return os.path.join(base_directory, directory, webuser_directory, filename)


def get_content_info(request, content):
    return {
        'name': content.name,
        'size': content.size,
        'extension': content.extension,
        'type': content.mime_type,
        'duration': "{:.0f}:{:02.0f}".format(
            *divmod(int(content.length), 60)
        ),
        'channels': 'mono' if content.channels == 1 else 'stereo',
        'sample_width': '{:d} bit'.format(content.sample_width),
        'frame_rate': '{:d} Hz'.format(content.sample_rate),
        'previewUrl': get_url(
            url=request.registry.settings['api.c3supload.url'],
            version=request.registry.settings['api.c3supload.version'],
            action='preview',
            content_id=content.id
        ),
        'deleteUrl': get_url(
            url=request.registry.settings['api.c3supload.url'],
            version=request.registry.settings['api.c3supload.version'],
            action='delete',
            content_id=content.id
        ),
        'deleteType': 'GET'
    }


def create_path(path):
    try:
        os.makedirs(path)
    except IOError:
        pass
    return os.path.exists(path)


def delete_file(absolute_path):
    # check file
    if not os.path.isfile(absolute_path):
        return True
    # delete file
    try:
        os.remove(absolute_path)
    except IOError:
        pass
    return not os.path.isfile(absolute_path)


def validate_upload(filename, absolute_path):

    # check filetype
    extension = os.path.splitext(filename)[1]
    if extension:
        extension = extension[1:]
    if extension not in lossless_audio_extensions():
        return _(u'Filetype not allowed.')

    # check mimetype
    mimetype = mime.from_file(absolute_path)
    if mimetype not in lossless_audio_mimetypes():
        return _(u'Mimetype not allowed.')


def save_upload_to_fs(descriptor, absolute_path, contentrange=None):

    # chunked file
    if contentrange:
        start, stop, length = contentrange
        complete = False
        # check file
        size = 0
        if os.path.isfile(absolute_path):
            size = os.path.getsize(absolute_path)
            if stop == length:
                complete = True
        if start != size:
            log.info(
                (
                    'Uploaderror: wrong chunkposition '
                    '(file %s, start: %s, size: %s).'
                ) % (
                    absolute_path, start, size
                )
            )
            return (False, None)
    # whole file
    else:
        complete = True
        # check file
        if os.path.isfile(absolute_path):
            log.info(
                (
                    'Uploaderror: file already exists (%s).'
                ) % (
                    absolute_path
                )
            )
            return (False, None)

    # save
    try:
        with open(absolute_path, 'a') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        raise HTTPInternalServerError

    return (
        os.path.getsize(absolute_path) == stop,
        complete
    )


def get_segments(audio):
    _total = len(audio)
    _segment = _preview_segment_duration
    _interval = _preview_segment_interval
    if _segment >= _total:
        yield audio
    else:
        start = 0
        end = _segment
        while end < _total:
            yield audio[start:end]
            start = end + _interval + 1
            end = start + _segment


def create_preview(audio, preview_path):

    # convert to mono
    mono = audio.set_channels(1)

    # mix segments
    preview = None
    for segment in get_segments(mono):
        preview = segment if not preview else preview.append(
            segment, crossfade=_preview_segment_crossfade
        )

    # fade in/out
    preview = preview.fade_in(_preview_fadein).fade_out(_preview_fadeout)

    # export
    try:
        preview.export(
            preview_path,
            format=_preview_format,
            parameters=[
                "-aq", _preview_quality,
                "-ar", _preview_bitrate
            ]
        )
    except:
        raise HTTPInternalServerError

    return os.path.isfile(preview_path)


def save_upload_to_db(request, filename, temporary_path):

    # archive uuid
    archive_info = os.path.join(
        request.registry.settings['api.c3supload.filepath'],
        _path_complete, 'archive.info'
    )
    if os.path.isfile(archive_info):
        with open(archive_info, 'r') as f:
            archive_uuid = f.read()
    else:
        while True:
            archive_uuid = str(uuid.uuid4())
            # ensure uniqueness
            if not Content.search_by_uuid(archive_uuid):
                break
        with open(archive_info, 'a') as f:
            f.write(archive_uuid)

    # content uuid
    while True:
        content_uuid = str(uuid.uuid4())
        # ensure uniqueness
        if not Content.search_by_uuid(content_uuid):
            break

    # move audio file to completed folder
    completed_path = get_path(request, _path_complete, content_uuid)
    preview_path = get_path(request, _path_preview, content_uuid)
    try:
        shutil.copyfile(temporary_path, completed_path)
        os.remove(temporary_path)
    except IOError:
        raise HTTPInternalServerError

    # create preview
    audio = AudioSegment.from_file(completed_path)
    create_preview(audio, preview_path)

    # save to db
    _content = {
        'processing_state': "uploaded",
        'archive': archive_uuid,
        'uuid': content_uuid,
        'user': WebUser.current_user(request).id,
        'name': str(filename),
        'category': 'audio',
        'mime_type': str(mime.from_file(completed_path)),
        'length': "%.6f" % audio.duration_seconds,
        'channels': int(audio.channels),
        'sample_rate': int(audio.frame_rate),
        'sample_width': int(audio.sample_width * 8),
        'size': os.path.getsize(completed_path),
        'path': completed_path,
        'preview_path': preview_path
    }
    contents = Content.create([_content])
    if not len(contents) == 1:
        return False
    return contents[0]


# --- service: upload ---------------------------------------------------------

repertoire_upload = Service(
    name=_prefix + 'upload',
    path=_prefix + '/v1/upload',
    description="uploads repertoire files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_upload.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_upload(request):
    response = request.response
    # cors headers explicitly not set for OPTIONS by cornice,
    # but required for the jQuery File Upload plugin
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@repertoire_upload.post(
    permission='create')
@Tdb.transaction(readonly=False)
def post_repertoire_upload(request):

    # create paths
    for subpath in [_path_temporary, _path_complete, _path_preview]:
        path = get_path(request, subpath)
        if not os.path.exists(path):
            create_path(path)

    # upload files
    files = []
    for name, fieldStorage in request.POST.items():

        # check fieldStorage
        if not isinstance(fieldStorage, FieldStorage):
            continue

        # configure upload
        filename = os.path.basename(fieldStorage.filename)
        filename_hash = hashlib.md5(filename).hexdigest()
        absolute_path = get_path(request, _path_temporary, filename_hash)
        contentrange = ContentRange.parse(
            request.headers.get('Content-Range', None)
        )

        # save to filesystem (temporary folder)
        ok, complete = save_upload_to_fs(
            descriptor=fieldStorage.file,
            absolute_path=absolute_path,
            contentrange=contentrange
        )
        if not ok:
            raise HTTPInternalServerError
        if not complete:
            files.append({
                'name': fieldStorage.filename,
                'size': os.path.getsize(absolute_path)
            })
            continue

        # validate file
        error = validate_upload(filename, absolute_path)
        if error:
            delete_file(absolute_path)
            files.append({
                'name': fieldStorage.filename,
                'error': error
            })
            continue

        # save to database
        content = save_upload_to_db(request, filename, absolute_path)
        if not content:
            raise HTTPInternalServerError
        files.append(get_content_info(request, content))

    return {'files': files}


# --- service: list -----------------------------------------------------------

repertoire_list = Service(
    name=_prefix + 'list',
    path=_prefix + '/v1/list',
    description="lists repertoire files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_list.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_list(request):
    return


@repertoire_list.get(
    permission='read')
@Tdb.transaction(readonly=False)
def get_repertoire_list(request):
    files = []
    contents = Content.current_orphans(request, 'audio')
    if contents:
        for content in contents:
            files.append(get_content_info(request, content))
    return {'files': files}


# --- service: show -----------------------------------------------------------

repertoire_show = Service(
    name=_prefix + 'show',
    path=_prefix + '/v1/show/{filename}',
    description="checks partially uploaded files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_show.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_show(request):
    return


@repertoire_show.get(
    permission='read')
@Tdb.transaction(readonly=True)
def get_repertoire_show(request):
    filename = request.matchdict['filename']
    if not filename:
        return {}
    filename_hash = hashlib.md5(filename).hexdigest()
    absolute_path = get_path(request, _path_temporary, filename_hash)
    if not os.path.isfile(absolute_path):
        return {}
    return {
        'name': filename,
        'size': os.path.getsize(absolute_path)
    }


# --- service: preview --------------------------------------------------------

repertoire_preview = Service(
    name=_prefix + 'preview',
    path=_prefix + '/v1/preview/{id}',
    description="previewd the uploaded repertoire files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_preview.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_preview(request):
    return


@repertoire_preview.get(
    permission='read')
@Tdb.transaction(readonly=True)
def get_repertoire_preview(request):
    content = Content.search_by_id(request.matchdict['id'])
    preview_path = content.preview_path
    if not os.path.isfile(preview_path):
        raise HTTPNotFound()
    if not content.user != WebUser.current_user:
        raise HTTPForbidden()
    return FileResponse(
        preview_path,
        request=request,
        content_type=str(content.mime_type)
    )


# --- service: delete ---------------------------------------------------------

repertoire_delete = Service(
    name=_prefix + 'delete',
    path=_prefix + '/v1/delete/{id}',
    description="deletes uploaded repertoire files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_delete.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_delete(request):
    return


@repertoire_delete.get(
    permission='delete')
@Tdb.transaction(readonly=False)
def get_repertoire_delete(request):
    content_id = request.matchdict['id']
    content = Content.search_by_id(content_id)
    info = get_content_info(request, content)
    log.info("{} deleted content {}\n".format(request.user, info))
    # delete preview
    name = content.name
    delete_file(get_path(request, _path_preview, content.uuid))
    # delete db
    content.delete([content])
    return {'files': [{name: True}]}
