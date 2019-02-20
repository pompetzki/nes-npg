import numpy as np
import torch as tr
import copy
from utilities.Conjugate_gradient import conjugate_gradient as cg
from utilities.Estimations import *

#######################################
# NPG
#######################################


class NPG:

    """ Init """
    """==============================================================="""
    def __init__(self, baseline, _delta=0.05, damping=1e-4,
                 _lambda=0.95, _gamma=0.98, normalizer=None):

        self.delta = _delta
        self.__delta = 2 * _delta
        self.damping = damping
        self.__lambda = _lambda
        self.__gamma = _gamma
        self.baseline = baseline
        self.__normalizer = normalizer

    """ Utility Functions """
    """==============================================================="""
    def line_search(self, old_policy, new_policy, observations):
        obs = tr.from_numpy(observations).float()
        old_mean, old_log_std = old_policy.network(obs)
        old_std = tr.exp(old_log_std)

        new_mean, new_log_std = new_policy.network(obs)
        new_std = tr.exp(new_log_std)
        kl = (old_std ** 2 + (old_mean - new_mean) ** 2)
        kl /= (2.0 * new_std ** 2 + 1e-10)
        kl += new_log_std - old_log_std - 0.5
        kl_mean = tr.mean(kl.sum(1, keepdim=True)).detach().numpy()
        return kl_mean <= self.__delta

    """ Main Functions """
    """==============================================================="""
    def do(self, env, policy, n_roll_outs):

        print("log_std:", policy.network.log_std)

        trajectories = env.roll_out(policy,
                                    n_roll_outs=n_roll_outs,
                                    render=False,
                                    normalizer=self.__normalizer)

        estimate_advantage(trajectories,
                           self.baseline, self.__gamma, self.__lambda)

        observations = np.concatenate([t["observations"]
                                       for t in trajectories])
        actions = np.concatenate([t["actions"]
                                  for t in trajectories]).reshape(-1, 1)
        advantages = np.concatenate([t["advantages"]
                                    for t in trajectories]).reshape(-1, 1)

        """ vanilla gradient """
        with tr.no_grad():
            fixed_log_probs = policy.get_log_prob(observations, actions)
            fixed_policy = copy.deepcopy(policy)

        log_probs = policy.get_log_prob(observations, actions)
        action_losses = tr.from_numpy(advantages).float() * tr.exp(
            log_probs - fixed_log_probs)
        action_loss = action_losses.mean()

        vpg = tr.autograd.grad(action_loss,
                               policy.network.parameters(), retain_graph=True)
        vpg_grad = np.concatenate([v.contiguous().detach().view(-1).numpy()
                                   for v in vpg])

        """ product inv(fisher) times vanilla gradient via conjugate grad """
        def get_npg(v):
            damping = self.damping
            kl = tr.mean(policy.get_kl(observations))
            grads = tr.autograd.grad(kl, policy.network.parameters(),
                                     create_graph=True)
            grads_flat = tr.cat([grad.view(-1) for grad in grads])
            kl_v = tr.sum(grads_flat * tr.from_numpy(v).float())
            grads_kl_v = tr.autograd.grad(kl_v, policy.network.parameters())
            flat_grad_grad_v = np.concatenate(
                [g.contiguous().view(-1).data.numpy() for g in grads_kl_v])
            return flat_grad_grad_v + v * damping

        npg_grad = cg(get_npg, vpg_grad)

        """ update policy """
        # nominator = vpg_grad.T @ npg_grad + 1e-20
        nominator = npg_grad.dot(get_npg(npg_grad))
        learning_rate = np.sqrt(self.__delta / nominator)
        current = policy.get_parameters()
        for i in range(100):
            new = current + 0.9 ** i * learning_rate * npg_grad
            policy.set_parameters(new)
            if self.line_search(fixed_policy, policy, observations):
                break
            elif i == 99:
                policy.set_parameters(current)

        """ update baseline """
        estimate_value(trajectories, self.__gamma)
        self.baseline.train(trajectories)

        """ update normalizer """
        if self.__normalizer is not None:
            self.__normalizer.update(trajectories)

        """ calculate return values """
        returns = np.asarray([np.sum(t["rewards"]) for t in trajectories])

        time_steps = np.array([t["time_steps"]
                               for t in trajectories]).sum() / n_roll_outs

        return returns, time_steps

    def get_title(self):
        return "NPG \u03B3 = {}, \u03BB = {}, \u03B4 = {} \n" \
               "Baseline: {} with {} epochs" .format(self.__gamma,
                                                     self.__lambda,
                                                     self.__delta,
                                                     self.baseline.hidden_dim,
                                                     self.baseline.epochs)






