# Project Charter v0.2 — Multimodal Battery Prediction

## 1. Governance metadata

| Field | Charter decision |
|---|---|
| **Official project title** | **Generalizable Multimodal Battery Degradation Modeling from Operating Histories, EIS, Pulse Resistance, and Capacity Check-Ups** |
| **Working shorthand** | **Multimodal Battery Prediction** |
| **Future model/toolkit label** | **CBAT** — *Condition-Based Aging Transformer* or *Counterfactual-Aware Battery Aging Toolkit*. This name is reserved for late-stage models only, after data products, baselines, strict splits, ablations, and uncertainty calibration are stable. |
| **Primary dataset basis** | Luh–Blank comprehensive battery aging dataset, version 2 as the intended modeling basis; Scientific Data article as the methods reference. |
| **Project type** | Baseline-first scientific ML project with staged governance, reproducible data products, pre-registered validation, falsification tests, and publication-oriented experiment cards. |
| **Primary deliverable** | A reproducible condition-generalization benchmark and modeling framework for battery degradation prediction from actual operating histories and multimodal check-up diagnostics. |
| **Primary publication unit** | A rigorous empirical study showing whether log-derived stress exposures and multimodal diagnostics improve prediction, calibration, knee-risk warning, and support-bounded policy-response ranking beyond nominal-protocol, EFC/time, semi-empirical, and capacity-only baselines. |

The charter acts as an operational contract: it authorizes the project, constrains scope, defines the scientific claim ladder, and prevents the model architecture from outrunning the evidence base. The governance approach combines lightweight PMO discipline with stage gates, RACI ownership, active decision logs, and a living experiment registry.

---

## 2. One-sentence charter

We test whether **actual log-derived operating exposures**, combined with **capacity, pulse-resistance, and quality-controlled EIS diagnostics**, enable battery degradation models that generalize across held-out operating regimes, quantify replicate-aware uncertainty, warn about degradation knees, and rank supported operating-policy alternatives without overclaiming same-cell counterfactual ground truth.

---

## 3. Executive charter statement

The project’s purpose is not simply to “predict lifetime.” The purpose is to determine whether a battery model can learn a degradation state from **realized stress history** and **multimodal diagnostic check-ups** that remains predictive when the operating condition changes.

The first publishable result should be a benchmark and ablation study, not a transformer. A CBAT-style architecture becomes justified only if simpler baselines, semi-empirical stress models, hierarchical replicate models, and gradient-boosted exposure models fail to explain the observed gains.

---

## 4. Scientific background

Lithium-ion battery degradation is path-dependent and multi-mechanism. Calendar exposure, SOC/voltage, temperature, charging rate, current profile, rest time, CV dwell, and prior age interact nonlinearly. The Scientific Data descriptor notes that SEI growth is primarily associated with SOC and temperature, while lithium plating depends on SOC, temperature, charging rate, and cell age, particularly during cold, high-C-rate, high-SOC charging.

The Luh–Blank dataset is unusually suitable for this project because it contains over 3 billion data points from 228 commercial NMC/C+SiO cells, includes result data such as capacity and impedance measured during check-ups, and publishes raw two-second measurement logs. The experimental design should always be treated as **76 operating conditions × 3 replicates**, not as 228 statistically independent conditions. The dataset includes 16 calendar-aging, 48 cyclic-aging, and 12 driving-profile parameter sets across 0, 10, 25, and 40 °C, with variation in SOC/voltage windows and charge/discharge rates.

The dataset also goes deeper than many open aging datasets: cells were aged down to approximately 40–50% nominal capacity, supporting post-knee and second-life analysis rather than stopping at the conventional 70–80% threshold.

The key scientific opportunity is to replace coarse protocol descriptors such as “25 °C, 10–90%, 1C” with **realized exposure histories**: time at voltage, time at temperature, current histograms, CV dwell, rest periods, charge/discharge asymmetry, temperature excursions, and check-up-induced burden.

---

## 5. Core scientific question

Can models trained on **actual operating-history exposure** and **multimodal diagnostic check-ups** generalize better to unseen aging regimes than models trained only on nominal protocol labels, elapsed time, EFC, or capacity trajectories?

More formally, for cell \(i\), check-up \(k\), diagnostic state \(D_{i,k}\), operating exposure \(E_{i,k:k+1}\), and target state \(Y_{i,k+1}\):

\[
\hat{Y}_{i,k+1} = f(D_{i,\le k}, E_{i,k:k+1}, M_i, C_i)
\]

where:

- \(D_{i,\le k}\) contains diagnostics at or before check-up \(k\);
- \(E_{i,k:k+1}\) contains actual exposure during the interval;
- \(M_i\) contains cell metadata and quality flags;
- \(C_i\) contains condition/protocol metadata;
- \(Y_{i,k+1}\) contains capacity, pulse resistance, EIS-derived features, resistance growth, and knee-risk labels.

The strongest defensible version is:

> Can multimodal supervision improve the learned degradation state enough to support robust, calibrated, support-bounded **policy-response ranking** under held-out experimental conditions?

---

## 6. Core scientific questions

| ID | Question | Operational form |
|---|---|---|
| **Q1 — Forecasting** | Can we predict future capacity fade and resistance growth? | Next-check-up and multi-step prediction of capacity, \(\Delta\)capacity, pulse resistance, \(R_0/R_1\), and EIS features. |
| **Q2 — State learning** | Does multimodal supervision improve the latent degradation state? | Capacity-only versus capacity+pulse versus capacity+pulse+EIS ablations under grouped holdout. |
| **Q3 — Knee warning** | Can we forecast degradation acceleration? | Probability of a knee within \(N\) check-ups or before a target horizon, with detector sensitivity. |
| **Q4 — Policy-response ranking** | Can supported operating alternatives be ranked by degradation severity? | Matched condition-level ranking with triplet uncertainty, support audit, and no same-cell counterfactual claim. |
| **Q5 — Uncertainty** | Does uncertainty reflect both model error and replicate variability? | Prediction intervals, conformal intervals, and replicate-level tolerance intervals by condition. |
| **Q6 — Stress mechanism proxies** | Do physically motivated stress interactions matter? | Feature ablations for high-SOC×high-T, cold×fast-charge, CV-at-high-voltage, check-up burden, and profile dynamics. |

---

## 7. Central hypothesis

Actual operating exposures extracted from LOG/EOC/LOG_AGE records contain degradation-relevant information discarded by nominal protocol labels. Multimodal diagnostic supervision from capacity, pulse resistance, and quality-controlled EIS constrains a latent degradation state better than capacity-only supervision, especially under condition-level and stressor-axis holdouts.

Testable form:

> Models using actual log-derived stress exposure features plus capacity, pulse, and gated EIS diagnostics will outperform nominal-protocol, EFC/time, semi-empirical, hierarchical, and capacity-only baselines on pre-registered prediction, uncertainty, knee-risk, and policy-ranking metrics under grouped validation.

---

## 8. Hypotheses and falsification thresholds

Thresholds should be finalized after the dataset audit confirms modality coverage, but the project should start with quantitative provisional thresholds.

| ID | Hypothesis | Required evidence | Falsification / downgrade trigger |
|---|---|---|---|
| **H1 — Exposure richness** | Actual log-derived exposures outperform nominal protocol labels. | ≥10% improvement in capacity or resistance MAE/CRPS over nominal-only models on leave-condition-out splits. | If actual exposure does not beat nominal labels under grouped splits, the “operating-history” claim is downgraded. |
| **H2 — Semi-empirical challenge** | ML exposure models add value beyond strong domain baselines. | Gradient-boosted or sequence exposure models beat semi-empirical and hierarchical baselines on at least two core metrics. | If ML does not beat semi-empirical baselines, publish as a negative/benchmark result and stop before deep models. |
| **H3 — Multimodal state value** | Pulse and EIS improve degradation-state learning beyond capacity-only. | Capacity+pulse or capacity+pulse+EIS improves prediction, ranking, calibration, or knee warning by ≥10% against capacity-only. | If EIS only reconstructs EIS but does not improve non-EIS outcomes, EIS becomes auxiliary, not central. |
| **H4 — Uncertainty validity** | Model uncertainty reflects replicate and condition variability. | 80/90/95% intervals achieve acceptable coverage by condition and stressor family; replicate tolerance intervals cover triplet spread. | If coverage collapses on condition or stressor holdout, no uncertainty-aware claim. |
| **H5 — Knee warning** | Multimodal state improves knee-risk warning. | Better AUROC/AUPRC, Brier score, lead time, or knee-time error than capacity-only under grouped validation. | If knee labels are unstable across detectors, knee results are exploratory only. |
| **H6 — Policy-response ranking** | Supported policy contrasts can be ranked. | Correct sign and useful ranking on pre-registered matched contrasts, with uncertainty intervals over condition triplets. | If matched-condition ranking fails, the project remains a forecasting/calibration study. |
| **H7 — Temporal history value** | History order matters beyond aggregate exposure. | True histories outperform shuffled-history and aggregate-only baselines. | If shuffled histories perform similarly, sequence models are not justified. |

---

## 9. Scope

### 9.1 In scope

| Area | In-scope definition |
|---|---|
| **Battery system** | Cell-level degradation of LG INR18650HG2 commercial NMC/C+SiO cells. |
| **Dataset** | Luh–Blank comprehensive battery aging dataset, with v2 result/log data intended as the canonical modeling basis and the Scientific Data paper as the experimental-methods reference. |
| **Input modalities** | Nominal protocol metadata, actual log-derived exposure, prior capacity, pulse diagnostics, gated EIS, LOG_AGE summaries, EOC events, and quality flags. |
| **Targets** | Capacity, \(\Delta\)capacity, pulse resistance, resistance growth, \(R_0/R_1\), EIS features, knee-risk probabilities, and policy-response rankings. |
| **Evaluation** | Leave-condition-out, leave-stressor-axis-out, profile holdout, early-to-late transfer, replicate calibration, modality ablation, support-bounded policy ranking. |
| **Models** | Trivial baselines, nominal models, semi-empirical stress models, hierarchical replicate models, GBMs, sequence models, multimodal latent-state models, privileged-EIS distillation, and late-stage CBAT-style policy emulation. |
| **Scientific outputs** | Dataset manifest, linked data products, validation protocol, baseline leaderboard, modality ablation, uncertainty audit, falsification report, paper skeleton, and reproducible code structure. |

### 9.2 Out of scope

The project will not initially claim:

- pack/module-level degradation;
- real-time BMS deployment readiness;
- warranty, certification, or safety decision support;
- thermal runaway prediction;
- direct mechanistic decomposition into SEI, LAM, LLI, lithium plating, or electrolyte depletion;
- universal transfer to other chemistries, formats, or manufacturers;
- field-operation generalization beyond laboratory evidence;
- true same-cell counterfactual ground truth;
- policy performance outside observed support;
- a transformer/CBAT architecture as the primary scientific contribution.

---

## 10. Data basis and provenance requirements

### 10.1 Dataset decision

The intended canonical basis is the Luh–Blank version-2 dataset.

| Data artifact | Charter decision |
|---|---|
| **Result data v2** | Canonical source for capacity, EIS, pulse, and check-up result modalities. |
| **Log data v2** | Canonical source for actual exposure extraction. |
| **Scientific Data paper** | Methods reference for cell selection, test matrix, check-up procedure, data records, and technical validation. |
| **Original v1 data** | Use only for methods comparison or if v2 lacks a necessary field. |
| **EIS addendum / fixed EIS archive** | Mandatory if any EIS archive is incomplete or if EIS coverage cannot be verified. |
| **Example scripts** | Use as reference for parsing, plotting, plausibility checks, and LOG_AGE generation; do not treat as a production pipeline without audit. |
| **Archive hashes** | Required before modeling. |

The public data records include CFG, EOC, EIS, PULSE, LOG, LOG_AGE, pool logs, slave logs, structure spreadsheets, plausibility checks, and result plot examples. The paper describes EOC, EIS, PULSE, LOG, and LOG_AGE as separate data records with distinct files, columns, and purposes.

### 10.2 Local manifest requirements

Before any model is trained, create:

```text
data/MANIFEST.sha256
data/dataset_manifest.json
data/schema_registry/
data/split_registry/
data/known_issues_register.md
```

The manifest must record:

- archive name, DOI, source, date downloaded;
- SHA-256 hash;
- extracted file count;
- row count by file family;
- cell count by modality;
- condition count;
- EIS coverage by cell/SOC/temperature/check-up;
- PULSE coverage by cell/SOC/temperature/check-up;
- LOG and LOG_AGE availability;
- known anomalies and data gaps;
- preprocessing script commit hash;
- generated table schema version.

### 10.3 Hard audit rules

A model result is invalid until these audits pass:

1. **Cell coverage:** verify 228 expected cell IDs and 76 parameter sets × 3 replicates.
2. **Modality coverage:** verify capacity, EIS, PULSE, LOG, and LOG_AGE coverage by cell.
3. **EIS integrity:** assert full intended cell coverage and valid-frequency masks before any EIS-supervised claim.
4. **PULSE provenance:** verify PULSE source and extraction path.
5. **Check-up alignment:** map each CU index to EOC, EIS, PULSE, LOG, and LOG_AGE timestamps.
6. **Unit consistency:** capacity in Ah, current in A, voltage in V, temperature in °C, impedance in mΩ/Ω, time in seconds/hours/days.
7. **Known anomalies:** flag pool temperature incidents, Peltier failure, Ethernet gaps, reboots, interpolation, and EOL truncation.
8. **Reproducibility:** freeze preprocessing code and schema before baseline leaderboard.

---

## 11. Measurement protocol boundaries

### 11.1 Check-up cadence and burden

The experiment begins with an initial CU, the second CU follows after one week, and subsequent CUs occur every three weeks in the published v1 period. The CU procedure includes temperature transition, capacity measurement, EIS, and pulse measurements.

Check-ups are not passive observations. Calendar-aging cells can accumulate meaningful cyclic burden during repeated capacity checks. The paper explicitly states that a considerable fraction of calendar-cell capacity fade may be caused by cyclic aging during check-ups, with calendar cells experiencing 43–63 EFCs primarily from capacity checks after the last CU shown.

**Charter rule:** check-up burden is a first-class confound and must be represented in the interval table.

### 11.2 Capacity measurement

The primary capacity target is the remaining usable discharge capacity measured during the standardized CU capacity procedure at room temperature, including complete CC–CV charge/discharge between 2.5 and 4.2 V at 1/3 C with 1/20 C cut-off.

### 11.3 EIS measurement

EIS is measured during CUs at RT and OT, across SOC points 10, 30, 50, 70, and 90%, over 50 mHz to 14.7 kHz. The data records also include valid flags, raw and compensated impedance values, amplitude/phase, real/imaginary parts, average temperature, and measurement duration.

EIS is a gated modality. The most accurate range is approximately 0.5 Hz to 5 kHz, excluding 100 Hz and 208.3 Hz; the 14.7 kHz point is always set to NaN; and the authors warn that individual inaccurate EIS points may remain after relaxed filtering.

### 11.4 PULSE measurement

PULSE measurements use rectangular ±1/3 C current signals and are repeated at the same five SOC points as EIS. The PULSE records include 10 ms and 1 s pulse resistance, voltage, current, temperature, SOC, and aging-condition context.

The paper states that PULSE measurements can be used for impedance estimation without further modification, while EIS may require additional filtering.

### 11.5 LOG and LOG_AGE

LOG contains two-second voltage, current, power, temperature, charge/energy, SoC/OCV estimates, scheduler states, and EOL flags. LOG_AGE is a reduced, uniform-resolution derivative that includes essential LOG columns plus capacity and characteristic resistances \(R_0/R_1\).

LOG_AGE is useful for prototyping, but final exposure claims should be traceable to LOG/EOC where possible because LOG_AGE includes interpolated/averaged data and inserts diagnostic values at specific result timestamps. The paper explains that \(C_{\text{remaining}}\) is inserted from EOC and \(R_0/R_1\) are derived from EIS and inserted after the last EIS measurement timestamp.

---

## 12. Governing principles

1. **Data product first; model second.**  
   Every model consumes versioned data products with traceable provenance.

2. **Baseline first; architecture later.**  
   CBAT is not authorized until the baseline leaderboard, ablation matrix, and uncertainty audit pass.

3. **Condition-level validation only for headline claims.**  
   Random row-level or cell-level splits are leakage smoke tests, not evidence.

4. **Treat 228 cells as 76 triplets.**  
   Replicates estimate within-condition variability; they do not create 228 independent regimes.

5. **EIS is gated, not assumed.**  
   EIS must improve a pre-registered non-EIS outcome or calibration/ranking claim.

6. **Targets are measurement-bound.**  
   Capacity, pulse resistance, and EIS features must always carry temperature, SOC, check-up index, and file provenance.

7. **Check-ups are interventions.**  
   Diagnostic cycling burden must be measured or flagged.

8. **Policy ranking is support-bounded.**  
   No claim is allowed outside experimental support or without overlap diagnostics.

9. **Uncertainty is a primary output.**  
   A model without calibration and replicate-aware intervals is incomplete.

10. **Falsification is mandatory.**  
    Negative results are valid project outcomes if generated under strict splits.

---

## 13. Data product architecture

The project should use a linked data-product system rather than one oversized modeling table.

| Data product | Purpose | Core contents |
|---|---|---|
| **`dataset_manifest`** | Provenance and audit | DOIs, archives, hashes, file counts, row counts, modality coverage, known issues, preprocessing commit. |
| **`cell_condition_table`** | Experimental design | `cell_id`, `parameter_set`, `replicate_id`, aging mode, temperature, voltage/SOC window, C-rates, profile label, slave/channel/pool. |
| **`checkup_event_table`** | Diagnostic events | CU index, timestamps, capacity results, EIS availability, pulse availability, RT/OT, SOC, validity flags. |
| **`run_event_table`** | Operational segments | CC charge, CV charge, discharge, rest, profile segments, scheduler states, data gaps, current/voltage/temperature summaries. |
| **`modality_table_eis`** | EIS spectra and features | Complex spectra, compensated spectra, valid-frequency mask, selected-frequency features, DRT features, RT/OT, SOC, validity flags. |
| **`modality_table_pulse`** | Pulse diagnostics | 10 ms and 1 s resistance, full pulse response if available, SOC, RT/OT, average measurement temperature. |
| **`interval_table`** | Main modeling table | One row per cell/check-up interval; joins prior state, exposure, target deltas, quality flags, split labels. |
| **`split_registry`** | Frozen evaluation | Leave-condition, stressor-axis, profile, replicate, and time-horizon fold IDs. |
| **`experiment_registry`** | Reproducibility | Model, features, targets, split, metrics, seed, hyperparameters, compute, result, interpretation. |

The four core objects are check-up events, operational run events, interval rows, and modality tables. High-dimensional structures such as EIS spectra, DRT vectors, and pulse responses should remain in modality tables and be referenced by keys rather than flattened prematurely.

---

## 14. Central interval table

The main modeling row is:

\[
(i, k, [t_{i,k}, t_{i,k+1}])
\]

where \(i\) is a physical cell and \(k\) is a check-up index.

### 14.1 Required interval definitions

| Interval type | Definition | Use |
|---|---|---|
| **Aging-only interval** | End of check-up \(k\) to start of check-up \(k+1\). | Clean exposure modeling without diagnostic burden. |
| **Measurement-to-measurement interval** | Diagnostic result at \(k\) to corresponding diagnostic result at \(k+1\). | Direct next-check-up transition prediction. |
| **Forecasting horizon interval** | Diagnostic state at \(k\), exposure known only up to forecast time or generated from a proposed policy. | Prospective forecasting and policy emulation. |

### 14.2 Required fields

| Category | Required fields |
|---|---|
| **Identity** | `cell_id`, `parameter_set`, `condition_id`, `replicate_id`, `dataset_version`, `chemistry`, `cell_model`, `slave_id`, `channel_id`, `pool_id` |
| **Time/indexing** | `checkup_k`, `t_result_k`, `t_interval_start`, `t_interval_end`, `t_result_k1`, `duration_s`, `duration_h`, `calendar_days` |
| **Prior state** | `capacity_k_Ah`, `capacity_soh_k`, `pulse_10ms_k`, `pulse_1s_k`, `R0_k`, `R1_k`, `eis_features_k`, `diag_temp_k`, `diag_soc_k`, `diag_RT_OT_k` |
| **Post state** | `capacity_k1_Ah`, `capacity_soh_k1`, `pulse_10ms_k1`, `pulse_1s_k1`, `R0_k1`, `R1_k1`, `eis_features_k1` |
| **Targets** | `delta_capacity_Ah`, `delta_capacity_per_day`, `delta_capacity_per_efc`, `delta_pulse_10ms`, `delta_pulse_1s`, `delta_R0`, `delta_R1`, `delta_eis_features`, `knee_label`, `knee_within_N`, `time_to_knee` |
| **Nominal protocol** | `aging_mode`, `nominal_temperature_C`, `voltage_window`, `soc_window_approx`, `nominal_charge_C_rate`, `nominal_discharge_C_rate`, `profile_label`, `cutoff_current`, `voltage_limits` |
| **Actual scalar exposure** | `efc_interval`, `Ah_throughput`, `Wh_throughput`, `mean_T`, `max_T`, `min_T`, `mean_V`, `max_V`, `min_V`, `mean_abs_I`, `max_abs_I`, `rest_hours`, `cv_hours` |
| **Histogram exposure** | `time_voltage_bins`, `time_soc_bins`, `time_temperature_bins`, `time_current_bins`, `charge_Crate_hist`, `discharge_Crate_hist` |
| **Coupled stress exposure** | `highV_highT_hours`, `highSOC_highT_hours`, `cold_fast_charge_hours`, `highV_CV_hours`, `voltage_temperature_dose`, `arrhenius_weighted_time`, `plating_proxy_exposure` |
| **Check-up burden** | `CU_EFC`, `CU_Ah_throughput`, `CU_Wh_throughput`, `CU_duration_h`, `RT_OT_transition_h`, `num_CU_events`, `capacity_check_burden` |
| **Quality flags** | `missingness_flag`, `interpolation_flag`, `data_gap_seconds`, `synthetic_pause_flag`, `EIS_available`, `EIS_valid_fraction`, `pulse_available`, `LOG_available`, `LOG_AGE_available`, `temperature_anomaly`, `peltier_anomaly`, `fault_or_EOL_flag` |
| **Provenance** | `cfg_file_id`, `eoc_file_id`, `eis_file_id`, `pulse_file_id`, `log_file_ids`, `log_age_file_id`, `file_hashes`, `preprocessing_version` |
| **Split labels** | `condition_fold`, `temperature_holdout_fold`, `soc_window_holdout_fold`, `c_rate_holdout_fold`, `profile_holdout_fold`, `replicate_calibration_fold`, `time_horizon_fold` |

---

## 15. Target taxonomy

| Priority | Target | Measurement-bound definition |
|---|---|---|
| **Primary** | Capacity | Remaining usable discharge capacity measured during standardized CU capacity procedure at RT. |
| **Primary** | \(\Delta\)capacity | \(capacity_k - capacity_{k+1}\), plus normalized variants per day, per EFC, per Ah, and per Wh. |
| **Primary** | Pulse resistance | 10 ms and 1 s pulse resistance at explicit SOC and RT/OT context; default benchmark should include RT 50% SOC plus all-SOC multi-output variants. |
| **Primary** | Resistance growth | \(\Delta\)pulse resistance and/or \(\Delta R_0/\Delta R_1\) across intervals. |
| **Secondary** | \(R_0/R_1\) | Characteristic EIS-derived resistances inserted into LOG_AGE; useful but leakage-sensitive. |
| **Secondary** | EIS features | Valid-frequency complex spectra, selected-frequency features, \(R_0/R_1\), geometric Nyquist features, DRT features, PCA/autoencoder embeddings, or ECM parameters after QA. |
| **Secondary** | Knee risk | Probability of knee within \(N\) check-ups or before a fixed horizon; never a single unquestioned ground-truth point. |
| **Exploratory** | Policy-response ranking | Condition-level ordering of supported operating alternatives, with replicate-aware uncertainty. |
| **Exploratory** | Mechanistic proxies | Lithium-plating proxy, CV anomalies, impedance shifts, cold-fast-charge exposure; no mechanistic identification claim in v1. |

---

## 16. EIS feature policy

EIS features must be built in tiers.

| Tier | Feature class | Description | Use |
|---|---|---|---|
| **E0** | Valid-frequency raw/compensated spectra | Mask 14.7 kHz, 100 Hz, 208.3 Hz, low-quality points, and invalid sweeps. | Full-spectrum model input and QA. |
| **E1** | Selected-frequency features | \(Re(Z)\), \(-Im(Z)\), magnitude, phase at stable frequency bands and SOC/temperature contexts. | Strong simple EIS baseline. |
| **E2** | Dataset-provided \(R_0/R_1\) | \(R_0\) and \(R_1\) from author-defined EIS reduction. | Low-dimensional diagnostic state. |
| **E3** | Geometric Nyquist features | Ohmic intercept, semicircle diameter, peak imaginary coordinate, tailhead slope. | Fast, interpretable, optimization-free features. |
| **E4** | DRT features | Peak areas associated with low-frequency diffusion, charge-transfer resistance, SEI-related processes, and high-frequency ohmic response. | Interpretable but gated by stability and regularization. |
| **E5** | Learned EIS embeddings | Autoencoder, contrastive encoder, or task-supervised EIS encoder. | Late-stage multimodal latent-state modeling. |

The DRT track should remain gated because it introduces regularization, peak-identification, and non-uniqueness choices. The proposed DRT feature map separates low-frequency diffusion, mid-frequency charge transfer, high-mid SEI-related response, and high-frequency ohmic response; direct Nyquist features act as a simpler backup.

---

## 17. Exposure feature taxonomy

| Feature family | Examples | Claim tested |
|---|---|---|
| **Trivial exposure** | elapsed days, check-up index, EFC, Ah throughput, Wh throughput | Do simple exposure variables suffice? |
| **Nominal protocol** | temperature setpoint, SOC/voltage window, nominal C-rate, aging mode, profile label | Are protocol labels enough? |
| **Actual scalar exposure** | realized mean/max/min T, V, I, estimated SOC, CV fraction, rest fraction | Do actual logs beat nominal labels? |
| **Histogram exposure** | time in voltage, SOC, temperature, current/C-rate bins | Does distributional exposure matter? |
| **Coupled stress exposure** | high-SOC×high-T, cold×fast-charge, high-voltage CV dwell, voltage×temperature dose | Do known stress interactions help? |
| **Sequence summaries** | interval traces, profile embeddings, segment order, CC/CV/rest/discharge transitions | Does temporal order matter beyond cumulative dose? |
| **Diagnostic state** | capacity, pulse, \(R_0/R_1\), EIS embeddings | Do diagnostics improve latent state? |
| **Nuisance/QA exposure** | pool anomaly, Peltier failure, data gaps, slave/channel, check-up burden | Are models exploiting artifacts? |
| **Exploratory causal-health features** | PCMCI/transfer-entropy edge metrics, Mahalanobis deflation scores, dynamic discharge-only dependency features | Do directed telemetry relationships reveal early degradation drift? |

The published data show why actual exposure matters: individual cell surface temperatures can deviate from pool setpoints, and severely aged, fast-charging cold cells can show temperature increases up to 11 K despite cooling.

---

## 18. Exploratory CausalHealth feature track

The information-theoretic feature track is exploratory, not part of the minimum publishable claim.

### 18.1 Purpose

To test whether directed relationships among voltage, current, temperature, and resistance proxies during controlled discharge segments produce health indicators that improve early warning or OOD generalization.

### 18.2 Guardrails

| Guardrail | Rule |
|---|---|
| **Discharge-only default** | Restrict causal-dependency features to discharge segments unless a separate charging-phase model is justified. |
| **CC algebraic-identity guard** | Under constant-current segments, do not treat \(R(t)=V(t)/|I|\) as independent of voltage. |
| **No causal overclaim** | PCMCI/transfer entropy features are statistical dependency features unless validated under explicit causal assumptions. |
| **Baseline comparison** | Must beat conventional exposure features and sequence summaries. |
| **Failure rule** | If shuffled histories or simple histograms match performance, discard this track. |

The proposed CausalHealth concept uses discharge-restricted dependency metrics, a constant-current algebraic-identity guard, PCMCI/transfer-entropy features, and Mahalanobis deflation scores; it should be treated as an optional feature experiment with strict exit criteria.

---

## 19. Leakage rules

No result is valid unless these rules are enforced.

1. **Prediction at \(k\)** may use diagnostics and logs at or before \(k\), never target diagnostics at \(k+1\).
2. **Transition emulation** may use exposure from \(k\) to \(k+1\) because it predicts the observed transition after the interval occurred.
3. **Prospective forecasting** may use only exposure up to forecast time or a proposed future policy trace.
4. **LOG_AGE inserted diagnostics** must be masked so that \(capacity_{k+1}\), \(R0_{k+1}\), or \(R1_{k+1}\) cannot leak into features for interval \(k\).
5. **Replicates from the same condition** must remain together in headline train/test splits.
6. **Condition metadata** may not encode target information through post-hoc labels.
7. **Check-up burden** must be either included as exposure or separated through aging-only intervals.
8. **Quality flags** must not be silently dropped; models must be evaluated with and without nuisance/artifact features.
9. **Random row-level splits** are leakage smoke tests only.
10. **Model selection** must occur inside the training/validation loop, never on held-out test conditions.

---

## 20. Modeling ladder

Every rung must produce an evaluation card before the next rung is authorized.

| Level | Model / artifact | Purpose | Exit criterion |
|---|---|---|---|
| **L0** | Data loader, manifest, QA dashboard | Reproduce file counts, modality coverage, plots, missingness, EIS validity, pulse availability, LOG gaps. | Data audit passes. |
| **L1** | Persistence / last-value / linear extrapolation | Establish trivial lower bound. | Benchmark created; all serious models must beat it. |
| **L2** | Time/EFC/Ah/Wh baseline | Test simple degradation exposure. | Quantifies trivial exposure ceiling. |
| **L3** | Nominal protocol regression | Temperature, voltage/SOC window, nominal C-rate, aging mode, profile. | Quantifies nominal-label ceiling. |
| **L4** | Semi-empirical stress model | Calendar/cycling stress, Arrhenius-like temperature terms, voltage/SOC stress, DOD/current terms. | Mandatory strong domain comparator. |
| **L5** | Mixed-effects / hierarchical replicate model | Explicitly models condition and triplet variability. | Required for uncertainty and replicate calibration comparisons. |
| **L6** | Quantile GBM / XGBoost / CatBoost on engineered exposure | First serious ML baseline; supports quantile intervals. | MVP scientific model. |
| **L7** | Sequence model on interval/run summaries | Tests temporal ordering beyond cumulative dose. | Continue only if it beats L6 under grouped holdout. |
| **L8** | Capacity-only latent-state model | Tests latent dynamics without multimodality. | Baseline for multimodal claim. |
| **L9** | Capacity + pulse multimodal model | First robust multimodal model. | Pulse must improve prediction, calibration, resistance, or ranking. |
| **L10** | Capacity + pulse + EIS model | Tests EIS as supervised diagnostic signal. | EIS must improve held-out generalization, calibration, ranking, or knee warning. |
| **L11** | Privileged-EIS teacher/student | EIS/DRT during training, deployment with logs/pulse/capacity only. | Student must beat non-privileged student. |
| **L12** | Physics-assisted uncertainty model | Optional PyBaMM/SPMe source domain, MMD alignment, conformal calibration. | Only after L6–L10 are stable; must improve calibration under domain shift. |
| **L13** | CBAT-style policy-response model | Support-bounded policy ranking under interventions. | Only after support audit, grouped ranking validation, and uncertainty calibration pass. |

Privileged-EIS distillation is authorized only if deployment without active EIS remains a project goal. In that case, the teacher may consume full EIS/DRT features, but the student must operate on deployable signals such as voltage, current, temperature, capacity, and pulse-derived features.

---

## 21. Validation protocol

### 21.1 Hard validation rule

Primary validation is conducted at the **condition/parameter-set level**, not by random rows or cells.

### 21.2 Required splits

| Split | Name | Grouping | Claim tested |
|---|---|---|---|
| **S0** | Random row/cell split | Rows or cells | Leakage smoke test only; not publishable evidence. |
| **S1** | Condition-grouped ID split | Entire condition triplets kept together | Debugging and baseline sanity. |
| **S2** | Leave-condition-out | `condition_id` / parameter set | Generalization to unseen protocols. |
| **S3** | Leave-temperature-out | 0, 10, 25, or 40 °C families | Temperature transfer. |
| **S4** | Leave-voltage/SOC-window-out | 0–100, 10–100, 10–90, calendar SOC levels | Voltage/SOC transfer. |
| **S5** | Leave-C-rate-out | Charge/discharge-rate combinations | Current-stressor transfer. |
| **S6** | Profile-aging holdout | WLTP/profile conditions | Dynamic-operation transfer. |
| **S7** | Early-to-late transfer | Early intervals train; late/post-knee test | Long-horizon and knee forecasting. |
| **S8** | Replicate calibration | Triplet variability | Prediction and tolerance interval calibration. |
| **S9** | Modality ablation | capacity vs capacity+pulse vs capacity+pulse+EIS | Diagnostic value. |
| **S10** | Matched policy ranking | Supported condition contrasts | Policy-response ordering. |

The validation matrix should use nested grouped folds and condition-cluster bootstrap rather than individual-cell bootstrap; the grouped design must explicitly keep parameter-set triplets together.

### 21.3 Statistical reporting

Every headline metric must report:

- mean over held-out conditions;
- median over held-out conditions;
- worst-condition error;
- condition-cluster bootstrap confidence interval;
- paired difference versus the strongest baseline;
- number of conditions and cells;
- number of check-up intervals;
- number of seeds;
- hyperparameter budget;
- compute time;
- failure cases by stressor family.

---

## 22. Policy-response ranking protocol

### 22.1 Estimand

The project estimates **condition-level policy-response effects**, not same-cell counterfactuals.

For two supported policies \(a\) and \(b\), define a contrast such as:

\[
\Delta_{a,b}(h) = \mathbb{E}[Y(h)\mid do(a), \mathcal{S}] - \mathbb{E}[Y(h)\mid do(b), \mathcal{S}]
\]

where \(h\) is a horizon and \(\mathcal{S}\) is the support region defined by observed temperature, voltage/SOC, current, profile, and age ranges.

### 22.2 Required support audit

Before ranking any alternative policy:

1. verify comparable operating region exists in observed data;
2. compute overlap across temperature, voltage/SOC, C-rate, age, and profile family;
3. reject extrapolated contrasts outside support;
4. report uncertainty using replicate triplets and condition bootstrap;
5. compare predicted sign and magnitude against held-out condition means.

### 22.3 Allowed claims

Allowed:

- “The model ranks policy A as more damaging than policy B within the observed support region.”
- “Predicted severity ordering matches held-out condition triplets for this contrast.”
- “The interval includes/excludes the empirical triplet-bootstrap effect.”

Not allowed:

- “This is the true counterfactual outcome for the same cell.”
- “This policy will generalize to arbitrary field usage.”
- “This model identifies the causal degradation mechanism.”
- “This policy ranking is valid outside the Luh–Blank support region.”

---

## 23. Uncertainty calibration protocol

Uncertainty is part of the model output, not an afterthought.

| Layer | Method | Use |
|---|---|---|
| **Point uncertainty** | Ensembles, Bayesian regression, quantile GBM, NGBoost, Gaussian likelihood heads | Prediction intervals and NLL/CRPS. |
| **Distribution-free calibration** | Split conformal prediction on grouped calibration sets | Finite-sample interval calibration under exchangeability assumptions. |
| **Replicate-aware uncertainty** | Triplet variance, hierarchical models, tolerance intervals | Cell-to-cell variability under the same condition. |
| **Condition-aware uncertainty** | Condition-cluster bootstrap | Error uncertainty over held-out operating regimes. |
| **Domain-shift calibration** | Weighted/conformalized residuals by stressor family | Calibration under leave-stressor-axis shifts. |
| **Optional advanced track** | MMD alignment with physics-based simulated trajectories and conformal calibration | Only after empirical models are stable. |

The domain-adaptive conformal idea is useful but should be late-stage. It couples conformal intervals with MMD alignment and, optionally, PyBaMM/SPMe source-domain trajectories; this is powerful but should not be allowed to distract from grouped empirical calibration on the physical triplets.

### Required uncertainty metrics

- NLL where probabilistic likelihood exists;
- CRPS;
- 80/90/95% prediction interval coverage;
- interval score / Winkler score;
- normalized interval width;
- calibration by condition and stressor family;
- replicate tolerance interval coverage;
- OOD coverage under leave-stressor-axis holdouts.

---

## 24. Knee-risk policy

Knee prediction is permitted only as probabilistic, sensitivity-tested risk estimation.

### 24.1 Primary knee target

Default target:

\[
P(\text{knee within next } N \text{ check-ups} \mid D_{\le k}, E_{\le k})
\]

and/or:

\[
P(\text{knee before horizon } h)
\]

### 24.2 Primary detector

The primary detector should be a constrained piecewise-linear breakpoint on capacity versus calendar time or EFC, with:

- minimum segment length;
- monotonicity checks;
- no future leakage for early-warning tasks;
- sensitivity to x-axis choice.

### 24.3 Required alternatives

Report sensitivity to at least two of:

- Kneedle / maximum chord distance;
- L-method / two-line fit;
- dynamic first-derivative threshold;
- curvature/Menger method;
- Bacon–Watts or bisector-style detector;
- capacity-threshold events such as 80%, 70%, 60%.

Automated knee detection can use a multi-detector framework, but recursive/multi-knee detection must include filters against spurious knees, monotonicity violations, and over-segmentation.

### 24.4 Reporting rules

Always report:

- knee detector;
- x-axis used: days, EFC, Ah throughput, or check-up index;
- smoothing method;
- \(N\)-check-up window;
- detector agreement/disagreement;
- label stability;
- probabilistic calibration.

---

## 25. Metrics

### 25.1 Prediction metrics

| Metric | Use |
|---|---|
| Capacity MAE/RMSE | Main point-prediction accuracy. |
| \(\Delta\)capacity MAE/RMSE | Interval transition error. |
| Capacity-rate error | Error per day, per EFC, per Ah, per Wh. |
| Pulse-resistance MAE/RMSE | Resistance/power-related prediction. |
| \(R_0/R_1\) error | EIS-derived resistance endpoint. |
| EIS feature error | Spectrum/embedding/feature prediction. |
| Multi-step trajectory error | Teacher-forced and free-rollout variants. |
| Worst-condition error | OOD robustness. |

### 25.2 Ranking metrics

| Metric | Use |
|---|---|
| Pairwise ranking accuracy | Condition-pair severity ordering. |
| Spearman \(\rho\) / Kendall \(\tau\) | Condition-level severity correlation. |
| Sign consistency | Whether predicted policy effect direction matches observed contrast. |
| Top-k harmful-condition identification | Operational screening. |
| Regret | Degradation penalty from choosing model-recommended policy versus best supported observed alternative. |

### 25.3 Uncertainty metrics

| Metric | Use |
|---|---|
| CRPS | Distributional prediction quality. |
| NLL | Likelihood calibration where available. |
| PICP-80/90/95 | Prediction interval coverage. |
| Interval score | Penalizes both width and misses. |
| Calibration error by condition | OOD reliability. |
| Replicate tolerance coverage | Cell-to-cell variability. |
| Condition-cluster bootstrap CI | Statistical uncertainty over condition families. |

### 25.4 Knee metrics

| Metric | Use |
|---|---|
| AUROC/AUPRC | Knee within next \(N\) check-ups. |
| Brier score | Probabilistic knee calibration. |
| Lead time at fixed false-positive rate | Early warning utility. |
| Knee-time MAE | Timing accuracy when labels are stable. |
| Detector stability | Sensitivity across knee definitions. |

### 25.5 Reproducibility metrics

Every evaluation card reports:

- model version;
- dataset manifest hash;
- split registry hash;
- preprocessing commit;
- random seeds;
- hyperparameter budget;
- CPU/GPU hours;
- wall-clock time;
- inference latency;
- environment file;
- failed runs.

---

## 26. Falsification tests

| Test | Failure interpretation |
|---|---|
| Actual exposure does not beat nominal protocol under leave-condition-out | Log-derived exposure claim weakened. |
| GBM/stress-feature model fails to beat semi-empirical baseline | Flexible ML not yet justified. |
| EIS improves only EIS reconstruction, not capacity/resistance/ranking/calibration | EIS is auxiliary, not central. |
| Pulse does not improve resistance prediction or calibration | Pulse branch should be narrowed or removed. |
| Random splits look strong but grouped splits collapse | Leakage or condition memorization. |
| Shuffled histories perform similarly to true histories | Temporal order not important. |
| Removing CV/high-voltage/cold-fast-charge features has no effect | Stress-interaction hypothesis weakened. |
| Removing check-up burden changes conclusions materially | Diagnostic burden was confounding the model. |
| Removing thermal anomaly periods changes conclusions materially | Model depends on nuisance artifacts. |
| Uncertainty intervals under-cover held-out conditions | No calibrated uncertainty claim. |
| Replicate tolerance intervals fail | Cell-to-cell variability not captured. |
| Policy ranking fails matched contrasts | No policy-response claim. |
| Knee labels unstable across detectors | Knee claim becomes exploratory. |
| EIS QA filters alter conclusions | EIS claim depends on fragile spectra. |
| Profile holdout collapses | No dynamic-operation generalization claim. |
| Same performance using nominal labels plus condition ID | Model is not learning transferable exposure physics. |

---

## 27. Research claim ladder

| Tier | Claim | Required evidence |
|---|---|---|
| **T0 — Infrastructure claim** | The dataset can be reproducibly ingested, audited, aligned, and versioned. | Manifest, hashes, file counts, QA dashboard, modality coverage, EIS coverage, split registry. |
| **T1 — Minimum viable claim** | Actual stress exposures improve next-check-up capacity and pulse-resistance prediction beyond elapsed-time, EFC, and nominal-protocol baselines. | L0–L6 under leave-condition-out. |
| **T2 — Minimum publishable claim** | Actual exposures plus multimodal diagnostics improve at least two of prediction, ranking, calibration, or knee warning beyond capacity-only and semi-empirical baselines. | L0–L10 ablation matrix under grouped validation. |
| **T3 — Strong claim** | A multimodal latent-state model generalizes to held-out stressor axes and profile aging with calibrated uncertainty. | L8–L11 beat L4–L6 on stressor-axis and profile holdouts. |
| **T4 — Ambitious claim** | A support-bounded policy-response model ranks alternative operating strategies under uncertainty. | L13 passes support audit, matched contrasts, calibration, and sensitivity analysis. |
| **T5 — Extension claim** | The framework transfers beyond the initial chemistry/dataset. | Separate external dataset, chemistry, or manufacturer; not part of the first publishable unit. |

The core publication should target T2. T3 and T4 are valuable but should not be required for project survival.

---

## 28. Success gates

| Gate | Artifact | Go criterion | No-go / pivot criterion |
|---|---|---|---|
| **G0** | Charter | Scope, claims, exclusions, RACI, gates accepted. | Ambiguous claim or uncontrolled scope. |
| **G1** | Dataset evidence memo | Versions, hashes, file counts, modality coverage, known issues documented. | Missing modality provenance or unresolved EIS coverage. |
| **G2** | Data product system | Manifest, condition, check-up, run, modality, interval, split tables generated. | Inconsistent alignment across modalities. |
| **G3** | QA dashboard | Missingness, EIS validity, pulse coverage, LOG gaps, anomalies visible per cell/condition. | Hidden data gaps or unflagged anomalies. |
| **G4** | Baseline leaderboard | L1–L6 run under grouped validation. | Serious baselines missing or random splits used as evidence. |
| **G5** | Modality ablation | Capacity, pulse, EIS contributions quantified. | Multimodal gains absent or only in-distribution. |
| **G6** | Uncertainty audit | Prediction and tolerance intervals evaluated by condition/replicate. | Calibration fails under grouped holdout. |
| **G7** | Knee audit | Primary and alternative knee detectors compared. | Labels unstable without clear reporting. |
| **G8** | Policy support audit | Supported contrasts defined and validated. | Ranking requires extrapolation outside support. |
| **G9** | Minimum paper package | T2 claim supported with falsification results. | Only weak/random-split gains. |
| **G10** | CBAT authorization | Latent multimodal model beats strong baselines under strict OOD validation. | Architecture work pauses; publish benchmark/negative result. |

---

## 29. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Dataset-version confusion | Corrupts provenance and makes results irreproducible. | Manifest, hashes, version registry, archive-specific row counts. |
| EIS incompleteness | Invalid multimodal coverage. | Full cell/SOC/temperature/check-up EIS audit before EIS modeling. |
| EIS noise | Spurious spectral features. | Valid-frequency mask, compensated spectra, geometric features, EIS-free baseline. |
| PULSE provenance issue | Misaligned pulse diagnostics. | Verify PULSE source, timestamps, and extraction. |
| Check-up-induced aging | Calendar-aging confound. | Aging-only vs measurement-to-measurement intervals; CU burden features. |
| LOG_AGE leakage | Future diagnostics leak through inserted values. | Strict cutoff masks and leakage tests. |
| Data gaps/interpolation | False exposure histories. | Gap flags, synthetic pause flags, with/without sensitivity analysis. |
| Thermal anomalies | Models may learn artifacts. | Anomaly flags; sensitivity excluding affected intervals. |
| Small-N conditions | Overconfident generalization. | Condition-level bootstrap, grouped splits, worst-condition reporting. |
| Overbuilt architecture | Complex model hides weak evidence. | Stage gates and baseline-first progression. |
| Weak policy framing | Causal overclaim. | Support audit, matched contrasts, no same-cell counterfactual claims. |
| Knee-label instability | Unreliable warning task. | Multi-detector sensitivity and probabilistic labels. |
| Uncalibrated uncertainty | Unsafe claims. | CRPS, interval scores, conformal calibration, replicate tolerance intervals. |
| Publication overclaim | Reviewer rejection. | Falsification tests, limitations, exact language discipline. |

---

## 30. Governance model

### 30.1 RACI

| Workstream | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Charter and scope | Project lead | PI/sponsor | domain/ML/statistics advisors | full team |
| Dataset audit | Data lead | Project lead | battery/domain advisor | full team |
| Schema/data products | Data lead | Project lead | ML/statistics advisor | full team |
| EIS QA and features | EIS/domain lead | Project lead | electrochemistry advisor | full team |
| Pulse targets | Data/domain lead | Project lead | battery advisor | full team |
| Exposure features | Data + ML leads | Project lead | domain advisor | full team |
| Validation protocol | Statistician/ML lead | Project lead | PI/sponsor | full team |
| Baselines | ML lead | Project lead | statistics/domain advisors | full team |
| Multimodal models | ML lead | Project lead | EIS/statistics advisors | full team |
| Uncertainty calibration | Statistician | Project lead | ML advisor | full team |
| Policy ranking | Project lead/statistician | PI/sponsor | domain/ML advisors | full team |
| Manuscript | Project lead | PI/sponsor | all contributors | full team |

RACI entries should be accompanied by rough time commitments for active phases. Assigning names is insufficient unless decision authority and resource commitments are explicit.

### 30.2 Re-chartering triggers

Re-charter if:

- dataset version or modality coverage differs materially from assumptions;
- EIS quality or coverage fails the gate;
- baseline leaderboard invalidates the main exposure hypothesis;
- multimodal ablations fail under grouped validation;
- thermal/nuisance artifacts materially affect conclusions;
- policy ranking lacks support/overlap;
- scope expands beyond Luh–Blank cell-level modeling;
- compute/timeline exceeds planned bounds by more than 15%;
- external dataset transfer becomes a required claim.

The project should explicitly avoid the “plan-as-reality” failure mode: the charter is a control document, not a guarantee that initial assumptions will survive data audit.

---

## 31. Living artifacts

Maintain these artifacts throughout the project:

1. `PROJECT_CHARTER.md`
2. `ASSUMPTION_REGISTER.md`
3. `DATASET_MANIFEST.json`
4. `MANIFEST.sha256`
5. `SCHEMA_REGISTRY/`
6. `SPLIT_REGISTRY/`
7. `EXPERIMENT_REGISTRY.csv`
8. `EVALUATION_CARDS/`
9. `RISK_ISSUE_LOG.md`
10. `DECISION_LOG.md`
11. `KNOWN_DATA_ISSUES.md`
12. `QA_DASHBOARD/`
13. `archive/PAPER_SKELETON.md`
14. `REPRODUCTION_README.md`

A practical workspace should include a shared repository, a project board for gates/tasks, and a lightweight visual map of data products, splits, and claim dependencies. The workspace may use any tooling, but it must maintain one source of truth for schemas, split definitions, experiment IDs, and evaluation cards.

---

## 32. First-cycle deliverables

The first project cycle must deliver:

| Deliverable | Acceptance criterion |
|---|---|
| Dataset evidence memo | Versions, DOIs, hashes, file counts, row counts, modalities, anomalies, and known issues documented. |
| Reproducible ingestion | One command creates manifest and file inventory. |
| EOC/EIS/PULSE reproduction plots | Core official-style plots reproduced or deviations explained. |
| QA dashboard | Missingness, validity, data gaps, EIS masks, pulse availability, and temperature anomalies visible. |
| Linked data products | Condition, check-up, run, modality, and interval tables generated. |
| Frozen split registry | LCO, LSAO, profile, replicate, and time-horizon splits saved. |
| Baseline leaderboard | L1–L6 evaluated under grouped splits. |
| Ablation matrix | Nominal-only, actual-exposure, capacity-only, capacity+pulse, capacity+EIS, capacity+pulse+EIS. |
| Uncertainty report | CRPS, interval coverage, condition coverage, replicate tolerance coverage. |
| Falsification report | Shuffled-history, removed-feature, removed-modality, random-vs-grouped split tests. |
| Paper skeleton | Figures, tables, claims, limitations, and result slots defined. |

---

## 33. Paper skeleton

1. **Motivation**  
   Why nominal protocol labels and EFC/time are insufficient for path-dependent battery degradation.

2. **Dataset and audit**  
   Luh–Blank design, modalities, check-up protocol, versioning, EIS gate, anomalies, and data-product construction.

3. **Problem formulation**  
   Interval transition prediction, multimodal degradation state, uncertainty, knee risk, and support-bounded policy ranking.

4. **Exposure construction**  
   Nominal features, actual scalar features, histograms, coupled stress exposures, check-up burden, sequence summaries.

5. **Targets and measurement definitions**  
   Capacity, pulse, \(R_0/R_1\), EIS features, knee labels, policy ranking endpoints.

6. **Validation protocol**  
   Leave-condition-out, stressor-axis holdout, profile holdout, early-to-late, replicate calibration, ablations.

7. **Baseline ladder**  
   Time/EFC, nominal, semi-empirical, hierarchical, GBM, sequence, multimodal latent-state models.

8. **Results**  
   Prediction, ranking, uncertainty, knee warning, worst-condition behavior.

9. **Falsification and sensitivity**  
   Shuffled histories, modality removal, stress-feature removal, thermal anomaly exclusion, EIS QA sensitivity.

10. **Discussion**  
    What actual histories add, when EIS helps, where uncertainty fails, and what policy-ranking claims are defensible.

11. **Limitations**  
    Chemistry scope, laboratory scope, condition count, no same-cell counterfactuals, EIS quality, knee-label ambiguity.

12. **Reproducibility**  
    Data manifest, schema, splits, code, experiment cards.

---

## 34. Decision rule

A technical choice is allowed only if it connects to at least one of:

1. a charter claim;
2. a target definition;
3. a data-product field;
4. a validation split;
5. a model-ladder rung;
6. an uncertainty metric;
7. a falsification test;
8. a paper figure/table.

This prevents uncontrolled ML exploration and keeps the project aligned with publishable evidence.

---

## 35. Final charter statement

The project will build a disciplined, reproducible research system for testing whether **actual operating-history exposure** and **multimodal diagnostic supervision** improve battery degradation modeling under strict held-out-condition validation.

The minimum successful project is a trustworthy benchmark showing what log-derived exposure, pulse diagnostics, and EIS do or do not add beyond strong baselines. The strong project is a calibrated multimodal latent-state model that generalizes across stressor axes. The ambitious project is a support-bounded policy-response ranking framework.

A CBAT-style model is authorized only after the data audit, linked data products, grouped validation protocol, baseline leaderboard, uncertainty audit, modality ablations, and falsification tests demonstrate reproducible gains under strict validation.

---

## Source anchors for dataset and implementation audit

These references should be resolved into full citation format in the final manuscript or repository documentation.

- Luh, M. & Blank, T. **Comprehensive battery aging dataset: capacity and impedance fade measurements of a lithium-ion NMC/C-SiO cell.** *Scientific Data* 11, 1004 (2024). DOI: `10.1038/s41597-024-03831-x`.
- Luh–Blank result data v2. DOI: `10.35097/1969`.
- Luh–Blank log data v2. DOI: `10.35097/kww7jv8ajuvchcah`.
- EIS fixed archive/addendum. DOI: `10.35097/krk531nmj4bsshha`.
- Example preprocessing scripts: `github.com/energystatusdata/bat-age-data-scripts`.
