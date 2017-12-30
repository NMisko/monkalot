"""Commands: "!calc"."""
import re

import pyparsing

from bot.commands.command import Command
from bot.utilities.math_parser import NumericStringParser
from bot.utilities.permission import Permission


class Calculator(Command):
    """A chat calculator that can do some pretty advanced stuff like sqrt and trigonometry.

    Example: !calc log(5^2) + sin(pi/4)
    """

    perm = Permission.User

    symbols = ["e", "pi", "sin", "cos", "tan", "abs", "trunc", "round", "sgn"]

    def __init__(self, bot):
        """Initialize variables."""
        self.nsp = NumericStringParser()
        self.responses = {}

    def match(self, bot, user, msg, tag_info):
        """Match if the message starts with !calc."""
        return msg.lower().startswith("!calc ")

    def run(self, bot, user, msg, tag_info):
        """Evaluate second part of message and write the result."""
        self.responses = bot.responses["Calculator"]
        expr = msg.split(' ', 1)[1]
        try:
            result = self.nsp.eval(expr)
            # if result.is_integer():
            #     result = int(result)
            reply = "{} = {}".format(expr, result)
            bot.write(reply)
        except ZeroDivisionError:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["div_by_zero"]["msg"], var))
        except OverflowError:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["number_overflow"]["msg"], var))
        except pyparsing.ParseException:
            var = {"<USER>": bot.displayName(user)}
            bot.write(bot.replace_vars(self.responses["wrong_input"]["msg"], var))
        except (TypeError, ValueError):  # Not sure which Errors might happen here.
            var = {"<USER>": bot.displayName(user), "<EXPRESSION>": expr}
            bot.write(bot.replace_vars(self.responses["default_error"]["msg"], var))

    def checkSymbols(self, msg):
        """Check whether s contains no letters, except e, pi, sin, cos, tan, abs, trunc, round, sgn."""
        msg = msg.lower()
        for s in self.symbols:
            msg = msg.lower().replace(s, '')
        return re.search('[a-zA-Z]', msg) is None
