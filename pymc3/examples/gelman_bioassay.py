import pymc3 as pm
from numpy import ones, array, random

# Samples for each dose level
n = 5 * ones(4, dtype=int)
# Log-dose
dose = array([-.86, -.3, -.05, .73])

with pm.Model() as model:

    # Logit-linear model parameters
    alpha = pm.Normal('alpha', 0, tau=0.01)
    beta = pm.Normal('beta', 0, tau=0.01)

    # Calculate probabilities of death
    theta = pm.Deterministic('theta', pm.math.invlogit(alpha + beta * dose))

    # Data likelihood
    deaths = pm.Binomial('deaths', n=n, p=theta, observed=[0, 1, 3, 5])

def run(n=1000):
    if n == "short":
        n = 50
    with model:
        random.seed(42)
        trace = pm.sample(n, init='random')
        pm.summary(trace, varnames=['alpha', 'beta'])

if __name__ == '__main__':
    run()
