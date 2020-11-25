import unicodedata
from typing import List

import pandas as pd

from .segment import Segment


class FeatureProcessor:
    """This reads the spreadsheet provided by Hayes."""

    def __init__(self, hayes_path: str):
        df = pd.read_excel(hayes_path).rename(columns={'Unnamed: 0': 'ipa'})
        # Fix errors in the original file.
        # This 'ŋ' should not have any diacritic.
        df.loc[33]['ipa'] = 'ŋ'
        # This 'ʕ' should be a fricative, therefore delayed_release is True.
        df.loc[57]['delayed release'] = '+'

        # Obtain all unicode categories.
        df['NFD'] = df['ipa'].apply(lambda s: unicodedata.normalize('NFD', s))
        df['unicode_category'] = df['NFD'].apply(lambda lst: [unicodedata.category(c) for c in lst])

        def tie_bar_treatment(item):
            """Treat tie bar specially."""
            nfd, cat = item
            return ['Tb' if char == '͡' else cc for char, cc in zip(nfd, cat)]

        df['category_x'] = df[['NFD', 'unicode_category']].apply(tie_bar_treatment, axis=1)

        # Remove anything with `Mn` category unicodes except 'ç', and use them as the base.
        base_df = df[(~df['category_x'].apply(lambda lst: 'Mn' in lst)) | (df['NFD'] == 'ç')]

        save_cols = list(base_df.columns)
        save_cols.remove('NFD')
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

        self._base_segments = list()
        for i, s in self._data.iterrows():
            kwargs = {f: to_value(s[c]) for f, c in feat2col.items()}
            seg = Segment(s['ipa'], **kwargs)
            self._base_segments.append(seg)
