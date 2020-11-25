from __future__ import annotations

import re
from dataclasses import dataclass
from functools import wraps
from typing import Optional

from .manner import is_obstruent
from .place import is_coronal, is_dorsal
from .vowel import is_low

_natural_classes = dict()


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


def check_exclusivity(parent_name: str):
    """This generates a function that checks if `seg` belongs to exactly one of these natural classes."""
    nc = _natural_classes[parent_name]

    def wrapped(seg: Segment):
        belongs = dict()
        for name, func in nc.items():
            belongs[name] = func(seg)
        if sum(belongs.values()) != 1:
            raise ExclusivityFailure(f'Obstruent check results: {belongs}')

    return wrapped


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
    ATR: bool
    nasal: bool
    labial: bool
    coronal: bool
    dorsal: bool
    anterior: opt_bool
    distributed: opt_bool
    strident: opt_bool
    lateral: bool
    labialdental: bool
    voice: bool
    spread_glottis: bool
    constricted_glottis: bool
    implosive: bool

    def __post_init__(self):
        if not is_obstruent(self) and self.delayed_release is not None:
            raise SegmentInvalid(f'delayed_release only used for obstruents.')

        if not is_coronal(self) and any(f is not None for f in [self.anterior, self.distributed, self.strident]):
            raise SegmentInvalid(f'Coronal features only used for coronals.')

        if not is_dorsal(self) and any(f is not None for f in [self.high, self.low, self.back, self.front, self.tense]):
            raise SegmentInvalid(f'Dorsal features only used for dorsals.')

        try:
            if is_low(self) and self.tense is not None:
                raise SegmentInvalid(f'Low vowels should have 0 tense feature.')
        except ConditionNotMet:
            pass
