from bot.paths import (
    HEARTHSTONE_CARD_API,
)
from bot.utilities.webcache import WebCache


class Hearthstone:
    """Hearthstone information."""

    def __init__(self, cache: WebCache):
        self.cache = cache

    def get_cards(self):
        """
        Returns dict of hearthstone cards.
        """
        return self.cache.get(HEARTHSTONE_CARD_API, fallback=[])
