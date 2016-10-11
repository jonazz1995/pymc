import unittest

from .checks import close_to
from .models import mv_simple, mv_simple_discrete, simple_2model
from .helpers import SeededTest
from pymc3.sampling import assign_step_methods, sample
from pymc3.model import Model
from pymc3.step_methods import (NUTS, BinaryGibbsMetropolis, Metropolis, Constant, Slice,
                                CompoundStep, MultivariateNormalProposal, HamiltonianMC)
from pymc3.distributions import Binomial, Normal, Bernoulli, Categorical, Uniform
from numpy.testing import assert_almost_equal
import numpy as np


class TestStepMethods(object):  # yield test doesn't work subclassing unittest.TestCase
    def check_stat(self, check, trace):
        for (var, stat, value, bound) in check:
            s = stat(trace[var][2000:], axis=0)
            close_to(s, value, bound)

    def test_step_continuous(self):
        start, model, (mu, C) = mv_simple()
        unc = np.diag(C) ** .5
        check = (('x', np.mean, mu, unc / 10.),
                 ('x', np.std, unc, unc / 10.))
        with model:
            steps = (
                Slice(),
                HamiltonianMC(scaling=C, is_cov=True, blocked=False),
                NUTS(scaling=C, is_cov=True, blocked=False),
                Metropolis(S=C, proposal_dist=MultivariateNormalProposal, blocked=True),
                Slice(blocked=True),
                HamiltonianMC(scaling=C, is_cov=True),
                NUTS(scaling=C, is_cov=True),
                CompoundStep([
                    HamiltonianMC(scaling=C, is_cov=True),
                    HamiltonianMC(scaling=C, is_cov=True, blocked=False)]),
            )
        for step in steps:
            trace = sample(8000, step=step, start=start, model=model, 
                    random_seed=1, progressbar=False)
            yield self.check_stat, check, trace

    def test_step_discrete(self):
        start, model, (mu, C) = mv_simple_discrete()
        unc = np.diag(C) ** .5
        check = (('x', np.mean, mu, unc / 10.),
                 ('x', np.std, unc, unc / 10.))
        with model:
            steps = (
                Metropolis(S=C, proposal_dist=MultivariateNormalProposal),
            )
        for step in steps:
            trace = sample(20000, step=step, start=start, model=model, 
                    random_seed=1, progressbar=False)
            self.check_stat(check, trace)

    def test_constant_step(self):
        with Model():
            x = Normal('x', 0, 1)
            start = {'x': -1}
            tr = sample(10, step=Constant([x]), start=start, progressbar=False)
        assert_almost_equal(tr['x'], start['x'], decimal=10)


class TestCompoundStep(unittest.TestCase):
    samplers = (Metropolis, Slice, HamiltonianMC, NUTS)

    def test_non_blocked(self):
        """Test that samplers correctly create non-blocked compound steps."""
        _, model = simple_2model()
        with model:
            for sampler in self.samplers:
                self.assertIsInstance(sampler(blocked=False), CompoundStep)

    def test_blocked(self):
        _, model = simple_2model()
        with model:
            for sampler in self.samplers:
                sampler_instance = sampler(blocked=True)
                self.assertNotIsInstance(sampler_instance, CompoundStep)
                self.assertIsInstance(sampler_instance, sampler)


class TestAssignStepMethods(unittest.TestCase):
    def test_bernoulli(self):
        """Test bernoulli distribution is assigned binary gibbs metropolis method"""
        with Model() as model:
            Bernoulli('x', 0.5)
            steps = assign_step_methods(model, [])
        self.assertIsInstance(steps, BinaryGibbsMetropolis)

    def test_normal(self):
        """Test normal distribution is assigned NUTS method"""
        with Model() as model:
            Normal('x', 0, 1)
            steps = assign_step_methods(model, [])
        self.assertIsInstance(steps, NUTS)

    def test_categorical(self):
        """Test categorical distribution is assigned binary gibbs metropolis method"""
        with Model() as model:
            Categorical('x', np.array([0.25, 0.75]))
            steps = assign_step_methods(model, [])
        self.assertIsInstance(steps, BinaryGibbsMetropolis)

    def test_binomial(self):
        """Test binomial distribution is assigned metropolis method."""
        with Model() as model:
            Binomial('x', 10, 0.5)
            steps = assign_step_methods(model, [])
        self.assertIsInstance(steps, Metropolis)

class TestSampleEstimates(SeededTest):
    def test_parameter_estimate(self):
        
        alpha_true, sigma_true = 1, 0.5
        beta_true = np.array([1, 2.5])

        size = 100

        X1 = np.random.randn(size)
        X2 = np.random.randn(size) * 0.2
        Y = alpha_true + beta_true[0] * X1 + beta_true[1] * X2 + np.random.randn(size) * sigma_true
        
        with Model() as model:
            alpha = Normal('alpha', mu=0, sd=10)
            beta = Normal('beta', mu=0, sd=10, shape=2)
            sigma = Uniform('sigma', lower=0.0, upper=1.0)
            mu = alpha + beta[0]*X1 + beta[1]*X2
            Y_obs = Normal('Y_obs', mu=mu, sd=sigma, observed=Y)
        
            for step_method in (NUTS(), Metropolis(), 
                            [Slice([alpha, sigma]), Metropolis([beta])]):
            
                trace = sample(1000, step=step_method, progressbar=False)
            
        
                assert np.isclose(np.median(trace.beta, 0), beta_true, rtol=0.1).all()
                assert np.isclose(np.median(trace.alpha), alpha_true, rtol=0.1)
                assert np.isclose(np.median(trace.sigma), sigma_true, rtol=0.1)