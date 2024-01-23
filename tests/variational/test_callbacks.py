#   Copyright 2024 The PyMC Developers
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import numpy as np
import pytensor
import pytest

import pymc as pm


@pytest.mark.parametrize("diff", ["relative", "absolute"])
@pytest.mark.parametrize("ord", [1, 2, np.inf])
def test_callbacks_convergence(diff, ord):
    cb = pm.variational.callbacks.CheckParametersConvergence(every=1, diff=diff, ord=ord)

    class _approx:
        params = (pytensor.shared(np.asarray([1, 2, 3])),)

    approx = _approx()

    with pytest.raises(StopIteration):
        cb(approx, None, 1)
        cb(approx, None, 10)


def test_tracker_callback():
    import time

    tracker = pm.callbacks.Tracker(
        ints=lambda *t: t[-1],
        ints2=lambda ap, h, j: j,
        time=time.time,
    )
    for i in range(10):
        tracker(None, None, i)
    assert "time" in tracker.hist
    assert "ints" in tracker.hist
    assert "ints2" in tracker.hist
    assert len(tracker["ints"]) == len(tracker["ints2"]) == len(tracker["time"]) == 10
    assert tracker["ints"] == tracker["ints2"] == list(range(10))
    tracker = pm.callbacks.Tracker(bad=lambda t: t)  # bad signature
    with pytest.raises(TypeError):
        tracker(None, None, 1)


OPTIMIZERS = [
    pm.sgd(learning_rate=0.1),
    pm.momentum(learning_rate=0.1),
    pm.nesterov_momentum(learning_rate=0.1),
    pm.adagrad(learning_rate=0.1),
    pm.rmsprop(learning_rate=0.1),
    pm.adadelta(learning_rate=0.1),
    pm.adam(learning_rate=0.1),
    pm.adamax(learning_rate=0.1),
]


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_reduce_lr_on_plateau(optimizer):
    cb = pm.variational.callbacks.ReduceLROnPlateau(
        optimizer=optimizer,
        patience=1,
        min_lr=0.001,
    )
    cb(None, [float("inf")], 1)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.1)
    assert cb.best == float("inf")
    cb(None, [float("inf"), 2], 2)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.1)
    assert cb.best == 2
    cb(None, [float("inf"), 2, 1], 3)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.1)
    assert cb.best == 1
    cb(None, [float("inf"), 2, 1, 99], 4)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.01)
    assert cb.best == 1
    cb(None, [float("inf"), 2, 1, 99, 0.9], 5)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.01)
    assert cb.best == 0.9
    cb(None, [float("inf"), 2, 1, 99, 0.9, 99], 6)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.001)
    assert cb.best == 0.9
    cb(None, [float("inf"), 2, 1, 99, 0.9, 99, 99], 7)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.001)
    assert cb.best == 0.9


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_exponential_decay(optimizer):
    cb = pm.variational.callbacks.ExponentialDecay(
        optimizer=optimizer,
        decay_steps=1,
        decay_rate=0.1,
        min_lr=0.001,
    )
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.1)
    cb(None, [float("inf")], 1)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.01)
    cb(None, [float("inf"), 2, 2], 2)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.001)
    cb(None, [float("inf"), 2, 2, 2], 3)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.001)
    cb(None, [float("inf"), 2, 2, 2, 2], 4)
    np.testing.assert_almost_equal(optimizer.keywords["learning_rate"], 0.001)
