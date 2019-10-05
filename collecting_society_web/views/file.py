# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import os
import logging

from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.models import Tdb
from portal_web.views import ViewBase

from ..services import _
from ..models import Content
from ..services.lossless_audio_formats import lossless_audio_extensions
from ..services.sheet_music_formats import sheet_music_extensions

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.FilesResource')
class FilesViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/file/list.pt',
        permission='list_content')
    def list(self):
        settings = self.request.registry.settings
        return {
            'url': ''.join([
                settings['api.c3supload.url'], '/',
                settings['api.c3supload.version']
            ])
        }

    @view_config(
        name='upload',
        renderer='../templates/file/upload.pt',
        permission='add_content')
    def upload(self):
        settings = self.request.registry.settings
        return {
            'extensions': (lossless_audio_extensions() +
                           sheet_music_extensions()),
            'url': ''.join([
                settings['api.c3supload.url'], '/',
                settings['api.c3supload.version']
            ])
        }


@view_defaults(
    context='..resources.FileResource')
class FileViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/file/show.pt',
        permission='view_content')
    def show(self):
        return {}

    @view_config(
        name='preview',
        permission='view_content')
    def preview(self):
        file = self.context.file
        preview_path = file.preview_path
        if not preview_path or not os.path.isfile(preview_path):
            raise HTTPNotFound()
        return FileResponse(
            preview_path,
            request=self.request,
            content_type=str(file.mime_type)
        )

    @view_config(
        name='delete',
        decorator=Tdb.transaction(readonly=False),
        permission='delete_content')
    def delete(self):
        name = self.context.file.name
        Content.delete([self.context.file])
        log.info("content delete successful for %s: %s (%s)" % (
            self.request.web_user, name, self.context.code
        ))
        self.request.session.flash(
            _(u"Content deleted: ") + name + ' (' + self.context.code + ')',
            _(u"Content deleted: ${cona} (${coco})",
              mapping={'cona': name, 'coco': self.context.code}),
            'main-alert-success'
        )
        return self.redirect('..')
