# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.views import ViewBase
from collecting_society_portal.models import Tdb

from ..services.lossless_audio_formats import lossless_audio_extensions
from ..services.sheet_music_formats import sheet_music_extensions

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.FilesResource')
class FilesViews(ViewBase):

    @view_config(
        name='',
        permission='authenticated')
    def root(self):
        return self.redirect('upload')

    @view_config(
        name='upload',
        renderer='../templates/file/upload.pt',
        permission='upload_files')
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
