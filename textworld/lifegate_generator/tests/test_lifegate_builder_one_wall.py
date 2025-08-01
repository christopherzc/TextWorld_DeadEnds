import textworld
import textworld.gym
import random
from textworld.lifegate_generator.lifegatev2 import LifeGateBuilder
from textworld.generator import World, Quest, Event

# For determining the position of the dying zone:
reverse_directions = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east"
}

def test_basic_lifegate(game_name = "", life_direction = "east", death_direction = "north", wall_coordinates = [(3, 2), (3, 5)]):
   base_folder = "/mnt/weka/home/christopher.cui/TextWorld_DeadEnds/"
   death_gate_dir = death_direction
   lifegate_builder = LifeGateBuilder(wall_coordinates = wall_coordinates,
                                    death_gate_dir = death_gate_dir,
                                    life_gate_dir = life_direction,
                                    base_folder = base_folder,
                                    quests=[])

   base_folder, formatted_game_name = lifegate_builder.make_game(game_name, True)
   request_infos = textworld.EnvInfos(description=True, inventory=True, location = True, 
                                      possible_admissible_commands = True, typed_entities = True, 
                                      admissible_commands = True,
                                      won = True, lost = True)
   testing_steps = 2000
   env_id = textworld.gym.register_game(base_folder + formatted_game_name + ".z8", 
                                        max_episode_steps = testing_steps,
                                        request_infos = request_infos)
   
   env = textworld.gym.make(env_id)

   # Test win condition
   obs, infos = env.reset() 

   score, moves, done = 0, 0, False
   total_score = 0
   actions = []
   for i in range(testing_steps):
      if i % 6 == 0 or i > 500:
         # Move towards goal
         action = 'go ' + life_direction
      elif i < 1000:
         # Move away from death wall
         action = 'go ' + reverse_directions[death_direction]
      else:
         # Only reason agent shouldn't have found lifegate by now is if it is between them and the death wall
         action = 'go ' + death_direction
      actions.append(action)
      obs, score, done, infos = env.step(action)
      total_score += score
      if done:
         print(f"Infos lost: {infos['lost']}, won: {infos['won']}")
         print(f'Done testing win conditions, last move: {action}, final score: {total_score}')
         if total_score != 1:
            f"Game should have (99.99%) been won. Check configuration life gate {life_direction}, death gate {death_direction}"
         break
      moves += 1

   env.close()

   # Test loss condition

   env = textworld.gym.make(env_id)

   obs, infos = env.reset() 

   score, moves, done = 0, 0, False
   total_score = 0
   directions = list(reverse_directions.keys())
   directions.remove(life_direction)
   for i in range(200):
      # Randomly move away from the life gate
      action = 'go ' + random.choice(directions)
      obs, score, done, infos = env.step(action)

      total_score += score
      if done:
        print(f'Done testing loss conditions last move: {action}, final score: {total_score}')
        print(f"Infos lost: {infos['lost']}, won: {infos['won']}")
        if infos['lost'] != True:
           f"Game should have (99.99%) been lost. Check configuration life gate {life_direction}, death gate {death_direction}"
        break
      moves += 1

   env.close()


test_basic_lifegate(game_name = 'lifegate_oned_no_drift', life_direction = "north", death_direction = "east", 
                    wall_coordinates = [(3, 2), (3, 5)])

test_basic_lifegate(game_name = 'lifegate_oned_no_drift', life_direction = "north", death_direction = "east", 
                    wall_coordinates = [(4, 2), (4, 5)])

test_basic_lifegate(game_name = 'lifegate_oned_no_drift', life_direction = "north", death_direction = "east", 
                    wall_coordinates = [(2, 3), (2, 5)])

test_basic_lifegate(game_name = 'lifegate_oned_no_drift', life_direction = "north", death_direction = "east", 
                    wall_coordinates = [(2, 5), (4, 5)])

test_basic_lifegate(game_name = 'lifegate_oned_no_drift', life_direction = "north", death_direction = "east", 
                    wall_coordinates = [(2, 2), (6, 2)])

