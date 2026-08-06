---
title: Autoregressive conditional heteroskedasticity - Wikipedia
id: autoregressive-conditional-heteroskedasticity-wikipedia
created: '2026-08-06T06:58:02.177257Z'
source: https://en.wikipedia.org/wiki/Autoregressive_conditional_heteroskedasticity
source_domain: en.wikipedia.org
fetched_at: '2026-08-06T06:58:02.177033Z'
fetch_provider: builtin
status: draft
type: note
tier: institutional
content_type: article
deprecated: false
---

Autoregressive conditional heteroskedasticity - Wikipedia
Jump to content
From Wikipedia, the free encyclopedia
Time series model
In
econometrics
, the
autoregressive conditional heteroskedasticity
(
ARCH
) model is a
statistical model
for
time series
data that describes the
variance
of the current
error term
or
innovation
as a function of the actual sizes of the previous time periods' error terms;
[
1
]
often the variance is related to the squares of the previous innovations. The ARCH model is appropriate when the error variance in a time series follows an
autoregressive
(AR) model; if an
autoregressive moving average
(ARMA) model is assumed for the error variance, the model is a
generalized autoregressive conditional heteroskedasticity
(
GARCH
) model.
[
2
]
ARCH models are commonly employed in modeling
financial
time series
that exhibit time-varying
volatility
and
volatility clustering
, i.e. periods of swings interspersed with periods of relative calm (this is, when the time series exhibits heteroskedasticity). ARCH-type models are sometimes considered to be in the family of
stochastic volatility
models, although this is strictly incorrect since at time
t
the volatility is completely predetermined (deterministic) given previous values.
[
3
]
Model specification
[
edit
]
To model a time series using an ARCH process, let
ϵ
t
{\displaystyle ~\epsilon _{t}~}
denote the error terms (return residuals, with respect to a mean process), i.e. the series terms. These
ϵ
t
{\displaystyle ~\epsilon _{t}~}
are split into a stochastic piece
z
t
{\displaystyle z_{t}}
and a time-dependent standard deviation
σ
t
{\displaystyle \sigma _{t}}
characterizing the typical size of the terms so that
ϵ
t
=
σ
t
z
t
{\displaystyle ~\epsilon _{t}=\sigma _{t}z_{t}~}
The random variable
z
t
{\displaystyle z_{t}}
is a strong
white noise
process. The series
σ
t
2
{\displaystyle \sigma _{t}^{2}}
is modeled by
σ
t
2
=
α
0
+
α
1
ϵ
t
−
1
2
+
⋯
+
α
q
ϵ
t
−
q
2
=
α
0
+
∑
i
=
1
q
α
i
ϵ
t
−
i
2
{\displaystyle \sigma _{t}^{2}=\alpha _{0}+\alpha _{1}\epsilon _{t-1}^{2}+\cdots +\alpha _{q}\epsilon _{t-q}^{2}=\alpha _{0}+\sum _{i=1}^{q}\alpha _{i}\epsilon _{t-i}^{2}}
,
where
α
0
>
0
{\displaystyle ~\alpha _{0}>0~}
and
α
i
≥
0
,
i
>
0
{\displaystyle \alpha _{i}\geq 0,~i>0}
.
An ARCH(
q
) model can be estimated using
ordinary least squares
. A method for testing whether the residuals
ϵ
t
{\displaystyle \epsilon _{t}}
exhibit time-varying heteroskedasticity using the
Lagrange multiplier test
was proposed by
Engle
(1982). This procedure is as follows:
Estimate the best fitting
autoregressive model
AR(
q
)
y
t
=
a
0
+
a
1
y
t
−
1
+
⋯
+
a
q
y
t
−
q
+
ϵ
t
=
a
0
+
∑
i
=
1
q
a
i
y
t
−
i
+
ϵ
t
{\displaystyle y_{t}=a_{0}+a_{1}y_{t-1}+\cdots +a_{q}y_{t-q}+\epsilon _{t}=a_{0}+\sum _{i=1}^{q}a_{i}y_{t-i}+\epsilon _{t}}
.
Obtain the squares of the error
ϵ
^
2
{\displaystyle {\hat {\epsilon }}^{2}}
and regress them on a constant and
q
lagged values:
ϵ
^
t
2
=
α
0
+
∑
i
=
1
q
α
i
ϵ
^
t
−
i
2
{\displaystyle {\hat {\epsilon }}_{t}^{2}=\alpha _{0}+\sum _{i=1}^{q}\alpha _{i}{\hat {\epsilon }}_{t-i}^{2}}
where
q
is the length of ARCH lags.
The
null hypothesis
is that, in the absence of ARCH components, we have
α
i
=
0
{\displaystyle \alpha _{i}=0}
for all
i
=
1
,
⋯
,
q
{\displaystyle i=1,\cdots ,q}
. The alternative hypothesis is that, in the presence of ARCH components, at least one of the estimated
α
i
{\displaystyle \alpha _{i}}
coefficients must be significant. In a sample of
T
residuals under the null hypothesis of no ARCH errors, the test statistic
T'R²
follows
χ
2
{\displaystyle \chi ^{2}}
distribution with
q
degrees of freedom, where
T
′
{\displaystyle T'}
is the number of equations in the model which fits the residuals vs the lags (i.e.
T
′
=
T
−
q
{\displaystyle T'=T-q}
). If
T'R²
is greater than the Chi-square table value, we
reject
the null hypothesis and conclude there is an ARCH effect in the
ARMA model
. If
T'R²
is smaller than the Chi-square table value, we do not reject the null hypothesis.
GARCH
[
edit
]
If an
autoregressive moving average
(ARMA) model is assumed for the error variance, the model is a generalized autoregressive conditional heteroskedasticity (GARCH) model.
[
2
]
In that case, the GARCH (
p
,
q
) model (where
p
is the order of the GARCH terms
σ
2
{\displaystyle ~\sigma ^{2}}
and
q
is the order of the ARCH terms
ϵ
2
{\displaystyle ~\epsilon ^{2}}
), following the notation of the original paper, is given by
y
t
=
x
t
′
b
+
ϵ
t
{\displaystyle y_{t}=x'_{t}b+\epsilon _{t}}
ϵ
t
|
y
t
−
1
∼
N
(
0
,
σ
t
2
)
{\displaystyle \epsilon _{t}|y_{t-1}\sim {\mathcal {N}}(0,\sigma _{t}^{2})}
σ
t
2
=
ω
+
α
1
ϵ
t
−
1
2
+
⋯
+
α
q
ϵ
t
−
q
2
+
β
1
σ
t
−
1
2
+
⋯
+
β
p
σ
t
−
p
2
=
ω
+
∑
i
=
1
q
α
i
ϵ
t
−
i
2
+
∑
i
=
1
p
β
i
σ
t
−
i
2
{\displaystyle \sigma _{t}^{2}=\omega +\alpha _{1}\epsilon _{t-1}^{2}+\cdots +\alpha _{q}\epsilon _{t-q}^{2}+\beta _{1}\sigma _{t-1}^{2}+\cdots +\beta _{p}\sigma _{t-p}^{2}=\omega +\sum _{i=1}^{q}\alpha _{i}\epsilon _{t-i}^{2}+\sum _{i=1}^{p}\beta _{i}\sigma _{t-i}^{2}}
Generally, when testing for heteroskedasticity in econometric models, the best test is the
White test
. However, when dealing with
time series
data, this means to test for ARCH and GARCH errors.
Exponentially weighted
moving average
(EWMA) is an alternative model in a separate class of exponential smoothing models. As an alternative to GARCH modelling it has some attractive properties such as a greater weight upon more recent observations, but also drawbacks such as an arbitrary decay factor that introduces subjectivity into the estimation.
GARCH(
p
,
q
) model specification
[
edit
]
The lag length
p
of a GARCH(
p
,
q
) process is established in three steps:
Estimate the best fitting AR(
q
) model
y
t
=
a
0
+
a
1
y
t
−
1
+
⋯
+
a
q
y
t
−
q
+
ϵ
t
=
a
0
+
∑
i
=
1
q
a
i
y
t
−
i
+
ϵ
t
{\displaystyle y_{t}=a_{0}+a_{1}y_{t-1}+\cdots +a_{q}y_{t-q}+\epsilon _{t}=a_{0}+\sum _{i=1}^{q}a_{i}y_{t-i}+\epsilon _{t}}
.
Compute and plot the autocorrelations of
ϵ
2
{\displaystyle \epsilon ^{2}}
by
ρ
(
i
)
=
∑
t
=
i
+
1
T
(
ϵ
^
t
2
−
σ
^
t
2
)
(
ϵ
^
t
−
i
2
−
σ
^
t
−
i
2
)
∑
t
=
1
T
(
ϵ
^
t
2
−
σ
^
t
2
)
2
{\displaystyle \rho (i)={{\sum _{t=i+1}^{T}({\hat {\epsilon }}_{t}^{2}-{\hat {\sigma }}_{t}^{2})({\hat {\epsilon }}_{t-i}^{2}-{\hat {\sigma }}_{t-i}^{2})} \over {\sum _{t=1}^{T}({\hat {\epsilon }}_{t}^{2}-{\hat {\sigma }}_{t}^{2})^{2}}}}
The asymptotic, that is for large samples, standard deviation of
ρ
(
i
)
{\displaystyle \rho (i)}
is
1
/
T
{\displaystyle 1/{\sqrt {T}}}
. Individual values that are larger than this indicate GARCH errors. To estimate the total number of lags, use the
Ljung–Box test
until the value of these are less than, say, 10% significant. The Ljung–Box
Q-statistic
follows
χ
2
{\displaystyle \chi ^{2}}
distribution with
n
degrees of freedom if the squared residuals
ϵ
t
2
{\displaystyle \epsilon _{t}^{2}}
are uncorrelated. It is recommended to consider up to T/4 values of
n
. The null hypothesis states that there are no ARCH or GARCH errors. Rejecting the null thus means that such errors exist in the
conditional variance
.
NGARCH
[
edit
]
This section
needs expansion
with:
[
4
]
[
5
]
. You can help by
adding missing information
.
(
October 2017
)
NAGARCH
[
edit
]
Nonlinear Asymmetric GARCH(1,1)
(
NAGARCH
) is a model with the specification:
[
6
]
[
7
]
σ
t
2
=
ω
+
α
(
ϵ
t
−
1
−
θ
σ
t
−
1
)
2
+
β
σ
t
−
1
2
{\displaystyle ~\sigma _{t}^{2}=~\omega +~\alpha (~\epsilon _{t-1}-~\theta ~\sigma _{t-1})^{2}+~\beta ~\sigma _{t-1}^{2}}
,
where
α
≥
0
,
β
≥
0
,
ω
>
0
{\displaystyle ~\alpha \geq 0,~\beta \geq 0,~\omega >0}
and
α
(
1
+
θ
2
)
+
β
<
1
{\displaystyle ~\alpha (1+~\theta ^{2})+~\beta <1}
, which ensures the non-negativity and stationarity of the variance process.
For stock returns, parameter
θ
{\displaystyle ~\theta }
is usually estimated to be positive; in this case, it reflects a phenomenon commonly referred to as the "leverage effect", signifying that negative returns increase future volatility by a larger amount than positive returns of the same magnitude.
[
6
]
[
7
]
This model should not be confused with the NARCH model, together with the NGARCH extension, introduced by Higgins and Bera in 1992.
[
8
]
IGARCH
[
edit
]
Integrated Generalized Autoregressive Conditional heteroskedasticity (IGARCH) is a restricted version of the GARCH model, where the persistent parameters sum up to one, and imports a
unit root
in the GARCH process.
[
9
]
The condition for this is
∑
i
=
1
p
β
i
+
∑
i
=
1
q
α
i
=
1
{\displaystyle \sum _{i=1}^{p}~\beta _{i}+\sum _{i=1}^{q}~\alpha _{i}=1}
.
EGARCH
[
edit
]
The exponential generalized autoregressive conditional heteroskedastic (EGARCH) model by Nelson & Cao (1991) is another form of the GARCH model. Formally, an EGARCH(p,q):
log
⁡
σ
t
2
=
ω
+
∑
k
=
1
q
β
k
g
(
Z
t
−
k
)
+
∑
k
=
1
p
α
k
log
⁡
σ
t
−
k
2
{\displaystyle \log \sigma _{t}^{2}=\omega +\sum _{k=1}^{q}\beta _{k}g(Z_{t-k})+\sum _{k=1}^{p}\alpha _{k}\log \sigma _{t-k}^{2}}
where
g
(
Z
t
)
=
θ
Z
t
+
λ
(
|
Z
t
|
−
E
(
|
Z
t
|
)
)
{\displaystyle g(Z_{t})=\theta Z_{t}+\lambda (|Z_{t}|-E(|Z_{t}|))}
,
σ
t
2
{\displaystyle \sigma _{t}^{2}}
is the
conditional variance
,
ω
{\displaystyle \omega }
,
β
{\displaystyle \beta }
,
α
{\displaystyle \alpha }
,
θ
{\displaystyle \theta }
and
λ
{\displaystyle \lambda }
are coefficients.
Z
t
{\displaystyle Z_{t}}
may be a
standard normal variable
or come from a
generalized error distribution
. The formulation for
g
(
Z
t
)
{\displaystyle g(Z_{t})}
allows the sign and the magnitude of
Z
t
{\displaystyle Z_{t}}
to have separate effects on the volatility. This is particularly useful in an asset pricing context.
[
10
]
[
11
]
Since
log
⁡
σ
t
2
{\displaystyle \log \sigma _{t}^{2}}
may be negative, there are no sign restrictions for the parameters.
GARCH-M
[
edit
]
The GARCH-in-mean (GARCH-M) model adds a heteroskedasticity term into the mean equation. It has the specification:
y
t
=
β
x
t
+
λ
σ
t
+
ϵ
t
{\displaystyle y_{t}=~\beta x_{t}+~\lambda ~\sigma _{t}+~\epsilon _{t}}
The residual
ϵ
t
{\displaystyle ~\epsilon _{t}}
is defined as:
ϵ
t
=
σ
t
×
z
t
{\displaystyle ~\epsilon _{t}=~\sigma _{t}~\times z_{t}}
QGARCH
[
edit
]
The Quadratic GARCH (QGARCH) model by Sentana (1995) is used to model asymmetric effects of positive and negative shocks.
In the example of a GARCH(1,1) model, the residual process
σ
t
{\displaystyle ~\sigma _{t}}
is
ϵ
t
=
σ
t
z
t
{\displaystyle ~\epsilon _{t}=~\sigma _{t}z_{t}}
where
z
t
{\displaystyle z_{t}}
is i.i.d. and
σ
t
2
=
K
+
α
ϵ
t
−
1
2
+
β
σ
t
−
1
2
+
ϕ
ϵ
t
−
1
{\displaystyle ~\sigma _{t}^{2}=K+~\alpha ~\epsilon _{t-1}^{2}+~\beta ~\sigma _{t-1}^{2}+~\phi ~\epsilon _{t-1}}
GJR-GARCH
[
edit
]
Similar to QGARCH, the Glosten-Jagannathan-Runkle GARCH (GJR-GARCH) model by Glosten, Jagannathan and Runkle (1993) also models asymmetry in the ARCH process. The suggestion is to model
ϵ
t
=
σ
t
z
t
{\displaystyle ~\epsilon _{t}=~\sigma _{t}z_{t}}
where
z
t
{\displaystyle z_{t}}
is i.i.d., and
σ
t
2
=
K
+
δ
σ
t
−
1
2
+
α
ϵ
t
−
1
2
+
ϕ
ϵ
t
−
1
2
I
t
−
1
{\displaystyle ~\sigma _{t}^{2}=K+~\delta ~\sigma _{t-1}^{2}+~\alpha ~\epsilon _{t-1}^{2}+~\phi ~\epsilon _{t-1}^{2}I_{t-1}}
where
I
t
−
1
=
0
{\displaystyle I_{t-1}=0}
if
ϵ
t
−
1
≥
0
{\displaystyle ~\epsilon _{t-1}\geq 0}
, and
I
t
−
1
=
1
{\displaystyle I_{t-1}=1}
if
ϵ
t
−
1
<
0
{\displaystyle ~\epsilon _{t-1}<0}
.
TGARCH model
[
edit
]
The Threshold GARCH (TGARCH) model by Zakoian (1994) is similar to GJR GARCH. The specification is one on conditional standard deviation instead of
conditional variance
:
σ
t
=
K
+
δ
σ
t
−
1
+
α
1
+
ϵ
t
−
1
+
+
α
1
−
ϵ
t
−
1
−
{\displaystyle ~\sigma _{t}=K+~\delta ~\sigma _{t-1}+~\alpha _{1}^{+}~\epsilon _{t-1}^{+}+~\alpha _{1}^{-}~\epsilon _{t-1}^{-}}
where
ϵ
t
−
1
+
=
ϵ
t
−
1
{\displaystyle ~\epsilon _{t-1}^{+}=~\epsilon _{t-1}}
if
ϵ
t
−
1
>
0
{\displaystyle ~\epsilon _{t-1}>0}
, and
ϵ
t
−
1
+
=
0
{\displaystyle ~\epsilon _{t-1}^{+}=0}
if
ϵ
t
−
1
≤
0
{\displaystyle ~\epsilon _{t-1}\leq 0}
. Likewise,
ϵ
t
−
1
−
=
ϵ
t
−
1
{\displaystyle ~\epsilon _{t-1}^{-}=~\epsilon _{t-1}}
if
ϵ
t
−
1
≤
0
{\displaystyle ~\epsilon _{t-1}\leq 0}
, and
ϵ
t
−
1
−
=
0
{\displaystyle ~\epsilon _{t-1}^{-}=0}
if
ϵ
t
−
1
>
0
{\displaystyle ~\epsilon _{t-1}>0}
.
fGARCH
[
edit
]
Hentschel's
fGARCH
model,
[
12
]
also known as
Family GARCH
, is an omnibus model that nests a variety of other popular symmetric and asymmetric GARCH models including APARCH, GJR, AVGARCH, NGARCH, etc.
COGARCH
[
edit
]
In 2004,
Claudia Klüppelberg
, Alexander Lindner and Ross Maller proposed a continuous-time generalization of the discrete-time GARCH(1,1) process. The idea is to start with the GARCH(1,1) model equations
ϵ
t
=
σ
t
z
t
,
{\displaystyle \epsilon _{t}=\sigma _{t}z_{t},}
σ
t
2
=
α
0
+
α
1
ϵ
t
−
1
2
+
β
1
σ
t
−
1
2
=
α
0
+
α
1
σ
t
−
1
2
z
t
−
1
2
+
β
1
σ
t
−
1
2
,
{\displaystyle \sigma _{t}^{2}=\alpha _{0}+\alpha _{1}\epsilon _{t-1}^{2}+\beta _{1}\sigma _{t-1}^{2}=\alpha _{0}+\alpha _{1}\sigma _{t-1}^{2}z_{t-1}^{2}+\beta _{1}\sigma _{t-1}^{2},}
and then to replace the strong white noise process
z
t
{\displaystyle z_{t}}
by the infinitesimal increments
d
L
t
{\displaystyle \mathrm {d} L_{t}}
of a
Lévy process
(
L
t
)
t
≥
0
{\displaystyle (L_{t})_{t\geq 0}}
, and the squared noise process
z
t
2
{\displaystyle z_{t}^{2}}
by the increments
d
[
L
,
L
]
t
d
{\displaystyle \mathrm {d} [L,L]_{t}^{\mathrm {d} }}
, where
[
L
,
L
]
t
d
=
∑
s
∈
[
0
,
t
]
(
Δ
L
t
)
2
,
t
≥
0
,
{\displaystyle [L,L]_{t}^{\mathrm {d} }=\sum _{s\in [0,t]}(\Delta L_{t})^{2},\quad t\geq 0,}
is the purely discontinuous part of the
quadratic variation
process of
L
{\displaystyle L}
. The result is the following system of
stochastic differential equations
:
d
G
t
=
σ
t
−
d
L
t
,
{\displaystyle \mathrm {d} G_{t}=\sigma _{t-}\,\mathrm {d} L_{t},}
d
σ
t
2
=
(
β
−
η
σ
t
2
)
d
t
+
φ
σ
t
−
2
d
[
L
,
L
]
t
d
,
{\displaystyle \mathrm {d} \sigma _{t}^{2}=(\beta -\eta \sigma _{t}^{2})\,\mathrm {d} t+\varphi \sigma _{t-}^{2}\,\mathrm {d} [L,L]_{t}^{\mathrm {d} },}
where the positive parameters
β
{\displaystyle \beta }
,
η
{\displaystyle \eta }
and
φ
{\displaystyle \varphi }
are determined by
α
0
{\displaystyle \alpha _{0}}
,
α
1
{\displaystyle \alpha _{1}}
and
β
1
{\displaystyle \beta _{1}}
. Now given some initial condition
(
G
0
,
σ
0
2
)
{\displaystyle (G_{0},\sigma _{0}^{2})}
, the system above has a pathwise unique solution
(
G
t
,
σ
t
2
)
t
≥
0
{\displaystyle (G_{t},\sigma _{t}^{2})_{t\geq 0}}
which is then called the continuous-time GARCH (
COGARCH
) model.
[
13
]
MF2-GARCH
[
edit
]
The multiplicative factor multi-frequency GARCH (MF2-GARCH) was proposed by Conrad and Engle (2025),
[
14
]
and it features stationary returns and allows for recursive long-term volatility forecasts. They exploit the fact that daily standardized volatility forecast errors of one-component GARCH models are essentially unpredictable based on past daily standardized forecast errors, but a rolling window moving average of past daily standardized forecast errors does have predictive power. The MF2-GARCH,
ϵ
t
=
σ
t
2
τ
t
z
t
{\displaystyle \epsilon _{t}={\sqrt {\sigma _{t}^{2}\tau _{t}}}z_{t}}
, where
z
t
{\displaystyle z_{t}}
is standard Gaussian, combines a short-term GJR-GARCH component
h
t
=
(
1
−
ϕ
)
+
(
α
+
γ
1
{
η
d
,
t
−
1
<
0
}
)
η
d
,
t
−
1
2
τ
t
−
1
+
β
h
t
−
1
{\displaystyle h_{t}=(1-\phi )+\left(\alpha +\gamma \mathbf {1} _{\{\eta _{d,t-1}<0\}}\right){\frac {\eta _{d,t-1}^{2}}{\tau _{t-1}}}+\beta h_{t-1}}
with
α
>
0
,
α
+
γ
>
0
,
β
>
0
{\displaystyle ~\alpha >0,\alpha +\gamma >0,\beta >0}
and
ϕ
=
α
+
γ
/
2
+
β
<
1
{\displaystyle ~\phi =\alpha +\gamma /2+\beta <1}
, and a long-term component specified as a multiplicative error model (MEM) for the past forecast errors of the GARCH component, exploiting the predictability in the averaged standardized forecast errors of the short-term component.
τ
t
=
λ
0
+
λ
1
1
m
∑
j
=
1
m
η
d
,
t
−
j
2
h
t
−
j
+
λ
2
τ
t
−
1
{\displaystyle \tau _{t}=\lambda _{0}+\lambda _{1}{\frac {1}{m}}\sum _{j=1}^{m}{\frac {\eta _{d,t-j}^{2}}{h_{t-j}}}+\lambda _{2}\tau _{t-1}}
with
λ
0
>
0
,
λ
1
>
0
,
λ
2
>
0
{\displaystyle ~\lambda _{0}>0,\lambda _{1}>0,\lambda _{2}>0}
and
λ
1
+
λ
2
<
1
{\displaystyle ~\lambda _{1}+\lambda _{2}<1}
.
m
{\displaystyle m}
is chosen by minimizing the Bayesian Information Criterion (BIC, SIC).
Empirically, the long-term volatility component is closely linked to news about macroeconomics and monetary policy. The immediate reaction of stock market indices to U.S. macroeconomic announcements (e.g., initial jobless claims or incoming orders) depends on the level of long-term stock market volatility.
[
15
]
ZD-GARCH
[
edit
]
An ARCH model without intercept was proposed by Hafner and Preminger (2015),
[
16
]
who set the intercept term to zero (
ω
=
0
{\displaystyle ~\omega =0}
), in the first order ARCH model
ϵ
t
=
σ
t
z
t
{\displaystyle ~\epsilon _{t}=~\sigma _{t}z_{t}}
, where
z
t
{\displaystyle z_{t}}
is i.i.d., and the conditional variance is:
σ
t
2
=
α
1
ϵ
t
−
1
2
.
{\displaystyle ~\sigma _{t}^{2}=~\alpha _{1}~\epsilon _{t-1}^{2}.}
This model was extended by Li, Zhang, Zhu and Ling (2018)
[
17
]
which consider the Zero-Drift GARCH (ZD-GARCH) with the specification:
σ
t
2
=
α
1
ϵ
t
−
1
2
+
β
1
σ
t
−
1
2
.
{\displaystyle ~\sigma _{t}^{2}=~\alpha _{1}~\epsilon _{t-1}^{2}+~\beta _{1}~\sigma _{t-1}^{2}.}
The ZD-GARCH model does not require
α
1
+
β
1
=
1
{\displaystyle ~\alpha _{1}+~\beta _{1}=1}
, and hence it nests the
Exponentially weighted moving average
(EWMA) model in "
RiskMetrics
". Since
ω
=
0
{\displaystyle ~\omega =0}
, the ZD-GARCH model is always non-stationary, and its statistical inference methods are quite different from those for the classical GARCH model. Based on the historical data, the parameters
α
1
{\displaystyle ~\alpha _{1}}
and
β
1
{\displaystyle ~\beta _{1}}
can be estimated by the generalized
QMLE
method.
Spatial and Spatiotemporal GARCH
[
edit
]
Spatial GARCH processes by Otto, Schmid and Garthoff (2018)
[
18
]
are considered as the spatial equivalent to the temporal generalized autoregressive conditional heteroscedasticity (GARCH) models.
[
19
]
In contrast to the temporal ARCH model, in which the distribution is known given the full information set for the prior periods, the distribution is not straightforward in the spatial and spatiotemporal setting due to the contemporaneous dependence between neighboring spatial locations. The spatial model is given by
ϵ
(
s
i
)
=
σ
(
s
i
)
z
(
s
i
)
{\displaystyle ~\epsilon (s_{i})=~\sigma (s_{i})z(s_{i})}
and
σ
(
s
i
)
2
=
α
i
+
∑
v
=
1
n
ρ
w
i
v
ϵ
(
s
v
)
2
,
{\displaystyle ~\sigma (s_{i})^{2}=~\alpha _{i}+\sum _{v=1}^{n}\rho w_{iv}\epsilon (s_{v})^{2},}
where
s
i
{\displaystyle ~s_{i}}
denotes the
i
{\displaystyle i}
-th spatial location and
w
i
v
{\displaystyle ~w_{iv}}
refers to the
i
v
{\displaystyle iv}
-th entry of a spatial weight matrix and
w
i
i
=
0
{\displaystyle w_{ii}=0}
for
i
=
1
,
.
.
.
,
n
{\displaystyle ~i=1,...,n}
. The spatial weight matrix defines which locations are considered to be adjacent.
In spatiotemporal extensions, the conditional variance is modelled as a joint function of spatially lagged past squared observations and temporally lagged volatilities, allowing for both cross-sectional and serial dependence. These models have been applied in fields such as environmental statistics, regional economics, and financial econometrics, where shocks can propagate over space and time. Recent reviews summarise methodological developments, estimation techniques, and applications across disciplines.
[
19
]
Gaussian process-driven GARCH
[
edit
]
In a different vein, the machine learning community has proposed the use of Gaussian process regression models to obtain a GARCH scheme.
[
20
]
This results in a nonparametric modelling scheme, which allows for: (i) advanced robustness to overfitting, since the model marginalises over its parameters to perform inference, under a Bayesian inference rationale; and (ii) capturing highly-nonlinear dependencies without increasing model complexity.
[
citation needed
]
References
[
edit
]
↑
Engle, Robert F.
(1982). "Autoregressive Conditional Heteroskedasticity with Estimates of the Variance of United Kingdom Inflation".
Econometrica
.
50
(4):
987–
1007.
doi
:
10.2307/1912773
.
JSTOR
1912773
.
1
2
Bollerslev, Tim
(1986). "Generalized Autoregressive Conditional Heteroskedasticity".
Journal of Econometrics
.
31
(3):
307–
327.
CiteSeerX
10.1.1.468.2892
.
doi
:
10.1016/0304-4076(86)90063-1
.
S2CID
8797625
.
↑
Brooks, Chris
(2014).
Introductory Econometrics for Finance
(3rd
ed.). Cambridge: Cambridge University Press. p.
461.
ISBN
9781107661455
.
↑
Lanne, Markku; Saikkonen, Pentti (July 2005).
"Non-linear GARCH models for highly persistent volatility"
(PDF)
.
The Econometrics Journal
.
8
(2):
251–
276.
doi
:
10.1111/j.1368-423X.2005.00163.x
.
hdl
:
10419/65348
.
JSTOR
23113641
.
S2CID
15252964
.
↑
Bollerslev, Tim; Russell, Jeffrey; Watson, Mark (May 2010).
"Chapter 8: Glossary to ARCH (GARCH)"
(PDF)
.
Volatility and Time Series Econometrics: Essays in Honor of Robert Engle
(1st
ed.). Oxford: Oxford University Press. pp.
137–
163.
ISBN
9780199549498
. Retrieved
27 October
2017
.
1
2
Engle, Robert F.; Ng, Victor K. (1993).
"Measuring and testing the impact of news on volatility"
(PDF)
.
Journal of Finance
.
48
(5):
1749–
1778.
Bibcode
:
1993JFin...48.1749E
.
doi
:
10.1111/j.1540-6261.1993.tb05127.x
.
SSRN
262096
.
It is not yet clear in the finance literature that the asymmetric properties of variances are due to changing leverage. The name "leverage effect" is used simply because it is popular among researchers when referring to such a phenomenon.
1
2
Posedel, Petra (2006).
"Analysis Of The Exchange Rate And Pricing Foreign Currency Options On The Croatian Market: The Ngarch Model As An Alternative To The Black Scholes Model"
(PDF)
.
Financial Theory and Practice
.
30
(4):
347–
368.
Special attention to the model is given by the parameter of asymmetry [theta (θ)] which describes the correlation between returns and variance.
6
...
6
In the case of analyzing stock returns, the positive value of [theta] reflects the empirically well known leverage effect indicating that a downward movement in the price of a stock causes more of an increase in variance more than a same value downward movement in the price of a stock, meaning that returns and variance are negatively correlated
↑
Higgins, M.L; Bera, A.K (1992). "A Class of Nonlinear Arch Models".
International Economic Review
.
33
(1):
137–
158.
doi
:
10.2307/2526988
.
JSTOR
2526988
.
↑
Caporale, Guglielmo Maria; Pittis, Nikitas; Spagnolo, Nicola (October 2003).
"IGARCH models and structural breaks"
.
Applied Economics Letters
.
10
(12):
765–
768.
doi
:
10.1080/1350485032000138403
.
ISSN
1350-4851
.
↑
St. Pierre, Eilleen F. (1998). "Estimating EGARCH-M Models: Science or Art".
The Quarterly Review of Economics and Finance
.
38
(2):
167–
180.
doi
:
10.1016/S1062-9769(99)80110-0
.
↑
Chatterjee, Swarn; Hubble, Amy (2016). "Day-Of-The-Whieek Effect In Us Biotechnology Stocks—Do Policy Changes And Economic Cycles Matter?".
Annals of Financial Economics
.
11
(2):
1–
17.
doi
:
10.1142/S2010495216500081
.
↑
Hentschel, Ludger (1995). "All in the family Nesting symmetric and asymmetric GARCH models".
Journal of Financial Economics
.
39
(1):
71–
104.
CiteSeerX
10.1.1.557.8941
.
doi
:
10.1016/0304-405X(94)00821-H
.
↑
Klüppelberg, C.
; Lindner, A.; Maller, R. (2004).
"A continuous-time GARCH process driven by a Lévy process: stationarity and second-order behaviour"
.
Journal of Applied Probability
.
41
(3):
601–
622.
doi
:
10.1239/jap/1091543413
.
hdl
:
10419/31047
.
S2CID
17943198
.
↑
Conrad, Christian M.; Engle, Rob (2025). "Modelling Volatility Cycles: The MF2-GARCH Model".
Journal of Applied Econometrics
.
40
(C):
438–
454.
doi
:
10.1002/jae.3118
.
hdl
:
10419/323894
.
↑
Conrad, Christian M.; Schoelkopf, Julius; Tushteva, Nikoleta (2025).
"Long-term volatility shapes the stock market's sensitivity to news"
.
Journal of Econometrics
106148.
doi
:
10.1016/j.jeconom.2025.106148
.
↑
Hafner, Christian M.; Preminger, Arie (2015). "An ARCH model without intercept".
Economics Letters
.
129
(C):
13–
17.
doi
:
10.1016/j.econlet.2015.01.029
.
↑
Li, D.; Zhang, X.; Zhu, K.; Ling, S. (2018).
"The ZD-GARCH model: A new way to study heteroscedasticity"
(PDF)
.
Journal of Econometrics
.
202
(1):
1–
17.
doi
:
10.1016/j.jeconom.2017.09.003
.
↑
Otto, P.; Schmid, W.; Garthoff, R. (2018). "Generalised spatial and spatiotemporal autoregressive conditional heteroscedasticity".
Spatial Statistics
.
26
(1):
125–
145.
arXiv
:
1609.00711
.
Bibcode
:
2018SpaSt..26..125O
.
doi
:
10.1016/j.spasta.2018.07.005
.
S2CID
88521485
.
1
2
Otto, P.; Dogan, O.; Taspinar, S.; Schmid, W.; Bera, A. K. (2025).
"Spatial and Spatiotemporal Volatility Models: A Review"
.
Journal of Economic Surveys
.
39
(3):
1037–
1091.
doi
:
10.1111/joes.12643
.
↑
Platanios, E.; Chatzis, S. (2014). "Gaussian process-mixture conditional heteroscedasticity".
IEEE Transactions on Pattern Analysis and Machine Intelligence
.
36
(5):
889–
900.
arXiv
:
1211.4410
.
Bibcode
:
2014ITPAM..36..888P
.
doi
:
10.1109/TPAMI.2013.183
.
PMID
26353224
.
S2CID
10424638
.
Further reading
[
edit
]
Bollerslev, Tim; Russell, Jeffrey; Watson, Mark (May 2010).
"Chapter 8: Glossary to ARCH (GARCH)"
(PDF)
.
Volatility and Time Series Econometrics: Essays in Honor of Robert Engle
(1st
ed.). Oxford: Oxford University Press. pp.
137–
163.
ISBN
9780199549498
.
Enders, W. (2004). "Modelling Volatility".
Applied Econometrics Time Series
(Second
ed.). John-Wiley & Sons. pp.
108–
155.
ISBN
978-0-471-45173-0
.
Engle, Robert F.
(1982). "Autoregressive Conditional Heteroscedasticity with Estimates of Variance of United Kingdom Inflation".
Econometrica
.
50
(4):
987–
1008.
doi
:
10.2307/1912773
.
JSTOR
1912773
.
S2CID
18673159
.
(the paper which sparked the general interest in ARCH models)
Engle, Robert F. (1995).
ARCH: selected readings
. Oxford University Press.
ISBN
978-0-19-877432-7
.
Engle, Robert F. (2001).
"GARCH 101: The Use of ARCH/GARCH Models in Applied Econometrics"
.
Journal of Economic Perspectives
.
15
(4):
157–
168.
doi
:
10.1257/jep.15.4.157
.
JSTOR
2696523
.
(a short, readable introduction)
Gujarati, D. N. (2003).
Basic Econometrics
. pp.
856–
862.
Hacker, R. S.; Hatemi-J, A. (2005).
"A Test for Multivariate ARCH Effects"
.
Applied Economics Letters
.
12
(7):
411–
417.
doi
:
10.1080/13504850500092129
.
S2CID
218639533
.
Nelson, D. B. (1991). "Conditional Heteroskedasticity in Asset Returns: A New Approach".
Econometrica
.
59
(2):
347–
370.
doi
:
10.2307/2938260
.
JSTOR
2938260
.
Otto, P.; Dogan, O.; Taspinar, S.; Schmid, W.; Bera, A. K. (2025).
"Spatial and Spatiotemporal Volatility Models: A Review"
.
Journal of Economic Surveys
.
39
(3):
1037–
1091.
doi
:
10.1111/joes.12643
.
v
t
e
Statistics
Outline
Index
Descriptive statistics
Continuous data
Center
Mean
Arithmetic
Arithmetic-Geometric
Contraharmonic
Cubic
Generalized/power
Geometric
Harmonic
Heronian
Heinz
Lehmer
Median
Mode
Dispersion
Average absolute deviation
Coefficient of variation
Interquartile range
Percentile
Range
Standard deviation
Variance
Shape
Central limit theorem
Moments
Kurtosis
L-moments
Skewness
Count data
Index of dispersion
Summary tables
Contingency table
Frequency distribution
Grouped data
Dependence
Partial correlation
Pearson product-moment correlation
Rank correlation
Kendall's τ
Spearman's ρ
Scatter plot
Graphics
Bar chart
Biplot
Box plot
Control chart
Correlogram
Fan chart
Forest plot
Histogram
Pie chart
Q–Q plot
Radar chart
Run chart
Scatter plot
Stem-and-leaf display
Violin plot
Heatmap
Scatter Plot Matrix
ECDF plot
Line chart
Statistical data processing
Transformations
Data transformation
Log transformation
Power transform
Box–Cox transformation
Yeo–Johnson transformation
Variance-stabilizing transformation
Anscombe transform
Fisher transformation
Scaling and normalization
Feature scaling
Normalization
Standardization (z-score)
Min–max normalization
Unit vector normalization
Data cleaning
Data cleaning
Outlier
Winsorizing
Truncation
Missing data
Data reduction
Dimensionality reduction
Principal component analysis
Factor analysis
Time-series preprocessing
Differencing
Detrending
Seasonal adjustment
Stationarity transformation
Data collection
Study design
Effect size
Missing data
Optimal design
Population
Replication
Sample size determination
Statistic
Statistical power
Survey methodology
Sampling
Cluster
Stratified
Opinion poll
Questionnaire
Standard error
Controlled experiments
Blocking
Factorial experiment
Interaction
Random assignment
Randomized controlled trial
Randomized experiment
Scientific control
Adaptive designs
Adaptive clinical trial
Stochastic approximation
Up-and-down designs
Observational studies
Cohort study
Cross-sectional study
Natural experiment
Quasi-experiment
Statistical inference
Statistical theory
Population
Statistic
Probability distribution
Sampling distribution
Order statistic
Empirical distribution
Density estimation
Statistical model
Model specification
L
p
space
Parameter
location
scale
shape
Parametric family
Likelihood
(monotone)
Location–scale family
Exponential family
Completeness
Sufficiency
Statistical functional
Bootstrap
U
V
Optimal decision
loss function
Efficiency
Statistical distance
divergence
Asymptotics
Robustness
Frequentist inference
Point estimation
Estimating equations
Maximum likelihood
Method of moments
M-estimator
Minimum distance
Unbiased estimators
Mean-unbiased minimum-variance
Rao–Blackwellization
Lehmann–Scheffé theorem
Median unbiased
Plug-in
Interval estimation
Confidence interval
Pivot
Likelihood interval
Prediction interval
Tolerance interval
Resampling
Bootstrap
Jackknife
Testing hypotheses
1- & 2-tails
Power
Uniformly most powerful test
Permutation test
Randomization test
Multiple comparisons
Parametric tests
Likelihood-ratio
Score/Lagrange multiplier
Wald
Specific tests
Z
-test
(normal)
Student's
t
-test
F
-test
Goodness of fit
Chi-squared
G
-test
Kolmogorov–Smirnov
Anderson–Darling
Lilliefors
Jarque–Bera
Normality
(Shapiro–Wilk)
Likelihood-ratio test
Model selection
Cross validation
AIC
BIC
Rank statistics
Sign
Sample median
Signed rank
(Wilcoxon)
Hodges–Lehmann estimator
Rank sum
(Mann–Whitney)
Nonparametric
anova
1-way
(Kruskal–Wallis)
2-way
(Friedman)
Ordered alternative
(Jonckheere–Terpstra)
Van der Waerden test
Bayesian inference
Bayesian probability
prior
posterior
Credible interval
Bayes factor
Bayesian estimator
Maximum posterior estimator
Correlation
Regression analysis
Correlation
Pearson product-moment
Partial correlation
Confounding variable
Coefficient of determination
Regression analysis
Errors and residuals
Regression validation
Mixed effects models
Simultaneous equations models
Multivariate adaptive regression splines (MARS)
Template:Least squares and regression analysis
Linear regression
Simple linear regression
Ordinary least squares
General linear model
Bayesian regression
Non-standard predictors
Nonlinear regression
Nonparametric
Semiparametric
Isotonic
Robust
Homoscedasticity and Heteroscedasticity
Generalized linear model
Exponential families
Logistic
(Bernoulli)
/
Binomial
/
Poisson regressions
Partition of variance
Analysis of variance (ANOVA, anova)
Analysis of covariance
Multivariate ANOVA
Degrees of freedom
Categorical
/
multivariate
/
time-series
/
survival analysis
Categorical
Cohen's kappa
Contingency table
Graphical model
Log-linear model
McNemar's test
Cochran–Mantel–Haenszel statistics
Multivariate
Regression
Manova
Principal components
Canonical correlation
Discriminant analysis
Cluster analysis
Classification
Structural equation model
Factor analysis
Multivariate distributions
Elliptical distributions
Normal
Time-series
General
Decomposition
Trend
Stationarity
Seasonal adjustment
Exponential smoothing
Cointegration
Structural break
Granger causality
Specific tests
Dickey–Fuller
Johansen
Q-statistic
(Ljung–Box)
Durbin–Watson
Breusch–Godfrey
Time domain
Autocorrelation (ACF)
partial (PACF)
Cross-correlation (XCF)
ARMA model
ARIMA model
(Box–Jenkins)
Autoregressive conditional heteroskedasticity (ARCH)
Vector autoregression (VAR)
(
Autoregressive model (AR)
)
Frequency domain
Spectral density estimation
Fourier analysis
Least-squares spectral analysis
Wavelet
Whittle likelihood
Survival
Survival function
Kaplan–Meier estimator (product limit)
Proportional hazards models
Accelerated failure time (AFT) model
First hitting time
Hazard function
Nelson–Aalen estimator
Test
Log-rank test
Applications
Biostatistics
Bioinformatics
Clinical trials
/
studies
Epidemiology
Medical statistics
Engineering statistics
Chemometrics
Methods engineering
Probabilistic design
Process
/
quality control
Reliability
System identification
Social statistics
Actuarial science
Census
Crime statistics
Demography
Econometrics
Jurimetrics
National accounts
Official statistics
Population statistics
Psychometrics
Spatial statistics
Cartography
Environmental statistics
Geographic information system
Geostatistics
Kriging
Category
Mathematics
portal
Commons
WikiProject
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
v
t
e
Volatility
Modelling volatility
Implied volatility
Volatility smile
Volatility clustering
Local volatility
Stochastic volatility
Jump-diffusion models
ARCH and GARCH
Trading volatility
Volatility arbitrage
Straddle
Volatility swap
IVX
VIX
Retrieved from "
https://en.wikipedia.org/w/index.php?title=Autoregressive_conditional_heteroskedasticity&oldid=1348476128
"
Categories
:
Nonlinear time series analysis
Autocorrelation
Hidden categories:
Articles with short description
Short description matches Wikidata
Use dmy dates from October 2017
Articles to be expanded from October 2017
All articles to be expanded
All articles with unsourced statements
Articles with unsourced statements from September 2021
Search
Search
Autoregressive conditional heteroskedasticity
17 languages
Add topic