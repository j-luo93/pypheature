"""No checks for the diacritics -- you might apply a syllabic diacritic to a vowel."""
from __future__ import annotations

from dataclasses import asdict
from typing import ClassVar, Dict, Optional

from .segment import Segment


class DiacriticInvalid(Exception):
    """Raise this if this diacritic is not recognized."""


class DiacriticMetaclass(type):

    __registry = dict()

    def __init__(cls, *args, **kwargs):
        name = cls.__name__
        if name != 'Diacritic' and name not in DiacriticMetaclass.__registry:
            DiacriticMetaclass.__registry[cls.ipa] = cls
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_diacritic(raw: str):
        if raw not in DiacriticMetaclass.__registry:
            raise DiacriticInvalid(f'Unrecognized diacritic "{raw}".')

        return DiacriticMetaclass.__registry[raw]()


def get_diacritic(raw: str) -> Diacritic:
    return DiacriticMetaclass.get_diacritic(raw)


class Diacritic(metaclass=DiacriticMetaclass):

    ipa: ClassVar[str]
    changes: ClassVar[Optional[Dict[str, bool]]] = None

    def apply_to(self, seg: Segment) -> Segment:
        kwargs = asdict(seg)
        kwargs['ipa'] += self.ipa
        for k, v in self.changes.items():
            kwargs[k] = v
        return Segment(**kwargs)

    def __repr__(self):
        return f'Diacritic("{self.ipa}")'


class Syllabic(Diacritic):

    ipa = '̩'
    changes = {'syllabic': True}


class Creaky(Diacritic):
    ipa = '̰'
    changes = {'spread_glottis': False, 'constricted_glottis': True}


class Breathy(Diacritic):
    ipa = '̤'
    changes = {'spread_glottis': True, 'constricted_glottis': False}


class Voiceless(Diacritic):
    ipa = '̥'
    changes = {'voice': False}


class Retracted(Diacritic):
    ipa = '̠'

    def apply_to(self, seg: Segment) -> Segment:
        kwargs = asdict(seg)
        kwargs['ipa'] += self.ipa  # pylint: disable=no-member
        if seg.is_dorsal:
            kwargs['front'] = False
            kwargs['back'] = True
        else:
            kwargs['anterior'] = False
            kwargs['distributed'] = True
        return Segment(**kwargs)


class Dental(Diacritic):
    ipa = '̪'
    changes = {'anterior': True, 'distributed': True}


class Advanced(Diacritic):
    ipa = '̟'
    changes = {'front': True, 'back': False}


class Long(Diacritic):
    ipa = 'ː'
    changes = {'long': True}


class Aspirated(Diacritic):
    ipa = 'ʰ'
    changes = {'spread_glottis': True, 'constricted_glottis': False}


class Palatalized(Diacritic):
    ipa = 'ʲ'
    changes = {'dorsal': True, 'high': True, 'low': False, 'front': True, 'back': False}


class Labialized(Diacritic):
    ipa = 'ʷ'
    change = {'labial': True, 'round': True}


class Velarized(Diacritic):
    ipa = 'ˠ'
    changes = {'dorsal': True, 'high': True, 'low': False, 'front': False, 'back': True}


class Pharyngealized(Diacritic):
    ipa = 'ˤ'
    changes = {'dorsal': True, 'high': False, 'low': True, 'front': False, 'back': True}


class Nasalized(Diacritic):
    ipa = '̃'
    changes = {'nasal': True}


class Rhoticity(Diacritic):
    ipa = 'ʽ'
    changes = {'coronal': True, 'anterior': True, 'distributed': True, 'strident': False}


class Ejective(Diacritic):
    ipa = 'ʼ'
    changes = {'spread_glottis': False, 'constricted_glottis': True}
