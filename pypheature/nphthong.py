"""This deals with diphthongs, triphthongs and more."""

from dataclasses import dataclass
from typing import List

from .segment import Segment


class InvalidNphthong(Exception):
    """Raise this if the nphthong is not made up of only vowels."""


@dataclass
class Nphthong:
    """This must contain all vowels or glides. Glides are permitted since `ipapy` automatically converts "au̯" to "aw"."""

    vowels: List[Segment]

    def __str__(self):
        return ''.join(map(str, self.vowels))

    def __len__(self):
        return len(self.vowels)

    def __post_init__(self):
        for vow in self.vowels:
            if not vow.is_vowel() and not vow.is_glide():
                raise InvalidNphthong(f'Not every segment is a vowel or glide: [{", ".join(map(str, self.vowels))}]')
