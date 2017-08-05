TODO:

* Synchronize commands with themselves
* Pyramid Game: level 7: more points
* Tests (create fake irc) https://docs.pytest.org/en/latest/
* oralpleasure !on / !off
* limit ability for native speech
* !rank without arguments


DESIGN DECISIONS:

* All commands in lowercase, but accept commandcalls in upper- and lowercase (cast '.lower()' on all commands, not the args though) ?
* There could be a combined list for both twitch- and BTTV-emotes to chose from for the 'Guess The Emote'-Game. Would be even more random but BTTV-emotes might fall short.
* Save all the data in one json-file with multiple objects or different json-files? (For now different json-files.)
* Native speech is lowest in the order of execution and gets only triggered if no custom command is executed beforehand.


IMPORTANT ISSUES / QUESTIONS:

* Commands that were added by users to the bot, e.g. while using '!addcommand', have to be lower in priority of execution. Otherwise important commands can be 'overwritten' by usercommands.
* Permissions for games: They should be able to be only started by Moderators, but played by Users.
* Emotes in the form of ;-) or ;-P could not be extracted from the twitchtv.emote-API, since they are stored as: '\\&lt\\;3' or '\\;-?(p|P)'.
