"""CSC111 Project 1: Text Adventure Game - Game Entities

Instructions (READ THIS FIRST!)
===============================

This Python module contains the entity classes for Project 1, to be imported and used by
 the `adventure` module.
 Please consult the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from dataclasses import dataclass


@dataclass
class Location:
    """A location in our text adventure game world.

    Instance Attributes:
        - id_num: The integer identifier for this location.
        - brief_description: A short description of the location (for repeated visits).
        - long_description: A detailed description of the location (for the first visit).
        - available_commands: A dict mapping valid command strings (e.g., 'look') to the ID of the destination location.
        - items: A list of names of items currently present in this location.
        - locked: Optional, A dict mapping item required to enter and the message displayed on illegal entry.
        - visited: A boolean indicating whether the player has visited this location at least once.

    Representation Invariants:
        - # TODO Describe any necessary representation invariants
    """

    # This is just a suggested starter class for Location.
    # You may change/add parameters and the data available for each Location object as you see fit.
    #
    # The only thing you must NOT change is the name of this class: Location.
    # All locations in your game MUST be represented as an instance of this class.

    id_num: int
    brief_description: str
    long_description: str
    available_commands: dict[str, int]
    items: list[str]
    locked: dict[str, str] | None = None
    visited: bool = False


@dataclass
class Item:
    """An item in our text adventure game world.

    Instance Attributes:
        - name: The name of the item (e.g., 'lucky mug').
        - description: A description of the item.
        - start_position: The location ID where this item is initially found.
        - target_position: The location ID where this item must be deposited to earn points.
        - target_points: The number of points awarded for depositing this item at the target position.
        - required_items: Optional list of item names required to get this item.
        - heavy: A boolean, if True, it counts toward 2-item weight limit, if False can carry unlimited amount of it


    Representation Invariants:
        - len(self.name) > 0
        - self.start_position > 0
        - self.target_position > 0
        - self.target_points >= 0
    """

    # NOTES:
    # This is just a suggested starter class for Item.
    # You may change these parameters and the data available for each Item object as you see fit.
    # (The current parameters correspond to the example in the handout).
    #
    # The only thing you must NOT change is the name of this class: Item.
    # All item objects in your game MUST be represented as an instance of this class.

    name: str
    description: str
    start_position: int
    target_position: int
    target_points: int
    required_items: list[str] | None = None
    heavy: bool = True


@dataclass
class Map:
    """A map in our text adventure game world

    Instance Attributes:
    - key: A dict mapping the id location and the location name for the map
    - grid: A string representation of the game map

    Representation Invariants:
        - all(isinstance(k, str) for k in self.key)
        - all(isinstance(v, str) for v in self.key.values())
        - self.grid is a non-empty string
    """
    key: dict[str, str]
    grid: str

    def display(self) -> str:
        """Return a formatted string representation of the map, including the map key and the grid layout."""

        key_lines = ", ".join(f"{key}: {value}" for key, value in self.key.items())
        return f"📜 MAP OF THE AREA 📜\nKey: {key_lines}\n{self.grid}"


# Note: Other entities you may want to add, depending on your game plan:
# - Puzzle class to represent special locations (could inherit from Location class if it seems suitable)
# - Player class
# etc.

if __name__ == "__main__":
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })
