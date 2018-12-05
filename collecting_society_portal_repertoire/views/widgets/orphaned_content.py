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

    def condition(self):
        return self.badge() > 0

    def icon(self):
        return "glyphicon glyphicon-leaf"

    def header(self):
        return _(u"Orphaned Files")

    def description(self):
        return _(u"This is the number of files you uploaded but didn't assign "
                 "to a creation yet. The easiest way to assign a file to a "
                 "creation is to go to the files list (by clicking on 'Files' "
                 "in the left-hand menu) and then click the 'Add Creation' "
                 "button of the respective list entry. Note that it can take "
                 "some time (under a minute to some hours -- depending on our "
                 "server load) to process uploaded files before files can be "
                 "added this way. Audio files will benefit from proper "
                 "metadata tags, for example, the title will be automatically "
                 "filled in the resp. field of the creation form.")

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

