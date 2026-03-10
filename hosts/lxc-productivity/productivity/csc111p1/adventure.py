"""CSC111 Project 1: Text Adventure Game - Game Manager

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations
import json
from typing import Optional

from game_entities import Location, Item, Map
from event_logger import Event, EventList

# Game Constants
MAX_MOVES = 50
MAX_ITEM = 2
FIND_POINT_VALUE = 5
REQUIRED_ITEMS = ["usb drive", "laptop charger", "lucky mug"]
TARGET_LOCATION = 4
MOVE_COMMANDS = ('go', 'take', 'pick', 'drop', 'examine', 'read')

# ANSI Color Codes
# ANSI escape codes for terminal colors.
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# Backgrounds
BG_BLUE = "\033[44m"
BG_GREEN = "\033[42m"
BG_RED = "\033[41m"


class Player:
    """Stores all player-related state for the AdventureGame.

    Instance Attributes:
    - location_id: The ID of the player's current location.
    - inventory: List of Item objects the player is carrying.
    - score: The player's current score.
    - moves: Number of moves the player has made.
    - found_items: Set of item names that have been picked up (for scoring).
    - deposited_items: Set of item names deposited at target (for scoring).

    Representation Invariants:
        - self.current_location_id in self._locations
        - self.moves >= 0
        - self.score >= 0
        - all(isinstance(item, Item) for item in self.inventory)
        - all(item.name in self.found_items for item in self.inventory
            if item.name in self.found_items)
    """

    location_id: int
    inventory: list[Item]
    score: int
    moves: int
    found_items: set[str]
    deposited_items: set[str]

    def __init__(self, start_location: int) -> None:
        self.location_id = start_location
        self.inventory = []
        self.score = 0
        self.moves = 0
        self.found_items = set()
        self.deposited_items = set()


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - ongoing: Whether the game is still in progress.


    Private Instance Attributes:
        - _locations: a mapping from location id to Location object. This represents all the locations in the game.
        - _items: a list of Item objects, representing all items in the game.
    """

    _locations: dict[int, Location]
    _items: list[Item]
    _map: Map
    _command_handlers: dict[str, object]

    ongoing: bool
    player: Player

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        (note: you are allowed to modify the format of the file as you see fit)

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """
        self._locations, self._items, self._map = self._load_game_data(game_data_file)

        self.player = Player(initial_location_id)
        self.ongoing = True

        self._command_handlers = {
            'help': self._handle_help,
            'look': self._handle_look,
            'inventory': self._handle_inventory,
            'score': self._handle_score,
            'log': self._handle_log,
            'quit': self._handle_quit,
            'go': self._handle_go,
            'take': self._handle_take,
            'pick': self._handle_pick,
            'drop': self._handle_drop,
            'examine': self._handle_examine,
            'read': self._handle_read,
            'buy': self._handle_buy
        }

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item], Map]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        (2) a list of all Item objects, and (3) a Map object.
"""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['id'], loc_data['brief_description'], loc_data['long_description'],
                                    loc_data['available_commands'], loc_data['items'], loc_data.get('locked'))
            locations[loc_data['id']] = location_obj

        items = []

        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['description'], item_data['start_position'],
                            item_data['target_position'], item_data['target_points'], item_data.get('required_items'),
                            item_data.get('heavy', True))
            items.append(item_obj)

        map_data = data.get("map", {"key": {}, "grid": ""})
        map_obj = Map(map_data["key"], map_data["grid"])

        return locations, items, map_obj

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """

        if loc_id is None:
            return self._locations[self.player.location_id]
        return self._locations[loc_id]

    def find_item_by_name(self, name: str) -> Optional[Item]:
        """Return the Item object with the given name, or None if not found."""
        for item in self._items:
            if item.name.lower() == name.lower():
                return item
        return None

    def check_win_condition(self) -> bool:
        """Check if the player has won by depositing all required items at the target location."""
        target_loc = self.get_location(TARGET_LOCATION)
        return all(item_name in target_loc.items for item_name in REQUIRED_ITEMS)

    def check_lose_condition(self) -> bool:
        """Check if the player has lost by exceeding maximum moves."""
        return self.player.moves >= MAX_MOVES

    def process_command(self, command: str, log: EventList) -> str:
        """Process a command, updating game state and log, and returning a result message."""
        parts = command.lower().strip()
        if not parts:
            return "I don't understand that command."

        parts = parts.split(" ", 1)
        verb = parts[0]
        noun = parts[1] if len(parts) > 1 else ""

        handler = self._command_handlers.get(verb)

        if handler is None:
            return "I don't understand that command."

        if verb in MOVE_COMMANDS:
            self.player.moves += 1

        result = handler(noun, log)

        loc = self.get_location()
        log.add_event(Event(loc.id_num, loc.long_description), command)

        return result

    def _grab_item(self, item_name: str) -> str:
        """Attempt to take an item from the current location."""

        loc = self.get_location()

        if item_name not in loc.items:
            return "You don't see that here."

        item = self.find_item_by_name(item_name)
        if item is None:
            return "Error: Item data not found."

        if item.heavy:
            heavy_count = sum(1 for i in self.player.inventory if i.heavy)
            if heavy_count >= MAX_ITEM:
                return "You can't carry more than 2 heavy items."

        loc.items.remove(item_name)
        self.player.inventory.append(item)

        if item_name not in self.player.found_items:
            self.player.score += FIND_POINT_VALUE
            self.player.found_items.add(item_name)

        return f"You picked up the {item_name}."

    # Handler Functions
    def _handle_quit(self, _noun: str, _log: EventList) -> str:
        """ Handle the 'quit' command.

        Quit the game and return a string informing user.
        """
        self.ongoing = False
        return "Quitting game."

    def _handle_look(self, _noun: str, _log: EventList) -> str:
        """ Handle the 'look' command.

        Return the long description of the location the player is currently at.
        """
        return self.get_location().long_description

    def _handle_inventory(self, _noun: str, _log: EventList) -> str:
        """ Handle the 'inventory' command.

        Return a formatted string listing all items currently carried by the player.
        """

        lines = ["Inventory:"]

        if not self.player.inventory:
            lines.append("  (empty)")
        else:
            for item in self.player.inventory:
                lines.append(f"  - {item.name}")
        return "\n".join(lines)

    def _handle_score(self, _noun: str, _log: EventList) -> str:
        """ Handle the 'score' command.

        Return a string containing the players' score and current moves used.
        """

        return f"Current Score: {self.player.score}\nMoves: {self.player.moves}/{MAX_MOVES}"

    def _handle_log(self, _noun: str, log: EventList) -> str:
        """ Handle the 'log' command.

        Display all the events that have taken place in the current game.
        """

        log.display_events()
        return ""

    def _handle_go(self, direction: str, _log: EventList) -> str:
        """ Handle the 'go' command.

        Go to the location specified unless not accessible to player either because it is not a valid command or
        because player does not have the right items to enter the area.
        """

        if not direction:
            return "Go where?"

        loc = self.get_location()
        command = f"go {direction}"

        if command not in loc.available_commands:
            return "You can't go that way."

        next_id = loc.available_commands[command]
        next_loc = self.get_location(next_id)

        # Locked room check
        if next_loc.locked is not None:
            required = next_loc.locked['required_item']
            if not any(item.name == required for item in self.player.inventory):
                return next_loc.locked['message']

        self.player.location_id = next_id
        return ""

    def _handle_take(self, noun: str, _log: EventList) -> str:
        """ Handle the 'take' command.

        Attempts to take the item.
        """

        if not noun:
            return "Take what?"
        return self._grab_item(noun)

    def _handle_pick(self, noun: str, _log: EventList) -> str:
        """ Handle the 'pick up' command.

        Attempts to pick up the item.
        """

        if not noun.startswith("up "):
            return "Did you mean 'pick up <item>'?"

        item_name = noun[3:]
        if not item_name:
            return "Pick up what?"

        return self._grab_item(item_name)

    def _handle_drop(self, noun: str, _log: EventList) -> str:
        """ Handle the 'drop' command.

        Attempts to drop the item.
        """

        item = None
        loc = self.get_location()

        for it in self.player.inventory:
            if it.name.lower() == noun.lower():
                item = it
                break

        if item:
            self.player.inventory.remove(item)
            loc.items.append(item.name)
            msg = f"You dropped the {noun}."
            if loc.id_num == item.target_position and item.name not in self.player.deposited_items:
                msg += f"\nYou deposited the {item.name} in the correct place! (+{item.target_points} points)"
                self.player.score += item.target_points
                self.player.deposited_items.add(item.name)
            return msg
        return "You aren't carrying that."

    def _handle_examine(self, noun: str, _log: EventList) -> str:
        """ Handle the 'examine' command.

        Attempts to return the description of the item being examined by the player.
        """

        target = None
        loc = self.get_location()

        for it in self.player.inventory:
            if it.name.lower() == noun.lower():
                target = it
                break
        if not target and noun in loc.items:
            target = self.find_item_by_name(noun)
        if target:
            return target.description
        return "You don't see that here."

    def _handle_read(self, noun: str, _log: EventList) -> str:
        """ Handle the 'read' command.

        Will return a string containing the contents the desired item to be read if it can be read.
        """

        loc = self.get_location()

        if not noun:
            return "Read what?"

        command = f"read {noun}"

        if command not in loc.available_commands:
            return f"You can't read {noun} here."

        if noun == "map":
            if not self._map:
                return "Map is not available."
            return self._map.display()

        return ""

    def _handle_buy(self, noun: str, _log: EventList) -> str:
        """ Handle the 'buy' command.

        Attempts to buy the item if it can be bought.
        """

        loc = self.get_location()
        command = f"buy {noun}"

        if command not in loc.available_commands:
            return f"You can't buy {noun} here."

        item = self.find_item_by_name(noun)
        if item is None:
            return f"{noun} is not available for purchase."

        required_items = item.required_items if item.required_items is not None else []
        inventory_items = {i.name for i in self.player.inventory}
        missing = [req for req in required_items if req not in inventory_items]
        if missing:
            return "You don't have the required item(s) to buy a tcard!"

        if any(i.name == noun for i in self.player.inventory):
            return f"You already have {noun}."

        if item.heavy:
            heavy_count = sum(1 for i in self.player.inventory if i.heavy)
            if heavy_count >= MAX_ITEM:
                return "You can't carry more than 2 heavy items."

        self.player.inventory.append(item)
        if noun in loc.items:
            loc.items.remove(noun)

        return f"You bought {noun}!"

    def _handle_help(self, _noun: str, _log: EventList) -> str:
        """Display all available command keywords (not location-specific)."""

        return (
            "Available commands:\n"
            "  help                - Show this help message\n"
            "  look                - Look around the current location\n"
            "  go <direction>      - Move in a direction (e.g., go north)\n"
            "  take <item>         - Take an item\n"
            "  pick up <item>      - Pick up an item\n"
            "  drop <item>         - Drop an item\n"
            "  examine <item>      - Examine an item\n"
            "  inventory           - View your inventory\n"
            "  score               - View your score and move count\n"
            "  log                 - View your movement log\n"
            "  read <object>       - Read something (e.g., read map)\n"
            "  buy <item>          - Buy an item (if available)\n"
            "  quit                - Quit the game"
        )


if __name__ == "__main__":
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })go

    game_log = EventList()
    game = AdventureGame('game_data.json', 1)
    menu = ["look", "inventory", "score", "log", "quit"]

    # Welcome banner
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{YELLOW}  CSC111 TEXT ADVENTURE: The Missing Project Files {RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{DIM}Find your USB drive, laptop charger, and lucky mug!{RESET}")
    print(f"{DIM}Return them to your dorm before the 1pm deadline.{RESET}\n")

    print(f"{DIM}If you need help at any time, just type: help{RESET}\n")

    # Log starting location
    start_loc = game.get_location()
    game_log.add_event(Event(start_loc.id_num, start_loc.long_description), None)

    while game.ongoing:
        location = game.get_location()

        # Check win condition
        if game.check_win_condition():
            print(f"\n{BOLD}{BG_GREEN}{WHITE} CONGRATULATIONS! {RESET}")
            print(f"{GREEN}You have returned all the missing items to your dorm room!{RESET}")
            print(f"{BOLD}Final Score: {YELLOW}{game.player.score}{RESET}")
            game.ongoing = False
            break

        # Check lose condition
        if game.check_lose_condition():
            print(f"\n{BOLD}{BG_RED}{WHITE} TIME'S UP! {RESET}")
            print(f"{RED}It's 1:00pm! The deadline has passed.{RESET}")
            print(f"{DIM}You ran out of time. GAME OVER.{RESET}")
            game.ongoing = False
            break

        # Location header
        print(f"\n{BOLD}{BG_BLUE}{WHITE} LOCATION {location.id_num} {RESET}")
        if not location.visited:
            print(f"{CYAN}{location.long_description}{RESET}")
            location.visited = True
        else:
            print(f"{DIM}{location.brief_description}{RESET}")

        # Show items at location
        if location.items:
            print(f"\n{YELLOW}👀 You see: {BOLD}{', '.join(location.items)}{RESET}")

        # Display possible actions
        print(f"\n{MAGENTA}{'─' * 40}{RESET}")
        print(f"{BOLD}Commands:{RESET}", end=" ")
        actions = list(location.available_commands.keys())
        actions.append("help")
        print(f"{GREEN}{', '.join(actions)}{RESET}" if actions else f"{DIM}(none){RESET}")

        # Get input
        choice = input(f"\n{BOLD}{WHITE}> {RESET}").lower().strip()

        print(f"{DIM}{'─' * 40}{RESET}")

        # Process command
        result_msg = game.process_command(choice, game_log)
        if result_msg:
            # Color the result based on content
            if "picked up" in result_msg or "deposited" in result_msg:
                print(f"{GREEN}{result_msg}{RESET}")
            elif "don't" in result_msg or "aren't" in result_msg or "locked" in result_msg:
                print(f"{RED}{result_msg}{RESET}")
            elif "Inventory" in result_msg or "Score" in result_msg:
                print(f"{CYAN}{result_msg}{RESET}")
            elif "Available commands" in result_msg:
                print(f"{CYAN}{result_msg}{RESET}")
            else:
                print(result_msg)
