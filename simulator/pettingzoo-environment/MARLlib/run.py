import unittest
from marllib import marl
import torch


class Test(unittest.TestCase):
    # def test_mpe(self):
    #     # discrete control
    #     env = marl.make_env(environment_name="mpe", map_name="simple_spread", force_coop=True)
    #     algo = marl.algos.hatrpo(hyperparam_source="test")
    #     model = marl.build_model(env, algo, {"core_arch": "mlp", "encode_layer": "8-8"})
    #     algo.fit(env, model, stop={"training_iteration": 5000}, local_mode=True, num_gpus=0,
    #              num_workers=2, share_policy="individual", checkpoint_end=False)

    def test_procon(self):
        env = marl.make_env(environment_name="procon_2023_uet", map_name="map2")
        algo = marl.algos.ippo(hyperparam_source="test")
        model = marl.build_model(env, algo, {"core_arch": "mlp"})
        algo.fit(env, model, stop={"training_iteration": 100000}, local_mode=True, num_gpus=1,
                 num_workers=5, share_policy="group", checkpoint_end=False)

    # def test_magent(self):
    #     env = marl.make_env(environment_name="magent", map_name="battlefield")
    #     algo = marl.algos.mappo(hyperparam_source="test")
    #     model = marl.build_model(env, algo, {"core_arch": "mlp"})
    #     algo.fit(env, model, stop={"training_iteration": 500}, local_mode=True, num_gpus=0,
    #              num_workers=2, share_policy="group", checkpoint_end=False)


if __name__ == '__main__':
    Test().test_procon()