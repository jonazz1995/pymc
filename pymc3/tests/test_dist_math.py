import numpy as np
import numpy.testing as npt
import theano.tensor as tt
import theano
import theano.tests.unittest_tools as utt
import pymc3 as pm
from scipy import stats, interpolate
import pytest

from ..theanof import floatX
from ..distributions import Discrete
from ..distributions.dist_math import (
    bound, factln, alltrue_scalar, MvNormalLogp,
    MvNormalLogpSum, SplineWrapper)


def test_bound():
    logp = tt.ones((10, 10))
    cond = tt.ones((10, 10))
    assert np.all(bound(logp, cond).eval() == logp.eval())

    logp = tt.ones((10, 10))
    cond = tt.zeros((10, 10))
    assert np.all(bound(logp, cond).eval() == (-np.inf * logp).eval())

    logp = tt.ones((10, 10))
    cond = True
    assert np.all(bound(logp, cond).eval() == logp.eval())

    logp = tt.ones(3)
    cond = np.array([1, 0, 1])
    assert not np.all(bound(logp, cond).eval() == 1)
    assert np.prod(bound(logp, cond).eval()) == -np.inf

    logp = tt.ones((2, 3))
    cond = np.array([[1, 1, 1], [1, 0, 1]])
    assert not np.all(bound(logp, cond).eval() == 1)
    assert np.prod(bound(logp, cond).eval()) == -np.inf

def test_alltrue_scalar():
    assert alltrue_scalar([]).eval()
    assert alltrue_scalar([True]).eval()
    assert alltrue_scalar([tt.ones(10)]).eval()
    assert alltrue_scalar([tt.ones(10),
                    5 * tt.ones(101)]).eval()
    assert alltrue_scalar([np.ones(10),
                    5 * tt.ones(101)]).eval()
    assert alltrue_scalar([np.ones(10),
                    True,
                    5 * tt.ones(101)]).eval()
    assert alltrue_scalar([np.array([1, 2, 3]),
                    True,
                    5 * tt.ones(101)]).eval()

    assert not alltrue_scalar([False]).eval()
    assert not alltrue_scalar([tt.zeros(10)]).eval()
    assert not alltrue_scalar([True,
                        False]).eval()
    assert not alltrue_scalar([np.array([0, -1]),
                        tt.ones(60)]).eval()
    assert not alltrue_scalar([np.ones(10),
                        False,
                        5 * tt.ones(101)]).eval()

def test_alltrue_shape():
    vals = [True, tt.ones(10), tt.zeros(5)]

    assert alltrue_scalar(vals).eval().shape == ()

class MultinomialA(Discrete):
    def __init__(self, n, p, *args, **kwargs):
        super(MultinomialA, self).__init__(*args, **kwargs)

        self.n = n
        self.p = p

    def logp(self, value):
        n = self.n
        p = self.p

        return bound(factln(n) - factln(value).sum() + (value * tt.log(p)).sum(),
                     value >= 0,
                     0 <= p, p <= 1,
                     tt.isclose(p.sum(), 1),
                     broadcast_conditions=False
        )


class MultinomialB(Discrete):
    def __init__(self, n, p, *args, **kwargs):
        super(MultinomialB, self).__init__(*args, **kwargs)

        self.n = n
        self.p = p

    def logp(self, value):
        n = self.n
        p = self.p

        return bound(factln(n) - factln(value).sum() + (value * tt.log(p)).sum(),
                     tt.all(value >= 0),
                     tt.all(0 <= p), tt.all(p <= 1),
                     tt.isclose(p.sum(), 1),
                     broadcast_conditions=False
        )


def test_multinomial_bound():

    x = np.array([1, 5])
    n = x.sum()

    with pm.Model() as modelA:
        p_a = pm.Dirichlet('p', floatX(np.ones(2)))
        MultinomialA('x', n, p_a, observed=x)

    with pm.Model() as modelB:
        p_b = pm.Dirichlet('p', floatX(np.ones(2)))
        MultinomialB('x', n, p_b, observed=x)

    assert np.isclose(modelA.logp({'p_stickbreaking__': [0]}),
                      modelB.logp({'p_stickbreaking__': [0]}))


class TestMvNormalLogp():

    def test_logp_with_tau(self):
        np.random.seed(42)

        chol_val = floatX(np.array([[1, 0], [ 0.9, 2]]))
        cov_val = floatX(np.dot(chol_val, chol_val.T))
        tau_val = floatX(np.linalg.inv(cov_val))
        tau = tt.matrix('tau')
        tau.tag.test_value = tau_val
        delta_val = floatX(np.random.randn(5, 2))
        delta = tt.matrix('delta')
        delta.tag.test_value = delta_val
        expect = stats.multivariate_normal(mean=np.zeros(2), cov=cov_val)
        expect = expect.logpdf(delta_val)
        logp_tau = MvNormalLogp('tau')(tau, delta)
        logp_tau_f = theano.function([tau, delta], logp_tau)
        logp_tau = logp_tau_f(tau_val, delta_val)
        npt.assert_allclose(logp_tau, expect)

    def test_logp_with_cov(self):
        np.random.seed(42)

        chol_val = floatX(np.array([[1, 0], [ 0.9, 2]]))
        cov_val = floatX(np.dot(chol_val, chol_val.T))
        cov = tt.matrix('cov')
        cov.tag.test_value = cov_val
        delta_val = floatX(np.random.randn(5, 2))
        delta = tt.matrix('delta')
        delta.tag.test_value = delta_val
        expect = stats.multivariate_normal(mean=np.zeros(2), cov=cov_val)
        expect = expect.logpdf(delta_val)
        logp_cov = MvNormalLogp()(cov, delta)
        logp_cov_f = theano.function([cov, delta], logp_cov)
        logp_cov = logp_cov_f(cov_val, delta_val)
        npt.assert_allclose(logp_cov, expect)

    @pytest.mark.skip(reason="Not yet implemented")
    def test_logp_with_chol(self):
        np.random.seed(42)

        chol_val = floatX(np.array([[1, 0], [ 0.9, 2]]))
        cov_val = floatX(np.dot(chol_val, chol_val.T))
        chol = tt.matrix('cov')
        chol.tag.test_value = chol_val
        delta_val = floatX(np.random.randn(5, 2))
        delta = tt.matrix('delta')
        delta.tag.test_value = delta_val
        expect = stats.multivariate_normal(mean=np.zeros(2), cov=cov_val)
        expect = expect.logpdf(delta_val)
        logp_chol = MvNormalLogp('chol')(chol, delta)
        logp_chol_f = theano.function([chol, delta], logp_chol)
        logp_chol = logp_chol_f(chol_val, delta_val)
        npt.assert_allclose(logp_chol, expect)

    def test_logpsum_with_cov(self):
        np.random.seed(42)

        chol_val = floatX(np.array([[1, 0], [ 0.9, 2]]))
        cov_val = floatX(np.dot(chol_val, chol_val.T))
        cov = tt.matrix('cov')
        cov.tag.test_value = cov_val
        delta_val = floatX(np.random.randn(5, 2))
        delta = tt.matrix('delta')
        delta.tag.test_value = delta_val
        expect = stats.multivariate_normal(mean=np.zeros(2), cov=cov_val)
        expect = expect.logpdf(delta_val).sum()
        logp_cov = MvNormalLogpSum()(cov, delta)
        logp_cov_f = theano.function([cov, delta], logp_cov)
        logp_cov = logp_cov_f(cov_val, delta_val)
        npt.assert_allclose(logp_cov, expect)

    def test_logpsum_with_chol(self):
        np.random.seed(42)

        chol_val = floatX(np.array([[1, 0], [ 0.9, 2]]))
        cov_val = floatX(np.dot(chol_val, chol_val.T))
        chol = tt.matrix('cov')
        chol.tag.test_value = chol_val
        delta_val = floatX(np.random.randn(5, 2))
        delta = tt.matrix('delta')
        delta.tag.test_value = delta_val
        expect = stats.multivariate_normal(mean=np.zeros(2), cov=cov_val)
        expect = expect.logpdf(delta_val).sum()
        logp_chol = MvNormalLogpSum('chol')(chol, delta)
        logp_chol_f = theano.function([chol, delta], logp_chol)
        logp_chol = logp_chol_f(chol_val, delta_val)
        npt.assert_allclose(logp_chol, expect)

    @theano.configparser.change_flags(compute_test_value="ignore")
    def test_grad(self):
        np.random.seed(42)

        def func(chol_vec, delta):
            chol = tt.stack([
                tt.stack([tt.exp(0.1 * chol_vec[0]), 0]),
                tt.stack([chol_vec[1], 2 * tt.exp(chol_vec[2])]),
            ])
            cov = floatX(tt.dot(chol, chol.T))
            return MvNormalLogpSum()(cov, delta)

        chol_vec_val = floatX(np.array([0.5, 1., -0.1]))

        delta_val = floatX(np.random.randn(1, 2))
        utt.verify_grad(func, [chol_vec_val, delta_val])

        delta_val = floatX(np.random.randn(5, 2))
        utt.verify_grad(func, [chol_vec_val, delta_val])

    @theano.configparser.change_flags(compute_test_value="ignore")
    def test_grad_with_chol(self):
        np.random.seed(42)

        def func(chol_vec, delta):
            chol = tt.stack([
                tt.stack([tt.exp(0.1 * chol_vec[0]), 0]),
                tt.stack([chol_vec[1], 2 * tt.exp(chol_vec[2])]),
            ])
            return MvNormalLogpSum('chol')(floatX(chol), delta)

        chol_vec_val = floatX(np.array([0.5, 1., -0.1]))

        delta_val = floatX(np.random.randn(1, 2))
        utt.verify_grad(func, [chol_vec_val, delta_val])

        delta_val = floatX(np.random.randn(5, 2))
        utt.verify_grad(func, [chol_vec_val, delta_val])

    @theano.configparser.change_flags(compute_test_value="ignore")
    def test_hessian(self):
        chol_vec = tt.vector('chol_vec')
        chol_vec.tag.test_value = floatX(np.array([0.1, 2, 3]))
        chol = tt.stack([
            tt.stack([tt.exp(0.1 * chol_vec[0]), 0]),
            tt.stack([chol_vec[1], 2 * tt.exp(chol_vec[2])]),
        ])
        cov = tt.dot(chol, chol.T)
        delta = tt.matrix('delta')
        delta.tag.test_value = floatX(np.ones((5, 2)))
        logp = MvNormalLogpSum()(cov, delta)
        g_cov, g_delta = tt.grad(logp, [cov, delta])
        tt.grad(g_delta.sum() + g_cov.sum(), [delta, cov])


class TestSplineWrapper(object):
    @theano.configparser.change_flags(compute_test_value="ignore")
    def test_grad(self):
        x = np.linspace(0, 1, 100)
        y = x * x
        spline = SplineWrapper(interpolate.InterpolatedUnivariateSpline(x, y, k=1))
        utt.verify_grad(spline, [0.5])

    @theano.configparser.change_flags(compute_test_value="ignore")
    def test_hessian(self):
        x = np.linspace(0, 1, 100)
        y = x * x
        spline = SplineWrapper(interpolate.InterpolatedUnivariateSpline(x, y, k=1))
        x_var = tt.dscalar('x')
        g_x, = tt.grad(spline(x_var), [x_var])
        with pytest.raises(NotImplementedError):
            tt.grad(g_x, [x_var])
