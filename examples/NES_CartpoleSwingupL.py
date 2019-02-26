from NES import *
from utilities.Environment import Environment
from models.SquaredFeaturePolicy import PolicySquare
from Agent import Agent
import pickle

#######################################
# Environment
#######################################


def main(load: bool = False, train: bool = False, benchmark: bool = False,
         save: bool = False, render: bool = True):
    """ set seed """
    np.random.seed(0)
    tr.manual_seed(0)

    """ define the environment """
    gym_env = 'CartpoleSwingLong-v0'
    env = Environment(gym_env)
    print("{:=^50s}".format(' Start {} '.format(gym_env)))

    if load:
        """ load pretrained policy, algorithm from data """
        print("{:=^50s}".format(' Load '))
        path = "{}_300_[5.]_NPG.p".format(gym_env)

        pickle_in = open(path, "rb")

        policy, algorithm = pickle.load(pickle_in)
    else:
        """ create policy, algorithm """
        print("{:=^50s}".format(' Init '))
        policy = PolicySquare(env)

        algorithm = NES(policy.length)

    """ create agent """
    agent = Agent(env, policy, algorithm)

    if train:
        """ train the policy """
        print("{:=^50s}".format(' Train '))
        agent.train_policy(episodes=500, n_roll_outs=1, save=save)

    if benchmark:
        """ check the results """
        print("{:=^50s}".format(' Benchmark '))
        agent.run_benchmark()

    if render:
        """ render one episode"""
        print("{:=^50s}".format(' Render '))
        agent.run_benchmark(episodes=1, render=True)

    return


if __name__ == '__main__':
    main(load=False, train=False, benchmark=True, save=False, render=True)
