"""Package containing all possible commands.

Splits commands into multiple variables:
activeGames: Commands that should always react (no cooldown), except when another activeGame is running
passiveGames: Commands that should always react (no cooldown)
games: activeGames + passiveGames
commands: all commands
"""

from .autogames import AutoGames
from .banme import BanMe
from .cache import Cache
from .calculator import Calculator
from .cardinfo import CardInfo
from .editcommandlist import EditCommandList
from .editcommandmods import EditCommandMods
from .editquotelist import EditQuoteList
from .guess_racetrack_game import GuessRacetrackGame
from .guessemotegame import GuessEmoteGame
from .guessminiongame import GuessMinionGame
from .kappagame import KappaGame
from .monkalotparty import MonkalotParty
from .notifications import Notifications
from .oralpleasure import Oralpleasure
from .outputquote import OutputQuote
from .outputstats import OutputStats
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
from .tip import Tip
from .topspammers import TopSpammers
from .userignore import UserIgnore


active_games = [
    KappaGame,
    GuessRacetrackGame,
    GuessEmoteGame,
    GuessMinionGame,
    MonkalotParty,
]

passive_games = [Pyramid]

other = [
    # EmoteReply,     # Deactivated due to request from IGetNoKick in Zetalot's channel 26.09.2017
    AutoGames,
    BanMe,
    Cache,
    Calculator,
    CardInfo,
    EditCommandList,
    EditCommandMods,
    EditQuoteList,
    Notifications,
    Oralpleasure,
    OutputQuote,
    OutputStats,
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
    StreamInfo,
    TentaReply,
    Tip,
    TopSpammers,
    UserIgnore,
    # Speech,  # Speech always has to be the last entry so it does not 'overwrite' commands which include the bots name.
]

# Repeat here the commands that should not get reloaded if the config gets rewritten
non_reload = [Speech]

commands = active_games + passive_games + other
games = active_games + passive_games
passivegames = passive_games
