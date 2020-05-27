"""Commands: "!calc"."""
import re

import math
import pyparsing

from bot.commands.command import Command
from bot.utilities.math_parser import NumericStringParser
from bot.utilities.permission import Permission

PRECISION = 5


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
        expr = msg.split(" ", 1)[1]
        try:
            result = self.nsp.eval(expr)

            # This condition fixes floating point errors, like 0.1 + 0.2 = 0.300...004
            # Rounds to <PRECISION> digits after the first non zero digit
            # E.g.: 0.30000004 -> 0.3
            #       0.000030030004 -> 0.00003003
            if abs(result) < 1:
                dist = abs(
                    int(math.log10(abs(result)))
                )  # How many zeroes are after ., before a non zero digit
                result = round(result, PRECISION + dist)
            else:
                result = round(result, PRECISION)
            reply = "{} = {}".format(expr, result)
            bot.write(reply)
        except ZeroDivisionError:
            var = {"<USER>": bot.display_name(user)}
            bot.write(bot.replace_vars(self.responses["div_by_zero"]["msg"], var))
        except OverflowError:
            var = {"<USER>": bot.display_name(user)}
            bot.write(bot.replace_vars(self.responses["number_overflow"]["msg"], var))
        except pyparsing.ParseException:
            var = {"<USER>": bot.display_name(user)}
            bot.write(bot.replace_vars(self.responses["wrong_input"]["msg"], var))
        except (TypeError, ValueError):  # Not sure which Errors might happen here.
            var = {"<USER>": bot.display_name(user), "<EXPRESSION>": expr}
            bot.write(bot.replace_vars(self.responses["default_error"]["msg"], var))

    def check_symbols(self, msg):
        """Check whether s contains no letters, except e, pi, sin, cos, tan, abs, trunc, round, sgn."""
        msg = msg.lower()
        for s in self.symbols:
            msg = msg.lower().replace(s, "")
        return re.search("[a-zA-Z]", msg) is None
