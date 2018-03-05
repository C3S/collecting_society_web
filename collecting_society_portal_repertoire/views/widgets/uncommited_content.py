# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _

from collecting_society_portal_repertoire.models import Content

class UncommitedContentWidget():

    def __init__(self, request):
        self.request = request
        self.template = '../../templates/widgets/uncommited_content.pt'

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        uncomm = self.get_len(Content.current_uncommits(self.request))
        output = render(
            self.template,
            { 'uncomm' : uncomm }
        )
        return output
