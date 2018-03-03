# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _

from collecting_society_portal_creative.models import Content

class RejectedContentWidget():

    def __init__(self, request):
        self.user_id = request.user.id
        self.template = '../../templates/widgets/rejected_content.pt'

    def generate_html(self):
        heading = _(u'Duplicates')
        body = render(
            self.template,
            {'rejected_content': self.rejected_content_count()}
        )
        return {'heading': heading, 'body': body}

    def get_rejected_content(self):
        return Content.search_duplicates_by_user(self.user_id)

    def rejected_content_count(self):
        list_rejected = self.get_rejected_content()
        if list_rejected:
            return len(list_rejected)
