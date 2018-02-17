# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...services import _


class DuplicateContentWidget():

    def __init__(self):
        #return self.duplicate_content_count(request.user)
        heading = _(u'Duplicates')
        body = render(
            '../../templates/widgets/duplicate_content.pt',
            {'duplicate_content': request.context.registry['content']['duplicate_content']},
            request=request
        )
        return {'heading': heading, 'body': body}

    def duplicate_content_count(user):
        return Content.search_duplicates_by_user(user.id)
