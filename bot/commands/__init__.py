"""Package containing all possible commands.

Splits commands into multiple variables:
activeGames: Commands that should always react (no cooldown), except when another activeGame is running
passiveGames: Commands that should always react (no cooldown)
games: activeGames + passiveGames
commands: all commands
"""

from .pyramid import Pyramid
from .kappagame import KappaGame
from .guessemotegame import GuessEmoteGame
from .guessminiongame import GuessMinionGame
from .monkalotparty import MonkalotParty
from .sleep import Sleep
from .editcommandlist import EditCommandList
from .editquotelist import editQuoteList
from .outputquote import outputQuote
from .outputstats import outputStats
from .calculator import Calculator
from .autogames import AutoGames
from .notifications import Notifications
from .pyramidreply import PyramidReply
from .tentareply import TentaReply
from .smorc import Smorc
from .slaphug import SlapHug
from .rank import Rank
from .editcommandmods import EditCommandMods
from .active import Active
from .pronouns import Pronouns
from .questions import Questions
from .oralpleasure import Oralpleasure
from .banme import BanMe
from .userignore import UserIgnore
from .speech import Speech
from .simplereply import SimpleReply
from .pyramidblock import PyramidBlock
from .spam import Spam
from .topspammers import TopSpammers
from .streaminfo import StreamInfo

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
    Sleep,
    EditCommandList,
    editQuoteList,
    outputQuote,
    outputStats,
    Calculator,
    AutoGames,
    Notifications,
    PyramidReply,
    # EmoteReply,     # Deactivated due to request from IGetNoKick in Zetalot's channel 26.09.2017
    TentaReply,
    Smorc,
    SlapHug,
    Rank,
    EditCommandMods,
    Active,
    Pronouns,
    Questions,
    Oralpleasure,
    BanMe,
    UserIgnore,
    Speech,
    SimpleReply,
    PyramidBlock,
    Spam,
    TopSpammers,
    StreamInfo
]

commands = activeGames + passiveGames + other
games = activeGames + passiveGames
passivegames = passiveGames
