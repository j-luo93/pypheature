from .segment import Segment, check_exclusivity, condition, natural_class
from .utils import compose

# -------------------------------------------------------------- #
#                       Sonority hierarchy                       #
# -------------------------------------------------------------- #


sonority_class = natural_class('sonority')


@sonority_class
def is_vowel(seg: Segment) -> bool:
    return seg.syllabic and not (is_glide(seg) or is_liquid(seg) or is_nasal(seg) or is_obstruent(seg))


@sonority_class
def is_glide(seg: Segment) -> bool:
    return not seg.syllabic and not seg.consonantal


@sonority_class
def is_liquid(seg: Segment) -> bool:
    return seg.consonantal and seg.approximant


@sonority_class
def is_nasal(seg: Segment) -> bool:
    return not seg.approximant and seg.sonorant


@sonority_class
def is_obstruent(seg: Segment) -> bool:
    return not seg.sonorant


class SonorityInvalid(Exception):
    """Invalid sonority constraint."""


check_sonority_exclusivity = check_exclusivity('sonority')

# -------------------------------------------------------------- #
#                           Obstruents                           #
# -------------------------------------------------------------- #


obstruent_cond = condition(is_obstruent)
obstruent_class = compose(natural_class('obstruent'),
                          obstruent_cond)


@obstruent_class
def is_stop(seg: Segment) -> bool:
    return not seg.continuant and not seg.delayed_release


@obstruent_class
def is_affricate(seg: Segment) -> bool:
    return not seg.continuant and seg.delayed_release


@obstruent_class
def is_fricative(seg: Segment) -> bool:
    return seg.consonantal and seg.delayed_release


class ObstruentInvalid(Exception):
    """Invalid obstruent constraint."""


check_obstruent_exclusivity = obstruent_cond(check_exclusivity('sonority'))

# -------------------------------------------------------------- #
#             Trills and taps. No exclusivity check.             #
# -------------------------------------------------------------- #

liquid_cond = condition(is_liquid)


@liquid_cond
def is_trill(seg: Segment) -> bool:
    return seg.trill


@liquid_cond
def is_tap(seg: Segment) -> bool:
    return seg.tap
