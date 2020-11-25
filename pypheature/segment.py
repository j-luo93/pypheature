from __future__ import annotations

import re
from dataclasses import dataclass
from functools import wraps
from typing import Optional

from .utils import compose

_natural_classes = dict()
_exclusivity_checks = dict()


def natural_class(parent_name: str):
    """A decorator for one natural class (e.g., stops). `parent_name` is used to indicate what is the parent class (stops are obstruents) or what is the dividing principle (obstruents and nasals are distinguished by sonority)."""
    if parent_name not in _natural_classes:
        _natural_classes[parent_name] = dict()
    nc = _natural_classes[parent_name]

    def wrap(func):
        """Register sonority class testing function."""

        name = re.match(r'^is_(\w+)$', func.__name__).group(1)
        nc[name] = func

        @wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

    return wrap


class ExclusivityFailure(Exception):
    """Raise this if exclusivity check failed."""


def add_exclusivity_check(parent_name: str):
    """This generates a function that checks if `seg` belongs to exactly one of these natural classes."""

    def wrapped(*args, **kwargs):
        nc = _natural_classes[parent_name]
        belongs = dict()
        for name, func in nc.items():
            belongs[name] = func(*args, **kwargs)
        if sum(belongs.values()) != 1:
            raise ExclusivityFailure(f'Obstruent check results: {belongs}')

    _exclusivity_checks[parent_name] = wrapped


add_exclusivity_check('sonority')
add_exclusivity_check('obstruent')
add_exclusivity_check('backness')
add_exclusivity_check('height')
add_exclusivity_check('coronal')


class ConditionNotMet(Exception):
    """Raise this when condition function does not return True."""


def condition(cond_func, *, _reverse: bool = False):

    def wrap(func):

        @wraps(func)
        def wrapped(*args, **kwargs):
            cond = cond_func(*args, **kwargs)
            if (_reverse and cond) or (not _reverse and not cond):
                raise ConditionNotMet(f'Condition function "{cond_func.__name__}" returns False.')
            return func(*args, **kwargs)

        return wrapped

    return wrap


reverse_condition = lambda func: condition(func, _reverse=True)


class SegmentInvalid(Exception):
    """Raise this if segment features are invalid."""


opt_bool = Optional[bool]


@dataclass
class Segment:
    ipa: str
    syllabic: bool
    consonantal: bool
    approximant: bool
    sonorant: bool
    continuant: bool
    delayed_release: opt_bool
    trill: bool
    tap: bool
    front: opt_bool
    back: opt_bool
    high: opt_bool
    low: opt_bool
    tense: opt_bool
    round: bool
    long: bool
    nasal: bool
    labial: bool
    coronal: bool
    dorsal: bool
    anterior: opt_bool
    distributed: opt_bool
    strident: opt_bool
    lateral: bool
    labiodental: bool
    voice: bool
    spread_glottis: bool
    constricted_glottis: bool

    # -------------------------------------------------------------- #
    #                             Manner                             #
    # -------------------------------------------------------------- #

    # --------------------- Sonority hierarchy --------------------- #

    sonority_class = natural_class('sonority')

    @sonority_class
    def is_vowel(self) -> bool:
        return self.syllabic and not (self.is_glide() or self.is_liquid() or self.is_nasal() or self.is_obstruent())

    @sonority_class
    def is_glide(self) -> bool:
        return not self.syllabic and not self.consonantal

    @sonority_class
    def is_liquid(self) -> bool:
        return self.consonantal and self.approximant

    @sonority_class
    def is_nasal(self) -> bool:
        return not self.approximant and self.sonorant

    @sonority_class
    def is_obstruent(self) -> bool:
        return not self.sonorant

    # ------------------------- Obstruents ------------------------- #

    obstruent_cond = condition(is_obstruent)
    obstruent_class = compose(natural_class('obstruent'),
                              obstruent_cond)

    @obstruent_class
    def is_stop(self) -> bool:
        return not self.continuant and not self.delayed_release

    @obstruent_class
    def is_affricate(self) -> bool:
        return not self.continuant and self.delayed_release

    @obstruent_class
    def is_fricative(self) -> bool:
        return self.continuant and self.delayed_release

    # ----------------------- Trills and taps ---------------------- #

    liquid_cond = condition(is_liquid)

    @liquid_cond
    def is_trill(self) -> bool:
        return self.trill

    @liquid_cond
    def is_tap(self) -> bool:
        return self.tap

    # -------------------------------------------------------------- #
    #                              Vowel                             #
    # -------------------------------------------------------------- #

    # -------------------------- Backness -------------------------- #

    vowel_cond = condition(is_vowel)
    backness_class = compose(natural_class('backness'),
                             vowel_cond)

    @backness_class
    def is_front(self) -> bool:
        return self.front and not self.back

    @backness_class
    def is_central(self) -> bool:
        return not self.front and not self.back

    @backness_class
    def is_back(self) -> bool:
        return not self.front and self.back

    # -------------------- Height and tenseness -------------------- #

    height_class = compose(natural_class('height'),
                           vowel_cond)

    @height_class
    def is_upper_high(self) -> bool:
        return self.high and not self.low and self.tense

    @height_class
    def is_lower_high(self) -> bool:
        return self.high and not self.low and not self.tense

    @height_class
    def is_upper_mid(self) -> bool:
        return not self.high and not self.low and self.tense

    @height_class
    def is_lower_mid(self) -> bool:
        return not self.high and not self.low and not self.tense

    @height_class
    def is_low(self) -> bool:
        return not self.high and self.low

    # -------------------------- Rounding -------------------------- #

    @vowel_cond
    def is_round(self) -> bool:
        return self.round

    # ----------------------- Other features ----------------------- #

    @vowel_cond
    def is_long(self) -> bool:
        return self.long

    @vowel_cond
    def is_nasalized(self) -> bool:
        """Whether this vowel is nasalized. This is different from `is_nasal` in the sonority section."""
        return self.nasal

    # -------------------------------------------------------------- #
    #                              Place                             #
    # -------------------------------------------------------------- #

    # -------------------------- Coronals -------------------------- #

    def is_coronal(self) -> bool:
        return self.coronal

    coronal_cond = condition(is_coronal)
    coronal_class = compose(natural_class('coronal'),
                            coronal_cond)

    @coronal_class
    def is_lamino_dental(self) -> bool:
        return self.anterior and self.distributed

    @coronal_class
    def is_apico_alveolar(self) -> bool:
        return self.anterior and not self.distributed

    @coronal_class
    def is_palato_alveolar(self) -> bool:
        return not self.anterior and self.distributed

    @coronal_class
    def is_retroflex(self) -> bool:
        return not self.anterior and not self.distributed

    # --------------------------- Dorsals -------------------------- #

    def is_dorsal(self) -> bool:
        return self.dorsal

    vowel_condition_r = reverse_condition(is_vowel)
    dorsal_condition = condition(is_dorsal)

    dorsal_consonant = compose(vowel_condition_r, dorsal_condition)

    @dorsal_consonant
    def is_fronted_velar(self) -> bool:
        return self.high and not self.low and self.front and not self.back

    @dorsal_consonant
    def is_central_velar(self) -> bool:
        return self.high and not self.low and not self.front and not self.back

    @dorsal_consonant
    def is_back_velar(self) -> bool:
        return self.high and not self.low and not self.front and self.back

    @dorsal_consonant
    def is_uvular(self) -> bool:
        return not self.high and not self.low and not self.front and self.back

    @dorsal_consonant
    def is_pharyngeal(self) -> bool:
        return not self.high and self.low and not self.front and self.back

    def __post_init__(self):

        # ------------------ some feature-level checks ----------------- #

        if not self.is_obstruent() and self.delayed_release is not None:
            raise SegmentInvalid(f'delayed_release only used for obstruents.')

        if not self.is_coronal() and any(f is not None for f in [self.anterior, self.distributed, self.strident]):
            raise SegmentInvalid(f'Coronal features only used for coronals.')

        if not self.is_dorsal() and any(f is not None for f in [self.high, self.low, self.back, self.front, self.tense]):
            raise SegmentInvalid(f'Dorsal features only used for dorsals.')

        try:
            if self.is_low() and self.tense is not None:
                raise SegmentInvalid(f'Low vowels should have 0 tense feature.')
        except ConditionNotMet:
            pass

        # -------------- natural class exclusivity checks -------------- #

        for name, func in _exclusivity_checks.items():
            try:
                func(self)
            except ConditionNotMet:
                pass
            except ExclusivityFailure as e:
                # Make exceptions for 'ʍ', 'ɦ', 'h'.
                if name == 'sonority' and self.ipa in ['ʍ', 'ɦ', 'h']:
                    continue
                raise e
