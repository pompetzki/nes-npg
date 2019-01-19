import numpy as np

#######################################
# Estimations
#######################################


def estimate_value(trajectories, _gamma):
    for t in trajectories:
        rewards = t["rewards"]
        values = np.zeros_like(rewards)
        for i in range(len(values) - 1, -1, -1):
            values[i] = rewards[i] if i == len(values) - 1 \
                else rewards[i] + _gamma * values[i + 1]
        t["values"] = values
    return


def estimate_advantage(trajectories, baseline, _gamma=0.98, _lambda=0.95):
    for t in trajectories:
        values = baseline.predict(t)
        rewards = t["rewards"]
        advantage = np.zeros_like(rewards)
        delta = np.zeros_like(rewards)
        delta[:-1] = \
            rewards[:-1] - values[:-1] + _gamma * values[1:]
        # if len(rewards) == 10000:
        #     delta[-1] = rewards[-1] - values[-1] \
        #                 + _gamma * values[-1]
        # else:
        #     delta[-1] = rewards[-1] - values[-1]
        delta[-1] = rewards[-1] - values[-1] + _gamma * values[-1]
        for i in range(len(delta) - 1, -1, -1):
            advantage[i] = delta[i] if i == len(delta) - 1 else \
                delta[i] + _gamma * _lambda * advantage[i + 1]
        t["advantages"] = advantage

    advantages = np.concatenate([t["advantages"] for t in trajectories])
    mean = np.mean(advantages)
    std = np.std(advantages)
    for t in trajectories:
        t["advantages"] = (t["advantages"] - mean)/(std + 1e-10)
    return
