# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import shutil
import logging
import magic
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

from ...services import _
from ...services.lossless_audio_formats import (
    lossless_audio_extensions,
    lossless_audio_mimetypes
)


log = logging.getLogger(__name__)
mime = magic.Magic(mime=True)

_prefix = 'repertoire'


# --- configuration -----------------------------------------------------------

_stage_part = 'part'
_stage_complete = 'complete'
_stage_preview = 'preview'

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


def get_url(url, version, action, filename):
    if url.endswith('/'):
        url = url[:-1]
    return '/'.join([url, version, action, filename])


def get_path(request, stage=_stage_complete, filename=None):
    base = request.registry.settings['api.c3supload.filepath']
    webuser = str(request.user.id)
    if filename:
        return os.path.join(base, webuser, stage, filename)
    return os.path.join(base, webuser, stage)


def get_info(request, filename):

    # get file paths
    file_part = get_path(request, _stage_part, filename)
    file_complete = get_path(request, _stage_complete, filename)

    # get status
    complete = os.path.isfile(file_complete)
    resumable = not complete and os.path.isfile(file_part)
    file = file_part if resumable else file_complete

    # file not found
    if not (complete or resumable):
        return {
            'name': filename,
            'complete': False,
            'resumable': False,
            'error': _(u'File not found')
        }

    # extension
    extension = os.path.splitext(filename)[1]
    if extension:
        extension = extension[1:]

    # load audio for properties
    audio = AudioSegment.from_file(file)

    return {
        'name': filename,
        'extension': extension,
        'type': mime.from_file(file),
        'size': os.path.getsize(file),
        'duration': "{:.0f}:{:02.0f}".format(
            *divmod(audio.duration_seconds, 60)
        ),
        'channels': 'mono' if audio.channels == 1 else 'stereo',
        'sample_width': '{:d} bit'.format(audio.sample_width * 8),
        'frame_rate': '{:d} Hz'.format(audio.frame_rate),
        'complete': complete,
        'resumable': resumable,
        'previewUrl': get_url(
            url=request.registry.settings['api.c3supload.url'],
            version=request.registry.settings['api.c3supload.version'],
            action='preview',
            filename=filename
        ),
        'deleteUrl': get_url(
            url=request.registry.settings['api.c3supload.url'],
            version=request.registry.settings['api.c3supload.version'],
            action='delete',
            filename=filename
        ),
        'deleteType': 'GET'
    }


def validate_file(request, info):

    # check filetype
    if info['extension'] not in lossless_audio_extensions():
        return _(u'Filetype not allowed.')

    # check mimetype
    if info['type'] not in lossless_audio_mimetypes():
        return _(u'Mimetype not allowed.')


def create_path(path):
    try:
        os.makedirs(path)
    except IOError:
        pass
    return os.path.exists(path)


def save_file(descriptor, file):

    # check file
    if os.path.isfile(file):
        return False

    # save file
    try:
        with open(file, 'w') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        raise HTTPInternalServerError

    return os.path.isfile(file)


def save_chunk(descriptor, file, part, contentrange):

    start, stop, length = contentrange

    # check file
    if os.path.isfile(file):
        return False

    # check chunk range
    size = 0
    if os.path.isfile(part):
        size = os.path.getsize(part)
    if start != size:
        return False

    # save chunk
    try:
        with open(part, 'a') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        raise HTTPInternalServerError

    # move part to file after last chunk
    if os.path.getsize(part) == length:
        try:
            shutil.copyfile(part, file)
            os.remove(part)
            return (os.path.getsize(file) == length)
        except IOError:
            raise HTTPInternalServerError

    return (os.path.getsize(part) == stop)


def get_segments(audio):
    _total = len(audio)
    _segment = _preview_segment_duration
    _interval = _preview_segment_interval
    if _segment >= _total:
        yield audio
    start = 0
    end = _segment
    while end < _total:
        yield audio[start:end]
        start = end + _interval + 1
        end = start + _segment


def create_preview(file_complete, file_preview):

    # load audio file
    audio = AudioSegment.from_file(file_complete)

    # convert to mono
    audio = audio.set_channels(1)

    # mix segments
    preview = None
    for segment in get_segments(audio):
        preview = segment if not preview else preview.append(
            segment, crossfade=_preview_segment_crossfade
        )

    # fade in/out
    preview = preview.fade_in(_preview_fadein).fade_out(_preview_fadeout)

    # export
    try:
        preview.export(
            file_preview,
            format=_preview_format,
            parameters=[
                "-aq", _preview_quality,
                "-ar", _preview_bitrate
            ]
        )
    except:
        raise HTTPInternalServerError

    return os.path.isfile(file_preview)


def delete_file(file):

    # check file
    if not os.path.isfile(file):
        return True

    # delete file
    try:
        os.remove(file)
    except IOError:
        pass

    return not os.path.isfile(file)


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
def post_repertoire_upload(request):

    # create paths
    for stage in [_stage_part, _stage_complete, _stage_preview]:
        path = get_path(request, stage)
        if not os.path.exists(path):
            create_path(path)

    # upload files
    files = []
    for name, fieldStorage in request.POST.items():
        if not isinstance(fieldStorage, FieldStorage):
            continue
        filename = os.path.basename(fieldStorage.filename)
        file_part = get_path(request, _stage_part, filename)
        file_complete = get_path(request, _stage_complete, filename)
        file_preview = get_path(request, _stage_preview, filename)

        # check file
        if os.path.isfile(file_complete):
            info = get_info(request, filename)
            info.update({'error': _(u'File already exists.')})
            files.append(info)
            continue

        # save chunk
        contentrange = ContentRange.parse(
            request.headers.get('Content-Range', None)
        )
        if contentrange:
            ok = save_chunk(
                descriptor=fieldStorage.file,
                file=file_complete,
                part=file_part,
                contentrange=contentrange
            )
            if not ok:
                raise HTTPInternalServerError

        # save whole file
        else:
            ok = save_file(
                descriptor=fieldStorage.file,
                file=file_complete
            )
            if not ok:
                raise HTTPInternalServerError

        # get info from file
        info = get_info(request, filename)

        # check mime type (after saving the file due to chunking)
        error = validate_file(request, info)
        if error:
            # delete file again
            # 2DO: prevent further chunks being sent by client on error.
            # Manual errors dont abort uploads. Http errors abort all uploads.
            if info['complete']:
                for stage in [_stage_part, _stage_complete, _stage_preview]:
                    file = get_path(request, stage, filename)
                    ok = delete_file(file)
                    if not ok:
                        raise HTTPInternalServerError
            # user feedback
            info.update({'error': error})
            files.append(info)
            continue

        # create preview
        if info['complete']:
            ok = create_preview(
                file_complete=file_complete,
                file_preview=file_preview
            )
            if not ok:
                raise HTTPInternalServerError

        log.info("{} uploaded file {}\n".format(request.user, info))
        files.append(info)

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
def get_repertoire_list(request):
    files = []
    path_complete = get_path(request, _stage_complete)
    if not os.path.isdir(path_complete):
        return {'files': []}
    for filename in os.listdir(path_complete):
        info = get_info(request, filename)
        if info:
            files.append(info)
    return {'files': files}


# --- service: show -----------------------------------------------------------

repertoire_show = Service(
    name=_prefix + 'show',
    path=_prefix + '/v1/show/{filename}',
    description="shows uploaded repertoire files",
    cors_policy=get_cors_policy(),
    acl=get_acl
)


@repertoire_show.options(
    permission=NO_PERMISSION_REQUIRED)
def options_repertoire_show(request):
    return


@repertoire_show.get(
    permission='read')
def get_repertoire_show(request):
    filename = request.matchdict['filename']
    return get_info(request, filename)


# --- service: preview --------------------------------------------------------

repertoire_preview = Service(
    name=_prefix + 'preview',
    path=_prefix + '/v1/preview/{filename}',
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
def get_repertoire_preview(request):
    filename = request.matchdict['filename']
    file = get_path(request, _stage_preview, filename)
    if not os.path.isfile(file):
        raise HTTPNotFound()
    return FileResponse(
        file,
        request=request,
        content_type=mime.from_file(file)
    )


# --- service: delete ---------------------------------------------------------

repertoire_delete = Service(
    name=_prefix + 'delete',
    path=_prefix + '/v1/delete/{filename}',
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
def get_repertoire_delete(request):
    filename = request.matchdict['filename']
    info = get_info(request, filename)
    log.info("{} deleted file {}\n".format(request.user, info))
    for stage in [_stage_part, _stage_complete, _stage_preview]:
        file = get_path(request, stage, filename)
        ok = delete_file(file)
        if not ok:
            return {'files': [{filename: False}]}
    return {'files': [{filename: True}]}
