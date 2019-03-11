from nes import *
from utilities.environment import Environment
from models.nn_policy import Policy
from agent import Agent
import pickle
import torch as tr

#######################################
# Environment
#######################################


def main(load: bool = False, train: bool = False, benchmark: bool = False,
         save: bool = False, render: bool = True):
    """ set seed """
    np.random.seed(0)
    tr.manual_seed(0)

    """ define the environment """
    gym_env = 'Qube-v0'
    env = Environment(gym_env)
    print("{:=^50s}".format(' Start {} '.format(gym_env)))

    if load:
        """ load pretrained policy, algorithm from data """
        print("{:=^50s}".format(' Load '))
        path = "trained_data/{}_300_5.0_NES_5R.p".format(gym_env)

        pickle_in = open(path, "rb")

        policy, algorithm = pickle.load(pickle_in)
    else:
        """ create policy, algorithm """
        print("{:=^50s}".format(' Init '))
        policy = Policy(env, hidden_dim=(10,))

        algorithm = NES(policy.length, sigma_init=1.0)

    """ create agent """
    agent = Agent(env, policy, algorithm)

    if train:
        """ train the policy """
        print("{:=^50s}".format(' Train '))
        agent.train_policy(episodes=600, n_roll_outs=15, save=save)

    if benchmark:
        """ check the results """
        print("{:=^50s}".format(' Benchmark '))
        agent.run_benchmark()

    if render:
        """ render one episode"""
        print("{:=^50s}".format(' Render '))
        agent.run_benchmark(episodes=5, render=True)

    return


if __name__ == '__main__':
    main(load=False, train=True, benchmark=True, save=True, render=True)
