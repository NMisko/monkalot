TODO:

* Modify scores if user gets something correct.
* Save chat statistics: E.g. 'How many Kappa's per minute', etc.
* Synchronize commands with themselves
* Pyramid Game: Add different pyramid levels: level 3: pleb pyramid -> small timout (60s), level 5: normal points, level 7: more points
* Cleverbot (Native Speech)
* Capitalize usernames for output
* Tests (create fake irc) https://docs.pytest.org/en/latest/
* Some way to ensure different games like 'Kappa Game' or 'Guess The Emote Game' cannot be run simultaneously while the rest of the botfunctions still work.


DESIGN DECISIONS:

* All commands in lowercase, but accept commandcalls in upper- and lowercase (cast '.lower()' on all commands, not the args though) ?
* There could be a combined list for both twitch- and BTTV-emotes to chose from for the 'Guess The Emote'-Game. Would be even more random but BTTV-emotes might fall short.
* Save all the data in one json-file with multiple objects or different json-files? (For now different json-files.)


IMPORTANT ISSUES / QUESTIONS:

* Commands that were added by users to the bot, e.g. while using '!addcommand', have to be lower in priority of execution. Otherwise important commands can be 'overwritten' by usercommands.
* Permissions for games: They should be able to be only started by Moderators, but played by Users.
* Emotes in the form of ;-) or ;-P could not be extracted from the twitchtv.emote-API, since they are stored as: '\\&lt\\;3' or '\\;-?(p|P)'.
