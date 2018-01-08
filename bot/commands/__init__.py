"""Package containing all possible commands.

Splits commands into multiple variables:
activeGames: Commands that should always react (no cooldown), except when another activeGame is running
passiveGames: Commands that should always react (no cooldown)
games: activeGames + passiveGames
commands: all commands
"""

from .active import Active
from .autogames import AutoGames
from .banme import BanMe
from .cache import Cache
from .calculator import Calculator
from .editcommandlist import EditCommandList
from .editcommandmods import EditCommandMods
from .editquotelist import editQuoteList
from .guessemotegame import GuessEmoteGame
from .guessminiongame import GuessMinionGame
from .kappagame import KappaGame
from .monkalotparty import MonkalotParty
from .notifications import Notifications
from .oralpleasure import Oralpleasure
from .outputquote import outputQuote
from .outputstats import outputStats
from .pronouns import Pronouns
from .pyramid import Pyramid
from .pyramidblock import PyramidBlock
from .pyramidreply import PyramidReply
from .questions import Questions
from .rank import Rank
from .simplereply import SimpleReply
from .slaphug import SlapHug
from .sleep import Sleep
from .smorc import Smorc
from .spam import Spam
from .speech import Speech
from .streaminfo import StreamInfo
from .tentareply import TentaReply
from .topspammers import TopSpammers
from .userignore import UserIgnore


activeGames = [
    KappaGame,
    GuessEmoteGame,
    GuessMinionGame,
    MonkalotParty
]

passiveGames = [
    Pyramid
]

other = [
    # EmoteReply,     # Deactivated due to request from IGetNoKick in Zetalot's channel 26.09.2017
    Active,
    AutoGames,
    BanMe,
    Cache,
    Calculator,
    EditCommandList,
    EditCommandMods,
    editQuoteList,
    Notifications,
    Oralpleasure,
    outputQuote,
    outputStats,
    Pronouns,
    PyramidBlock,
    PyramidReply,
    Questions,
    Rank,
    SimpleReply,
    SlapHug,
    Sleep,
    Smorc,
    Spam,
    Speech,
    StreamInfo,
    TentaReply,
    TopSpammers,
    UserIgnore
]

commands = activeGames + passiveGames + other
games = activeGames + passiveGames
passivegames = passiveGames
