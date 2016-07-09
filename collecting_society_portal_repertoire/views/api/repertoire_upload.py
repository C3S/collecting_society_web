# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import shutil
import logging
import magic
from cgi import FieldStorage

from webob.byterange import ContentRange
from pyramid.response import FileResponse
from pyramid.security import NO_PERMISSION_REQUIRED
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


log = logging.getLogger(__name__)
mime = magic.Magic(mime=True)

_prefix = 'repertoire'


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


def authenticate(request):
    if not request.user:
        raise HTTPForbidden


def get_url(url, version, action, filename):
    if url.endswith('/'):
        url = url[:-1]
    return '/'.join([url, version, action, filename])


def get_path(request, filename=None):
    base = request.registry.settings['api.c3supload.filepath']
    webuser = str(request.user.id)
    if filename:
        return os.path.join(base, webuser, filename)
    return os.path.join(base, webuser)


def get_info(request, file):
    filename = os.path.basename(file)
    uploaded = os.path.isfile(file)
    resumable = os.path.isfile(file + '.part')
    if resumable:
        file += '.part'
    if not (uploaded or resumable):
        return {
            'name': filename,
            'resumable': False,
            'error': _(u'File not found')
        }
    return {
        'name': filename,
        'resumable': resumable,
        'size': os.path.getsize(file),
        'type': mime.from_file(file),
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


def create_path(path):
    try:
        os.makedirs(path)
    except IOError:
        pass
    return os.path.exists(path)


def save_file(descriptor, file):
    if os.path.isfile(file):
        return False
    try:
        with open(file, 'w') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        raise HTTPInternalServerError
    return os.path.isfile(file)


def save_chunk(descriptor, file, contentrange):
    chunkfile = file + ".part"
    start, stop, length = contentrange
    size = 0
    if os.path.isfile(chunkfile):
        size = os.path.getsize(chunkfile)
    if start != size:
        return False
    try:
        with open(chunkfile, 'a') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        raise HTTPInternalServerError
    if os.path.getsize(chunkfile) == length:
        try:
            shutil.copyfile(chunkfile, file)
            os.remove(chunkfile)
            return (os.path.getsize(file) == length)
        except IOError:
            raise HTTPInternalServerError
    return (os.path.getsize(chunkfile) == stop)


def delete_file(file):
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
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


class UploadSchema(MappingSchema):
    echo = SchemaNode(
        String(),
        location="body",
        type='str'
    )


@repertoire_upload.options()
def options_repertoire_upload(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@repertoire_upload.post(
    validators=(authenticate))
def post_repertoire_upload(request):

    # create path
    path = get_path(request)
    if not os.path.exists(path):
        create_path(path)

    # upload files
    files = []
    for name, fieldStorage in request.POST.items():
        if not isinstance(fieldStorage, FieldStorage):
            continue

        filename = os.path.basename(fieldStorage.filename)
        file = get_path(request, filename)

        if os.path.isfile(file):
            info = get_info(request, file)
            info.update({'error': _(u'File already exists.')})
            files.append(info)
            continue

        # chunked file
        contentrange = ContentRange.parse(
            request.headers.get('Content-Range', None)
        )
        if contentrange:
            ok = save_chunk(
                descriptor=fieldStorage.file,
                file=file,
                contentrange=contentrange
            )
            if not ok:
                raise HTTPInternalServerError

        # whole file
        else:
            ok = save_file(
                descriptor=fieldStorage.file,
                file=file
            )
            if not ok:
                raise HTTPInternalServerError

        info = get_info(request, file)
        files.append(info)
    return {'files': files}


# --- service: list -----------------------------------------------------------

repertoire_list = Service(
    name=_prefix + 'list',
    path=_prefix + '/v1/list',
    description="lists repertoire files",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@repertoire_list.options()
def options_repertoire_list(request):
    return


@repertoire_list.get(
    validators=(authenticate))
def get_repertoire_list(request):
    files = []
    uploadpath = get_path(request)
    if not os.path.isdir(uploadpath):
        return {'files': []}
    for filename in os.listdir(uploadpath):
        if filename.endswith('.part'):
            continue
        file = get_path(request, filename)
        info = get_info(request, file)
        if info:
            files.append(info)
    return {'files': files}


# --- service: show -----------------------------------------------------------

repertoire_show = Service(
    name=_prefix + 'show',
    path=_prefix + '/v1/show/{filename}',
    description="shows uploaded repertoire files",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@repertoire_show.options()
def options_repertoire_show(request):
    return


@repertoire_show.get(
    validators=(authenticate))
def get_repertoire_show(request):
    filename = request.matchdict['filename']
    file = get_path(request, filename)
    return get_info(request, file)


# --- service: preview --------------------------------------------------------

repertoire_preview = Service(
    name=_prefix + 'preview',
    path=_prefix + '/v1/preview/{filename}',
    description="previewd the uploaded repertoire files",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@repertoire_preview.options()
def options_repertoire_preview(request):
    return


@repertoire_preview.get(
    validators=(authenticate))
def get_repertoire_preview(request):
    filename = request.matchdict['filename']
    file = get_path(request, filename)
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
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@repertoire_delete.options()
def options_repertoire_delete(request):
    return


@repertoire_delete.get(
    validators=(authenticate))
def get_repertoire_delete(request):
    filename = request.matchdict['filename']
    file = get_path(request, filename)
    ok = delete_file(file)
    if not ok:
        raise HTTPInternalServerError
    return
