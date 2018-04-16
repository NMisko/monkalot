"""Spellcorrection module, for custom word sets.

Forked from https://github.com/phatpiglet/autocorrect and modified so it uses
a fixed set of words.
"""

from itertools import chain

ALPHABET = 'abcdefghijklmnopqrstuvwxyz\','


class SpellCorrection(object):
    """Corrects a word based on given set of words."""

    def __init__(self, words):
        """Initialize word set."""
        self.words = words

    def spell(self, word):
        """Return lowercase correction of word.

        If no such word exists, returns False instead.
        """
        w = Word(word)
        candidates = (self.known([word]) or self.known(w.typos()) or self.known(w.double_typos()))
        if candidates:
            # Take the first candidate
            correction = candidates.pop()
        else:
            correction = False
        return correction

    def known(self, words):
        """{'Gazpacho', 'gazzpacho'} => {'gazpacho'}."""
        return {w.lower() for w in words} & self.words


class Word(object):
    """Container for word-based methods."""

    def __init__(self, word):
        """
        Generate slices to assist with type definitions.

        'the' => (('', 'the'), ('t', 'he'),
                  ('th', 'e'), ('the', ''))

        """
        word_ = word.lower()
        slice_range = range(len(word_) + 1)
        self.slices = tuple((word_[:i], word_[i:])
                            for i in slice_range)
        self.word = word

    def _deletes(self):
        """th."""
        return {concat(a, b[1:])
                for a, b in self.slices[:-1]}

    def _transposes(self):
        """teh."""
        return {concat(a, reversed(b[:2]), b[2:])
                for a, b in self.slices[:-2]}

    def _replaces(self):
        """tge."""
        return {concat(a, c, b[1:])
                for a, b in self.slices[:-1]
                for c in ALPHABET}

    def _inserts(self):
        """thwe."""
        return {concat(a, c, b)
                for a, b in self.slices
                for c in ALPHABET}

    def typos(self):
        """Letter combinations one typo away from word."""
        return (self._deletes() | self._transposes() |
                self._replaces() | self._inserts())

    def double_typos(self):
        """Letter combinations two typos away from word."""
        return {e2 for e1 in self.typos()
                for e2 in Word(e1).typos()}


def concat(*args):
    """reversed('th'), 'e' => 'hte'."""
    try:
        return ''.join(args)
    except TypeError:
        return ''.join(chain.from_iterable(args))
