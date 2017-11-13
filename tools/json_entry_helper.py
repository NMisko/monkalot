import argparse
import json
from collections import OrderedDict

# WARNING: I don't know what will happen if you edit the JSON file while running this helper script...
# WARNING2: Improper use or bug due to my carelessness CAN WIPE your file. BACKUP your json files !!!

class JSONHelper(object):
    RESPONSES_CONTENT = {
        "msg" : "Fill in message with <VAR>",
        "info" : "Fill in info",
        "args_info": {
            "<VAR>": "Fill in variable description"
        }
    }

    def __init__(self, path, autosave=True, safemode=True):
        self._autosave = autosave
        self._safemode = safemode
        self._path = path

        self.end = False
        self.changed = False

        self.loadJSON()

    def mainLoop(self):
        # act like a simple console to edit JSON file

        c = ''
        commands = {
            's' : self.saveJSON,
            'd' : self.deleteEntry,
            'a' : self.addEntry,
            'au' : self.toggleAutosave,
            'sa' : self.toggleSafemode,
            'q' : self.quit
        }

        # main loop here
        while not self.end:
            self.printInstructions()
            c = input("Command: ").lower()

            if c in commands:
                commands[c]()
            else :
                print("Invalid command. Please try again")


    def printInstructions(self):
        print('=' * 50)
        if not self._safemode:
            print("Currently safe mode is off, you may overwrite your existing JSON entries when adding new one.")
        if not self._autosave:
            print("Currently autosave is off, you need to save JSON manually.")
        if self.changed:
            print("Changes on current file is not saved yet")
        print("Current file: {}\n".format(self._path))
        print(r"Enter commands: [S]ave JSON / [D]elete entry / [A]dd entry / Toggle [Au]tosave /  Toggle [Sa]femode / [Q]uit")


    def toggleAutosave(self):
        # XOR 1 means toggle
        self._autosave ^= True

    def toggleSafemode(self):
        self._safemode ^= True

    def loadJSON(self):
        with open(self._path, encoding="utf-8") as fp:
            self._jObj = json.load(fp, object_pairs_hook=OrderedDict)

        # Only read hash JSON. I don't know how to handle hash in array, valid non-hash JSON values like intergers for this case...
        if not isinstance(self._jObj, dict):
            raise TypeError("Expecting a hash from json({}), but it is {}".format(self._path, type(self._jObj)))

    def saveJSON(self):
        with open(self._path, 'w', encoding="utf-8") as file:
            json.dump(self._jObj, file, ensure_ascii=False, indent=4)

        # reload JSON object, not sure if really needed or not
        self.loadJSON()
        self.changed = False

    def deleteEntry(self):
        # Example:
        # hash has a.b.c.d.e in layer
        #            b has bc, bd in addtion to c
        #            b = {"c" : hash of d to e, "bc" : some data, "bd" ... }
        # If you enter a in path, everything will be cleared.
        # If you enter a.b.c in path, d,e AND c will be removed. But bc, bd are intact
        #

        print("\nEnter the JSON path (with dots) you want to remove, path.to.somewhere.asexample\n")
        p = input("Path: ").strip()
        # Just go back to main menu if enter nothing
        if p == "":
            print("Entered nothing, go back to menu")
            return
        subpaths = p.split('.')

        d = self._jObj

        try:
            for sp in subpaths[ :len(subpaths)-1]:
                d = d[sp]

            # reach destination successfully, don't know last key is valid or not
            del d[subpaths[-1]]
            print("\nEntry deleted!")

            self.changed = True
            if self._autosave:
                self.saveJSON()

        except KeyError as ke:
            print("Path cannot be found at {}".format(ke))


    def addEntry(self):
        # Example:
        # hash has a.b.c.d in layer
        # If you enter a.b.c.d.e.f in path, a.b.c.d.e will be creted. a.b.c.d.e.f will contain RESPONSES_CONTENT.
        # If you enter a.b in path, b will contain RESPONSES_CONTENT. c,d WILL BE LOST.
        # If you enter a.b in path, but safe mode is on, nothing will be changed. Safe mode only allows entries to be created on undefined hash.
        #

        print("\nEnter the JSON path (with dots) you want to add template content, path.to.somewhere.asexample.type1")
        print("path.to.somewhere.type1 will contain a hash of RESPONSES_CONTENT\n")
        p = input("Path: ").strip()

        # Just go back to main menu
        if p == '':
            print("Entered nothing, go back to menu")
            return

        subpaths = p.split('.')

        d = self._jObj

        # different from deleteEntry(), we create empty hashes if key is not defined
        # But if subpath is used AND is not a hash, then it is an error in path

        try:
            for sp in subpaths[ :len(subpaths)-1]:
                if sp not in d:
                    # create new dict when key not found
                    d[sp] = {}
                    d = d[sp]
                else:
                    if not isinstance(d[sp], dict):
                        raise TypeError("Path at {} is not a dict".format(sp))
                    d = d[sp]
        except TypeError as e:
            print(e)
            return

        if self._safemode and subpaths[-1] in d:
            print("Safe mode is on, does not allow overwrite on existing entries")
            return

        d[subpaths[-1]] = JSONHelper.RESPONSES_CONTENT.copy()
        self.changed = True
        print("\nEntry added!")
        if self._autosave:
            self.saveJSON()

    def quit(self):
        self.end = True

        # Do any cleanup here if needed
        print("Bye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="Helper for editing .json files.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            allow_abbrev=False
    )

    parser.add_argument('path',
            type=str,
            nargs='?',
            default=r'..\channels\template\configs\responses.json',
            #default=r'test.json',
            help='path to the .json file you want to edit'
    )

    parser.add_argument('--noautosave',
            action="store_false",
            dest='autosave',
            help='turn off autosave'
    )

    parser.add_argument('--nosafemode',
            action="store_false",
            dest='safemode',
            help='turn off safemode on creating entries'
    )

    args = parser.parse_args()
    h = JSONHelper(args.path, autosave=args.autosave, safemode=args.safemode)
    h.mainLoop()
