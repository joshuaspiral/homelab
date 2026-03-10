"""CSC111 Project 1: Text Adventure Game - Simulator

Instructions (READ THIS FIRST!)
===============================

This Python module contains code for Project 1 that allows a user to simulate
an entire playthrough of the game. Please consult the project handout for
instructions and details.

You can copy/paste your code from Assignment 1 into this file, and modify it as
needed to work with your game.

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
from event_logger import Event, EventList
from adventure import AdventureGame


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough.
    """
    # Private Instance Attributes:
    #   - game: The AdventureGame instance that this simulation uses.
    #   - _events: A collection of the events to process during the simulation.
    game: AdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        """
        Initialize a new game simulation based on the given game data, that runs through the given commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from the location at initial_location_id
        """
        self._events = EventList()
        self.game = AdventureGame(game_data_file, initial_location_id)

        # First event
        loc = self.game.get_location()
        self._events.add_event(Event(loc.id_num, loc.long_description), None)

        self.generate_events(commands)

    def generate_events(self, commands: list[str]) -> None:
        """
        Generate events in this simulation, based on current_location and commands, a valid list of commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from current_location
        """
        for cmd in commands:
            self.game.process_command(cmd, self._events)

    def get_id_log(self) -> list[int]:
        """
        Get back a list of all location IDs in the order that they are visited within a game simulation
        that follows the given commands.
        """
        # Note: We have completed this method for you. Do NOT modify it for A1.

        return self._events.get_id_log()

    def run(self) -> None:
        """
        Run the game simulation and log location descriptions.
        """
        # Note: We have completed this method for you. Do NOT modify it for A1.

        current_event = self._events.first  # Start from the first event in the list

        while current_event:
            print(current_event.description)
            if current_event is not self._events.last:
                print("You choose:", current_event.next_command)

            # Move to the next event in the linked list
            current_event = current_event.next


if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })

    # Win Walkthrough
    # Strategy:
    # 1. Get Fob (Loc 1) to enter Morrison (Loc 4)
    # 2. Get Wallet (Loc 7)
    # 3. Enter Morrison (via Cafe Loc 5) to get Passport (Loc 4)
    # 4. Go to TCard Office (Loc 6) to buy TCard (requires Wallet + Passport)
    # 5. Drop heavy items (Wallet, Passport) to free space
    # 6. Go to Robarts (Loc 3) (requires TCard) to get USB, Charger
    # 7. Deliver USB, Charger to Morrison
    # 8. Get Mug (Loc 5) and deliver to Morrison
    win_walkthrough = [
        "take fob",
        "go west",          # To Tutorial (7)
        "take wallet",
        "go east",          # To Bahen (1)
        "go east",          # To St George (2)
        "go east",          # To Cafe (5)
        "go north",         # To Morrison (4) - Needs Fob
        "take passport",
        "go south",         # To Cafe (5)
        "go south",         # To TCard Office (6)
        "buy tcard",        # Needs Wallet + Passport
        "drop wallet",      # Free up weight
        "drop passport",    # Free up weight
        "go north",         # To Cafe (5)
        "go west",          # To St George (2)
        "go north",         # To Robarts (3) - Needs TCard
        "take usb drive",
        "take laptop charger",
        "go east",          # To Morrison (4)
        "drop usb drive",
        "drop laptop charger",
        "go south",         # To Cafe (5)
        "take lucky mug",
        "go north",         # To Morrison (4)
        "drop lucky mug"    # Win!
    ]
    # Expected Log: Locations visited.
    # 1 -> 7 -> 1 -> 2 -> 5 -> 4 -> 5 -> 6 -> 5 -> 2 -> 3 -> 4 -> 5 -> 4
    expected_log = [1, 1, 7, 7, 1, 2, 5, 4, 4, 5, 6, 6, 6, 6, 5, 2, 3, 3, 3, 4, 4, 4, 5, 5, 4, 4]
    sim = AdventureGameSimulation('game_data.json', 1, win_walkthrough)
    assert expected_log == sim.get_id_log(), f"Win walkthrough failed log: {sim.get_id_log()}"
    assert sim.game.check_win_condition(), "Win walkthrough failed to meet win condition"
    # Lose Demo (run out of moves by going back and forth)
    lose_demo = ["go east", "go west"] * 25
    expected_log = [1] + [2, 1] * 25
    sim = AdventureGameSimulation('game_data.json', 1, lose_demo)
    assert expected_log == sim.get_id_log(), f"Lose demo failed log: {sim.get_id_log()}"
    assert sim.game.check_lose_condition(), "Lose demo failed to meet lose condition"

    # Inventory Demo
    inventory_demo = ["take fob", "inventory"]
    expected_log = [1, 1, 1]
    sim = AdventureGameSimulation('game_data.json', 1, inventory_demo)
    assert expected_log == sim.get_id_log(), f"Inventory demo failed log: {sim.get_id_log()}"
    assert any(item.name == "fob" for item in sim.game.inventory), "Inventory demo failed to pick up item"

    # Scores Demo
    scores_demo = ["take fob", "score"]
    expected_log = [1, 1, 1]
    sim = AdventureGameSimulation('game_data.json', 1, scores_demo)
    assert expected_log == sim.get_id_log(), f"Scores demo failed log: {sim.get_id_log()}"
    assert sim.game.score > 0, "Scores demo failed to increase score"

    # Enhancement Demos
    # 1. Simple puzzle - need tcard to enter Robarts
    # Attempt to enter Robarts without TCard (Fail), then with TCard (Success)
    simple_enhancement_demo = [
        "go east",      # To 2
        "go north",     # To 3 (Fail - Locked). Stays at 2.
        "go west",      # Back to 1
        "take fob",
        "go west",      # To 7
        "take wallet",
        "go east",      # To 1
        "go east",      # To 2
        "go east",      # To 5
        "go north",     # To 4 (use fob)
        "take passport",
        "go south",     # To 5
        "go south",     # To 6
        "buy tcard",
        "drop wallet",
        "drop passport",
        "go north",     # To 5
        "go west",      # To 2
        "go north"      # To 3 (Success!)
    ]
    # Log: [1 (init), 2, 2, 1, 1, 7, 7, 1, 2, 5, 4, 4, 5, 6, 6, 6, 6, 5, 2, 3]
    expected_log = [1, 2, 2, 1, 1, 7, 7, 1, 2, 5, 4, 4, 5, 6, 6, 6, 6, 5, 2, 3]
    sim = AdventureGameSimulation('game_data.json', 1, simple_enhancement_demo)
    assert expected_log == sim.get_id_log(), f"Enhancement demo failed log: {sim.get_id_log()}"
    assert sim.game.current_location_id == 3, "Enhancement demo failed to enter Robarts"

    print("All simulation tests passed!")
