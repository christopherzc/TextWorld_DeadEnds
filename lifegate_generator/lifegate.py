import random
import json
from textworld import GameMaker


colors_array = ['red', 'blue', 'yellow', 'orange', 'purple', 'green', 'black', 'white', 'gold', 'shining', 'weird', 'strange']
shapes_array = ['square', 'box', 'circle', 'star', 'cresent', 'triangle', 'rhombus', 'dot', 'spiral', 'cone', 'line']

class LifeGateBuilder:

  # For determining the position of the dying zone:
  reverse_directions = {
      "north": "south",
      "south": "north",
      "east": "west",
      "west": "east"
  }

  def __init__(self, length = 8, wall_row = 4, wall_width = 3, wall_col_start = 2, life_gate_dir = 'north', death_gate_dir = 'east'):
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

    # TODO Add cases for when the death gate is to the south or north
    # TODO Add cases for when the lifegate is to the east or west
    # For now, always place the agent somewhere on the row opposite to the life gate
    if self.death_gate_dir == 'east' and self.life_gate_dir == 'north':
      self.d_rows += [i for i in range(wall_row, length)]
      self.d_cols += [i for i in range(wall_col_start + wall_width, length - 1)]

      self.dead_zone_locs += [(i, length - 1) for i in range(length)]
      self.life_gate_loc.append((0, random.randint(1, length - 2)))

      self.player_col = random.randint(0, int(self.length/2))
      self.player_row = -1
    elif death_gate_dir == 'west' and self.life_gate_dir == 'north':
      self.d_rows += [i for i in range(wall_row, length)]
      self.d_cols += [i for i in range(1, wall_col_start)]

      self.dead_zone_locs += [(i, 0) for i in range(length)]
      self.life_gate_loc.append((0, random.randint(1, length - 2)))

      self.player_col = random.randint(int(self.length/2), length - 1)
      self.player_row = -1
    elif death_gate_dir == 'north' and self.life_gate_dir == 'east':
      self.d_rows += [i for i in range(1, wall_row)]
      self.d_cols += [i for i in range(wall_col_start, length)]

      self.dead_zone_locs += [(0, i) for i in range(length)]
      self.life_gate_loc.append((random.randint(1, length - 2), 0))

      self.player_row = random.randint(int(self.length/2), length - 1)
      self.player_col = -1

    self.dying_rooms = []
    for i in self.d_rows:
      for j in self.d_cols:
        self.dying_rooms.append((i, j))

    self.dead_rooms = self.dead_zone_locs

    self.life_rooms = self.life_gate_loc

    # Set a flag to prevent the custom mechanic from repeatedly triggering itself.
    self.custom_code = "Fate-is-intervening is a truth state that varies. Fate-is-intervening is false."


  def make_game(self, game_name = 'lifegate_base', print_layout = False):
    taken_names, actual_rooms, M = self.generate_rooms(GameMaker())

    # Frozen set for easier wall checking:
    wall_set = {frozenset([a, b]) for a, b in self.walls}
    print(wall_set)

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
                    except:
                      failed_connections += 1

    # Randomly set the player somewhere in the left corner (hard coded for now until we get stuff working)
    M.set_player(actual_rooms[self.player_row][self.player_col])
    print(f'Player set in room {actual_rooms[self.player_row][self.player_col].name}')

    M.compile(path = "./" + game_name, custom_code = self.custom_code)
    self.generate_room_dict(taken_names, game_name)
    if print_layout:
      self.pretty_print_map(taken_names)

  def pretty_print_map(self, taken_names):
    # Step 1: Find max length for padding
    max_length = max(len(name) for name in taken_names) + 3

    # Step 2: Format names and organize into grid
    named_rooms_formatted = []
    named_rooms_formatted_unpadded = []
    rows = []
    raw_rows = []
    for room in taken_names:
        padded_name = room.ljust(max_length)
        rows.append(padded_name)
        raw_rows.append(room)
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
    for i in range(self.length):
      room_rows = []
      for j in range(self.length):
        room_name, taken_names = self.get_room_name(taken_names)
        # room = GameMaker.new_room("<< " + room_name + " >>")
        room = GameMaker.new_room(room_name, i7_custom_code = "")

        # Get the room identifier and see if this works for inform7
        # room_name = room.id
        if (i, j) in self.dying_rooms:
          room_mechanic = f"""
Instead of doing something when the player is in the {room.id} and fate-is-intervening is false:
    let N be a random number from 1 to 100;
    if N > 40:
        now fate-is-intervening is true;
        try going {self.death_gate_dir};
        now fate-is-intervening is false;
        stop the action;
    otherwise:
        now fate-is-intervening is true;
        try looking;
        now fate-is-intervening is false;
        stop the action;"""
        elif (i, j) in self.dead_rooms:
          room_mechanic = f"""
Before an actor doing something when the actor is the player and the player is in the {room.id}:
    end the story finally; [Lose]"""
        elif (i, j) in self.life_rooms:
          room_mechanic = f"""
Before an actor doing something when the actor is the player and the player is in the {room.id}:
    end the story finally; [Win]"""
        else:
          room_mechanic = f"""
Instead of doing something when the player is in the {room.id} and fate-is-intervening is false:
    let N be a random number from 1 to 100;
    if N > 70: 
        now fate-is-intervening is true;
        try going {self.death_gate_dir};
        now fate-is-intervening is false;
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

