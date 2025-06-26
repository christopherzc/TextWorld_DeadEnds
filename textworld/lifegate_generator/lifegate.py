import random
import json
from textworld import GameMaker
from textworld.generator import World, Quest, Event


colors_array = ['red', 'blue', 'yellow', 'orange', 'purple', 'green', 'black', 'white', 'gold', 'shining', 'weird', 'strange']
shapes_array = ['square', 'box', 'circle', 'star', 'cresent', 'triangle', 'rhombus', 'dot', 'spiral', 'cone', 'line']


# For determining the position of the dying zone:
reverse_directions = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east"
}
# TODO: The file path where the game is saved is hard-coded right now. Need to make it a variable to be passed in.

class LifeGateBuilder:

  def __init__(self, length = 8, wall_row = 4, wall_width = 3, wall_col_start = 2, 
               life_gate_dir = 'north', death_gate_dir = 'east',
               base_folder = "./", quests = []):
    self.base_folder = base_folder
    self.quests = quests
    self.length = length
    self.wall_row = wall_row
    self.wall_width = wall_width
    self.wall_col_start = wall_col_start
    self.life_gate_dir = life_gate_dir
    self.death_gate_dir = death_gate_dir

    assert wall_col_start + wall_width < length, "No trapping the agent in an unwinnable scenario"
    assert life_gate_dir != death_gate_dir, "Cannot have life gate and death row on same wall"

    # Always have the walls be between the agent start position and the life gate
    if self.death_gate_dir in ["east", "west"]:
      self.walls = [((wall_row - 1, wall_col_start + i), (wall_row, wall_col_start + i)) for i in range(wall_width)]
    else:
      self.walls = [((wall_row + i, wall_col_start - 1), (wall_row + i, wall_col_start)) for i in range(wall_width)]

    self.dead_zone_locs = []
    self.d_rows = []
    self.life_gate_loc = []
    self.d_cols = []
    self.player_row = 0
    self.player_col = 0

    self.place_zones()

    self.dying_rooms = []
    for i in self.d_rows:
      for j in self.d_cols:
        self.dying_rooms.append((i, j))

    self.dead_rooms = self.dead_zone_locs

    self.life_rooms = self.life_gate_loc

    # Set a flag to prevent the custom mechanic from repeatedly triggering itself.
    self.custom_code = """
activate-game-mechanics is a truth state that varies.
Before reading a command:
    now activate-game-mechanics is true.
"""


  def make_game(self, game_name = 'lifegate_base', print_layout = False):
    taken_names, actual_rooms, M = self.generate_rooms(GameMaker())

    # Frozen set for easier wall checking:
    wall_set = {frozenset([a, b]) for a, b in self.walls}

    # Keep track of established connections
    num_connections = 0
    failed_connections = 0

    # Make the connections:
    for j, row in enumerate(actual_rooms):
        for i, room in enumerate(row):
            current_pos = (j, i)

            # South:
            if j + 1 < len(actual_rooms):
                neighbor_pos = (j + 1, i)
                pair = frozenset([current_pos, neighbor_pos])
                if pair not in wall_set:
                    south_room = actual_rooms[j + 1][i]
                    try:
                      s_corridor = M.connect(room.south, south_room.north)
                      # print(f'{room.name} is north of {south_room.name}')
                      num_connections += 1
                    except:
                      failed_connections += 1

            # North:
            if j - 1 >= 0:
                neighbor_pos = (j - 1, i)
                pair = frozenset([current_pos, neighbor_pos])
                if pair not in wall_set:
                    north_room = actual_rooms[j - 1][i]
                    try:
                      n_corridor = M.connect(room.north, north_room.south)
                      num_connections += 1
                      # print(f'{room.name} is south of {north_room.name}')
                    except:
                      failed_connections += 1

            # East:
            if i + 1 < len(row):
                neighbor_pos = (j, i + 1)
                pair = frozenset([current_pos, neighbor_pos])
                if pair not in wall_set:
                    east_room = actual_rooms[j][i + 1]
                    try:
                      e_corridor = M.connect(room.east, east_room.west)
                      num_connections += 1
                      # print(f'{room.name} is west of {east_room.name}')
                    except:
                      failed_connections += 1

            # West:
            if i - 1 >= 0:
                neighbor_pos = (j, i - 1)
                pair = frozenset([current_pos, neighbor_pos])
                if pair not in wall_set:
                    west_room = actual_rooms[j][i - 1]
                    try:
                      w_corridor = M.connect(room.west, west_room.east)
                      num_connections += 1
                      # print(f'{room.name} is east of {west_room.name}')
                    except:
                      failed_connections += 1

    # Randomly set the player somewhere in the left corner (hard coded for now until we get stuff working)
    M.set_player(actual_rooms[self.player_row][self.player_col])
    # print(f'Player set in room {actual_rooms[self.player_row][self.player_col].name}')

    # Need to make a cleaner function-based way of doing this but for now this is fine
    M.quests = [self.generate_quests(M, actual_rooms)]
    M.compile(path = self.base_folder + self.format_save_string(), custom_code = self.custom_code)
    self.generate_room_dict(taken_names, game_name)
    if print_layout:
      self.pretty_print_map(actual_rooms)

    return self.base_folder, self.format_save_string()

  def format_save_string(self):
     # Default save string for game:
     return f"lifegate_{self.length}x{self.length}_walls{self.wall_row}_{self.wall_width}_{self.wall_col_start}_{self.death_gate_dir}_{self.life_gate_dir}"

  def generate_quests(self, M, actual_rooms):
     # Use the specified dead and life rooms to create quests.
    fail_events = []
    win_events = []
    for room_loc in self.dead_rooms:
      #  print(f'{actual_rooms[room_loc[0]][room_loc[1]].name} is a dead room')
       fail_events.append(Event(conditions={M.new_fact("at", M.player, actual_rooms[room_loc[0]][room_loc[1]])}))

    for room_loc in self.life_rooms:
      #  print(f'{actual_rooms[room_loc[0]][room_loc[1]].name} is a life room')
       win_events.append(Event(conditions={M.new_fact("at", M.player, actual_rooms[room_loc[0]][room_loc[1]])}))

    return Quest(win_events = win_events, fail_events = fail_events)
       
  def pretty_print_map(self, actual_rooms):
    # Step 0: Flatten the 2d actual rooms list into a single list of rooms
    room_names = [room.name for row in actual_rooms for room in row]

    # Step 1: Find max length for padding
    max_length = max(len(room) for room in room_names) + 3

    # Step 2: Format names and organize into grid
    named_rooms_formatted = []
    named_rooms_formatted_unpadded = []
    rows = []
    raw_rows = []
    for room_name in room_names:
        padded_name = room_name.ljust(max_length)
        rows.append(padded_name)
        raw_rows.append(room_name)
        if len(rows) == self.length:
            named_rooms_formatted.append(rows)
            rows = []
            named_rooms_formatted_unpadded.append(raw_rows)
            raw_rows = []

    # Add any remaining partial row
    if rows:
        named_rooms_formatted.append(rows)

    def add_marker(array, x, y, marker):
      array[x][y] = array[x][y].rstrip() + marker
      array[x][y] = array[x][y].ljust(max_length)
      return array

    named_rooms_formatted = add_marker(named_rooms_formatted, self.player_row, self.player_col, "[A]")

    for wall in self.walls:
      r1 = wall[0]
      r2 = wall[1]
      named_rooms_formatted = add_marker(named_rooms_formatted, r1[0], r1[1], "[W]")

    for i in self.d_rows:
      for j in self.d_cols:
        named_rooms_formatted = add_marker(named_rooms_formatted, i, j, "[D]")

    for death in self.dead_zone_locs:
      named_rooms_formatted = add_marker(named_rooms_formatted, death[0], death[1], "[X]")

    for life in self.life_gate_loc:
      named_rooms_formatted = add_marker(named_rooms_formatted, life[0], life[1], "[G]")

    # Step 5: Print the grid
    for row in named_rooms_formatted:
        print(row)


  def generate_room_dict(self, taken_names, game_name):
    # Generate a dictionary to hold room types.
    named_rooms_formatted_unpadded = []
    raw_rows = []
    for room in taken_names:
        raw_rows.append(room)
        if len(raw_rows) == self.length:
            named_rooms_formatted_unpadded.append(raw_rows)
            raw_rows = []

    # Wish there was a better way of doing this but I'm not sure of one that doesn't involve injecting inform7 code which is a pain
    dying_rooms = []
    dead_rooms = []
    life_room = []
    for i in self.d_rows:
      for j in self.d_cols: dying_rooms.append(named_rooms_formatted_unpadded[i][j])

    for death in self.dead_zone_locs: dead_rooms.append(named_rooms_formatted_unpadded[death[0]][death[1]])

    for life in self.life_gate_loc: life_room.append(named_rooms_formatted_unpadded[life[0]][life[1]])

    with open(game_name + '_room_info.json', 'w') as f:
        json.dump({'Dying' : dying_rooms, 'Dead': dead_rooms, 'Life': life_room}, f, indent=4)

  def generate_rooms(self, GameMaker):
    taken_names = []
    actual_rooms = []
    room_ids = [] # Sanity check: Make sure no room has more than 1 mechanic.
    for i in range(self.length):
      room_rows = []
      for j in range(self.length):
        room_name, taken_names = self.get_room_name(taken_names)
        # room = GameMaker.new_room("<< " + room_name + " >>")
        room = GameMaker.new_room(room_name, i7_custom_code = "")

        # Get the room identifier and see if this works for inform7
        # room_name = room.id
        if (i, j) in self.dying_rooms:
          # print(f'Room {room_name} is a dying room')
          assert room.id not in room_ids, f"Room {room.id} already has a mechanic assigned to it"
          room_ids.append(room.id)
          room_mechanic = f"""
Instead of doing something when the player is in the {room.id} and activate-game-mechanics is true:
    now activate-game-mechanics is false;
    let N be a random number from 1 to 100;
    if N > 40:
        try going {self.death_gate_dir};
        stop the action;
    otherwise:
        say "You cannot muster the energy to move. You were in room {room.name}.";"""
        elif (i, j) in self.dead_rooms:
          # print(f'Room {room_name} is a dead room')
          assert room.id not in room_ids, f"Room {room.id} already has a mechanic assigned to it"
          room_ids.append(room.id)
          room_mechanic = f"""
Before an actor doing something when the actor is the player and the player is in the {room.id}:
    end the story finally; [Lose]"""
        elif (i, j) in self.life_rooms:
          # print(f'Room {room_name} is a life room')
          assert room.id not in room_ids, f"Room {room.id} already has a mechanic assigned to it"
          room_ids.append(room.id)
          room_mechanic = f"""
Before an actor doing something when the actor is the player and the player is in the {room.id}:
    end the story finally; [Win]"""
        else:
          # print(f'No special mechanics for room {room_name} at ({i}, {j})')
          assert room.id not in room_ids, f"Room {room.id} already has a mechanic assigned to it"
          room_ids.append(room.id)
          room_mechanic = f"""
Instead of doing something when the player is in the {room.id} and activate-game-mechanics is true:
    now activate-game-mechanics is false;
    let N be a random number from 1 to 100;
    if N > 70: 
        try going {self.death_gate_dir};
        stop the action;
    otherwise:
        continue the action;"""

        self.custom_code += room_mechanic + "\n"
        # room = GameMaker.new_room(room_name, i7_custom_code = room_mechanic)
        room_rows.append(room)
      actual_rooms.append(room_rows)

    return taken_names, actual_rooms, GameMaker

  def get_room_name(self, taken_names):
    color = random.choice(colors_array)
    shape = random.choice(shapes_array)
    room_name = color + " " + shape
    while room_name in taken_names:
      color = random.choice(colors_array)
      shape = random.choice(shapes_array)
      room_name = color + " " + shape

    taken_names.append(room_name)
    return room_name, taken_names


  def place_zones(self):
    L = self.length
    wr = self.wall_row
    wc = self.wall_col_start
    ww = self.wall_width

    D = self.death_gate_dir
    G = self.life_gate_dir

    # death on EAST wall, life on NORTH wall
    if D=='east' and G=='north':
        self.d_rows           = list(range(wr,   L))
        self.d_cols           = list(range(wc+ww, L-1))
        self.dead_zone_locs   = [(r, L-1) for r in range(L)]
        self.life_gate_loc    = [(0, random.randint(1, L-2))]
        self.player_col       = random.randint(0, int(L/2))
        self.player_row       = -1

    # death=EAST, life=SOUTH
    elif D=='east' and G=='south':
        self.d_rows           = list(range(0,    wr+1))
        self.d_cols           = list(range(wc+ww, L-1))
        self.dead_zone_locs   = [(r, L-1) for r in range(L)]
        self.life_gate_loc    = [(L-1, random.randint(1, L-2))]
        self.player_col       = random.randint(0, int(L/2))
        self.player_row       =  0

    # death=WEST, life=NORTH
    elif D=='west' and G=='north':
        self.d_rows           = list(range(wr,   L))
        self.d_cols           = list(range(0,    wc))
        self.dead_zone_locs   = [(r, 0)   for r in range(L)]
        self.life_gate_loc    = [(0, random.randint(1, L-2))]
        self.player_col       = random.randint(int(L/2), L-1)
        self.player_row       = -1

    # death=WEST, life=SOUTH
    elif D=='west' and G=='south':
        self.d_rows           = list(range(0,    wr+1))
        self.d_cols           = list(range(0,    wc))
        self.dead_zone_locs   = [(r, 0)   for r in range(L)]
        self.life_gate_loc    = [(L-1, random.randint(1, L-2))]
        self.player_col       = random.randint(int(L/2), L-1)
        self.player_row       =  0

    # death=NORTH, life=EAST
    elif D=='north' and G=='east':
        self.d_rows           = list(range(1,    wr))
        self.d_cols           = list(range(0,   wc))
        self.dead_zone_locs   = [(0, c)   for c in range(L)]
        self.life_gate_loc    = [(random.randint(1, L-2), L-1)]
        self.player_row       = random.randint(int(L/2), L-1)
        self.player_col       = 0

    # death=NORTH, life=WEST
    elif D=='north' and G=='west':
        self.d_rows           = list(range(1,    wr))
        self.d_cols           = list(range(0,    wc+ww))
        self.dead_zone_locs   = [(0, c)   for c in range(L)]
        self.life_gate_loc    = [(random.randint(1, L-2), 0)]
        self.player_row       = random.randint(int(L/2), L-1)
        self.player_col       = L-1

    # death=SOUTH, life=EAST
    elif D=='south' and G=='east':
        self.d_rows           = list(range(wr+1, L))
        self.d_cols           = list(range(wc,   L))
        self.dead_zone_locs   = [(L-1, c) for c in range(L)]
        self.life_gate_loc    = [(random.randint(1, L-2), L-1)]
        self.player_row       = 0
        self.player_col       = random.randint(int(L/2), L-1)

    # death=SOUTH, life=WEST
    elif D=='south' and G=='west':
        self.d_rows           = list(range(wr+1, L))
        self.d_cols           = list(range(0,    wc+ww))
        self.dead_zone_locs   = [(L-1, c) for c in range(L)]
        self.life_gate_loc    = [(random.randint(1, L-2), 0)]
        self.player_row       = 0
        self.player_col       = random.randint(int(L/2), L-1)

    else:
        raise ValueError(f"Unsupported gate combination: death={D}, life={G}")
