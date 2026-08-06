---
title: Geometric Brownian motion - Wikipedia
id: geometric-brownian-motion-wikipedia
created: '2026-08-06T06:58:03.561626Z'
source: https://en.wikipedia.org/wiki/Geometric_Brownian_motion
source_domain: en.wikipedia.org
fetched_at: '2026-08-06T06:58:03.561398Z'
fetch_provider: builtin
status: draft
type: note
tier: institutional
content_type: article
deprecated: false
---

Geometric Brownian motion - Wikipedia
Jump to content
From Wikipedia, the free encyclopedia
Continuous stochastic process
For the simulation generating the realizations, see below.
A
geometric Brownian motion
(
GBM
), also known as an
exponential Brownian motion
, is a continuous-time
stochastic process
in which the
logarithm
of the randomly varying quantity follows a
Brownian motion
with
drift
.
[
1
]
It is an important example of stochastic processes satisfying a
stochastic differential equation
(SDE); in particular, it is used in
mathematical finance
to model stock prices in the
Black–Scholes model
.
Stochastical differential equation
[
edit
]
A stochastic process
S
t
is said to follow a GBM if it satisfies the following
stochastic differential equation
(SDE):
d
S
t
=
μ
S
t
d
t
+
σ
S
t
d
W
t
{\displaystyle dS_{t}=\mu S_{t}\,dt+\sigma S_{t}\,dW_{t}}
where
W
t
{\displaystyle W_{t}}
is a
Wiener process or Brownian motion
, and
μ
{\displaystyle \mu }
('the percentage drift') and
σ
{\displaystyle \sigma }
('the percentage volatility') are constants.
The former parameter is used to model deterministic trends, while the latter parameter models unpredictable events occurring during the motion.
Solution
[
edit
]
For an arbitrary initial value
S
0
the above SDE has the analytic solution (under
Itô's interpretation
):
S
t
=
S
0
exp
⁡
(
(
μ
−
σ
2
2
)
t
+
σ
W
t
)
.
{\displaystyle S_{t}=S_{0}\exp \left(\left(\mu -{\frac {\sigma ^{2}}{2}}\right)t+\sigma W_{t}\right).}
The derivation requires the use of
Itô calculus
. Applying
Itô's formula
leads to
d
(
ln
⁡
S
t
)
=
(
ln
⁡
S
t
)
′
d
S
t
+
1
2
(
ln
⁡
S
t
)
″
d
S
t
d
S
t
=
d
S
t
S
t
−
1
2
1
S
t
2
d
S
t
d
S
t
{\displaystyle d(\ln S_{t})=(\ln S_{t})'dS_{t}+{\frac {1}{2}}(\ln S_{t})''\,dS_{t}\,dS_{t}={\frac {dS_{t}}{S_{t}}}-{\frac {1}{2}}\,{\frac {1}{S_{t}^{2}}}\,dS_{t}\,dS_{t}}
where
d
S
t
d
S
t
{\displaystyle dS_{t}\,dS_{t}}
is the
quadratic variation
of the SDE.
d
S
t
d
S
t
=
σ
2
S
t
2
d
W
t
2
+
2
σ
S
t
2
μ
d
W
t
d
t
+
μ
2
S
t
2
d
t
2
{\displaystyle dS_{t}\,dS_{t}\,=\,\sigma ^{2}\,S_{t}^{2}\,dW_{t}^{2}+2\sigma S_{t}^{2}\mu \,dW_{t}\,dt+\mu ^{2}S_{t}^{2}\,dt^{2}}
When
d
t
→
0
{\displaystyle dt\to 0}
,
d
t
{\displaystyle dt}
converges to 0 faster than
d
W
t
{\displaystyle dW_{t}}
, 
since
d
W
t
2
=
O
(
d
t
)
{\displaystyle dW_{t}^{2}=O(dt)}
. So the above infinitesimal can be simplified by
d
S
t
d
S
t
=
σ
2
S
t
2
d
t
{\displaystyle dS_{t}\,dS_{t}\,=\,\sigma ^{2}\,S_{t}^{2}\,dt}
Plugging the value of
d
S
t
{\displaystyle dS_{t}}
in the above equation and simplifying we obtain
ln
⁡
S
t
S
0
=
(
μ
−
σ
2
2
)
t
+
σ
W
t
.
{\displaystyle \ln {\frac {S_{t}}{S_{0}}}=\left(\mu -{\frac {\sigma ^{2}}{2}}\,\right)t+\sigma W_{t}\,.}
Taking the exponential and multiplying both sides by
S
0
{\displaystyle S_{0}}
gives the solution claimed above.
Arithmetic Brownian motion
[
edit
]
The process for
X
t
=
ln
⁡
S
t
S
0
{\displaystyle X_{t}=\ln {\frac {S_{t}}{S_{0}}}}
, satisfying the SDE
d
X
t
=
(
μ
−
σ
2
2
)
d
t
+
σ
d
W
t
,
{\displaystyle dX_{t}=\left(\mu -{\frac {\sigma ^{2}}{2}}\,\right)dt+\sigma dW_{t}\,,}
or more generally the process solving the SDE
d
X
t
=
m
d
t
+
v
d
W
t
,
{\displaystyle dX_{t}=m\,dt+v\,dW_{t}\,,}
where
m
{\displaystyle m}
and
v
>
0
{\displaystyle v>0}
are real constants and for an initial condition
X
0
{\displaystyle X_{0}}
, is called an Arithmetic Brownian Motion (ABM). This was the model postulated by
Louis Bachelier
in 1900 for stock prices, in the first published attempt to model Brownian motion, known today as
Bachelier model
. As was shown above, the ABM SDE can be obtained through the logarithm of a GBM via Itô's formula. Similarly, a GBM can be obtained by exponentiation of an ABM through Itô's formula.
Properties
[
edit
]
The above solution
S
t
{\displaystyle S_{t}}
(for any value of t) is a
log-normally distributed
random variable
with
expected value
and
variance
given by
[
2
]
E
⁡
(
S
t
)
=
S
0
e
μ
t
,
{\displaystyle \operatorname {E} (S_{t})=S_{0}e^{\mu t},}
Var
⁡
(
S
t
)
=
S
0
2
e
2
μ
t
(
e
σ
2
t
−
1
)
.
{\displaystyle \operatorname {Var} (S_{t})=S_{0}^{2}e^{2\mu t}\left(e^{\sigma ^{2}t}-1\right).}
They can be derived using the fact that
Z
t
=
exp
⁡
(
σ
W
t
−
1
2
σ
2
t
)
{\displaystyle Z_{t}=\exp \left(\sigma W_{t}-{\frac {1}{2}}\sigma ^{2}t\right)}
is a
martingale
, and that
E
⁡
[
exp
⁡
(
2
σ
W
t
−
σ
2
t
)
∣
F
s
]
=
e
σ
2
(
t
−
s
)
exp
⁡
(
2
σ
W
s
−
σ
2
s
)
,
∀
0
≤
s
<
t
.
{\displaystyle \operatorname {E} \left[\exp \left(2\sigma W_{t}-\sigma ^{2}t\right)\mid {\mathcal {F}}_{s}\right]=e^{\sigma ^{2}(t-s)}\exp \left(2\sigma W_{s}-\sigma ^{2}s\right),\quad \forall 0\leq s<t.}
The
probability density function
of
S
t
{\displaystyle S_{t}}
is:
f
S
t
(
s
;
μ
,
σ
,
t
)
=
1
2
π
1
s
σ
t
exp
⁡
(
−
(
ln
⁡
s
−
ln
⁡
S
0
−
(
μ
−
1
2
σ
2
)
t
)
2
2
σ
2
t
)
.
{\displaystyle f_{S_{t}}(s;\mu ,\sigma ,t)={\frac {1}{\sqrt {2\pi }}}\,{\frac {1}{s\sigma {\sqrt {t}}}}\,\exp \left(-{\frac {\left(\ln s-\ln S_{0}-\left(\mu -{\frac {1}{2}}\sigma ^{2}\right)t\right)^{2}}{2\sigma ^{2}t}}\right).}
Derivation of GBM probability density function
To derive the probability density function for GBM, we must use the
Fokker–Planck equation
to evaluate the time evolution of the PDF:
∂
p
∂
t
=
−
∂
∂
S
[
μ
S
p
(
t
,
S
)
]
+
1
2
∂
2
∂
S
2
[
σ
2
S
2
p
(
t
,
S
)
]
,
p
(
0
,
S
)
=
δ
(
S
−
S
0
)
{\displaystyle {\partial p \over {\partial t}}=-{\partial  \over {\partial S}}[\mu Sp(t,S)]+{1 \over {2}}{\partial ^{2} \over {\partial S^{2}}}[\sigma ^{2}S^{2}p(t,S)],\quad p(0,S)=\delta (S-S_{0})}
where
δ
(
S
)
{\displaystyle \delta (S)}
is the
Dirac delta function
. To simplify the computation, we may introduce a logarithmic transform
x
=
log
⁡
(
S
/
S
0
)
{\displaystyle x=\log(S/S_{0})}
, leading to the form of GBM:
d
x
=
(
μ
−
1
2
σ
2
)
d
t
+
σ
d
W
{\displaystyle dx=\left(\mu -{1 \over {2}}\sigma ^{2}\right)dt+\sigma \,dW}
Then the equivalent Fokker–Planck equation for the evolution of the PDF becomes:
∂
p
∂
t
+
(
μ
−
1
2
σ
2
)
∂
p
∂
x
=
1
2
σ
2
∂
2
p
∂
x
2
,
p
(
0
,
x
)
=
δ
(
x
)
{\displaystyle {\partial p \over {\partial t}}+\left(\mu -{1 \over {2}}\sigma ^{2}\right){\partial p \over {\partial x}}={1 \over {2}}\sigma ^{2}{\partial ^{2}p \over {\partial x^{2}}},\quad p(0,x)=\delta (x)}
Define
V
=
μ
−
σ
2
/
2
{\displaystyle V=\mu -\sigma ^{2}/2}
and
D
=
σ
2
/
2
{\displaystyle D=\sigma ^{2}/2}
. By introducing the new variables
ξ
=
x
−
V
t
{\displaystyle \xi =x-Vt}
and
τ
=
D
t
{\displaystyle \tau =Dt}
, the derivatives in the Fokker–Planck equation may be transformed as:
∂
t
p
=
D
∂
τ
p
−
V
∂
ξ
p
∂
x
p
=
∂
ξ
p
∂
x
2
p
=
∂
ξ
2
p
{\displaystyle {\begin{aligned}\partial _{t}p&=D\partial _{\tau }p-V\partial _{\xi }p\\\partial _{x}p&=\partial _{\xi }p\\\partial _{x}^{2}p&=\partial _{\xi }^{2}p\end{aligned}}}
Leading to the new form of the Fokker–Planck equation:
∂
p
∂
τ
=
∂
2
p
∂
ξ
2
,
p
(
0
,
ξ
)
=
δ
(
ξ
)
{\displaystyle {\partial p \over {\partial \tau }}={\partial ^{2}p \over {\partial \xi ^{2}}},\quad p(0,\xi )=\delta (\xi )}
However, this is the canonical form of the
heat equation
. which has the solution given by the
heat kernel
:
p
(
τ
,
ξ
)
=
1
4
π
τ
exp
⁡
(
−
ξ
2
4
τ
)
{\displaystyle p(\tau ,\xi )={1 \over {\sqrt {4\pi \tau }}}\exp \left(-{\xi ^{2} \over 4\tau }\right)}
Plugging in the original variables leads to the PDF for GBM:
p
(
t
,
S
)
=
1
S
2
π
σ
2
t
exp
⁡
{
−
[
log
⁡
(
S
/
S
0
)
−
(
μ
−
1
2
σ
2
)
t
]
2
2
σ
2
t
}
{\displaystyle p(t,S)={1 \over {S{\sqrt {2\pi \sigma ^{2}t}}}}\exp \left\{-{\left[\log(S/S_{0})-\left(\mu -{1 \over 2}\sigma ^{2}\right)t\right]^{2} \over {2\sigma ^{2}t}}\right\}}
When deriving further properties of GBM, use can be made of the SDE of which GBM is the solution, or the explicit solution given above can be used. For example, consider the stochastic process log(
S
t
). This is an interesting process, because in the  Black–Scholes model it is related to the
log return
of the stock price. Using
Itô's lemma
with
f
(
S
) = log(
S
) gives
d
log
⁡
(
S
)
=
f
′
(
S
)
d
S
+
1
2
f
″
(
S
)
S
2
σ
2
d
t
=
1
S
(
σ
S
d
W
t
+
μ
S
d
t
)
−
1
2
σ
2
d
t
=
σ
d
W
t
+
(
μ
−
σ
2
/
2
)
d
t
.
{\displaystyle {\begin{alignedat}{2}d\log(S)&=f'(S)\,dS+{\frac {1}{2}}f''(S)S^{2}\sigma ^{2}\,dt\\[6pt]&={\frac {1}{S}}\left(\sigma S\,dW_{t}+\mu S\,dt\right)-{\frac {1}{2}}\sigma ^{2}\,dt\\[6pt]&=\sigma \,dW_{t}+(\mu -\sigma ^{2}/2)\,dt.\end{alignedat}}}
It follows that
E
⁡
log
⁡
(
S
t
)
=
log
⁡
(
S
0
)
+
(
μ
−
σ
2
/
2
)
t
{\displaystyle \operatorname {E} \log(S_{t})=\log(S_{0})+(\mu -\sigma ^{2}/2)t}
.
This result can also be derived by applying the logarithm to the explicit solution of GBM:
log
⁡
(
S
t
)
=
log
⁡
(
S
0
exp
⁡
(
(
μ
−
σ
2
2
)
t
+
σ
W
t
)
)
=
log
⁡
(
S
0
)
+
(
μ
−
σ
2
2
)
t
+
σ
W
t
.
{\displaystyle {\begin{alignedat}{2}\log(S_{t})&=\log \left(S_{0}\exp \left(\left(\mu -{\frac {\sigma ^{2}}{2}}\right)t+\sigma W_{t}\right)\right)\\[6pt]&=\log(S_{0})+\left(\mu -{\frac {\sigma ^{2}}{2}}\right)t+\sigma W_{t}.\end{alignedat}}}
Taking the expectation yields the same result as above:
E
⁡
log
⁡
(
S
t
)
=
log
⁡
(
S
0
)
+
(
μ
−
σ
2
/
2
)
t
{\displaystyle \operatorname {E} \log(S_{t})=\log(S_{0})+(\mu -\sigma ^{2}/2)t}
.
Multivariate version
[
edit
]
GBM can be extended to the case where there are multiple correlated price paths.
[
3
]
Each price path follows the underlying process
d
S
t
i
=
μ
i
S
t
i
d
t
+
σ
i
S
t
i
d
W
t
i
,
{\displaystyle dS_{t}^{i}=\mu _{i}S_{t}^{i}\,dt+\sigma _{i}S_{t}^{i}\,dW_{t}^{i},}
where the Wiener processes are correlated such that
E
⁡
(
d
W
t
i
d
W
t
j
)
=
ρ
i
,
j
d
t
{\displaystyle \operatorname {E} (dW_{t}^{i}\,dW_{t}^{j})=\rho _{i,j}\,dt}
where
ρ
i
,
i
=
1
{\displaystyle \rho _{i,i}=1}
.
For the multivariate case, this implies that
Cov
⁡
(
S
t
i
,
S
t
j
)
=
S
0
i
S
0
j
e
(
μ
i
+
μ
j
)
t
(
e
ρ
i
,
j
σ
i
σ
j
t
−
1
)
.
{\displaystyle \operatorname {Cov} (S_{t}^{i},S_{t}^{j})=S_{0}^{i}S_{0}^{j}e^{(\mu _{i}+\mu _{j})t}\left(e^{\rho _{i,j}\sigma _{i}\sigma _{j}t}-1\right).}
A multivariate formulation that maintains the driving Brownian motions
W
t
i
{\displaystyle W_{t}^{i}}
independent is
d
S
t
i
=
μ
i
S
t
i
d
t
+
∑
j
=
1
d
σ
i
,
j
S
t
i
d
W
t
j
,
{\displaystyle dS_{t}^{i}=\mu _{i}S_{t}^{i}\,dt+\sum _{j=1}^{d}\sigma _{i,j}S_{t}^{i}\,dW_{t}^{j},}
where the correlation between
S
t
i
{\displaystyle S_{t}^{i}}
and
S
t
j
{\displaystyle S_{t}^{j}}
is now expressed through the
σ
i
,
j
=
ρ
i
,
j
σ
i
σ
j
{\displaystyle \sigma _{i,j}=\rho _{i,j}\,\sigma _{i}\,\sigma _{j}}
terms.
Use in finance
[
edit
]
Main article:
Black–Scholes model
Geometric Brownian motion is used to model stock prices in the Black–Scholes model and is the most widely used model of stock price behavior.
[
4
]
Some of the arguments for using GBM to model stock prices are:
The expected returns of GBM are independent of the value of the process (stock price), which agrees with what we would expect in reality.
[
4
]
A GBM process only assumes positive values, just like real stock prices.
A GBM process shows the same kind of 'roughness' in its paths as we see in real stock prices.
Calculations with GBM processes are relatively easy.
However, GBM is not a completely realistic model, in particular it falls short of reality in the following points:
In real stock prices, volatility changes over time (possibly
stochastically
), but in GBM, volatility is assumed constant.
In real life, stock prices often show jumps caused by unpredictable events or news, but in GBM, the path is continuous (no discontinuity).
Apart from modeling stock prices, Geometric Brownian motion has also found applications in the monitoring of trading strategies.
[
5
]
Extensions
[
edit
]
In an attempt to make GBM more realistic as a model for stock prices, also in relation to the
volatility smile
problem, one can drop the assumption that the volatility (
σ
{\displaystyle \sigma }
) is constant. If we assume that the volatility is a
deterministic
function of the stock price and time, this is called a
local volatility
model. A straightforward extension of the Black Scholes GBM is a local volatility SDE whose distribution is a mixture of distributions of GBM, the lognormal mixture dynamics, resulting in a convex combination of Black Scholes prices for options.
[
3
]
[
6
]
[
7
]
[
8
]
If instead we assume that the volatility has a randomness of its own—often described by a different equation driven by a different Brownian Motion—the model is called a
stochastic volatility
model, see for example the
Heston model
.
[
9
]
See also
[
edit
]
Brownian surface
Feynman–Kac formula
References
[
edit
]
↑
Ross, Sheldon M. (2014).
"Variations on Brownian Motion"
.
Introduction to Probability Models
(11th
ed.). Amsterdam: Elsevier. pp.
612–
14.
ISBN
978-0-12-407948-9
.
↑
Øksendal, Bernt K. (2002),
Stochastic Differential Equations: An Introduction with Applications
, Springer, p.
326,
ISBN
3-540-63720-6
1
2
Musiela, M., and Rutkowski, M. (2004), Martingale Methods in Financial Modelling, 2nd Edition, Springer Verlag, Berlin.
1
2
Hull, John (2009). "12.3".
Options, Futures, and other Derivatives
(7
ed.).
↑
Rej, A.; Seager, P.; Bouchaud, J.-P. (January 2018).
"You are in a drawdown. When should you start worrying?"
.
Wilmott
.
2018
(93):
56–
59.
arXiv
:
1707.01457
.
doi
:
10.1002/wilm.10646
.
S2CID
157827746
.
↑
Fengler, M. R. (2005), Semiparametric modeling of implied volatility, Springer Verlag, Berlin. DOI
https://doi.org/10.1007/3-540-30591-2
↑
Brigo, Damiano
;
Mercurio, Fabio
(2002). "Lognormal-mixture dynamics and calibration to market volatility smiles".
International Journal of Theoretical and Applied Finance
.
5
(4):
427–
446.
doi
:
10.1142/S0219024902001511
.
↑
Brigo, D, Mercurio, F, Sartorelli, G. (2003). Alternative asset-price dynamics and volatility smile, QUANT FINANC, 2003, Vol: 3, Pages: 173 - 183,
ISSN
1469-7688
↑
Heston, Steven L.
(1993). "A closed-form solution for options with stochastic volatility with applications to bond and currency options".
Review of Financial Studies
.
6
(2):
327–
343.
doi
:
10.1093/rfs/6.2.327
.
JSTOR
2962057
.
S2CID
16091300
.
External links
[
edit
]
Geometric Brownian motion models for stock movement except in rare events.
Excel Simulation of a Geometric Brownian Motion to simulate Stock Prices
"Interactive Web Application: Stochastic Processes used in Quantitative Finance"
. Archived from
the original
on 2015-09-20
. Retrieved
2015-07-03
.
v
t
e
Stochastic processes
Discrete time
Bernoulli process
Branching process
Chinese restaurant process
Galton–Watson process
Independent and identically distributed random variables
Markov chain
Moran process
Random walk
Loop-erased
Self-avoiding
Biased
Maximal entropy
Continuous time
Additive process
Airy process
Bessel process
Birth–death process
pure birth
Brownian motion
Bridge
Dyson
Excursion
Fractional
Geometric
Meander
Cauchy process
Contact process
Continuous-time random walk
Cox process
Diffusion process
Empirical process
Feller process
Fleming–Viot process
Gamma process
Geometric process
Hawkes process
Hunt process
Interacting particle systems
Itô diffusion
Itô process
Jump diffusion
Jump process
Lévy process
Local time
Markov additive process
McKean–Vlasov process
Ornstein–Uhlenbeck process
Poisson process
Compound
Non-homogeneous
Quasimartingale
Schramm–Loewner evolution
Semimartingale
Sigma-martingale
Stable process
Superprocess
Telegraph process
Variance gamma process
Wiener process
Wiener sausage
Both
Branching process
Gaussian process
Hidden Markov model (HMM)
Markov process
Martingale
Differences
Local
Sub-
Super-
Random dynamical system
Regenerative process
Renewal process
Stochastic chains with memory of variable length
White noise
Fields and other
Dirichlet process
Gaussian random field
Gibbs measure
Hopfield model
Ising model
Potts model
Boolean network
Markov random field
Percolation
Pitman–Yor process
Point process
Cox
Determinantal
Poisson
Random field
Random graph
Time series models
Autoregressive conditional heteroskedasticity (ARCH) model
Autoregressive integrated moving average (ARIMA) model
Autoregressive (AR) model
Autoregressive moving-average (ARMA) model
Generalized autoregressive conditional heteroskedasticity (GARCH) model
Moving-average (MA) model
Financial models
Binomial options pricing model
Black–Derman–Toy
Black–Karasinski
Black–Scholes
Chan–Karolyi–Longstaff–Sanders (CKLS)
Chen
Constant elasticity of variance (CEV)
Cox–Ingersoll–Ross (CIR)
Garman–Kohlhagen
Heath–Jarrow–Morton (HJM)
Heston
Ho–Lee
Hull–White
Korn-Kreer-Lenssen
LIBOR market
Rendleman–Bartter
SABR volatility
Vašíček
Wilkie
Actuarial models
Bühlmann
Cramér–Lundberg
Risk process
Sparre–Anderson
Queueing models
Bulk
Fluid
Generalized queueing network
M/G/1
M/M/1
M/M/c
Properties
Càdlàg paths
Continuous
Continuous paths
Ergodic
Exchangeable
Feller-continuous
Gauss–Markov
Markov
Mixing
Piecewise-deterministic
Predictable
Progressively measurable
Self-similar
Stationary
Time-reversible
Limit theorems
Central limit theorem
Donsker's theorem
Doob's martingale convergence theorems
Ergodic theorem
Fisher–Tippett–Gnedenko theorem
Large deviation principle
Law of large numbers (weak/strong)
Law of the iterated logarithm
Maximal ergodic theorem
Sanov's theorem
Zero–one laws
(
Blumenthal
,
Borel–Cantelli
,
Engelbert–Schmidt
,
Hewitt–Savage
,
Kolmogorov
,
Lévy
)
Inequalities
Burkholder–Davis–Gundy
Doob's martingale
Doob's upcrossing
Kunita–Watanabe
Marcinkiewicz–Zygmund
Tools
Cameron–Martin theorem
Convergence of random variables
Doléans-Dade exponential
Doob decomposition theorem
Doob–Meyer decomposition theorem
Doob's optional stopping theorem
Dynkin's formula
Feynman–Kac formula
Filtration
Girsanov theorem
Infinitesimal generator
Itô integral
Itô's lemma
Kolmogorov continuity theorem
Kolmogorov extension theorem
Kosambi–Karhunen–Loève theorem
Lévy–Prokhorov metric
Malliavin calculus
Martingale representation theorem
Optional stopping theorem
Prokhorov's theorem
Quadratic variation
Reflection principle
Skorokhod integral
Skorokhod's representation theorem
Skorokhod space
Snell envelope
Stochastic differential equation
Tanaka
Stopping time
/
Hitting time
Stratonovich integral
Uniform integrability
Usual hypotheses
Wiener space
Classical
Abstract
Disciplines
Actuarial mathematics
Control theory
Econometrics
Ergodic theory
Extreme value theory (EVT)
Large deviations theory
Mathematical finance
Mathematical statistics
Probability theory
Queueing theory
Renewal theory
Ruin theory
Signal processing
Statistics
Stochastic analysis
Time series analysis
Machine learning
List of topics
Category
Retrieved from "
https://en.wikipedia.org/w/index.php?title=Geometric_Brownian_motion&oldid=1354252393
"
Category
:
Wiener process
Hidden categories:
Articles with short description
Short description is different from Wikidata
Articles with example Python (programming language) code
Search
Search
Geometric Brownian motion
12 languages
Add topic