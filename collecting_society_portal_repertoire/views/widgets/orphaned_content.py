# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _

from collecting_society_portal_repertoire.models import Content

class OrphanedContentWidget():

    def __init__(self, request):
        self.request = request
        self.template = '../../templates/widgets/orphaned_content.pt'

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        orph = self.get_len(Content.current_orphans(self.request))
        output = render(
            self.template,
            { 'orph' : orph }
        )
        return output
