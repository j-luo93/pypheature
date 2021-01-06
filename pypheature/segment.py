"""This file contains the class for representing a segment, and many methods supporting `is_*` operations, such as `is_vowel` and `is_stop`.

One issue with using the option feature values (0tense, in addition to +tense and -tense) is that it might lead to undefined behavior.
For instance, `is_tense` might be defined as `self.tense` and `is_lax` `not self.tense`. Both `is_*` operations expect bool return values,
but they are not mutually exclusive, when the feature is 0tense, you should expect to both methods to return False. However, since `not None`
is taken to be `True`, `is_lax` would return the incorrect `True`.

One might attempt to define a special value for those optional features -- let's call it `Undefined`, and any logic operation involving
`Undefined` and other normal bool values would lead to `Undefined` results too. This is still problematic because `is_*` operations
expect bool returns -- `is_lax` should still return `False` when you have 0tense. Moreover, the lazy evaluation for conditional expressions
might lead to unexpected behavior when values that are `Undefined` get evaluated in one setting but not in another one.

Therefore, I opt to explicitly check the value by using equality check, e.g., `tense == "+"`, instead of assuming "+" means `True`. Calling
`__bool__` on these values implicitly is illegal.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from functools import wraps
from typing import ClassVar, List, Optional, Union

from .utils import RemoveableMethod, compose, temp

_natural_classes = dict()
_exclusivity_checks = dict()


class ExclusivityFailure(Exception):
    """Raise this if exclusivity check failed."""


class ConditionNotMet(Exception):
    """Raise this when condition function does not return True."""


def gen_condition(cond_func, *, _reverse: bool = False):

    def wrap(func):

        @wraps(func)
        def wrapped(*args, **kwargs):
            cond = cond_func(*args, **kwargs)
            if (_reverse and cond) or (not _reverse and not cond):
                raise ConditionNotMet(f'Condition function "{cond_func.__name__}" returns False.')
            return func(*args, **kwargs)

        return wrapped

    return wrap


reverse_condition = lambda func: gen_condition(func, _reverse=True)


def natural_class(parent_name: str, *, condition=None):
    """A decorator for one natural class (e.g., stops). `parent_name` is used to indicate
    what is the parent class (stops are obstruents) or what is the dividing principle (obstruents and nasals are distinguished by sonority).
    In addition, this add an exclusivity check for this natural class.

    `condition` is used in two different ways. For exclusivity checks, `condition` is called before any check, and if it failed, no check
    should be performed. For the decorated `is_*` operation, if `condition` is not met, it would return False.
    """
    if parent_name not in _natural_classes:
        _natural_classes[parent_name] = dict()
    nc = _natural_classes[parent_name]

    def wrap(func):
        """Register natural class testing function."""

        name = re.match(r'^is_(\w+)$', func.__name__).group(1)
        nc[name] = func

        @wraps(func)
        def wrapped(*args, **kwargs):
            if condition is not None and not condition(*args, **kwargs):
                return False
            return func(*args, **kwargs)

        def check_exclusivity(*args, **kwargs):
            belongs = dict()
            # If `condition` not met, then we don't need to check exclusivity.
            if condition is not None and not condition(*args, **kwargs):
                return

            for name, func in nc.items():
                belongs[name] = func(*args, **kwargs)
            if sum(belongs.values()) != 1:
                raise ExclusivityFailure(f'Exclusivity check for {parent_name} results: {belongs}')

        _exclusivity_checks[parent_name] = check_exclusivity

        return wrapped

    # Generate a function that checks if the segment belongs to exactly one of these natural classes.
    return wrap


class InvalidSegment(Exception):
    """Raise this if segment features are invalid."""


class InvalidCoercion(Exception):
    """Raise this if you are turning an `OptionalBool` object into a `bool` value."""


class Feature:

    allowed_values: ClassVar[list] = [True, False, None]
    _value: Optional[bool]

    def __init__(self, value: Union[Optional[bool], Feature]):
        if isinstance(value, Feature):
            self._value = value.value
        else:
            assert value in self.allowed_values
            self._value = value

    def __repr__(self):
        return f'v({self._value})'

    def __bool__(self):
        raise InvalidCoercion(f'Cannot turn this into a boolean.')

    @property
    def value(self):
        return self._value

    def __eq__(self, other: Optional[bool]):
        if all(other is not value for value in self.allowed_values):
            raise TypeError(f'Cannot check equality with value {other}.')
        return self.value is other


class TernaryFeature(Feature):

    allowed_values: ClassVar[list] = [True, False, None]


class BinaryFeature(Feature):

    allowed_values: ClassVar[list] = [True, False]


@dataclass
class Segment(RemoveableMethod):
    base: str
    syllabic: BinaryFeature
    consonantal: BinaryFeature
    approximant: BinaryFeature
    sonorant: BinaryFeature
    continuant: BinaryFeature
    delayed_release: TernaryFeature
    trill: BinaryFeature
    tap: BinaryFeature
    dorsal: BinaryFeature
    front: TernaryFeature
    back: TernaryFeature
    high: TernaryFeature
    low: TernaryFeature
    tense: TernaryFeature
    round: BinaryFeature
    long: BinaryFeature
    overlong: BinaryFeature
    nasal: BinaryFeature
    coronal: BinaryFeature
    anterior: TernaryFeature
    distributed: TernaryFeature
    strident: TernaryFeature
    lateral: BinaryFeature
    labial: BinaryFeature
    labiodental: BinaryFeature
    voice: BinaryFeature
    spread_glottis: BinaryFeature
    constricted_glottis: BinaryFeature

    diacritics: List[str] = field(default_factory=list)

    def __str__(self):
        return self.base + ''.join(self.diacritics)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: Segment):
        if not isinstance(other, Segment):
            raise TypeError(f'Can only compare with segments.')
        return str(self) == str(other)

    def check_features(self, fv: List[str]):
        sign2value = {
            '+': True,
            '-': False,
            '0': None
        }
        for fstr in fv:
            sign = fstr[0]
            name = fstr[1:]
            feat = getattr(self, name)
            # This equality check includes both value check (whether the values are identical) and
            # allowed value check (whether the specified value is allowed).
            if feat != sign2value[sign]:
                return False
        return True

    # -------------------------------------------------------------- #
    #                             Manner                             #
    # -------------------------------------------------------------- #

    # --------------------- Sonority hierarchy --------------------- #

    sonority_class = temp(natural_class('sonority'))

    @sonority_class
    def is_vowel(self) -> bool:
        return self.check_features(['+syllabic']) and not (self.is_glide() or self.is_liquid() or self.is_nasal() or self.is_obstruent())

    @sonority_class
    def is_glide(self) -> bool:
        # Make exceptions for 'ʍ', 'ɦ', 'h'.
        if self.base in ['ʍ', 'ɦ', 'h']:
            return False
        return self.check_features(['-syllabic', '-consonantal'])

    @sonority_class
    def is_liquid(self) -> bool:
        return self.check_features(['+consonantal', '+approximant'])

    @sonority_class
    def is_nasal(self) -> bool:
        return self.check_features(['-approximant', '+sonorant'])

    @sonority_class
    def is_obstruent(self) -> bool:
        return self.check_features(['-sonorant'])

    # ------------------------- Obstruents ------------------------- #

    obstruent_class = temp(natural_class('obstruent', condition=is_obstruent))

    @obstruent_class
    def is_stop(self) -> bool:
        return self.check_features(['-continuant', '-delayed_release'])

    @obstruent_class
    def is_affricate(self) -> bool:
        return self.check_features(['-continuant', '+delayed_release'])

    @obstruent_class
    def is_fricative(self) -> bool:
        return self.check_features(['+continuant', '+delayed_release'])

    # ----------------------- Trills and taps ---------------------- #

    liquid_cond = temp(gen_condition(is_liquid))

    @liquid_cond
    def is_trill(self) -> bool:
        return self.check_features(['+trill'])

    @liquid_cond
    def is_tap(self) -> bool:
        return self.check_features(['+tap'])

    # -------------------------------------------------------------- #
    #                              Vowel                             #
    # -------------------------------------------------------------- #

    # -------------------------- Backness -------------------------- #

    backness_class = temp(natural_class('backness', condition=is_vowel))

    @backness_class
    def is_front(self) -> bool:
        return self.check_features(['+front', '-back'])

    @backness_class
    def is_central(self) -> bool:
        return self.check_features(['-front', '-back'])

    @backness_class
    def is_back(self) -> bool:
        return self.check_features(['-front', '+back'])

    # -------------------- Height and tenseness -------------------- #

    height_class = temp(natural_class('height', condition=is_vowel))

    @height_class
    def is_upper_high_vowel(self) -> bool:
        return self.check_features(['+high', '-low', '+tense'])

    @height_class
    def is_lower_high_vowel(self) -> bool:
        return self.check_features(['+high', '-low', '-tense'])

    @height_class
    def is_upper_mid_vowel(self) -> bool:
        return self.check_features(['-high', '-low', '+tense'])

    @height_class
    def is_lower_mid_vowel(self) -> bool:
        return self.check_features(['-high', '-low', '-tense'])

    @height_class
    def is_low_vowel(self) -> bool:
        return self.check_features(['-high', '+low'])

    # -------------------------- Rounding -------------------------- #

    vowel_cond = temp(gen_condition(is_vowel))

    @vowel_cond
    def is_round(self) -> bool:
        return self.check_features(['+round'])

    # ----------------------- Other features ----------------------- #

    # Duration checks apply to both consonants and vowels.

    duration_class = temp(natural_class('duration'))

    @duration_class
    def is_short(self) -> bool:
        return self.check_features(['-long'])

    @duration_class
    def is_long(self) -> bool:
        return self.check_features(['+long', '-overlong'])

    @duration_class
    def is_overlong(self) -> bool:
        return self.check_features(['+overlong'])

    @vowel_cond
    def is_nasalized(self) -> bool:
        """Whether this vowel is nasalized. This is different from `is_nasal` in the sonority section."""
        return self.check_features(['+nasal'])

    # -------------------------------------------------------------- #
    #                              Place                             #
    # -------------------------------------------------------------- #

    # -------------------------- Coronals -------------------------- #

    def is_coronal(self) -> bool:
        return self.check_features(['+coronal'])

    coronal_class = temp(natural_class('coronal', condition=is_coronal))

    @coronal_class
    def is_lamino_dental(self) -> bool:
        return self.check_features(['+anterior', '+distributed'])

    @coronal_class
    def is_apico_alveolar(self) -> bool:
        return self.check_features(['+anterior', '-distributed'])

    @coronal_class
    def is_palato_alveolar(self) -> bool:
        return self.check_features(['-anterior', '+distributed'])

    @coronal_class
    def is_retroflex(self) -> bool:
        return self.check_features(['-anterior', '-distributed'])

    # --------------------------- Dorsals -------------------------- #

    def is_dorsal(self) -> bool:
        return self.check_features(['+dorsal'])

    dorsal_consonant = temp(compose(reverse_condition(is_vowel),
                                    gen_condition(is_dorsal)))

    @dorsal_consonant
    def is_fronted_velar(self) -> bool:
        return self.check_features(['+high', '-low', '+front', '-back'])

    @dorsal_consonant
    def is_central_velar(self) -> bool:
        return self.check_features(['+high', '-low', '-front', '-back'])

    @dorsal_consonant
    def is_back_velar(self) -> bool:
        return self.check_features(['+high', '-low', '-front', '+back'])

    @dorsal_consonant
    def is_uvular(self) -> bool:
        return self.check_features(['-high', '-low', '-front', '+back'])

    @dorsal_consonant
    def is_pharyngeal(self) -> bool:
        return self.check_features(['-high', '+low', '-front', '+back'])

    # --------------------- Laryngeal features --------------------- #

    glottal_width_class = temp(natural_class('glottal_width'))

    @glottal_width_class
    def is_spread_glottis(self) -> bool:
        return self.check_features(['+spread_glottis', '-constricted_glottis'])

    @glottal_width_class
    def is_constricted_glottis(self) -> bool:
        return self.check_features(['-spread_glottis', '+constricted_glottis'])

    @glottal_width_class
    def is_normal_glottis(self) -> bool:
        return self.check_features(['-spread_glottis', '-constricted_glottis'])

    def __post_init__(self):
        # Property convert every feature value.
        for field in fields(self):
            ftype = field.type
            fname = field.name
            raw_value = getattr(self, fname)
            if ftype in ['BinaryFeature', BinaryFeature]:
                setattr(self, fname, BinaryFeature(raw_value))
            elif ftype in ['TernaryFeature', TernaryFeature]:
                setattr(self, fname, TernaryFeature(raw_value))

        # ------------------ some feature-level checks ----------------- #
        # pylint: disable=singleton-comparison
        if not self.is_obstruent() and self.delayed_release != None:
            raise InvalidSegment(f'delayed_release only used for obstruents.')

        if not self.is_coronal() and any(f != None for f in [self.anterior, self.distributed, self.strident]):
            raise InvalidSegment(f'Coronal features only used for coronals.')

        if not self.is_dorsal() and any(f != None for f in [self.high, self.low, self.back, self.front, self.tense]):
            raise InvalidSegment(f'Dorsal features only used for dorsals.')

        # Some diacritics might violate this constraint (esp for pharyngealized vowels like "iˤ").
        if self.is_low_vowel() and self.tense != None and not self.diacritics:
            raise InvalidSegment(f'Low vowels should have 0 tense feature.')

        # 'ʍ' is a bit weird -- we define it as an obstruent, but it is +tense.
        if self.tense != None and not (self.is_glide() or self.is_vowel() or self.base == 'ʍ'):
            raise InvalidSegment(f'Only glides or vowels can have non-zero tense value.')

        # pylint: enable=singleton-comparison

        # -------------- natural class exclusivity checks -------------- #

        for name, func in _exclusivity_checks.items():
            try:
                func(self)
            except ConditionNotMet:
                pass
