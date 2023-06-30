import functools

from pettingzoo.utils.env import AECEnv


class CustomEnvironment(AECEnv):
    metadata = {
        "name": "custom_environment_v0",
    }

    def __init__(self):
        pass

    def step(self, actions):
        pass

    def reset(self, seed=None, options=None):
        pass



    def render(self):
        pass

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.action_spaces[agent]