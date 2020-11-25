"""No checks for the diacritics -- you might apply a syllabic diacritic to a vowel."""

from dataclasses import asdict
from typing import ClassVar, Dict, Optional

from .segment import Segment


class Diacritic:

    ipa: ClassVar[str]
    changes: Optional[ClassVar[Dict[str, bool]]] = None

    def apply_to(self, seg: Segment) -> Segment:
        kwargs = asdict(seg)
        kwargs['ipa'] += self.ipa
        for k, v in self.changes.items():
            kwargs[k] = v
        return Segment(**kwargs)


class Syllabic(Diacritic):

    ipa = '̩'
    changes = {'syllabic': True}


class Creaky(Diacritic):
    ipa = '̰'
    changes = {'spread_glottis': False, 'constricted': True}


class Breathy(Diacritic):
    ipa = '̤'
    changes = {'spread_glottis': True, 'constricted': False}


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
    changes = {'spread_glottis': True, 'constricted': False}


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
