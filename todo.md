TODO:

-> Moved to Projects/Monkalot


DESIGN DECISIONS:

* All commands in lowercase, but accept commandcalls in upper- and lowercase (cast '.lower()' on all commands, not the args though) ?
* Save all the data in one json-file with multiple objects or different json-files? (For now different json-files.)
* Native speech is lowest in the order of execution and gets only triggered if no custom command is executed beforehand.


IMPORTANT ISSUES / QUESTIONS:

* Commands that were added by users to the bot, e.g. while using '!addcommand', have to be lower in priority of execution. Otherwise important commands can be 'overwritten' by usercommands.
* Emotes in the form of ;-) or ;-P could not be extracted from the twitchtv.emote-API, since they are stored as: '\\&lt\\;3' or '\\;-?(p|P)'.
