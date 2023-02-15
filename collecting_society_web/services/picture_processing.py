# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from PIL import Image
import io
from . import _
import logging

log = logging.getLogger(__name__)


def picture_processing(fp):
    """
    normalizes an image and creates a thumbnail

    Args:
      fp (C filepointer): input file, the image is stored in

    Returns quadrupel:
      string: error message, if a problem occured, otherwise success
      byte buffer: picture data
      byte buffer: thumbnail data
      string: mimetype of the picture data
    """

    try:
        fp.flush()  # last bytes would be truncated without this
        image = Image.open(fp.name)
        thumb = image.copy()
        thumb.thumbnail((84, 84), Image.ANTIALIAS)
        image.thumbnail((509, 509), Image.ANTIALIAS)
        with io.BytesIO() as picture_thumbnail_data:
            thumb.save(picture_thumbnail_data, "JPEG")
            picture_thumbnail_data.seek(0)
            thumbnail = picture_thumbnail_data.read()
        with io.BytesIO() as picture_data:
            image.save(picture_data, "JPEG")
            picture_data.seek(0)
            if not picture_data:
                return _('Unable to process picture')
            picture = picture_data.read()
            mimetype = 'image/jpeg'  # = mimetype
    except IOError as e:
        return _('Error while processing picture data: "${e}"',
                 mapping={'e': e}), None, None, None
    return None, picture, thumbnail, mimetype
