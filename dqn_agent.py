# dqn_tf_agent.py

import os
import json
from distutils.command.config import config

import numpy as np
import tensorflow as tf
from replay_buffer import ReplayBuffer


class DQNAgentTF:
    def __init__(
        self,
        configs,
    ):

        # state_dim: int,
        # action_dim: int ,
        # gamma: float = 0.99,
        # lr: float = 1e-3,
        # buffer_capacity: int = 100_000,
        # batch_size: int = 128,
        # epsilon_start: float = 1.0,
        # epsilon_end: float = 0.05,
        # epsilon_decay_steps: int = 50_000,
        # target_update_freq: int = 1_000,
        self.state_dim = configs.state_dim
        self.action_dim = configs.action_dim
        self.gamma = configs.gamma
        self.batch_size = configs.batch_size

        # main and target networks
        self.model = self._build_model(configs.state_dim, configs.action_dim, configs.lr)
        self.target_model = self._build_model(configs.state_dim, configs.action_dim, configs.lr)
        self.target_model.set_weights(self.model.get_weights())

        self.replay_buffer = ReplayBuffer(configs.buffer_capacity)

        # epsilon-greedy
        self.epsilon = configs.epsilon_start
        self.epsilon_start = configs.epsilon_start
        self.epsilon_end = configs.epsilon_end
        self.epsilon_decay_steps = configs.epsilon_decay_steps
        self.total_steps = 0

        self.target_update_freq = configs.target_update_freq

    # ----------------- model -----------------

    def _build_model(self, state_dim: int, action_dim: int, lr: float):
        inputs = tf.keras.Input(shape=(state_dim,))
        x = tf.keras.layers.Dense(64, activation="relu")(inputs)
        x = tf.keras.layers.Dense(64, activation="relu")(x)
        outputs = tf.keras.layers.Dense(action_dim, activation=None)(x)
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
            loss="mse",
        )
        return model

    # ----------------- policy -----------------

    def select_action(self, state):
        """
        state: list/np.array shape (state_dim,)
        returns: action int in [0, action_dim-1]
        """
        self.total_steps += 1

        # epsilon linear decay
        frac = min(1.0, self.total_steps / float(self.epsilon_decay_steps))
        self.epsilon = self.epsilon_start + frac * (self.epsilon_end - self.epsilon_start)

        if np.random.rand() < self.epsilon:
            return np.random.randint(self.action_dim)

        state_arr = np.array(state, dtype=np.float32)[None, :]  # shape (1, state_dim)
        q_values = self.model.predict(state_arr, verbose=0)[0]
        return int(np.argmax(q_values))

    # ----------------- memory -----------------

    def store_transition(self, state, action, reward, next_state, done):
        self.replay_buffer.push(state, action, reward, next_state, done)

    # ----------------- training -----------------

    def train_step(self):
        if len(self.replay_buffer) < self.batch_size:
            return  # not enough data

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(
            self.batch_size
        )

        # Q(s, a)
        q_values = self.model.predict(states, verbose=0)

        # Q_target(s', a')
        next_q_values = self.target_model.predict(next_states, verbose=0)
        max_next_q = np.max(next_q_values, axis=1)

        # build target Q
        target_q = np.copy(q_values)
        for i in range(self.batch_size):
            if dones[i]:
                target_q[i, actions[i]] = rewards[i]
            else:
                target_q[i, actions[i]] = rewards[i] + self.gamma * max_next_q[i]

        # one gradient step
        self.model.train_on_batch(states, target_q)

        # update target network
        if self.total_steps % self.target_update_freq == 0:
            self.target_model.set_weights(self.model.get_weights())

    # ----------------- save / load -----------------

    def save(self, directory: str):
        os.makedirs(directory, exist_ok=True)
        # weights
        self.model.save_weights(os.path.join(directory, "q_net_weights.weights.h5"))
        self.target_model.save_weights(os.path.join(directory, "target_q_net_weights.weights.h5"))

        # meta (epsilon, steps)
        meta = {
            "epsilon": float(self.epsilon),
            "total_steps": int(self.total_steps),
            "state_dim": int(self.state_dim),
            "action_dim": int(self.action_dim),
        }
        with open(os.path.join(directory, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, directory: str):
        # load meta (optional but recommended)
        meta_path = os.path.join(directory, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            self.epsilon = meta.get("epsilon", self.epsilon)
            self.total_steps = meta.get("total_steps", self.total_steps)

        # weights
        q_path = os.path.join(directory, "q_net_weights.h5")
        target_path = os.path.join(directory, "target_q_net_weights.h5")
        if os.path.exists(q_path):
            self.model.load_weights(q_path)
        if os.path.exists(target_path):
            self.target_model.load_weights(target_path)