import textworld
import textworld.gym
from lifegate import LifeGateBuilder

game_name = 'lifegate_base_inform7'
death_gate_dir = 'north'
lifegate_builder = LifeGateBuilder(wall_row = 2,
                                   wall_width = 4,
                                   wall_col_start = 3,
                                   death_gate_dir = death_gate_dir,
                                   life_gate_dir = 'east')
lifegate_builder.make_game(game_name, True)


request_infos = textworld.EnvInfos(description=True, inventory=True, location = True, possible_admissible_commands = True, typed_entities = True, admissible_commands = True)

env_id = textworld.gym.register_game("./" + game_name + ".ulx",
                                    request_infos = request_infos)
env = textworld.gym.make(env_id)
env.close()
env = textworld.gym.make(env_id)
obs, infos = env.reset() 

print("GAME START:\n")
print(obs)
score, moves, done = 0, 0, False
testing = True
total_score = 0
if testing:
  acts = ['go east','go east','go east','go east','go east','go east','go east','go east']
  acts = ['go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west', 'go west']
  # acts = ['go north', 'go north', 'go north', 'go north', 'go north', 'go north', 'go north']
  for act in acts:
      obs, score, done, infos = env.step(act)
      print(obs)
      print(infos['admissible_commands'])
      print("\n___\n")
      total_score += score
      if done:
        print(f'Done, last move: {act}, final score: {total_score}')
        break
      moves += 1
else:
  while not done:
    command = input("> ")
    if "exit" in command.lower() or 'quit' in command.lower():
      env.close()
      break
    obs, score, done, truncated, infos = env.step(command)
    total_score += score
    if done:
        print(f'Done, last move: {act}, final score: {total_score}')
        break
    print(obs)
    print(infos['admissible_commands'])
    moves += 1

