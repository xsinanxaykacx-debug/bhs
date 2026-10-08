# EPL Betting Market Research

> **A disciplined, pre-registered research program investigating whether reproducible economic betting edges exist in the English Premier League 1X2 market.**

**Status:** 🔒 Research program closed  
**Evidence base:** 2015/16–2024/25  
**Blind data:** 2026/27 — locked and never used in completed research  
**Conclusion:** **No statistically reliable, sustainable OOS betting edge identified**

---

## Executive Summary

This repository contains a multi-stage research program designed to test whether publicly available EPL pre-match market information can be transformed into a repeatable economic betting edge.

The project deliberately separates structural market relationships from profitability, discovery from confirmation, in-sample performance from out-of-sample performance, statistical significance from economic significance, and exploratory ideas from frozen hypothesis tests.

Across **20 completed research paths**, no strategy satisfied the predefined requirements for a supported, statistically reliable and economically meaningful out-of-sample edge.

This is **not** a claim that the EPL 1X2 market is mathematically efficient.

> **Within the tested 2015/16–2024/25 EPL 1X2 data universe and the frozen hypotheses documented here, no sustainable and statistically reliable betting edge was demonstrated under blind OOS validation.**

---

## What Was Tested?

| Research area | Result |
|---|---|
| Price-movement structure | **STRONG OOS relationship** |
| ROI / Edge signals | **NEGATIVE** |
| Feature engineering | **PASS** |
| Market-movement + Elo | **INCONCLUSIVE / WEAK** |
| Goal-difference exploratory models | **WEAK / UNCERTAIN** |
| Opening → closing ROI | **NOT SUPPORTED** |
| Draw movement | **NOT SUPPORTED** |
| Favourite–longshot bias | **NOT SUPPORTED** |
| Corner-form signal | **NOT SUPPORTED** |
| Optimal odds-band discovery | **NOT SUPPORTED** |
| Cross-bookmaker mispricing | **NOT SUPPORTED** |
| Pinnacle sharp vs retail lag | **NOT SUPPORTED** |
| ML/value betting — MLR | **NOT SUPPORTED / RED FLAG** |
| Context-adjusted ML — LightGBM | **NOT SUPPORTED** |
| xG expansion | **REJECTED as a research extension** |

### The central finding

Some relationships are real. The important finding is that **statistical predictability did not translate into a robust economic edge after blind OOS validation**.

---

## The Strongest Structural Result

### Chain 1 — Price Movement Structure

The first major research chain tested whether opening-to-closing market movements contained reproducible relationships with Asian Handicap and Over/Under market variables.

**Blind OOS result:**
- 10 / 12 primary tests successful
- No red flags
- **STRONG OOS**

This established an important distinction:

> Market prices contain measurable structure. That does **not** automatically imply that the structure can be converted into profitable betting.

The subsequent ROI research failed to demonstrate a reliable conversion from this structure into economic edge.

---

## The Economic Tests

### H9 — Machine Learning Value Betting

Multinomial Logistic Regression estimated H/D/A probabilities from 49 pre-match contextual features.

Result:
- Train ROI: **+9.48%**
- Validation ROI: **−5.60%**
- OOS ROI: **−3.80%**
- OOS statistical support: **failed**
- **NOT SUPPORTED / RED FLAG**

### H17 — LightGBM Context Residual

A later frozen experiment compared LightGBM model probability with B365 opening implied probability and placed at most one bet per match when the residual exceeded the frozen threshold.

| Split | N | ROI | BCa lower | Permutation p | MDD |
|---|---:|---:|---:|---:|---:|
| Train | 3,031 | +185.92% | +179.83% | 0.0001 | 4.00% |
| Validation | 366 | −6.71% | −19.48% | 0.3426 | 31.08% |
| OOS | 365 | **+3.84%** | **−9.05%** | **0.5847** | **31.97%** |

### Interpretation

The enormous training result is **not** treated as proof of a real edge.

> **Strong in-sample optimism / strong overfit signal; economic generalization failed.**

The OOS result was positive in raw ROI, but the confidence interval crossed zero, the permutation test was non-significant, and maximum drawdown exceeded the frozen 20% limit.

Therefore: **H17 = NOT SUPPORTED**.

---

## Methodological Discipline

Every formal hypothesis followed the same core philosophy:

### 1. Pre-declared protocol
The hypothesis, feature definition, thresholds, sample split and decision criteria were frozen before the formal run.

### 2. Strict temporal separation
- **Train:** 2015/16–2022/23
- **Validation:** 2023/24
- **Blind OOS:** 2024/25

The blind OOS period was not used to tune the strategy.

### 3. No post-hoc rescue
A negative result was not converted into a positive result by changing thresholds, changing model parameters, selecting a more convenient odds band, changing the sample, or repeatedly rerunning until a positive result appeared.

A genuinely new idea requires a **new hypothesis and a new frozen protocol**.

### 4. Multiple-testing control
Where multiple related tests were performed, **Benjamini–Hochberg FDR** was used.

### 5. Economic validation
A strategy was not considered successful merely because it had positive ROI, a positive coefficient, predictive power, or a low raw p-value.

The decision framework also considered confidence interval, sample size, permutation significance, maximum drawdown, and multiple-testing correction.

---

## Data Integrity

The core research dataset covers **2015/16 → 2024/25**, approximately **3,800 EPL matches**.

The feature-engineering audit established:
- 3,800 / 3,800 rows
- deterministic processing
- no same-day leakage
- no self-reference
- no look-ahead
- 2026/27 never read by the completed H17 pipeline

The project uses only information that is available within the defined pre-match information boundary for each experiment.

---

## 2026/27 Blind Data

### 🔒 E0 (10).csv

The 2026/27 dataset is intentionally **locked**.

It is not used to discover hypotheses, tune thresholds, select features, validate strategies, or explain historical results.

This separation is intentional. The blind season remains protected so that any future protocol can be evaluated without contaminating the existing research record.

---

## Why xG Was Not Added

xG was considered as a possible data-expansion direction.

It was rejected for this research program because the project did not want to turn the study into an open-ended feature-engineering exercise where increasingly sophisticated representations of historical team performance are repeatedly searched for an edge.

> **Do not extend the closed EPL 1X2 program simply by adding another commonly available performance descriptor.**

This is a methodological stopping decision, not a claim that xG has no predictive value.

---

## Research Architecture

~~~text
Market Structure
      ↓
Feature Engineering
      ↓
Exploratory Relationships
      ↓
Frozen Economic Hypotheses
      ↓
Blind OOS Validation
      ↓
Statistical + Economic Decision
      ↓
Archive / Reject / Continue
~~~

The key distinction is:

~~~text
Predictive relationship
        ≠
Economic betting edge
~~~

---

## Related Research & Benchmarking

This project is intentionally positioned against existing football market-efficiency and betting-research work. The purpose is not to claim superiority, but to document where our methodology overlaps with other serious public studies, where it differs, and what each approach does well.

### 1. [vladapl21/odds-calibration](https://github.com/vladapl21/odds-calibration)

**Scope:** 7,600 Premier League matches (2005–2024), bookmaker closing lines, implied-probability calibration, walk-forward Elo/gradient boosting and Kelly staking.

**Common ground:** EPL 1X2, bookmaker odds, walk-forward validation, model-vs-market comparison, and the distinction between predictive signal and profitable betting.

**Strength:** Large EPL historical universe and a clear market-calibration question. It is a particularly useful benchmark for the proposition that genuine predictive information does not necessarily produce a profitable strategy.

**Difference / limitation relative to this project:** Its primary emphasis is calibration and model competition with the market. Our program places greater emphasis on separately frozen economic hypotheses, multiple-testing control, blind OOS decision criteria, and explicit rejection/closure of unsupported mechanisms.

**Relevance:** Very high.

### 2. [panosppkn/football-market-efficiency](https://github.com/panosppkn/football-market-efficiency)

**Scope:** Football market efficiency and price-dispersion opportunities using expanding-window out-of-sample testing.

**Common ground:** walk-forward OOS, implied probabilities, pricing-error analysis, ROI, bootstrap robustness, and price dispersion.

**Strength:** Strong reproducibility orientation and a clear attempt to turn market structure into an economically testable rule. It separates average-market pricing from best-available quoted prices.

**Difference / limitation relative to this project:** Its main economic result focuses on best-price dispersion. Exact timestamped executability, liquidity and stake constraints are acknowledged limitations. Our study is broader in the number of independent mechanisms tested and uses a stricter closed-program / blind-OOS stopping philosophy.

**Relevance:** Very high.

### 3. [Bury20-80/football-betting-market-efficiency](https://github.com/Bury20-80/football-betting-market-efficiency)

**Scope:** 12,459 matches across five major European leagues (2019/20–2025/26), market calibration and favourite-longshot bias.

**Common ground:** calibration vs profitability, favourite-longshot bias, bookmaker odds, bootstrap methods, temporal validation, and testing whether apparent market structure becomes economically useful.

**Strength:** Large multi-league universe and a useful test of whether favourite/longshot effects generalize beyond one competition.

**Difference / limitation relative to this project:** Broader geographic scope but less focused on the EPL-only question. Our program investigates a wider range of EPL-specific mechanisms, including price movement, cross-bookmaker dispersion, sharp-vs-retail lag and context-adjusted ML residuals.

**Relevance:** High for benchmarking H11/H12-style hypotheses.

### 4. [tanamsethi31/footymodel](https://github.com/tanamsethi31/footymodel)

**Scope:** Stats-first football betting research using Dixon-Coles/Poisson, lineup-aware modelling, walk-forward backtests and bookmaker closing odds.

**Common ground:** asks whether positive EV survives against bookmaker prices, walk-forward backtesting, calibration checks, documented negative results, and separation of prediction quality from betting profitability.

**Strength:** An excellent example of a repository that publishes rejected hypotheses and negative results, while also testing genuinely new information such as lineups and player-level data.

**Difference / limitation relative to this project:** Its later stages include live/paper-trading and lineup-aware research. Our completed program is intentionally closed and does not keep adding features after the frozen hypothesis family has been exhausted.

**Relevance:** High.

### Benchmarking principle

These repositories should not be interpreted as proof that the EPL 1X2 market is perfectly efficient, nor should a positive historical result in any one repository be treated as proof of a durable betting edge.

The useful comparison is methodological:

**Predictive relationship**  
**≠**  
**Economic betting edge**

A historical ROI result becomes materially more persuasive when it survives temporal separation, genuinely unseen OOS data, pre-declared decision rules, adequate sample size, uncertainty estimation, multiple-testing control where appropriate, drawdown checks, and realistic execution assumptions.

### What this project adds to the benchmark

The distinctive contribution of this repository is not a claim to have discovered a better prediction algorithm. It is the breadth and closure discipline of the research program:

- **20 independently investigated research paths**
- frozen protocols before formal tests
- explicit Train / Validation / Blind OOS separation
- protected 2026/27 blind data
- statistical significance separated from economic significance
- BCa bootstrap and sign-permutation testing where specified
- BH-FDR for related hypothesis families
- minimum-N and maximum-drawdown criteria
- negative and inconclusive results retained in the research record
- no post-hoc threshold/model rescue
- explicit stopping decision rather than indefinite feature expansion

The resulting conclusion is deliberately narrow:

> **The tested mechanisms did not demonstrate a sustainable, statistically reliable economic edge in blind OOS validation.**

This is a research result for the defined 2015/16–2024/25 EPL 1X2 universe and frozen protocols, not a universal statement that all football betting markets are efficient.

---

## Final Research Status

### 🔒 CLOSED

The EPL 1X2 research program is currently closed.

**20 research paths were completed.** None reached the project's definition of a supported betting edge.

The archive is considered immutable.

The project will not continue indefinitely by adding H21, H22, H23, or similar incremental EPL 1X2 hypotheses without a genuinely new research basis.

A future study would require a clearly defined change such as:
- a different betting market,
- a different competition,
- genuinely new data, or
- a newly designed research protocol.

---

## What This Project Does Not Claim

This project does **not** claim that EPL markets are perfectly efficient, that no bettor can ever make money, that no future strategy can work, that xG/injuries/lineups are useless, or that statistical relationships cannot exist.

It claims only what the experiments support:

> **The tested mechanisms did not demonstrate a sustainable, statistically reliable economic edge in blind OOS validation.**

That distinction is essential.

---

## Research Philosophy

The project treats a negative result as a legitimate scientific result.

A strategy that looks excellent in discovery but fails out of sample is not a failure of the research process. It is information.

Likewise, a statistically significant relationship that cannot survive economic validation is not automatically a betting opportunity.

> **The objective is not to find a profitable strategy at any cost. The objective is to find out whether a profitable strategy survives a fair test.**

If it does not, the correct output is **NO EDGE FOUND**.

---

## Repository Contents

The repository contains the project's research record, including:
- frozen research protocols
- feature-engineering scripts
- inventory and audit scripts
- exploratory analysis scripts
- economic test scripts
- result workbooks
- diagnostic utilities
- project memory and closing records

The historical archive should be treated as **read-only research evidence**.

---

## Closing Statement

> **20 research paths.  
> 3,800 historical EPL matches.  
> Multiple independent mechanisms.  
> Blind OOS validation.  
> No supported sustainable betting edge identified.**

The strongest positive result in the project was a **structural market relationship**, not a profitable betting strategy.

That is precisely why the research is closed rather than endlessly optimized.

**The result is not “the market is certainly efficient.”**

> **No reliable edge was demonstrated under the tested mechanisms and frozen protocols.**

---

## Repository

**GitHub:** https://github.com/xsinanxaykacx-debug/bhs

**Status:** 🔒 ARCHIVED / RESEARCH CLOSED  
**Blind dataset:** 🔒 2026/27 protected  
**Economic edge:** **NOT FOUND**