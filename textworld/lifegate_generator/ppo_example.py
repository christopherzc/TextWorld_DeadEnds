# pip install stable-baselines3 gymnasium==0.29 textworld

import gymnasium as gym, numpy as np, textworld, textworld.gym
from lifegate import LifeGateBuilder
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor 
import wandb
from wandb.integration.sb3 import WandbCallback

TOTAL_STEPS = 1000000
wandb.login(key="7ac5fa575c2f9092fe38d20f0e5f957408ecee38")  # ensure you have logged in to Weights & Biases

# Launch a new run
wandb.init(
    project="lifegate-ppo",
    entity="pearls-lab",
    sync_tensorboard=True,         # auto‐sync SB3’s tensorboard logs
    config={
        "total_timesteps": TOTAL_STEPS,
        "max_steps_per_episode": 50,
        # add any hyperparams you care about here
    }
)

# ------------ build / register game
gname = "lifegate_base_inform7"
death_gate_dir = 'north'
lifegate_builder = LifeGateBuilder(wall_row = 2,
                                   wall_width = 4,
                                   wall_col_start = 3,
                                   death_gate_dir = death_gate_dir,
                                   life_gate_dir = 'east')
lifegate_builder.make_game(gname, True)
eid = textworld.gym.register_game(f"./{gname}.ulx",
                                  request_infos=textworld.EnvInfos(description=True, won=True, lost=True))
base_env = textworld.gym.make(eid)
GO_CMDS = ["go north", "go south", "go east", "go west"]
# ------------ adapters ------------------------------------------------------
class TWtoGymnasium(gym.Env):
    def __init__(self, env):
        self.env = env
        self.action_space      = gym.spaces.Discrete(len(GO_CMDS))
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(1,), dtype=np.uint8)
    @property
    def unwrapped(self): return self
    def reset(self, *, seed=None, options=None):
        return self.env.reset() , {}
    def step(self, a):
        obs, r, done, info = self.env.step(a)
        return obs, r, done, False, info

class FixedTW(gym.Wrapper):
    def __init__(self, env, max_len=256):
        super().__init__(env)
        self.max_len = max_len
        self.action_space      = gym.spaces.Discrete(len(GO_CMDS))
        self.observation_space = gym.spaces.Box(0,255,(max_len,),np.uint8)
        self.steps = 0
        self.MAX_STEPS = 50
    def _vec(self, txt):
        b = txt.encode("ascii","ignore")[:self.max_len]
        arr = np.zeros(self.max_len,np.uint8); arr[:len(b)] = np.frombuffer(b,np.uint8)
        return arr
    def reset(self, **kw):
        obs, _ = self.env.reset(**kw)
        self.steps = 0
        return self._vec(obs[0]), {}
    def step(self, a):
        obs, r, done, trunc, info = self.env.step(GO_CMDS[a])
        self.steps += 1
        # ---------- custom reward shaping -----------------  ### NEW
        if done:  
            if info.get("won", False):
                r = +1.0             # reached a life-gate
            elif info.get("lost", False):
                r = -1.0             # fell into a death-gate

        # ---------- hard step limit ------------------------  ### NEW
        if not done and self.steps >= self.MAX_STEPS:
            trunc = True             # gymnasium’s “time limit” flag
            done  = True
            # optional: give a small penalty for timing out
            # r -= 0.1
        return self._vec(obs), r, done, trunc, info

vec_env = DummyVecEnv([
    lambda: Monitor(FixedTW(TWtoGymnasium(base_env)))
])

# ------------ train & demo ---------------------------------------------------
model = PPO(
    "MlpPolicy",
    vec_env,
    verbose=1,
    tensorboard_log="./tb_logs/"      # needed for sync_tensorboard=True
)

model.learn(
    total_timesteps=TOTAL_STEPS,
    log_interval=1,
    callback=WandbCallback(
        model_save_path="./models/",  # optional: checkpoint your model
        verbose=2
    )
)

obs = vec_env.reset(); done = False
while not done:
    act, _ = model.predict(obs, deterministic=True)
    obs, rew, done, _, _ = vec_env.step(act)
print("Episode finished, last reward =", rew)
