import functools
import numpy as np
from gym.spaces import Discrete, Box
from pettingzoo.utils.env import AECEnv
from pettingzoo.utils import agent_selector, wrappers
import game
from entities.utils.enums import Team


def env(map_path: str, render_mode=None):
    internal_render_mode = render_mode if render_mode != "ansi" else "human"
    myenv = raw_env(map_path=map_path, render_mode=internal_render_mode)
    # myenv = wrappers.TerminateIllegalWrapper(myenv, illegal_reward=-1)
    myenv = wrappers.AssertOutOfBoundsWrapper(myenv)
    myenv = wrappers.OrderEnforcingWrapper(myenv)
    return myenv


class raw_env(AECEnv):
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 2,
        "name": "go_v5"
    }

    def __init__(self, map_path, render_mode=None):
        super().__init__()

        self.game = game.Game(map_path)
        self.map_path = map_path
        self.map_width = self.game.current_state.map.width
        self.map_height = self.game.current_state.map.height
        self.render_mode = render_mode
        self.possible_agents = [
            *("team1_craftsman" + str(i+1) for i in range(self.game.current_state.team1_craftsman_count())),
            *("team2_craftsman" + str(i+1) for i in range(self.game.current_state.team2_craftsman_count()))
        ]

        self.action_spaces = {agent: Discrete(17) for agent in self.possible_agents}
        self.observation_spaces = {agent: Box(low=0, high=1, shape=(self.map_height* self.map_width* 12,), dtype=bool)
                                   for agent in self.possible_agents}

    def observe(self, agent: str) -> np.ndarray:
        return self.game.gym_observable_space

    def step(self, action):
        current_agent = self.agent_selection
        if self.dones[current_agent]:
            return self._was_done_step(action)

        if self.game.is_game_over:
            self.dones = {agent: True for agent in self.agents}
            winning_team = self.game.winning_team
            print("winning team:", winning_team)
            score_difference = abs(self.game.score_difference)
            if winning_team == Team.TEAM1:
                # agents whose name starts with "team1" are in team 1
                # get reward 1 and others get reward -1
                self.rewards = {agent: 1+score_difference if agent.startswith("team1") else -2-score_difference for agent in self.agents}
            elif winning_team == Team.TEAM2:
                self.rewards = {agent: 1+score_difference if agent.startswith("team2") else -2-score_difference for agent in self.agents}
            else:
                self.rewards = {agent: 0 for agent in self.agents}
        else:
            self.game.gym_add_command(current_agent, action)

        # When the agent is the last agent of the team, process the turn and switch to the next team
        next_agent = self._agent_selector.agent_order[(self._agent_selector._current_agent + 1) % len(self._agent_selector.agent_order)]
        if current_agent.startswith("team1") and next_agent.startswith("team2"):
            self.game.process_turn()
        elif current_agent.startswith("team2") and next_agent.startswith("team1"):
            self.game.process_turn()

        self.agent_selection = self._agent_selector.next()
        # Adds .rewards to ._cumulative_rewards
        self._accumulate_rewards()

        if self.render_mode == "human":
            self.render()

    def reset(self, seed=None, options=None):
        # Reset the game by loading the map again
        self.game.load_map(self.map_path)

        self.agents = self.possible_agents[:]
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.dones = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.next()

    def render(self, mode="human"):
        pass

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.action_spaces[agent]