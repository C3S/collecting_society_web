# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _

from collecting_society_portal_repertoire.models import Content

class RejectedContentWidget():

    def __init__(self, request):
        self.request = request
        self.template = '../../templates/widgets/rejected_content.pt'

    def dupl(self):
        return Content.current_rejects(self.request, 'dupl')

    def ferrors(self):
        return Content.current_rejects(self.request, 'ferrors')

    def lossyc(self):
        return Content.current_rejects(self.request, 'lossyc')

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
                'dupl' : dupl,
                'ferrors' : ferrors,
                'lossyc' : lossyc,
                'rejects' : rejects
            }
        )
        return output
