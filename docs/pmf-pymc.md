
# Probabilistic Matrix Factorization for Making Personalized Recommendations

The model discussed in this analysis was developed by Ruslan Salakhutdinov and Andriy Mnih. All of the code and supporting text, when not referenced, is the original work of [Mack Sweeney](https://www.linkedin.com/in/macksweeney).

## Motivation

Say I download a handbook of a hundred jokes, and I'd like to know very quickly which ones will be my favorite. So maybe I read a few, I laugh, I read a few more, I stop laughing, and I indicate on a scale of -10 to 10 how funny I thought each joke was. Maybe I do this for 5 jokes out of the 100. Now I go to the back of the book, and there's a little program included for calculating my preferences for all the other jokes. I enter in my preference numbers and shazam! The program spits out a list of all 100 jokes, sorted in the order I'll like them. That certainly would be nice. Today we'll write a program that does exactly this.

We'll start out by getting some intuition for how our model will work. Then we'll formalize our intuition. Afterwards, we'll examine the dataset we are going to use. Once we have some notion of what our data looks like, we'll define some baseline methods for predicting preferences for jokes. Following that, we'll look at Probabilistic Matrix Factorization (PMF), which is a more sophisticated Bayesian method for predicting preferences. Having detailed the PMF model, we'll use PyMC3 for MAP estimation and MCMC inference. Finally, we'll compare the results obtained with PMF to those obtained from our baseline methods and discuss the outcome.

## Intuition

Normally if we want recommendations for something, we try to find people who are similar to us and ask their opinions. If Bob, Alice, and Monty are all similar to me, and they all like knock-knock jokes, I'll probably like knock-knock jokes. Now this isn't always true. It depends on what we consider to be "similar". In order to get the best bang for our buck, we really want to look for people who have the most similar sense of humor. Humor being a complex beast, we'd probably like to break it down into something more understandable. We might try to characterize each joke in terms of various factors. Perhaps jokes can be dry, sarcastic, crude, sexual, political, etc. Now imagine we go through our handbook of jokes and assign each joke a rating in each of the categories. How dry is it? How sarcastic is it? How much does it use sexual innuendos? Perhaps we use numbers between 0 and 1 for each category. Intuitively, we might call this the joke's humor profile.

Now let's suppose we go back to those 5 jokes we rated. At this point, we can get a richer picture of our own preferences by looking at the humor profiles of each of the jokes we liked and didn't like. Perhaps we take the averages across the 5 humor profiles and call this our ideal type of joke. In other words, we have computed some notion of our inherent _preferences_ for various types of jokes. Suppose Bob, Alice, and Monty all do the same. Now we can compare our preferences and determine how similar each of us really are. I might find that Bob is the most similar and the other two are still more similar than other people, but not as much as Bob. So I want recommendations from all three people, but when I make my final decision, I'm going to put more weight on Bob's recommendation than those I get from Alice and Monty.

While the above procedure sounds fairly effective as is, it also reveals an unexpected additional source of information. If we rated a particular joke highly, and we know its humor profile, we can compare with the profiles of other jokes. If we find one with very close numbers, it is probable we'll also enjoy this joke. Both this approach and the one above are commonly known as _neighborhood approaches_. Techniques that leverage both of these approaches simultaneously are often called _collaborative filtering_ [[1]](http://www2.research.att.com/~volinsky/papers/ieeecomputer.pdf). The first approach we talked about uses user-user similarity, while the second uses item-item similarity. Ideally, we'd like to use both sources of information. The idea is we have a lot of items available to us, and we'd like to work together with others to filter the list of items down to those we'll each like best. My list should have the items I'll like best at the top and those I'll like least at the bottom. Everyone else wants the same. If I get together with a bunch of other people, we all read 5 jokes, and we have some efficient computational process to determine similarity, we can very quickly order the jokes to our liking.

## Formalization

Let's take some time to make the intuitive notions we've been discussing more concrete. We have a set of $M$ jokes, or _items_ ($M = 100$ in our example above). We also have $N$ people, whom we'll call _users_ of our recommender system. For each item, we'd like to find a $D$ dimensional factor composition (humor profile above) to describe the item. Ideally, we'd like to do this without actually going through and manually labeling all of the jokes. Manual labeling would be both slow and error-prone, as different people will likely label jokes differently. So we model each joke as a $D$ dimensional vector, which is its latent factor composition. Furthermore, we expect each user to have some preferences, but without our manual labeling and averaging procedure, we have to rely on the latent factor compositions to learn $D$ dimensional latent preference vectors for each user. The only thing we get to observe is the $N \times M$ ratings matrix $R$ provided by the users. Entry $R_{ij}$ is the rating user $i$ gave to item $j$. Many of these entries may be missing, since most users will not have rated all 100 jokes. Our goal is to fill in the missing values with predicted ratings based on the latent variables $U$ and $V$. We denote the predicted ratings by $R_{ij}^*$. We also define an indicator matrix $I$, with entry $I_{ij} = 0$ if $R_{ij}$ is missing and $I_{ij} = 1$ otherwise.

So we have an $N \times D$ matrix of user preferences which we'll call $U$ and an $M \times D$ factor composition matrix we'll call $V$. We also have a $N \times M$ rating matrix we'll call $R$. We can think of each row $U_i$ as indications of how much each user prefers each of the $D$ latent factors. Each row $V_j$ can be thought of as how much each item can be described by each of the latent factors. In order to make a recommendation, we need a suitable prediction function which maps a user preference vector $U_i$ and an item latent factor vector $V_j$ to a predicted ranking. The choice of this prediction function is an important modeling decision, and a variety of prediction functions have been used. Perhaps the most common is the dot product of the two vectors, $U_i \cdot V_j$ [[1]](http://www2.research.att.com/~volinsky/papers/ieeecomputer.pdf).

To better understand CF techniques, let us explore a particular example. Imagine we are seeking to recommend jokes using a model which infers five latent factors, $V_j$, for $j = 1,2,3,4,5$. In reality, the latent factors are often unexplainable in a straightforward manner, and most models make no attempt to understand what information is being captured by each factor.  However, for the purposes of explanation, let us assume the five latent factors might end up capturing the humor profile we were discussing above. So our five latent factors are: dry, sarcastic, crude, sexual, and political. Then for a particular user $i$, imagine we infer a preference vector $U_i = <0.2, 0.1, 0.3, 0.1, 0.3>$. Also, for a particular item $j$, we infer these values for the latent factors: $V_j = <0.5, 0.5, 0.25, 0.8, 0.9>$. Using the dot product as the prediction function, we would calculate 0.575 as the ranking for that item, which is more or less a neutral preference given our -10 to 10 rating scale.

$$0.2 \times 0.5 + 0.1 \times 0.5 + 0.3 \times 0.25 + 0.1 \times 0.8 + 0.3
\times 0.9 = 0.575$$


# Data

The [v1 Jester dataset](http://eigentaste.berkeley.edu/dataset/) provides something very much like the handbook of jokes we have been discussing. The original version of this dataset was constructed in conjunction with the development of the [Eigentaste recommender system](http://eigentaste.berkeley.edu/about.html) [[2]](http://goldberg.berkeley.edu/pubs/eigentaste.pdf). At this point in time, v1 contains over 4.1 million continuous ratings in the range [-10, 10] of 100 jokes from 73,421 users. These ratings were collected between Apr. 1999 and May 2003. In order to reduce the training time of the model for illustrative purposes, 1,000 users who have rated all 100 jokes will be selected randomly. We will implement a model that is suitable for collaborative filtering on this data and evaluate it in terms of root mean squared error (RMSE) to validate the results.

Let's begin by exploring our data. We want to get a general feel for what it looks like and a sense for what sort of patterns it might contain.


```
% matplotlib inline
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


data = pd.read_csv('data/jester-dataset-v1-dense-first-1000.csv')
data.head()
```




<div style="max-height:1000px;max-width:1500px;overflow:auto;">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
      <th>7</th>
      <th>8</th>
      <th>9</th>
      <th>10</th>
      <th>...</th>
      <th>91</th>
      <th>92</th>
      <th>93</th>
      <th>94</th>
      <th>95</th>
      <th>96</th>
      <th>97</th>
      <th>98</th>
      <th>99</th>
      <th>100</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td> 4.08</td>
      <td>-0.29</td>
      <td> 6.36</td>
      <td> 4.37</td>
      <td>-2.38</td>
      <td>-9.66</td>
      <td>-0.73</td>
      <td>-5.34</td>
      <td> 8.88</td>
      <td> 9.22</td>
      <td>...</td>
      <td> 2.82</td>
      <td>-4.95</td>
      <td>-0.29</td>
      <td> 7.86</td>
      <td>-0.19</td>
      <td>-2.14</td>
      <td> 3.06</td>
      <td> 0.34</td>
      <td>-4.32</td>
      <td> 1.07</td>
    </tr>
    <tr>
      <th>1</th>
      <td>-6.17</td>
      <td>-3.54</td>
      <td> 0.44</td>
      <td>-8.50</td>
      <td>-7.09</td>
      <td>-4.32</td>
      <td>-8.69</td>
      <td>-0.87</td>
      <td>-6.65</td>
      <td>-1.80</td>
      <td>...</td>
      <td>-3.54</td>
      <td>-6.89</td>
      <td>-0.68</td>
      <td>-2.96</td>
      <td>-2.18</td>
      <td>-3.35</td>
      <td> 0.05</td>
      <td>-9.08</td>
      <td>-5.05</td>
      <td>-3.45</td>
    </tr>
    <tr>
      <th>2</th>
      <td> 6.84</td>
      <td> 3.16</td>
      <td> 9.17</td>
      <td>-6.21</td>
      <td>-8.16</td>
      <td>-1.70</td>
      <td> 9.27</td>
      <td> 1.41</td>
      <td>-5.19</td>
      <td>-4.42</td>
      <td>...</td>
      <td> 7.23</td>
      <td>-1.12</td>
      <td>-0.10</td>
      <td>-5.68</td>
      <td>-3.16</td>
      <td>-3.35</td>
      <td> 2.14</td>
      <td>-0.05</td>
      <td> 1.31</td>
      <td> 0.00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>-3.79</td>
      <td>-3.54</td>
      <td>-9.42</td>
      <td>-6.89</td>
      <td>-8.74</td>
      <td>-0.29</td>
      <td>-5.29</td>
      <td>-8.93</td>
      <td>-7.86</td>
      <td>-1.60</td>
      <td>...</td>
      <td> 4.37</td>
      <td>-0.29</td>
      <td> 4.17</td>
      <td>-0.29</td>
      <td>-0.29</td>
      <td>-0.29</td>
      <td>-0.29</td>
      <td>-0.29</td>
      <td>-3.40</td>
      <td>-4.95</td>
    </tr>
    <tr>
      <th>4</th>
      <td> 1.31</td>
      <td> 1.80</td>
      <td> 2.57</td>
      <td>-2.38</td>
      <td> 0.73</td>
      <td> 0.73</td>
      <td>-0.97</td>
      <td> 5.00</td>
      <td>-7.23</td>
      <td>-1.36</td>
      <td>...</td>
      <td> 1.46</td>
      <td> 1.70</td>
      <td> 0.29</td>
      <td>-3.30</td>
      <td> 3.45</td>
      <td> 5.44</td>
      <td> 4.08</td>
      <td> 2.48</td>
      <td> 4.51</td>
      <td> 4.66</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 100 columns</p>
</div>




```
# Extract the ratings from the DataFrame
all_ratings = np.ndarray.flatten(data.values)
ratings = pd.Series(all_ratings)

# Plot histogram and density.
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
ratings.plot(kind='density', ax=ax1, grid=False)
ax1.set_ylim(0, 0.08)
ax1.set_xlim(-11, 11)

# Plot histogram
ratings.plot(kind='hist', ax=ax2, bins=20, grid=False)
ax2.set_xlim(-11, 11)
plt.show()
```


![png](pmf-pymc_files/pmf-pymc_4_0.png)



```
ratings.describe()
```




    count    100000.000000
    mean          0.996219
    std           5.265215
    min          -9.950000
    25%          -2.860000
    50%           1.650000
    75%           5.290000
    max           9.420000
    dtype: float64




This must be a decent batch of jokes. From our exploration above, we know most ratings are in the range -1 to 10, and positive ratings are more likely than negative ratings. Let's look at the means for each joke to see if we have any particularly good (or bad) humor here.



```
joke_means = data.mean(axis=0)
joke_means.plot(kind='bar', grid=False, figsize=(16, 6),
                title="Mean Ratings for All 100 Jokes")
```




    <matplotlib.axes._subplots.AxesSubplot at 0x7fc46a3c5fd0>




![png](pmf-pymc_files/pmf-pymc_7_1.png)


While the majority of the jokes generally get positive feedback from users, there are definitely a few that stand out as poor humor. Let's take a look at the worst and best joke, just for fun.


```
import os

# Worst and best joke?
worst_joke_id = joke_means.argmin()
best_joke_id = joke_means.argmax()

# Let's see for ourselves. Load the jokes.
joke_dir = 'data/jokes'
files = [os.path.join(joke_dir, fname) for fname in os.listdir(joke_dir)]
jokes = [fname for fname in files if fname.endswith('txt')]
nums = [filter(lambda c: c.isdigit(), fname) for fname in jokes]
joke_dict = {k: v for k, v in zip(nums, jokes)}

def read_joke(joke_id):
    fname = joke_dict[joke_id]
    with open(fname) as f:
        return f.read()

print 'The worst joke:\n---------------\n%s\n' % read_joke(worst_joke_id)
print 'The best joke:\n--------------\n%s' % read_joke(best_joke_id)
```

    The worst joke:
    ---------------
    A Joke 
    How many teddybears does it take to change a lightbulb?
    It takes only one teddybear, but it takes a whole lot of lightbulbs.
    
    The best joke:
    --------------
    A Joke 
    A radio conversation of a US naval ship with Canadian authorities ... 
    
    Americans: Please divert your course 15 degrees to the North to avoid a collision.
    Canadians: Recommend you divert YOUR course 15 degrees to the South to avoid a collision.
    Americans: This is the Captain of a US Navy ship.  I say again, divert YOUR course.
    Canadians: No. I say again, you divert YOUR course.
    Americans: This is the aircraft carrier USS LINCOLN, the second largest ship in the United States' Atlantic Fleet. We are accompanied by three destroyers, three cruisers and numerous support vessels. I demand that you change your course 15 degrees north, that's ONE FIVE DEGREES NORTH, or counter-measures will be undertaken to ensure the safety of this ship.
    Canadians: This is a lighthouse. Your call.
    


Make sense to me. We now know there are definite popularity differences between the jokes. Some of them are simply funnier than others, and some are downright lousy. Looking at the joke means allowed us to discover these general trends. Perhaps there are similar trends across users. It might be the case that some users are simply more easily humored than others. Let's take a look.


```
user_means = data.mean(axis=1)
fig, ax = plt.subplots(figsize=(16, 6))
user_means.plot(kind='bar', grid=False, ax=ax,
                title="Mean Ratings for All 1000 Users")
ax.set_xticklabels('')  # 1000 labels is nonsensical
fig.show()
```


![png](pmf-pymc_files/pmf-pymc_11_0.png)


We see even more significant trends here. Some users rate nearly everything highly, and some (though not as many) rate nearly everything negatively. These observations will come in handy when considering models to use for predicting user preferences on unseen jokes.

# Methods

Having explored the data, we're now ready to dig in and start addressing the problem. We want to predict how much each user is going to like all of the jokes he or she has not yet read.


## Baselines

Every good analysis needs some kind of baseline methods to compare against. It's difficult to claim we've produced good results if we have no reference point for what defines "good". We'll define three very simple baseline methods and find the RMSE using these methods. Our goal will be to obtain lower RMSE scores with whatever model we produce.

### Uniform Random Baseline

Our first baseline is about as dead stupid as you can get. Every place we see a missing value in $R$, we'll simply fill it with a number drawn uniformly at random in the range [-10, 10]. We expect this method to do the worst by far.

$$R_{ij}^* \sim Uniform$$

### Global Mean Baseline

This method is only slightly better than the last. Wherever we have a missing value, we'll fill it in with the mean of all observed ratings.

$$\text{global_mean} = \frac{1}{N \times M} \sum_{i=1}^N \sum_{j=1}^M I_{ij}(R_{ij})$$

$$R_{ij}^* = \text{global_mean}$$

### Mean of Means Baseline

Now we're going to start getting a bit smarter. We imagine some users might be easily amused, and inclined to rate all jokes more highly. Other users might be the opposite. Additionally, some jokes might simply be more witty than others, so all users might rate some jokes more highly than others in general. We can clearly see this in our graph of the joke means above. We'll attempt to capture these general trends through per-user and per-joke rating means. We'll also incorporate the global mean to smooth things out a bit. So if we see a missing value in cell $R_{ij}$, we'll average the global mean with the mean of $U_i$ and the mean of $V_j$ and use that value to fill it in.

$$\text{user_means} = \frac{1}{M} \sum_{j=1}^M I_{ij}(R_{ij})$$

$$\text{joke_means} = \frac{1}{N} \sum_{i=1}^N I_{ij}(R_{ij})$$

$$R_{ij}^* = \frac{1}{3} \left(\text{user_means}_i + \text{ joke_means}_j + \text{ global_mean} \right)$$



```
from collections import OrderedDict


# Create a base class with scaffolding for our 3 baselines.

def split_title(title):
    """Change "BaselineMethod" to "Baseline Method"."""
    words = []
    tmp = [title[0]]
    for c in title[1:]:
        if c.isupper():
            words.append(''.join(tmp))
            tmp = [c]
        else:
            tmp.append(c)
    words.append(''.join(tmp))
    return ' '.join(words)


class Baseline(object):
    """Calculate baseline predictions."""

    def __init__(self, train_data):
        """Simple heuristic-based transductive learning to fill in missing
        values in data matrix."""
        self.predict(train_data.copy())

    def predict(self, train_data):
        raise NotImplementedError(
            'baseline prediction not implemented for base class')

    def rmse(self, test_data):
        """Calculate root mean squared error for predictions on test data."""
        return rmse(test_data, self.predicted)
    
    def __str__(self):
        return split_title(self.__class__.__name__)
        


# Implement the 3 baselines.

class UniformRandomBaseline(Baseline):
    """Fill missing values with uniform random values."""

    def predict(self, train_data):
        nan_mask = np.isnan(train_data)
        masked_train = np.ma.masked_array(train_data, nan_mask)
        pmin, pmax = masked_train.min(), masked_train.max()
        N = nan_mask.sum()
        train_data[nan_mask] = np.random.uniform(pmin, pmax, N)
        self.predicted = train_data


class GlobalMeanBaseline(Baseline):
    """Fill in missing values using the global mean."""

    def predict(self, train_data):
        nan_mask = np.isnan(train_data)
        train_data[nan_mask] = train_data[~nan_mask].mean()
        self.predicted = train_data


class MeanOfMeansBaseline(Baseline):
    """Fill in missing values using mean of user/item/global means."""

    def predict(self, train_data):
        nan_mask = np.isnan(train_data)
        masked_train = np.ma.masked_array(train_data, nan_mask)
        global_mean = masked_train.mean()
        user_means = masked_train.mean(axis=1)
        item_means = masked_train.mean(axis=0)
        self.predicted = train_data.copy()
        n, m = train_data.shape
        for i in xrange(n):
            for j in xrange(m):
                if np.ma.isMA(item_means[j]):
                    self.predicted[i,j] = np.mean(
                        (global_mean, user_means[i]))
                else:
                    self.predicted[i,j] = np.mean(
                        (global_mean, user_means[i], item_means[j]))
                    
                    
baseline_methods = OrderedDict()
baseline_methods['ur'] = UniformRandomBaseline
baseline_methods['gm'] = GlobalMeanBaseline
baseline_methods['mom'] = MeanOfMeansBaseline
```

## Probabilistic Matrix Factorization

[Probabilistic Matrix Factorization (PMF)](http://papers.nips.cc/paper/3208-probabilistic-matrix-factorization.pdf) [3] is a probabilistic approach to the collaborative filtering problem that takes a Bayesian perspective. The ratings $R$ are modeled as draws from a Gaussian distribution.  The mean for $R_{ij}$ is $U_i V_j^T$. The precision $\alpha$ is a fixed parameter that reflects the uncertainty of the estimations; the normal distribution is commonly reparameterized in terms of precision, which is the inverse of the variance. Complexity is controlled by placing zero-mean spherical Gaussian priors on $U$ and $V$. In other words, each row of $U$ is drawn from a multivariate Gaussian with mean $\mu = 0$ and precision which is some multiple of the identity matrix $I$. Those multiples are $\alpha_U$ for $U$ and $\alpha_V$ for $V$. So our model is defined by:

$\newcommand\given[1][]{\:#1\vert\:}$

\begin{equation}
P(R \given U, V, \alpha^2) = 
    \prod_{i=1}^N \prod_{j=1}^M
        \left[ \mathcal{N}(R_{ij} \given U_i V_j^T, \alpha^{-1}) \right]^{I_{ij}}
\end{equation}

\begin{equation}
P(U \given \alpha_U^2) =
    \prod_{i=1}^N \mathcal{N}(U_i \given 0, \alpha_U^{-1} \boldsymbol{I})
\end{equation}

\begin{equation}
P(V \given \alpha_U^2) =
    \prod_{j=1}^M \mathcal{N}(V_j \given 0, \alpha_V^{-1} \boldsymbol{I})
\end{equation}

Given small precision parameters, the priors on $U$ and $V$ ensure our latent variables do not grow too far from 0. This prevents overly strong user preferences and item factor compositions from being learned. This is commonly known as complexity control, where the complexity of the model here is measured by the magnitude of the latent variables. Controlling complexity like this helps prevent overfitting, which allows the model to generalize better for unseen data. We must also choose an appropriate $\alpha$ value for the normal distribution for $R$. So the challenge becomes choosing appropriate values for $\alpha_U$, $\alpha_V$, and $\alpha$. This challenge can be tackled with the soft weight-sharing methods discussed by [Nowland and Hinton, 1992](http://www.cs.toronto.edu/~fritz/absps/sunspots.pdf) [4]. However, for the purposes of this analysis, we will stick to using point estimates obtained from our data.


```
import time
import logging
import pymc3 as pm
import theano
import scipy as sp


# Enable on-the-fly graph computations, but ignore 
# absence of intermediate test values.
theano.config.compute_test_value = 'ignore'

# Set up logging.
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PMF(object):
    """Probabilistic Matrix Factorization model using pymc3."""

    def __init__(self, train, dim, alpha=2, std=0.01, bounds=(-10, 10)):
        """Build the Probabilistic Matrix Factorization model using pymc3.

        :param np.ndarray train: The training data to use for learning the model.
        :param int dim: Dimensionality of the model; number of latent factors.
        :param int alpha: Fixed precision for the likelihood function.
        :param float std: Amount of noise to use for model initialization.
        :param (tuple of int) bounds: (lower, upper) bound of ratings.
            These bounds will simply be used to cap the estimates produced for R.

        """
        self.dim = dim
        self.alpha = alpha
        self.std = np.sqrt(1.0 / alpha)
        self.bounds = bounds
        self.data = train.copy()
        n, m = self.data.shape

        # Perform mean value imputation
        nan_mask = np.isnan(self.data)
        self.data[nan_mask] = self.data[~nan_mask].mean()

        # Low precision reflects uncertainty; prevents overfitting.
        # Set to the mean variance across users and items.
        self.alpha_u = 1 / self.data.var(axis=1).mean()
        self.alpha_v = 1 / self.data.var(axis=0).mean()

        # Specify the model.
        logging.info('building the PMF model')
        with pm.Model() as pmf:
            U = pm.MvNormal(
                'U', mu=0, tau=self.alpha_u * np.eye(dim),
                shape=(n, dim), testval=np.random.randn(n, dim) * std)
            V = pm.MvNormal(
                'V', mu=0, tau=self.alpha_v * np.eye(dim),
                shape=(m, dim), testval=np.random.randn(m, dim) * std)
            R = pm.Normal(
                'R', mu=theano.tensor.dot(U, V.T), tau=self.alpha * np.ones((n, m)),
                observed=self.data)

        logging.info('done building the PMF model') 
        self.model = pmf
        
    def __str__(self):
        return self.name
   
```

We'll also need functions for calculating the MAP and performing sampling on our PMF model. When the observation noise variance $\alpha$ and the prior variances $\alpha_U$ and $\alpha_V$ are all kept fixed, maximizing the log posterior is equivalent to minimizing the sum-of-squared-errors objective function with quadratic regularization terms.

$$
E = \frac{1}{2} \sum_{i=1}^N \sum_{j=1}^M I_{ij} (R_{ij} - U_i V_j^T)^2 +
    \frac{\lambda_U}{2} \sum_{i=1}^N \|U\|_{Fro}^2 +
    \frac{\lambda_V}{2} \sum_{j=1}^M \|V\|_{Fro}^2,
$$

where $\lambda_U = \alpha_U / \alpha$, $\lambda_V = \alpha_V / \alpha$, and $\|\cdot\|_{Fro}^2$ denotes the Frobenius norm [3]. Minimizing this objective function gives a local minimum, which is essentially a maximum a posteriori (MAP) estimate. While it is possible to use a fast Stochastic Gradient Descent procedure to find this MAP, we'll be finding it using the utilities built into `pymc3`. In particular, we'll use `find_MAP` with Powell optimization (`scipy.optimize.fmin_powell`). Having found this MAP estimate, we can use it as our starting point for MCMC sampling.

Since it is a reasonably complex model, we expect the MAP estimation to take some time. So let's save it after we've found it. Note that we define a function for finding the MAP below, assuming it will receive a namespace with some variables in it. Then we attach that function to the PMF class, where it will have such a namespace after initialization. The PMF class is defined in pieces this way so I can say a few things between each piece to make it clearer.


```
try:
    import ujson as json
except ImportError:
    import json


# First define functions to save our MAP estimate after it is found.
# We adapt these from `pymc3`'s `backends` module, where the original
# code is used to save the traces from MCMC samples.
def save_np_vars(vars, savedir):
    """Save a dictionary of numpy variables to `savedir`. We assume
    the directory does not exist; an OSError will be raised if it does.
    """
    logging.info('writing numpy vars to directory: %s' % savedir)
    os.mkdir(savedir)
    shapes = {}
    for varname in vars:
        data = vars[varname]
        var_file = os.path.join(savedir, varname + '.txt')
        np.savetxt(var_file, data.reshape(-1, data.size))
        shapes[varname] = data.shape

        ## Store shape information for reloading.
        shape_file = os.path.join(savedir, 'shapes.json')
        with open(shape_file, 'w') as sfh:
            json.dump(shapes, sfh)
            
            
def load_np_vars(savedir):
    """Load numpy variables saved with `save_np_vars`."""
    shape_file = os.path.join(savedir, 'shapes.json')
    with open(shape_file, 'r') as sfh:
        shapes = json.load(sfh)

    vars = {}
    for varname, shape in shapes.items():
        var_file = os.path.join(savedir, varname + '.txt')
        vars[varname] = np.loadtxt(var_file).reshape(shape)
        
    return vars


# Now define the MAP estimation infrastructure.
def _map_dir(self):
    basename = 'pmf-map-d%d' % self.dim
    return os.path.join('data', basename)

def _find_map(self):
    """Find mode of posterior using Powell optimization."""
    tstart = time.time()
    with self.model:
        logging.info('finding PMF MAP using Powell optimization...')
        self._map = pm.find_MAP(fmin=sp.optimize.fmin_powell, disp=True)

    elapsed = int(time.time() - tstart)
    logging.info('found PMF MAP in %d seconds' % elapsed)
    
    # This is going to take a good deal of time to find, so let's save it.
    save_np_vars(self._map, self.map_dir)
    
def _load_map(self):
    self._map = load_np_vars(self.map_dir)

def _map(self):
    try:
        return self._map
    except:
        if os.path.isdir(self.map_dir):
            self.load_map()
        else:
            self.find_map()
        return self._map

    
# Update our class with the new MAP infrastructure.
PMF.find_map = _find_map
PMF.load_map = _load_map
PMF.map_dir = property(_map_dir)
PMF.map = property(_map)
```

So now our PMF class has a `map` `property` which will either be found using Powell optimization or loaded from a previous optimization. Once we have the MAP, we can use it as a starting point for our MCMC sampler. We'll need a sampling function in order to draw MCMC samples to approximate the posterior distribution of the PMF model.


```
# Draw MCMC samples.
def _trace_dir(self):
    basename = 'pmf-mcmc-d%d' % self.dim
    return os.path.join('data', basename)

def _draw_samples(self, nsamples=1000, njobs=2):
    # First make sure the trace_dir does not already exist.
    if os.path.isdir(self.trace_dir):
        raise OSError(
            'trace directory %s already exists. Please move or delete.' % self.trace_dir)
    start = self.map  # use our MAP as the starting point
    with self.model:
        logging.info('drawing %d samples using %d jobs' % (nsamples, njobs))
        step = pm.NUTS(scaling=start)
        backend = pm.backends.Text(self.trace_dir)
        logging.info('backing up trace to directory: %s' % self.trace_dir)
        self.trace = pm.sample(nsamples, step, start=start, njobs=njobs, trace=backend)
        
def _load_trace(self):
    with self.model:
        self.trace = pm.backends.text.load(self.trace_dir)

        
# Update our class with the sampling infrastructure.
PMF.trace_dir = property(_trace_dir)
PMF.draw_samples = _draw_samples
PMF.load_trace = _load_trace
```

We could define some kind of default trace property like we did for the MAP, but that would mean using possibly nonsensical values for `nsamples` and `njobs`. Better to leave it as a non-optional call to `draw_samples`. Finally, we'll need a function to make predictions using our inferred values for $U$ and $V$. For user $i$ and joke $j$, a prediction is generated by drawing from $\mathcal{N}(U_i V_j^T, \alpha)$. To generate predictions from the sampler, we generate an $R$ matrix for each $U$ and $V$ sampled, then we combine these by averaging over the $K$ samples.

\begin{equation}
P(R_{ij}^* \given R, \alpha, \alpha_U, \alpha_V) \approx
    \frac{1}{K} \sum_{k=1}^K \mathcal{N}(U_i V_j^T, \alpha)
\end{equation}

We'll want to inspect the individual $R$ matrices before averaging them for diagnostic purposes. So we'll write code for the averaging piece during evaluation. The function below simply draws an $R$ matrix given a $U$ and $V$ and the fixed $\alpha$ stored in the PMF object.


```
def _predict(self, U, V):
    """Estimate R from the given values of U and V."""
    R = np.dot(U, V.T)
    n, m = R.shape
    sample_R = np.array([
        [np.random.normal(R[i,j], self.std) for j in xrange(m)]
        for i in xrange(n)
    ])

    # bound ratings
    low, high = self.bounds
    sample_R[sample_R < low] = low
    sample_R[sample_R > high] = high
    return sample_R


PMF.predict = _predict
```

One final thing to note: the dot products in this model are often constrained using a logistic function $g(x) = 1/(1 + exp(-x))$, that bounds the predictions to the range [0, 1]. To facilitate this bounding, the ratings are also mapped to the range [0, 1] using $t(x) = (x + min) / range$. The authors of PMF also introduced a constrained version which performs better on users with less ratings [3]. Both models are generally improvements upon the basic model presented here. However, in the interest of time and space, these will not be implemented here.

# Evaluation

## Metrics

In order to understand how effective our models are, we'll need to be able to evaluate them. We'll be evaluating in terms of root mean squared error (RMSE), which looks like this:

\begin{equation}
RMSE = \sqrt{ \frac{ \sum_{i=1}^N \sum_{j=1}^M I_{ij} (R_{ij} - R_{ij}^*)^2 }
                   { \sum_{i=1}^N \sum_{j=1}^M I_{ij} } }
\end{equation}

In this case, the RMSE can be thought of as the standard deviation of our predictions from the actual user preferences.


```
# Define our evaluation function.
def rmse(test_data, predicted):
    """Calculate root mean squared error.
    Ignoring missing values in the test data.
    """
    I = ~np.isnan(test_data)   # indicator for missing values
    N = I.sum()                # number of non-missing values
    sqerror = abs(test_data - predicted) ** 2  # squared error array
    mse = sqerror[I].sum() / N                 # mean squared error
    return np.sqrt(mse)                        # RMSE
```

## Training Data vs. Test Data

The next thing we need to do is split our data into a training set and a test set. Matrix factorization techniques use [transductive learning](http://en.wikipedia.org/wiki/Transduction_%28machine_learning%29) rather than inductive learning. So we produce a test set by taking a random sample of the cells in the full $N \times M$ data matrix. The values selected as test samples are replaced with `nan` values in a copy of the original data matrix to produce the training set. Since we'll be producing random splits, let's also write out the train/test sets generated. This will allow us to replicate our results. We'd like to be able to idenfity which split is which, so we'll take a hash of the indices selected for testing and use that to save the data.


```
import hashlib


# Define a function for splitting train/test data.
def split_train_test(data, percent_test=10):
    """Split the data into train/test sets.
    :param int percent_test: Percentage of data to use for testing. Default 10.
    """
    n, m = data.shape             # # users, # jokes
    N = n * m                     # # cells in matrix
    test_size = N / percent_test  # use 10% of data as test set
    train_size = N - test_size    # and remainder for training

    # Prepare train/test ndarrays.
    train = data.copy().values
    test = np.ones(data.shape) * np.nan

    # Draw random sample of training data to use for testing.
    tosample = np.where(~np.isnan(train))       # ignore nan values in data
    idx_pairs = zip(tosample[0], tosample[1])   # tuples of row/col index pairs
    indices = np.arange(len(idx_pairs))         # indices of index pairs
    sample = np.random.choice(indices, replace=False, size=test_size)

    # Transfer random sample from train set to test set.
    for idx in sample:
        idx_pair = idx_pairs[idx]
        test[idx_pair] = train[idx_pair]  # transfer to test set
        train[idx_pair] = np.nan          # remove from train set

    # Verify everything worked properly
    assert(np.isnan(train).sum() == test_size)
    assert(np.isnan(test).sum() == train_size)
    
    # Finally, hash the indices and save the train/test sets.
    index_string = ''.join(map(str, np.sort(sample)))
    name = hashlib.sha1(index_string).hexdigest()
    savedir = os.path.join('data', name)
    save_np_vars({'train': train, 'test': test}, savedir)
    
    # Return train set, test set, and unique hash of indices.
    return train, test, name


def load_train_test(name):
    """Load the train/test sets."""
    savedir = os.path.join('data', name)
    vars = load_np_vars(savedir)
    return vars['train'], vars['test']

# train, test, name = split_train_test(data)
```

In order to facilitate reproducibility, I've produced a train/test split using the code above which we'll now use for all the evaluations below.


```
train, test = load_train_test('6bb8d06c69c0666e6da14c094d4320d115f1ffc8')
```

# Results


```
# Let's see the results:
baselines = {}
for name in baseline_methods:
    Method = baseline_methods[name]
    method = Method(train)
    baselines[name] = method.rmse(test)
    print '%s RMSE:\t%.5f' % (method, baselines[name])

```

    Uniform Random Baseline RMSE:	7.77062
    Global Mean Baseline RMSE:	5.25004
    Mean Of Means Baseline RMSE:	4.79832


As expected: the uniform random baseline is the worst by far, the global mean baseline is next best, and the mean of means method is our best baseline. Now let's see how PMF stacks up.


```
# We use a fixed precision for the likelihood.
# This reflects uncertainty in the dot product.
# We choose 2 in the footsteps Salakhutdinov
# Mnihof.
ALPHA = 2

# The dimensionality D; the number of latent factors.
# We can adjust this higher to try to capture more subtle
# characteristics of each joke. However, the higher it is,
# the more expensive our inference procedures will be.
# Specifically, we have D(N + M) latent variables. For our
# Jester dataset, this means we have D(1100), so for 5
# dimensions, we are sampling 5500 latent variables.
DIM = 5


pmf = PMF(train, DIM, ALPHA, std=0.05)
```

    INFO:root:building the PMF model
    INFO:root:done building the PMF model


## Predictions Using MAP


```
# Find MAP for PMF.
pmf.find_map()
# pmf.load_map()
```

    INFO:root:finding MAP using Powell optimization...
    INFO:root:found MAP in 2575 seconds


    Optimization terminated successfully.
             Current function value: 1553644.881552
             Iterations: 33
             Function evaluations: 1644948


Excellent. The first thing we want to do is make sure the MAP estimate we obtained is reasonable. We can do this by computing RMSE on the predicted ratings obtained from the MAP values of $U$ and $V$. First we define a function for generating the predicted ratings $R$ from $U$ and $V$. We ensure the actual rating bounds are enforced by setting all values below -10 to -10 and all values above 10 to 10. Finally, we compute RMSE for both the training set and the test set. We expect the test RMSE to be higher. The difference between the two gives some idea of how much we have overfit. Some difference is always expected, but a very low RMSE on the training set with a high RMSE on the test set is a definite sign of overfitting.


```
def eval_map(pmf_model, train, test):
    U = pmf_model.map['U']
    V = pmf_model.map['V']
    
    # Make predictions and calculate RMSE on train & test sets.
    predictions = pmf_model.predict(U, V)
    train_rmse = rmse(train, predictions)
    test_rmse = rmse(test, predictions)
    overfit = test_rmse - train_rmse
    
    # Print report.
    print 'PMF MAP training RMSE: %.5f' % train_rmse
    print 'PMF MAP testing RMSE:  %.5f' % test_rmse
    print 'Train/test difference: %.5f' % overfit
    
    return test_rmse
    

# Add eval function to PMF class.
PMF.eval_map = eval_map
```


```
# Evaluate PMF MAP estimates.
pmf_map_rmse = pmf.eval_map(train, test)
pmf_improvement = baselines['mom'] - pmf_map_rmse
print 'PMF MAP Improvement:   %.5f' % pmf_improvement
```

    PMF MAP training RMSE: 4.00824
    PMF MAP testing RMSE:  4.02974
    Train/test difference: 0.02150
    PMF MAP Improvement:   0.76858


So we see a pretty nice improvement here when compared to our best baseline, which was the mean of means method. We also have a fairly small difference in the RMSE values between the train and the test sets. This indicates that the point estimates for $\alpha_U$ and $\alpha_V$ that we calculated from our data are doing a good job of controlling model complexity. Now let's see if we can improve our estimates by approximating our posterior distribution with MCMC sampling. We'll draw 1000 samples and back them up using the `pymc3.backend.Text` backend.

## Predictions using MCMC


```
# Draw MCMC samples.
pmf.draw_samples(5000, njobs=3)

# uncomment to load previous trace rather than drawing new samples.
# pmf.load_trace()
```

    INFO:root:drawing 5000 samples using 3 jobs
    /home/mack/anaconda/lib/python2.7/site-packages/theano/scan_module/scan_perform_ext.py:133: RuntimeWarning: numpy.ndarray size changed, may indicate binary incompatibility
      from scan_perform.scan_perform import *
    INFO:root:backing up trace to directory: data/pmf-mcmc-d5


     [-----------------100%-----------------] 5001 of 5000 complete in 7506.2 sec

### Diagnostics and Posterior Predictive Check

The next step is to check how many samples we should discard as burn-in. Normally, we'd do this using a traceplot to get some idea of where the sampled variables start to converge. In this case, we have high-dimensional samples, so we need to find a way to approximate them. One way was proposed by [Salakhutdinov and Mnih, p.886](https://www.cs.toronto.edu/~amnih/papers/bpmf.pdf). We can calculate the Frobenius norms of $U$ and $V$ at each step and monitor those for convergence. This essentially gives us some idea when the average magnitude of the latent variables is stabilizing. The equations for the Frobenius norms of $U$ and $V$ are shown below. We will use `numpy`'s `linalg` package to calculate these.

$$
\|U\|_{Fro}^2 = \sqrt{\sum_{i=1}^N \sum_{d=1}^D |U_{id}|^2}, \hspace{40pt}
\|V\|_{Fro}^2 = \sqrt{\sum_{j=1}^M \sum_{d=1}^D |V_{jd}|^2}
$$


```
def _norms(pmf_model, monitor=('U', 'V'), ord='fro'):
    """Return norms of latent variables at each step in the
    sample trace. These can be used to monitor convergence
    of the sampler.
    """
    monitor = ('U', 'V')
    norms = {var: [] for var in monitor}
    for sample in pmf_model.trace:
        for var in monitor:
            norms[var].append(np.linalg.norm(sample[var], ord))
    return norms


def _traceplot(pmf_model):
    """Plot Frobenius norms of U and V as a function of sample #."""
    trace_norms = pmf_model.norms()
    u_series = pd.Series(trace_norms['U'])
    v_series = pd.Series(trace_norms['V'])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    u_series.plot(kind='line', ax=ax1, grid=False,
                  title="$\|U\|_{Fro}^2$ at Each Sample")
    v_series.plot(kind='line', ax=ax2, grid=False,
                  title="$\|V\|_{Fro}^2$ at Each Sample")
    ax1.set_xlabel("Sample Number")
    ax2.set_xlabel("Sample Number")
    
    
PMF.norms = _norms
PMF.traceplot = _traceplot
```


```
pmf.traceplot()
```


![png](pmf-pymc_files/pmf-pymc_44_0.png)


It appears we get convergence of $U$ and $V$ after about 200 samples. When testing for convergence, we also want to see convergence of the particular statistics we are looking for, since different characteristics of the posterior may converge at different rates. Let's also do a traceplot of the RSME. We'll compute RMSE for both the train and the test set, even though the convergence is indicated by RMSE on the training set alone. In addition, let's compute a running RMSE on the train/test sets to see how aggregate performance improves or decreases as we continue to sample.


```
def _running_rmse(pmf_model, test_data, train_data, burn_in=0, plot=True):
    """Calculate RMSE for each step of the trace to monitor convergence.
    """
    burn_in = burn_in if len(pmf_model.trace) >= burn_in else 0
    results = {'per-step-train': [], 'running-train': [],
               'per-step-test': [], 'running-test': []}
    R = np.zeros(test_data.shape)
    for cnt, sample in enumerate(pmf_model.trace[burn_in:]):
        sample_R = pmf_model.predict(sample['U'], sample['V'])
        R += sample_R
        running_R = R / (cnt + 1)
        results['per-step-train'].append(rmse(train_data, sample_R))
        results['running-train'].append(rmse(train_data, running_R))
        results['per-step-test'].append(rmse(test_data, sample_R))
        results['running-test'].append(rmse(test_data, running_R))
    
    results = pd.DataFrame(results)

    if plot:
        results.plot(
            kind='line', grid=False, figsize=(15, 7),
            title='Per-step and Running RMSE From Posterior Predictive')
        
    # Return the final predictions, and the RMSE calculations
    return running_R, results


PMF.running_rmse = _running_rmse
```


```
predicted, results = pmf.running_rmse(test, train, burn_in=200)
```


![png](pmf-pymc_files/pmf-pymc_47_0.png)



```
# And our final RMSE?
final_test_rmse = results['running-test'].values[-1]
final_train_rmse = results['running-train'].values[-1]
print 'Posterior predictive train RMSE: %.5f' % final_train_rmse
print 'Posterior predictive test RMSE:  %.5f' % final_test_rmse
print 'Train/test difference:           %.5f' % (final_test_rmse - final_train_rmse)
print 'Improvement from MAP:            %.5f' % (pmf_map_rmse - final_test_rmse)
print 'Improvement from Mean of Means:  %.5f' % (baselines['mom'] - final_test_rmse)
```

    Posterior predictive train RMSE: 3.92230
    Posterior predictive test RMSE:  4.18027
    Train/test difference:           0.25797
    Improvement from MAP:            -0.15052
    Improvement from Mean of Means:  0.61806


We have some interesting results here. As expected, our MCMC sampler provides lower error on the training set. However, it seems it does so at the cost of overfitting the data. This results in a decrease in test RMSE as compared to the MAP, even though it is still much better than our best baseline. So why might this be the case? Recall that we used point estimates for our precision paremeters $\alpha_U$ and $\alpha_V$ and we chose a fixed precision $\alpha$. It is quite likely that by doing this, we constrained our posterior in a way that biased it towards the training data. In reality, the variance in the user ratings and the joke ratings is unlikely to be equal to the means of sample variances we used. Also, the most reasonable observation precision $\alpha$ is likely different as well.

## Summary of Results

Let's summarize our results.


```
size = 100  # RMSE doesn't really change after 100th sample anyway.
all_results = pd.DataFrame({
    'uniform random': np.repeat(baselines['ur'], size),
    'global means': np.repeat(baselines['gm'], size),
    'mean of means': np.repeat(baselines['mom'], size),
    'PMF MAP': np.repeat(pmf_map_rmse, size),
    'PMF MCMC': results['running-test'][:size],
})
fig, ax = plt.subplots(figsize=(10, 5))
all_results.plot(kind='line', grid=False, ax=ax,
                 title='RMSE for all methods')
ax.set_xlabel("Number of Samples")
ax.set_ylabel("RMSE")
```




    <matplotlib.text.Text at 0x7f5327451a10>




![png](pmf-pymc_files/pmf-pymc_51_1.png)


# Summary

We set out to predict user preferences for unseen jokes. First we discussed the intuitive notion behind the user-user and item-item neighborhood approaches to collaborative filtering. Then we formalized our intuitions. With a firm understanding of our problem context, we moved on to exploring our subset of the Jester data. After discovering some general patterns, we defined three baseline methods: uniform random, global mean, and mean of means. With the goal of besting our baseline methods, we implemented the basic version of Probabilistic Matrix Factorization (PMF) using `pymc3`.

Our results demonstrate that the mean of means method is our best baseline on our prediction task. As expected, we are able to obtain a significant decrease in RMSE using the PMF MAP estimate obtained via Powell optimization. We illustrated one way to monitor convergence of an MCMC sampler with a high-dimensionality sampling space using the Frobenius norms of the sampled variables. The traceplots using this method seem to indicate that our sampler converged to the posterior. Results using this posterior showed that attempting to improve the MAP estimation using MCMC sampling actually overfit the training data and increased test RMSE. This was likely caused by the constraining of the posterior via fixed precision parameters $\alpha$, $\alpha_U$, and $\alpha_V$.

As a followup to this analysis, it would be interesting to also implement the logistic and constrained versions of PMF. We expect both models to outperform the basic PMF model. We could also implement the [fully Bayesian version of PMF](https://www.cs.toronto.edu/~amnih/papers/bpmf.pdf) (BPMF), which places hyperpriors on the model parameters to automatically learn ideal mean and precision parameters for $U$ and $V$. This would likely resolve the issue we faced in this analysis. We would expect BPMF to improve upon the MAP estimation produced here by learning more suitable hyperparameters and parameters. For a basic (but working!) implementation of BPMF in `pymc3`, see [this gist](https://gist.github.com/macks22/00a17b1d374dfc267a9a).

If you made it this far, then congratulations! You now have some idea of how to build a basic recommender system. These same ideas and methods can be used on many different recommendation tasks. Items can be movies, products, advertisements, courses, or even other people. Any time you can build yourself a user-item matrix with user preferences in the cells, you can use these types of collaborative filtering algorithms to predict the missing values. If you want to learn more about recommender systems, the first reference is a good place to start.

## References

1.  Y. Koren, R. Bell, and C. Volinsky, “Matrix Factorization Techniques for Recommender Systems,” Computer, vol. 42, no. 8, pp. 30–37, Aug. 2009.
2.  K. Goldberg, T. Roeder, D. Gupta, and C. Perkins, “Eigentaste: A constant time collaborative filtering algorithm,” Information Retrieval, vol. 4, no. 2, pp. 133–151, 2001.
3.  A. Mnih and R. Salakhutdinov, “Probabilistic matrix factorization,” in Advances in neural information processing systems, 2007, pp. 1257–1264.
4.  S. J. Nowlan and G. E. Hinton, “Simplifying Neural Networks by Soft Weight-sharing,” Neural Comput., vol. 4, no. 4, pp. 473–493, Jul. 1992.
5.  R. Salakhutdinov and A. Mnih, “Bayesian Probabilistic Matrix Factorization Using Markov Chain Monte Carlo,” in Proceedings of the 25th International Conference on Machine Learning, New York, NY, USA, 2008, pp. 880–887.





