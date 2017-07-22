TODO:

* save scores to database
* synchronize commands with themselves
* cleverbot
* capitalize usernames
* tests (create fake irc) https://docs.pytest.org/en/latest/
* port entire thing to python3


DESIGN DECISIONS:

* All commands in lowercase, but accept commandcalls in upper- and lowercase (cast '.lower()' on all commands, not the args though) ?


IMPORTANT ISSUES / QUESTIONS:

* Commands that were added by users to the bot, e.g. while using '!addcommand', have to be lower in priority of execution. Otherwise important commands can be 'overwritten' by usercommands.
* Permissions for games: They should be able to be only started by Moderators, but played by Users.