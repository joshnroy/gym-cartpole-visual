# -*- coding: utf-8 -*-
"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/sutton/book/code/pole.c
permalink: https://perma.cc/C9ZM-652R
"""

import math
import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
import sys
from random import randrange
import matplotlib.pyplot as plt

class CartPoleVisualEnv(gym.Env):
    """
    Description:
        A pole is attached by an un-actuated joint to a cart, which moves along a frictionless track. The pendulum starts upright, and the goal is to prevent it from falling over by increasing and reducing the cart's velocity.
    Source:
        This environment corresponds to the version of the cart-pole problem described by Barto, Sutton, and Anderson
    Observation:
        Type: Image that is the rendered version of the environment

    Actions:
        Type: Discrete(2)
        Num	Action
        0	Push cart to the left
        1	Push cart to the right

        Note: The amount the velocity is reduced or increased is not fixed as it depends on the angle the pole is pointing. This is because the center of gravity of the pole increases the amount of energy needed to move the cart underneath it
    Reward:
        Reward is 1 for every step taken, including the termination step
    Starting State:
        All observations are assigned a uniform random value between ±0.05
    Episode Termination:
        Pole Angle is more than ±12°
        Cart Position is more than ±2.4 (center of the cart reaches the edge of the display)
        Episode length is greater than 200
        Solved Requirements
        Considered solved when the average reward is greater than or equal to 195.0 over 100 consecutive trials.
    """

    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second' : 50
    }

    def __init__(self, num_levels, start_level):
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = (self.masspole + self.masscart)
        self.polelength = 5# 0.5 # actually half the pole's length
        self.polewidth = 5
        self.cartwidth = 20
        self.cartheight = 10
        self.polemass_length = (self.masspole * self.polelength)
        self.force_mag = 10.
        self.tau = 0.02  # seconds between state updates
        self.kinematics_integrator = 'euler'
        self.polecolor = np.array([0., 0., 1.])
        self.cartcolor = np.array([1., 1., 0.])
        self.axlecolor = np.array([1., 0., 1.])
        self.trackcolor = np.array([0., 1., 1.])
        self.backgroundcolor = np.array([1., 1., 1.])

        # Angle at which to fail the episode
        self.theta_threshold_radians = 12 * 2 * math.pi / 360
        self.x_threshold = 2.4

        self.offset = start_level

        # Angle limit set to 2 * theta_threshold_radians so failing observation is still within bounds
        high = np.array([
            self.x_threshold * 2,
            np.finfo(np.float32).max,
            self.theta_threshold_radians * 2,
            np.finfo(np.float32).max])

        self.action_space = spaces.Discrete(2)
        # self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8)

        self.num_levels = num_levels
        if self.num_levels == 0:
            self.seed = self.seed_set(randrange(2**32))
        else:
            to_set = self.offset
            self.seed = self.seed_set(to_set)
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

    def seed_set(self, seed=None):
        # if seed is not None:
        #     np.random.seed(seed)
        self.np_random, seed = seeding.np_random(seed)
        return seed

    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        state = self.state
        x, x_dot, theta, theta_dot = state
        force = self.force_mag if action==1 else -self.force_mag
        costheta = math.cos(theta)
        sintheta = math.sin(theta)
        temp = (force + self.polemass_length * theta_dot * theta_dot * sintheta) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta* temp) / (self.polelength * (4.0/3.0 - self.masspole * costheta * costheta / self.total_mass))
        xacc  = temp - self.polemass_length * thetaacc * costheta / self.total_mass
        if self.kinematics_integrator == 'euler':
            x  = x + self.tau * x_dot
            x_dot = x_dot + self.tau * xacc
            theta = theta + self.tau * theta_dot
            theta_dot = theta_dot + self.tau * thetaacc
        else: # semi-implicit euler
            x_dot = x_dot + self.tau * xacc
            x  = x + self.tau * x_dot
            theta_dot = theta_dot + self.tau * thetaacc
            theta = theta + self.tau * theta_dot
        self.state = (x,x_dot,theta,theta_dot)
        done =  x < -self.x_threshold \
                or x > self.x_threshold \
                or theta < -self.theta_threshold_radians \
                or theta > self.theta_threshold_radians
        done = bool(done)

        if not done:
            reward = 1.0
        elif self.steps_beyond_done is None:
            # Pole just fell!
            self.steps_beyond_done = 0
            reward = 1.0
        else:
            if self.steps_beyond_done == 0:
                logger.warn("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True' -- any further steps are undefined behavior.")
            self.steps_beyond_done += 1
            reward = 0.0

        img = self.render().astype(np.uint8)
        # return (img.astype(np.float32), np.asarray([self.state[1], self.state[3]]).astype(np.float32)), reward, done, {"level_seed": self.seed}
        done = np.int64(done).astype(np.int32)
        dic = {"level_seed": np.int32(self.seed)}
        return img, reward, done, dic

    def reset(self):
        if self.num_levels == 0:
            self.seed = self.seed_set(randrange(2**32))
        else:
            self.seed = self.seed_set(self.offset)
        # self.state = np.random.uniform(low=-0.05, high=0.05, size=(4,))
        self.state = np.random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        img = self.render().astype(np.uint8)
        self.change_color()
        img = self.render().astype(np.uint8)
        # if self.seed == 0:
        #     plt.imshow(img)
        #     plt.savefig("seed0.png")
        # elif self.seed == 1:
        #     plt.imshow(img)
        #     plt.savefig("seed1.png")

        # return {"rgb": img.astype(np.float32), "vel": np.asarray([self.state[1], self.state[3]]).astype(np.float32)}
        return img

    def change_color(self):
        self.polecolor = np.clip(self.np_random.normal(0.5, 0.5, 3), 0., 1.)
        self.cartcolor = np.clip(self.np_random.normal(0.5, 0.5, 3), 0., 1.)
        self.axlecolor = np.clip(self.np_random.normal(0.5, 0.5, 3), 0., 1.)
        self.trackcolor = np.clip(self.np_random.normal(0.5, 0.5, 3), 0., 1.)
        self.backgroundcolor = np.clip(self.np_random.normal(0.5, 0.5, 3), 0., 1.)

        self.pole.set_color(self.polecolor[0], self.polecolor[1], self.polecolor[2])
        self.axle.set_color(self.axlecolor[0], self.axlecolor[1], self.axlecolor[2])
        self.cart.set_color(self.cartcolor[0], self.cartcolor[1], self.cartcolor[2])
        self.track.set_color(self.trackcolor[0], self.trackcolor[1], self.trackcolor[2])
        self.background.set_color(self.backgroundcolor[0], self.backgroundcolor[1], self.backgroundcolor[2])

    def render(self, mode='rgb'):
        screen_width = 64
        screen_height = 64

        world_width = self.x_threshold*2
        scale = screen_width/world_width
        carty = 10 # TOP OF CART
        polewidth = self.polewidth # 10
        polelen = scale * 2 * self.polelength
        cartwidth = self.cartwidth # 50
        cartheight = self.cartheight # 30

        if self.viewer is None:
            from gym.envs.classic_control import rendering
            self.viewer = rendering.Viewer(screen_width, screen_height)
            self.background = rendering.FilledPolygon([(0,0), (0,64), (64,64), (64,0)])
            self.background.set_color(self.backgroundcolor[0], self.backgroundcolor[1], self.backgroundcolor[2])
            self.viewer.add_geom(self.background)
            l,r,t,b = -cartwidth/2, cartwidth/2, cartheight/2, -cartheight/2
            axleoffset =cartheight/4.0
            self.cart = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
            self.carttrans = rendering.Transform()
            self.cart.add_attr(self.carttrans)
            self.viewer.add_geom(self.cart)
            l,r,t,b = -polewidth/2,polewidth/2,polelen-polewidth/2,-polewidth/2
            self.pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
            self.pole.set_color(self.polecolor[0], self.polecolor[1],
                    self.polecolor[2])
            self.poletrans = rendering.Transform(translation=(0, axleoffset))
            self.pole.add_attr(self.poletrans)
            self.pole.add_attr(self.carttrans)
            self.viewer.add_geom(self.pole)
            self.axle = rendering.make_circle(polewidth/2)
            self.axle.add_attr(self.poletrans)
            self.axle.add_attr(self.carttrans)
            self.axle.set_color(self.axlecolor[0], self.axlecolor[1],
                    self.axlecolor[2])
            self.cart.set_color(self.cartcolor[0], self.cartcolor[1],
                    self.cartcolor[2])
            self.viewer.add_geom(self.axle)
            self.track = rendering.Line((0,carty), (screen_width,carty))
            self.track.set_color(self.trackcolor[0], self.trackcolor[1],
                    self.trackcolor[2])
            self.viewer.add_geom(self.track)

        if self.state is None: return None

        x = self.state
        cartx = x[0]*scale+screen_width/2.0 # MIDDLE OF CART
        self.carttrans.set_translation(cartx, carty)
        self.poletrans.set_rotation(-x[2])

        return self.viewer.render(return_rgb_array = True)

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None
