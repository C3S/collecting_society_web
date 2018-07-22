# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...models import Content

from ...services import _


class OrphanedContentWidget():

    def __init__(self, request, category='all'):
        self.party = request.party.id
        self.template = '../../templates/widgets/orphaned_content.pt'
        self.category = category

    def icon(self):
        return "glyphicon glyphicon-leaf"

    def header(self):
        return _(u"Orphaned Content")

    def description(self):
        return _(u"Number of files you uploaded but didn't assign to a creation yet")

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        orph = self.get_len(Content.search_orphans(self.party, self.category))
        output = render(
            self.template,
            {'orph': orph}
        )
        return output

    def badge(self):
        return self.get_len(Content.search_orphans(self.party, self.category))

