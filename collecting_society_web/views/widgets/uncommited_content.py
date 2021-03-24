# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...models import Content

from ...services import _


class UncommitedContentWidget():

    def __init__(self, request, category='all'):
        self.party = request.party.id
        self.template = '../../templates/widgets/uncommited_content.pt'
        self.category = category

    def condition(self):
        return self.badge() > 0

    def icon(self):
        return "glyphicon glyphicon-send"

    def header(self):
        return _(u"Uncommitted Content")

    def description(self):
        return _(
            u"Number of artists, creations, and releases you didn't yet"
            u"release to be valid in the C3S database"
        )

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    # def output(self):
    #     uncomm = self.get_len(
    #         Content.search_uncommits(self.party, self.category))
    #     output = render(
    #         self.template,
    #         {'uncomm': uncomm}
    #     )
    #     return output

    def badge(self):
        return self.get_len(
            Content.search_uncommits(self.party, self.category))
