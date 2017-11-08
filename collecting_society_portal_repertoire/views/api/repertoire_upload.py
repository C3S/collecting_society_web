# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import shutil
import logging
import magic
import hashlib
import uuid
import datetime
import time
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

from collecting_society_portal.services import (
    benchmark,
    csv_export,
    csv_import
)
from collecting_society_portal.models import (
    Tdb,
    WebUser,
    Checksum
)
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
_path_uploaded = 'uploaded'
_path_rejected = 'rejected'
_path_preview = 'preview'

# 2DO: _preview_default
_preview_format = 'ogg'
_preview_quality = '0'
_preview_samplerate = '16000'
_preview_fadein = 1000
_preview_fadeout = 1000
_preview_segment_duration = 8000
_preview_segment_crossfade = 2000
_preview_segment_interval = 54000

_hash_algorithm = hashlib.sha256

_checksum_algorithm = hashlib.sha256
_checksum_postfix = '.checksums'


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


def get_hostname():
    return 'processing'


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
    # admin feedback
    log.info(("file deleted: %s\n") % (absolute_path))
    return not os.path.isfile(absolute_path)


def move_file(source, target):
    # check file
    if not os.path.isfile(source):
        return False
    if os.path.isfile(target):
        return False
    # move file
    try:
        os.rename(source, target)
    except IOError:
        pass
    return (os.path.isfile(target) and not os.path.isfile(source))


def create_paths(request):
    for subpath in [_path_temporary,
                    _path_uploaded,
                    _path_preview,
                    _path_rejected]:
        path = get_path(request, subpath)
        if not os.path.exists(path):
            create_path(path)


def move_files_with_prefixes(source, target):
    ok = True
    for postfix in ['', _checksum_postfix]:
        ok = (ok and move_file(source + postfix, target + postfix))
    return ok


def delete_files_with_identifiers(request, identifiers):
    for subpath in [_path_temporary,
                    _path_uploaded,
                    _path_preview,
                    _path_rejected]:
        for identifier in identifiers:
            for postfix in ['', _checksum_postfix]:
                path = get_path(request, subpath, identifier + postfix)
                if os.path.isfile(path):
                    delete_file(path)


def panic(request, reason, identifiers):
    # admin feedback
    # 2DO: mail
    log.info(
        (
            "Panic: %s\n"
            "Deleting all files:\n"
            "- User %s\n"
            "- Identifiers %s\n"
        ) % (
            reason, request.user, identifiers
        )
    )
    delete_files_with_identifiers(request, identifiers)
    raise HTTPInternalServerError


def save_upload_to_fs(descriptor, absolute_path, contentrange=None):

    # chunked file
    if contentrange:
        begin, end, length = contentrange
        complete = False
        # check file
        size = 0
        if os.path.isfile(absolute_path):
            size = os.path.getsize(absolute_path)
            if end == length:
                complete = True
        if begin != size:
            # admin feedback
            log.info(
                (
                    'Uploaderror: wrong chunkposition '
                    '(file %s, begin: %s, size: %s).'
                ) % (
                    absolute_path, begin, size
                )
            )
            return (False, None)
    # whole file
    else:
        complete = True
        descriptor.seek(0)
        end = descriptor.tell()
        descriptor.seek(0)
        # check file
        if os.path.isfile(absolute_path):
            # admin feedback
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
        os.path.getsize(absolute_path) == end,
        complete
    )


def save_upload_to_db(content):
    contents = Content.create([content])
    if not len(contents) == 1:
        return False
    return contents[0]


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


def create_checksum(descriptor, algorithm=hashlib.sha256):
    checksum = algorithm(descriptor.read())
    descriptor.seek(0)
    return checksum


def save_checksum(path, algorithm, checksum, contentrange=None):
    begin, end, _ = contentrange
    csv_export(
        path=path,
        fieldnames=[
            'begin',
            'end',
            'algorithm',
            'checksum'
        ],
        row={
            'begin': begin,
            'end': end,
            'algorithm': algorithm,
            'checksum': checksum
        }
    )


def save_checksums_to_db(content, path):
    checksums = []
    timestamp = datetime.datetime.now()
    rows = csv_import(path)
    for row in rows:
        checksums.append({
            'origin': 'content,%s' % (content.id),
            'code': str(row['checksum']),
            'timestamp': timestamp,
            'algorithm': str(row['algorithm']),
            'begin': int(row['begin']),
            'end': int(row['end'])
        })
    Checksum.create(checksums)


def is_collision(contentrange, checksum):
    begin, end, length = contentrange
    collisions = Checksum.search_collision(
        code=checksum.hexdigest(),
        algorithm=_checksum_algorithm.__name__,
        begin=begin,
        end=end
    )
    if not collisions:
        return False
    return True


def get_content_uuid():
    while True:
        content_uuid = str(uuid.uuid4())
        if not Content.search_by_uuid(content_uuid):
            break
    return content_uuid


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
    ok = True
    try:
        preview.export(
            preview_path,
            format=_preview_format,
            parameters=[
                "-aq", _preview_quality,
                "-ar", _preview_samplerate
            ]
        )
    except:
        ok = False

    return (ok and os.path.isfile(preview_path))


def raise_abuse_rank(request):
    rank_max = int(request.registry.settings['abuse_rank.max'])
    current_rank = request.session['abuse_rank']['current']
    current_rank = (current_rank + 1) % (rank_max + 1)
    request.session['abuse_rank']['current'] = current_rank
    log.debug(
        (
            "raised session abuse rank of user %s to %s\n"
        ) % (
            request.user, request.session['abuse_rank']['current']
        )
    )


def ban(request):
    request.session['abuse_rank']['banned'] = True
    request.session['abuse_rank']['bantime'] = time.time()
    web_user = WebUser.current_web_user(request)
    if not web_user.abuse_rank:
        web_user.abuse_rank = 0
    web_user.abuse_rank += 1
    web_user.save()
    log.info(
        (
            "banned upload for user %s (db abuse rank: %s)\n"
        ) % (
            web_user, web_user.abuse_rank
        )
    )


def is_banned(request):
    if 'abuse_rank' not in request.session:
        request.session['abuse_rank'] = {
            'current': 0, 'banned': False, 'bantime': None
        }
    banned = request.session['abuse_rank']['banned']
    if not banned:
        return False
    currenttime = time.time()
    bantime = int(request.session['abuse_rank']['bantime'])
    removeban = int(request.registry.settings['abuse_rank.removeban'])
    if currenttime > bantime + removeban:
        request.session['abuse_rank']['banned'] = False
        request.session['abuse_rank']['current'] = 0
        web_user = WebUser.current_web_user(request)
        log.debug(
            (
                "removed upload ban for user %s (db abuse rank: %s)\n"
            ) % (
                web_user, web_user.abuse_rank
            )
        )
    return request.session['abuse_rank']['banned']


def still_banned_for(request):
    if 'abuse_rank' not in request.session:
        return 0
    banned = request.session['abuse_rank']['banned']
    if not banned:
        return 0
    currenttime = time.time()
    bantime = int(request.session['abuse_rank']['bantime'])
    removeban = int(request.registry.settings['abuse_rank.removeban'])
    seconds_still_banned_for = bantime + removeban - currenttime
    if seconds_still_banned_for <= 0:
        return 0
    return seconds_still_banned_for

        
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
    create_paths(request)

    # upload files
    files = []
    for name, fieldStorage in request.POST.items():

        # check fieldStorage
        if not isinstance(fieldStorage, FieldStorage):
            continue

        # configure upload
        rank = (request.registry.settings['abuse_rank.active'] == 'true')
        rank_max = int(request.registry.settings['abuse_rank.max'])
        hostname = get_hostname()
        descriptor = fieldStorage.file
        filename = os.path.basename(fieldStorage.filename).encode('utf-8')
        filename_hash = _hash_algorithm(filename).hexdigest()
        temporary_path = get_path(request, _path_temporary, filename_hash)
        contentrange = ContentRange.parse(
            request.headers.get('Content-Range', None)
        )
        contentlength = request.headers.get('Content-Length', None)

        # create checksum
        with benchmark(request, name='checksum', uid=filename,
                       normalize=descriptor, scale=100*1024*1024):
            checksum = create_checksum(
                descriptor=descriptor,
                algorithm=_checksum_algorithm
            )
            save_checksum(
                path=temporary_path + _checksum_postfix,
                algorithm=_checksum_algorithm.__name__,
                checksum=checksum.hexdigest(),
                contentrange=contentrange or (0, contentlength, contentlength)
            )

        # abuse rank
        if rank:
            if is_banned(request):
                files.append({
                    'name': fieldStorage.filename,
                    'error': _("Abuse detected. Wait for " + str(int(still_banned_for(request))) + " seconds before trying another upload."),
                })
                continue
            if is_collision(contentrange, checksum):
                raise_abuse_rank(request)
            current_rank = request.session['abuse_rank']['current']
            if current_rank == rank_max:
                ban(request)

        # save to filesystem (-> temporary)
        ok, complete = save_upload_to_fs(
            descriptor=descriptor,
            absolute_path=temporary_path,
            contentrange=contentrange
        )
        if not ok:
            pass
        if not complete:
            # client feedback
            files.append({
                'name': fieldStorage.filename,
                'size': os.path.getsize(temporary_path)
            })
            continue

        # get content uuid
        content_uuid = get_content_uuid()

        # get uuid paths
        uploaded_path = get_path(request, _path_uploaded, content_uuid)
        rejected_path = get_path(request, _path_rejected, content_uuid)
        preview_path = get_path(request, _path_preview, content_uuid)

        # validate file
        error = validate_upload(filename, temporary_path)
        if error:
            # move files (temporary -> rejected)
            ok = move_files_with_prefixes(
                source=temporary_path, target=rejected_path
            )
            if not ok:
                panic(
                    request,
                    reason="Files could not be moved.",
                    identifiers=[filename_hash, content_uuid]
                )
            # save file to database
            _content = {
                'uuid': content_uuid,
                'processing_hostname': hostname,
                'processing_state': "rejected",
                'rejection_reason': "format_error",
                'user': WebUser.current_user(request).id,
                'name': str(name),
                'category': 'audio',
                'mime_type': str(mime.from_file(rejected_path)),
                'size': os.path.getsize(rejected_path),
                'path': rejected_path
            }
            content = save_upload_to_db(_content)
            if not content:
                panic(
                    request,
                    reason="Content could not be created.",
                    identifiers=[filename_hash, content_uuid]
                )
            # save checksums to database
            # admin feedback
            # 2DO: Mail
            log.info(
                (
                    "Content rejected (format error): %s\n"
                ) % (
                    rejected_path
                )
            )
            # client feedback
            files.append({
                'name': fieldStorage.filename,
                'error': error
            })
            continue

        # create preview
        with benchmark(request, name='preview', uid=filename,
                       normalize=temporary_path, scale=100*1024*1024):
            audio = AudioSegment.from_file(temporary_path)
            ok = create_preview(audio, preview_path)
            if not ok:
                panic(
                    request,
                    reason="Preview could not be created.",
                    identifiers=[filename_hash]
                )

        # move files (temporary -> uploaded)
        ok = move_files_with_prefixes(
            source=temporary_path, target=uploaded_path
        )
        if not ok:
            panic(
                request,
                reason="Files could not be moved.",
                identifiers=[filename_hash, content_uuid]
            )

        # save file to database
        _content = {
            'uuid': content_uuid,
            'processing_hostname': hostname,
            'processing_state': "uploaded",
            'user': WebUser.current_user(request).id,
            'name': str(filename),
            'category': 'audio',
            'mime_type': str(mime.from_file(uploaded_path)),
            'size': os.path.getsize(uploaded_path),
            'path': uploaded_path,
            'preview_path': preview_path,
            'length': "%.6f" % audio.duration_seconds,
            'channels': int(audio.channels),
            'sample_rate': int(audio.frame_rate),
            'sample_width': int(audio.sample_width * 8)
        }
        content = save_upload_to_db(_content)
        if not content:
            panic(
                request,
                reason="Content could not be created.",
                identifiers=[filename_hash, content_uuid]
            )
        # save checksums to database
        save_checksums_to_db(
            content=content,
            path=uploaded_path + _checksum_postfix
        )

        # client feedback
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
    filename = request.matchdict['filename'].encode('utf-8')
    if not filename:
        return {}
    filename_hash = _hash_algorithm(filename).hexdigest()
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
    # admin feedback
    log.info("{} deleted content {}\n".format(request.user, info))
    name = content.name
    content.active = False
    content.save()
    return {'files': [{name: True}]}
