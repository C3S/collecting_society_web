# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import json
import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from colander import (
    MappingSchema,
    SchemaNode,
    String,
    DateTime
)

log = logging.getLogger(__name__)

__prefix__ = 'c3smembership'

echo = Service(
    name=__prefix__ + 'echo',
    path=__prefix__ + '/v1/echo',
    description="echo",
    permission=NO_PERMISSION_REQUIRED,
    environment='development'
)


@echo.post()
def post_echo(request):
    content = json.loads(request.body)
    return {
        'status': 200,
        'data': {
            'echo': content['echo']
        }
    }
