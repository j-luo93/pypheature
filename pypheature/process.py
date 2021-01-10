import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from .diacritic import Diacritic, InvalidDiacritic, get_diacritic
from .nphthong import Nphthong
from .segment import FValue, Segment, sign2value


class InvalidBaseSegment(Exception):
    """Raise this when there is no base segment found."""


class FeatureProcessor:
    """This reads the spreadsheet provided by Hayes."""

    def __init__(self, hayes_path: Optional[str] = None):
        hayes_path = hayes_path or Path(__file__).parent.parent / 'data/FeaturesDoulosSIL.xls'
        df = pd.read_excel(hayes_path).rename(columns={'Unnamed: 0': 'ipa'})

        # -------------- Fix errors in the original file. -------------- #

        # This 'ŋ' should not have any diacritic.
        df.at[33, 'ipa'] = 'ŋ'

        # This 'ʕ' should be a fricative, therefore delayed_release is True.
        df.at[57, 'delayed release'] = '+'

        # Add 'ɐ' which is merged with 'a'.
        df = df.append(df.loc[3].copy(), ignore_index=True)
        df.at[len(df) - 1, 'ipa'] = 'ɐ'

        # Add 'ɜ' which is merged with 'ə'
        df = df.append(df.loc[11].copy(), ignore_index=True)
        df.at[len(df) - 1, 'ipa'] = 'ɜ'

        # Define 'ʜ' as the voiceless pharyngeal trill (I don't know how to define the place of epiglottis), which is close to
        # the voiceless pharyngeal fricative 'ħ'.
        df = df.append(df.loc[56].copy(), ignore_index=True)
        df.at[len(df) - 1, 'ipa'] = 'ʜ'
        # A trill is a liquid, not an obstruent (like fricative).
        df.at[len(df) - 1, 'sonorant'] = '+'
        df.at[len(df) - 1, 'approximant'] = '+'
        df.at[len(df) - 1, 'delayed release'] = '0'
        df.at[len(df) - 1, 'trill'] = '+'

        # Define 'ʡ' as the voiced counterpart for 'ʜ'.
        df = df.append(df.loc[len(df) - 1].copy(), ignore_index=True)
        df.at[len(df) - 1, 'ipa'] = 'ʡ'
        df.at[len(df) - 1, 'voice'] = '+'

        # Obtain all unicode categories.
        df['ipa'] = df['ipa'].apply(lambda s: unicodedata.normalize('NFD', s))
        df['unicode_category'] = df['ipa'].apply(lambda lst: [unicodedata.category(c) for c in lst])

        def tie_bar_treatment(item):
            """Treat tie bar specially."""
            ipa, cat = item
            return ['Tb' if char == '͡' else cc for char, cc in zip(ipa, cat)]

        df['category_x'] = df[['ipa', 'unicode_category']].apply(tie_bar_treatment, axis=1)

        # Remove anything with `Mn` category unicodes except 'ç' and 'c͡ç', and use them as the base.
        base_df = df[(~df['category_x'].apply(lambda lst: 'Mn' in lst)) | (df['ipa'] == 'ç') | (df['ipa'] == 'c͡ç')]

        save_cols = list(base_df.columns)
        save_cols.remove('unicode_category')
        save_cols.remove('category_x')
        self._data = base_df[save_cols].copy()

        # -------------------- Process base segments ------------------- #

        feat2col = {f: f
                    for f in ['syllabic', 'consonantal', 'approximant', 'sonorant', 'continuant', 'trill', 'tap',
                              'front', 'back', 'high', 'low', 'tense', 'round', 'long', 'nasal', 'anterior',
                              'distributed', 'strident', 'lateral', 'labiodental', 'voice']
                    }
        feat2col['delayed_release'] = 'delayed release'
        feat2col['spread_glottis'] = 'spread gl'
        feat2col['constricted_glottis'] = 'constr gl'
        feat2col['labial'] = 'LABIAL'
        feat2col['coronal'] = 'CORONAL'
        feat2col['dorsal'] = 'DORSAL'

        def to_value(s):
            if s == '+':
                return True
            elif s == '-':
                return False
            assert s in ['0', 0]
            return None

        self._base_segments: Dict[str, Segment] = dict()
        for i, s in self._data.iterrows():
            kwargs = {f: to_value(s[c]) for f, c in feat2col.items()}
            # NOTE(j_luo) Every feature is not overlong in this sheet.
            kwargs['overlong'] = False
            seg = Segment(s['ipa'], **kwargs)
            self._base_segments[s['ipa']] = seg

        # Obtain regex for matching the leading base segment.
        pat = '(' + '|'.join(sorted(self._base_segments, key=len, reverse=True)) + ')'
        self._base_regex = re.compile(rf'^{pat}')

        # Store feature vector to segment mappings.
        self._fv2segment = defaultdict(list)

    def load_repository(self, repo: List[str]):
        for raw in repo:
            segment = self.process(raw)
            if isinstance(segment, Segment):
                self._fv2segment[segment.fv].append(segment)

    def change_features(self, segment: Segment, updates: List[str]) -> Segment:
        d = dict(segment.fv)
        d.update({update[1:]: sign2value[update[0]] for update in updates})
        new_fv = tuple([(k, d[k]) for k in sorted(d)])
        candidates = self._fv2segment[new_fv]
        if len(candidates) != 1:
            raise RuntimeError(f'Cannot find the unique mapped value.')
        return candidates[0]

    @lru_cache(maxsize=None)
    def process(self, raw: str) -> Union[Segment, Nphthong]:
        """Process one raw segments by decomposing it into one base segment and multiple diacritics if any."""
        raw = unicodedata.normalize('NFD', raw)

        def get_base(s: str):
            match = self._base_regex.match(s)
            if match is None:
                raise InvalidBaseSegment(f'Cannot find the base segment from {s}, which is part of {raw}.')
            base_raw = match.group(1)
            base = self._base_segments[base_raw]
            return base

        def safe_get_diacritic(idx: int) -> Diacritic:
            # Try longer ones first.
            if idx < len(raw) - 1:
                try:
                    return get_diacritic(raw[idx: idx + 2])
                except InvalidDiacritic:
                    pass
            return get_diacritic(raw[idx])

        bases = [get_base(raw)]
        i = len(bases[-1].base)
        while i < len(raw):
            try:
                # Apply diacritic to the last base segment.
                d = safe_get_diacritic(i)
                bases[-1] = d.apply_to(bases[-1])
                i += len(d)
            except InvalidDiacritic:
                bases.append(get_base(raw[i:]))
                i += len(bases[-1].base)
        if len(bases) == 1:
            return bases[0]
        return Nphthong(bases)
