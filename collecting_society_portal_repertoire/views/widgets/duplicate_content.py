# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _

from collecting_society_portal_creative.models import Content

class DuplicateContentWidget():

    def __init__(self, request):
        self.request = request
        self.template = '../../templates/widgets/duplicate_content.pt'

    def generate_html(self):
        heading = _(u'Duplicates')
        body = render(
            self.template,
            {'duplicate_content': self.duplicate_content_count()},
            request=self.request
        )
        return {'heading': heading, 'body': body}

    def get_duplicate_content(self):
        return Content.search_duplicates_by_user(self.request)

    def duplicate_content_count(self):
        list_duplicates = self.get_duplicate_content()
        if list_duplicates:
            return len(list_duplicates)
