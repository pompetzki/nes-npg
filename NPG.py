import numpy as np
import gym
import matplotlib.pyplot as plt
from Policies import SoftmaxPolicy
import Features

#######################################
# NPG using Softmax Policy
#######################################


class NPG:
    # Define training setup
    # --------------------------------
    # gamma is the discount factor.
    # lambda is the bias-variance tradeoff for the advantage function.
    # T is the max number of steps in a single run of the simulation.
    # K is the number of episodes for training the algorithm.
    # delta is the normalized step size of the parameter update.

    def __init__(self, env, policy, episodes, features):
        np.random.seed(1)
        self.env = env
        self.policy = policy
        self.__n_Actions = env.action_space.n
        self.__K = episodes
        self.__lambda = 0.95
        self.__gamma = 0.98
        self.__delta = 0.00025
        self.__eps = np.finfo(np.float32).eps.item()
        self.W = np.random.rand(4, 2)
        self.feature = features

    def train(self):
        rewards_per_episode = []
        for i_episode in range(self.__K):
            print("Episode ", i_episode, ":")
            log_gradients = []  # [[], []]
            rewards = []

            state = self.env.reset()
            state = state[None, :]
            # state = self.feature.featurize_state(state)
            self.env.seed(0)
            while(True):
                # self.env.render()

                old_state = state

                prob = self.policy.get_action_prob(state, self.W)
                action = np.random.choice(self.__n_Actions, p=prob[0])
                state, reward, done, _ = self.env.step(action)
                state = state[None, :]
                # state = self.feature.featurize_state(state)

                p_grad = self.policy.get_p_grad(old_state, self.W)[action, :]
                log_grad = p_grad / prob[0, action]
                log_grad = np.dot(old_state.T, log_grad[None, :])

                # for i in range(self.__n_Actions):
                    # log_gradients[i].append(log_grad[:, i])
                log_gradients.append(log_grad.reshape((8, 1), order='F'))
                rewards.append(reward)

                if done:
                    print("Trial finished after {} timesteps."
                          .format(np.sum(rewards)))
                    break
            self.__update_parameters(log_gradients, rewards)
            # print(self.W)
            rewards_per_episode.append(np.sum(rewards))

        return self.W, rewards_per_episode

    def __update_parameters(self, log_gradients, rewards):
        for n in range(1):  # self.__n_Actions):
            g = self.__compute_gradient(log_gradients, rewards)
            fisher = self.__compute_fisher(log_gradients)
            try:
                inv_fisher = np.linalg.inv(fisher)
                nominator = (g.T @ inv_fisher) @ g
                if nominator <= 0:
                    print("Nominator <= 0: ", nominator)
                else:
                    learning_rate = np.sqrt(self.__delta/nominator)
                    step = np.multiply(learning_rate, (inv_fisher @ g))

                    c = np.dot(step.T, fisher)
                    c = np.dot(c, step)
                    if c > (self.__delta*(1 + 0.0001)):
                        print("condition: ", c, " > ", self.__delta)
                    else:
                        self.W += step.reshape((4, 2), order='F')
            except np.linalg.LinAlgError:
                print("Skipping parameter update due to singular matrix.")
                pass
        return

    def __compute_gradient(self, log_g, rewards):
        g = 0
        advantage = np.zeros(len(log_g))
        for i in range(len(log_g)):
            advantage[i] = sum([r * (self.__gamma ** t) for t, r in
                                enumerate(rewards[i:])])
        advantage = (advantage - np.mean(advantage)) / (np.std(advantage) +
                                                        self.__eps)
        for i in range(len(log_g)):
            g += log_g[i] * advantage[i]

        return g/len(log_g)

    def __compute_fisher(self, log_g):
        f = sum([(lg.reshape(-1, 1) @ lg.reshape(-1, 1).T) for lg in log_g])
        f = np.diagonal(f)[None, :]
        f = np.diagflat(f)
        return f/len(log_g)
