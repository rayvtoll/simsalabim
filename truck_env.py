from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np

from sim_manager import SimManager


class TruckEnv(Env):
    def __init__(self):
        self.action_space = Discrete(100)
        self.observation_space = Box(low=-3, high=250, shape=(1,), dtype=np.float64)
        self.state = 0
        self.done = False
        self.running = False
        self.sim_env = SimManager(3, 10000)

    def step(self, action):
        # print(action)
        wait_time = self.sim_env.run_sim(action)

        done = True
        info = {}
        if wait_time > 70 and wait_time < 80:
            reward = 1

        else:
            reward = -1

        return np.float32(self.state), reward, done, False, info

    def render(self):
        """TODO Add a nested comment explaining why this method is empty, or complete the implementation"""
        pass

    def reset(self, seed=None):
        super().reset(seed=seed)
        # Reset the simmulation enviroment
        self.sim_env.reset_shedual()
        # Get a local copy of the schedule
        schedule = self.sim_env.shedual.trucks

        battery = []
        arriaval_time = []
        # Extract the data from the schedule
        for i in schedule:
            battery.append(i.Battery)
            arriaval_time.append(i.Arrival_Time)
        self.state = 100
        info = {}
        return np.float32(self.state), info
