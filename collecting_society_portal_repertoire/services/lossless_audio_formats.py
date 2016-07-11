# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire


_lossless_audio_formats = {
    'Waveform Audio File Format': {
        'ext': ['wav', 'wave'],
        'mime': [
            'audio/wav', 'audio/x-wav',
            'audio/wave', 'audio/x-pn-wav'
        ]
    },
    'Au': {
        'ext': ['au', 'snd'],
        'mime': [
            'audio/basic', 'audio/x-basic',
            'audio/au', 'audio/x-au', 'audio/x-pn-au'
        ]
    },
    'Free Lossless Audio Codec': {
        'ext': ['flac'],
        'mime': [
            'audio/flac', 'audio/x-flac'
        ]
    },
    'Monkeys Audio': {
        'ext': ['ape'],
        'mime': [
            'audio/x-monkeys-audio', 'audio/x-ape'
        ]
    },
    # 'WavPack': {
    #     'ext': ['wv'],
    #     'mime': [
    #         'audio/x-wavpack'
    #     ]
    # },
    # 'True Audio': {
    #     'ext': ['tta'],
    #     'mime': [
    #         'audio/tta',
    #         'audio/x-tta'
    #     ]
    # },
    # 'Shorten': {
    #     'ext': ['shn'],
    #     'mime': ['application/x-shorten']
    # }
}


def lossless_audio_formats():
    return _lossless_audio_formats


def lossless_audio_extensions():
    return [
        extension
        for lossless_format in _lossless_audio_formats
        for extension in _lossless_audio_formats[lossless_format]['ext']
    ]


def lossless_audio_mimetypes():
    return [
        mimetype
        for lossless_format in _lossless_audio_formats
        for mimetype in _lossless_audio_formats[lossless_format]['mime']
    ]
