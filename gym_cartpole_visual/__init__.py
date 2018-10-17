from gym.envs.registration import register

register(
    id='cartpole-visual-v1',
    entry_point='gym_cartpole_visual.envs:CartPoleVisualEnv',
)
# register(
#     id='cartpole-visual-extrahard-v1',
#     entry_point='gym_cartpole_visual.envs:CartpoleVisualExtraHardEnv',
# )