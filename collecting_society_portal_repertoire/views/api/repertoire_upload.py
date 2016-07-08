# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import shutil
import logging
import magic
from cgi import FieldStorage

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


def get_cors_policy():
    return {
        'origins': os.environ['API_C3SUPLOAD_CORS_ORIGINS'].split(","),
        'credentials': True,
        'headers': [
            'Content-Type',
            'Content-Range',
            'Content-Disposition',
            'Content-Description'
        ]
    }


def authenticate(request):
    pass


def get_url(url, version, action, filename):
    if url.endswith('/'):
        url = url[:-1]
    return '/'.join([url, version, action, filename])


def get_path(request, filename=None):
    base = request.registry.settings['api.c3supload.filepath']
    webuser = '1'  # 2DO: return webuserid
    if filename:
        return os.path.join(base, webuser, filename)
    return os.path.join(base, webuser)


def get_info(request, resource):

    # POST
    if isinstance(resource, FieldStorage):
        filename = os.path.basename(resource.filename)
        filesize = os.fstat(resource.file.fileno()).st_size
        mimetype = mime.from_buffer(resource.file.read())

    # GET
    if isinstance(resource, str):
        if not os.path.isfile(resource):
            return False
        filename = os.path.basename(resource)
        filesize = os.path.getsize(resource)
        mimetype = mime.from_file(resource)

    preview_url = get_url(
        url=request.registry.settings['api.c3supload.url'],
        version=request.registry.settings['api.c3supload.version'],
        action='preview',
        filename=filename
    )
    delete_url = get_url(
        url=request.registry.settings['api.c3supload.url'],
        version=request.registry.settings['api.c3supload.version'],
        action='delete',
        filename=filename
    )
    return {
        'name': filename,
        'size': filesize,
        'type': mimetype,
        'previewUrl': preview_url,
        'deleteUrl': delete_url,
        'deleteType': 'DELETE'
    }


def create_path(path):
    try:
        os.makedirs(path)
    except IOError:
        pass
    return os.path.exists(path)


def save_file(descriptor, file):
    try:
        with open(file, 'w') as f:
            shutil.copyfileobj(descriptor, f)
    except IOError:
        pass
    return os.path.isfile(file)


def delete_file(file):
    try:
        os.remove(file)
    except IOError:
        pass
    return not os.path.isfile(file)


# --- service: upload ---------------------------------------------------------

upload = Service(
    name=_prefix + 'upload',
    path=_prefix + '/v1/upload',
    description="upload",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


class UploadSchema(MappingSchema):
    echo = SchemaNode(
        String(),
        location="body",
        type='str'
    )


@upload.options()
def options_upload(request):
    return


@upload.get()
def get_upload(request):
    files = []
    uploadpath = get_path(request)
    for filename in os.listdir(uploadpath):
        file = get_path(request, filename)
        info = get_info(request, file)
        if info:
            files.append(info)
    return {'files': files}


@upload.post()
def post_upload(request):
    files = []
    for name, fieldStorage in request.POST.items():
        if not isinstance(fieldStorage, FieldStorage):
            continue
        info = get_info(request, fieldStorage)
        file = get_path(request, info['name'])
        if os.path.isfile(file):
            info['error'] = _('File already exists.')
        else:
            path = get_path(request)
            if not os.path.exists(path):
                create_path(path)
            save_file(
                descriptor=fieldStorage.file,
                file=file
            )
        files.append(info)
    return {'files': files}


# --- service: delete ---------------------------------------------------------

delete = Service(
    name=_prefix + 'delete',
    path=_prefix + '/v1/delete/{filename}',
    description="delete",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@delete.delete()
def delete_delete(request):
    filename = request.matchdict['filename']
    file = get_path(request, filename)
    return delete_file(file)


# --- service: preview --------------------------------------------------------

preview = Service(
    name=_prefix + 'preview',
    path=_prefix + '/v1/preview/{filename}',
    description="preview",
    permission=NO_PERMISSION_REQUIRED,
    cors_policy=get_cors_policy()
)


@preview.get()
def get_preview(request):
    filename = request.matchdict['filename']
    file = get_path(request, filename)
    if not os.path.isfile(file):
        raise HTTPNotFound()
    return FileResponse(
        file,
        request=request,
        content_type=mime.from_file(file)
    )
