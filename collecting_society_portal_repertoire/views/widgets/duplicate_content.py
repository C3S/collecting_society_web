# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.view import (
    view_config,
    view_defaults
)
from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views import ViewBase

from collecting_society_portal.models import WebUser
from collecting_society_portal_creative.models import Content

@view_defaults(
    context='..resources.RepertoireResource',
    permission='read')
class DuplicateContentWidget(ViewBase):

    @view_config(
        name='')
    def root(self):
        return self.redirect(RepertoireResource, 'duplicate_content_count')

    def duplicate_content_count():
        web_user = WebUser.current_web_user(get_current_request)
        return Content.search_duplicates_by_user(web_user.id)
