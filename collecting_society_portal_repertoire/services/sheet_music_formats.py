# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire


_sheet_music_formats = {
    'Portable Document Format': {
        'ext': ['pdf'],
        'mime': [
            'application/pdf'
        ]
    }
}


def sheet_music_formats():
    return _sheet_music_formats


def sheet_music_extensions():
    return [
        extension
        for sheet_music_format in _sheet_music_formats
        for extension in _sheet_music_formats[sheet_music_format]['ext']
    ]


def sheet_music_mimetypes():
    return [
        mimetype
        for sheet_music_format in _sheet_music_formats
        for mimetype in _sheet_music_formats[sheet_music_format]['mime']
    ]
