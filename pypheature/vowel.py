from .manner import is_vowel
from .segment import Segment, check_exclusivity, condition, natural_class
from .utils import compose

# -------------------------------------------------------------- #
#                            Backness                            #
# -------------------------------------------------------------- #

vowel_cond = condition(is_vowel)
backness_class = compose(natural_class('backness'),
                         vowel_cond)


@backness_class
def is_front(seg: Segment) -> bool:
    return seg.front and not seg.back


@backness_class
def is_central(seg: Segment) -> bool:
    return not seg.front and not seg.back


@backness_class
def is_back(seg: Segment) -> bool:
    return not seg.front and seg.back


check_backness_exclusivity = vowel_cond(check_exclusivity('backness'))


# -------------------------------------------------------------- #
#                      Height and tenseness                      #
# -------------------------------------------------------------- #

height_class = compose(natural_class('height'),
                       vowel_cond)


@height_class
def is_upper_high(seg: Segment) -> bool:
    return seg.high and not seg.low and seg.tense


@height_class
def is_lower_high(seg: Segment) -> bool:
    return seg.high and not seg.low and not seg.tense


@height_class
def is_upper_mid(seg: Segment) -> bool:
    return not seg.high and not seg.low and seg.tense


@height_class
def is_lower_mid(seg: Segment) -> bool:
    return not seg.high and not seg.low and not seg.tense


@height_class
def is_low(seg: Segment) -> bool:
    return not seg.high and seg.low


check_height_exclusivity = vowel_cond(check_exclusivity('height'))

# -------------------------------------------------------------- #
#                            Rounding                            #
# -------------------------------------------------------------- #


@vowel_cond
def is_round(seg: Segment) -> bool:
    return seg.round

# -------------------------------------------------------------- #
#                         Other features                         #
# -------------------------------------------------------------- #


@vowel_cond
def is_ATR(seg: Segment) -> bool:
    return seg.ATR


@vowel_cond
def is_long(seg: Segment) -> bool:
    return seg.long


@vowel_cond
def is_nasalized(seg: Segment) -> bool:
    """Whether this vowel is nasalized. This is different from `is_nasal` in the sonority section."""
    return seg.nasal
