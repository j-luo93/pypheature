from .manner import is_vowel
from .segment import (Segment, check_exclusivity, condition, natural_class,
                      reverse_condition)
from .utils import compose

# -------------------------------------------------------------- #
#                            Coronals                            #
# -------------------------------------------------------------- #


def is_coronal(seg: Segment) -> bool:
    return seg.coronal


coronal_cond = condition(is_coronal)
coronal_class = compose(natural_class('coronal'),
                        coronal_cond)


@coronal_class
def is_lamino_dental(seg: Segment) -> bool:
    return seg.anterior and seg.distributed


@coronal_class
def is_apico_alveolar(seg: Segment) -> bool:
    return seg.anterior and not seg.distributed


@coronal_class
def is_palato_alveolar(seg: Segment) -> bool:
    return not seg.anterior and seg.distributed


@coronal_class
def is_retroflex(seg: Segment) -> bool:
    return not seg.anterior and not seg.distributed


check_coronal_exclusivity = coronal_cond(check_exclusivity('coronal'))


# -------------------------------------------------------------- #
#                             Dorsals                            #
# -------------------------------------------------------------- #


def is_dorsal(seg: Segment) -> bool:
    return seg.dorsal


vowel_condition_r = reverse_condition(is_vowel)
dorsal_condition = condition(is_dorsal)

dorsal_consonant = compose(vowel_condition_r, dorsal_condition)


@dorsal_consonant
def is_fronted_velar(seg: Segment) -> bool:
    return seg.high and not seg.low and seg.front and not seg.back


@dorsal_consonant
def is_central_velar(seg: Segment) -> bool:
    return seg.high and not seg.low and not seg.front and not seg.back


@dorsal_consonant
def is_back_velar(seg: Segment) -> bool:
    return seg.high and not seg.low and not seg.front and seg.back


@dorsal_consonant
def is_uvular(seg: Segment) -> bool:
    return not seg.high and not seg.low and not seg.front and seg.back


@dorsal_consonant
def is_pharyngeal(seg: Segment) -> bool:
    return not seg.high and seg.low and not seg.front and seg.back
