# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import os
import logging

# configure logging
if os.environ.get('ENVIRONMENT') == 'development':
    from pprint import pformat

    def pformat_filter(record):
        if record.levelname == 'DEBUG':
            if not isinstance(record.msg, str):
                record.msg = pformat(record.msg)
        return True
    logger = logging.getLogger(__name__)
    logger.handlers[0].addFilter(pformat_filter)
