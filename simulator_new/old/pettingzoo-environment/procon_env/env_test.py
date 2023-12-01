from pettingzoo.test import api_test
from procon2023_uet import env

procon_env = env('../../assets/map2.txt', render_mode='human')
api_test(procon_env, num_cycles=1000, verbose_progress=True)