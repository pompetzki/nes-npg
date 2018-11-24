import numpy as np
import gym
import matplotlib.pyplot as plt

#######################################
# NPG using Softmax Policy
#######################################

env = gym.make('CartPole-v0')
env.seed(0)
np.random.seed(0)


class NPG:
    # Define training setup
    # --------------------------------
    # gamma is the discount factor.
    # lambda is the bias-variance tradeoff for the advantage function.
    # T is the max number of steps in a single run of the simulation.
    # K is the number of episodes for training the algorithm.
    # delta is the normalized step size of the parameter update.

    def __init__(self, env, policy, episodes):
        self.env = env
        self.policy = policy
        self.__n_Actions = env.action_space.n
        self.W = np.random.sample((4, self.__n_Actions))
        self.__K = episodes
        self.__lambda_ = 0.95
        self.__gamma_ = 0.98
        self.__delta = 0.0025
        self.__eps = np.finfo(np.float32).eps.item()

    def train(self):
        rewards_per_episode = []
        for i_episode in range(self.__K):

            log_gradients = []
            rewards = []

            state = self.env.reset()[None, :]
            self.env.seed(0)
            while(True):
                self.env.render()

                old_state = state
                prob = self.policy.get_action_prob(state, self.W)
                action = np.random.choice(self.__n_Actions, p=prob[0])

                state, reward, done, _ = self.env.step(action)
                state = state[None, :]

                p_grad = self.policy.get_p_grad(old_state, self.W)[action, :]
                log_grad = p_grad / prob[0, action]
                log_grad = np.dot(old_state.T, log_grad[None, :])

                log_gradients.append(log_grad)
                rewards.append(reward)

                if done:
                    print("Trial finished after {} timesteps."
                          .format(np.sum(rewards)))
                    break

            self.__update_parameters(log_gradients, rewards)
            rewards_per_episode.append(np.sum(rewards))

        return self.W, rewards_per_episode

    def __update_parameters(self, log_gradients, rewards):
        for i in range(len(log_gradients)):
            self.W += self.__delta * log_gradients[i] * sum(
                [r * (self.__gamma_ ** r) for t, r in enumerate(rewards[i:])])
        return


class SoftmaxPolicy:

    # Returns array of shape (1, n_actions) containing the probabilities
    # of each action.
    def get_action_prob(self, state, w):
        # state.shape = (1,n) // w.shape = (n, n_actions)
        x = np.dot(state, w)
        x = np.exp(x)
        return x/np.sum(x)

    # Returns the Jacobian matrix of the policy with respect to
    # the parameters w.
    def get_p_grad(self, state, w):
        prob = self.get_action_prob(state, w)
        prob = prob.reshape(-1, 1)
        return np.diagflat(prob) - np.dot(prob, prob.T)


def run_benchmark(policy, w):
    total_rewards = np.zeros(100)
    print("Starting Benchmark:")
    print("-------------------")
    for i_episode in range(100):
        print("Episode {}:".format(i_episode+1))

        observation = env.reset()
        for t in range(200):
            env.render()
            probs = policy.get_action_prob(observation[None, :], w)
            action = np.argmax(probs)
            observation, reward, done, info = env.step(action)
            total_rewards[i_episode] += reward
            if done:
                print("Reward reached: ", total_rewards[i_episode])
                print("Episode finished after {} timesteps.".format(t + 1))
                break
    average = np.sum(total_rewards)/100
    print("Average Reward: ", average)
    if average >= 195:
        return True
    else:
        return False


policy = SoftmaxPolicy()
algorithm = NPG(env, policy, 200)
w, r = algorithm.train()
plt.plot(np.arange(len(r)), r)
plt.show()
passed = run_benchmark(policy, w)
print(passed)
env.close()
