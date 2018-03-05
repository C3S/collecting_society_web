# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...models import Content


class RejectedContentWidget():

    def __init__(self, request, category='all'):
        self.party = request.party.id
        self.template = '../../templates/widgets/rejected_content.pt'
        self.category = category

    def dupl(self):
        return Content.search_rejects(self.party, 'dupl', self.category)

    def ferrors(self):
        return Content.search_rejects(self.party, 'ferrors', self.category)

    def lossyc(self):
        return Content.search_rejects(self.party, 'lossyc', self.category)

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        dupl = self.get_len(self.dupl())
        ferrors = self.get_len(self.ferrors())
        lossyc = self.get_len(self.lossyc())
        rejects = dupl + ferrors + lossyc
        output = render(
            self.template,
            {
                'dupl': dupl,
                'ferrors': ferrors,
                'lossyc': lossyc,
                'rejects': rejects
            }
        )
        return output
