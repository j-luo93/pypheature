from .segment import Segment, natural_class

glottal_width_class = natural_class('glottal_width')


@glottal_width_class
def is_spread_glottis(seg: Segment) -> bool:
    return seg.spread_glottis and not seg.constricted_glottis


@glottal_width_class
def is_constricted_glottis(seg: Segment) -> bool:
    return not seg.spread_glottis and seg.constricted_glottis


@glottal_width_class
def is_normal_glottis(seg: Segment) -> bool:
    return not seg.spread_glottis and not seg.constricted_glottis
