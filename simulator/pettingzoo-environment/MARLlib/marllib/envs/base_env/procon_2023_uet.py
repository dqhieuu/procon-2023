from ray.rllib.env.multi_agent_env import MultiAgentEnv
from gym.spaces import Dict as GymDict, Discrete, Box
import supersuit as ss
from ray.rllib.env import PettingZooEnv
import time
from procon_env import procon2023_uet


REGISTRY = {
    "map2": procon2023_uet.env
}

policy_mapping_dict = {
    "map2": {
        "description": "two teams compete to achieve the highest score",
        "team_prefix": ("team1_", "team2_"),
        "all_agents_one_policy": False,
        "one_agent_one_policy": False,
    },
}

# import numpy
# numpy.set_printoptions(threshold=9999999)

class RLlibProcon2023Uet(MultiAgentEnv):
    def __init__(self, env_config):
        map = env_config["map_name"]
        env_config.pop("map_name", None)
        env = REGISTRY[map]("../../assets/{}.txt".format(map), **env_config)

        # keep obs and action dim same across agents
        # pad_action_space_v0 will auto mask the padding actions
        env = ss.pad_observations_v0(env)
        env = ss.pad_action_space_v0(env)

        self.env = PettingZooEnv(env)
        self.action_space = self.env.action_space
        self.observation_space = GymDict({"obs": self.env.observation_space, "state": self.env.observation_space})
        self.agents = self.env.agents
        self.num_agents = len(self.agents)
        env_config["map_name"] = map
        self.env_config = env_config

    def reset(self):
        ready_agent_obs_dict = self.env.reset()
        obs = {}
        for agent in ready_agent_obs_dict.keys():
            obs[agent] = {"obs": ready_agent_obs_dict[agent], "state": ready_agent_obs_dict[agent]}
        return obs

    def step(self, action_dict):
        o, r, d, info = self.env.step(action_dict)
        rewards = {}
        obs = {}
        for key in o.keys():
            rewards[key] = r[key]
            obs[key] = {
                "obs": o[key],
                "state": o[key],
            }
        dones = {"__all__": d["__all__"]}
        return obs, rewards, dones, info

    def close(self):
        self.env.close()

    def render(self, mode=None):
        self.env.render()
        time.sleep(0.05)
        return True

    def get_env_info(self):
        env_info = {
            "space_obs": self.observation_space,
            "space_act": self.action_space,
            "num_agents": self.num_agents,
            "episode_limit": 100,
            "policy_mapping_info": policy_mapping_dict
        }
        return env_info
