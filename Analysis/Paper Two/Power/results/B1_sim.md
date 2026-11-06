# Study B1 sample-size simulation

## Criteria (1.10)

| Family | Sample | Lowest own rate, scene-by-cell SD 0 | Lowest own rate, scene-by-cell SD 0.10 | Highest rival rate | (a) >= .80 and >= .70 | (b) every rival <= .05 |
| --- | --- | --- | --- | --- | --- | --- |
| Prompting and delegation (H1) | target 96 (main0, main1) | 0.96 | 0.87 | 0.02 | met | met |
| Prompting and delegation (H1) | fallback 72 (fall0, fall1) | 0.87 | 0.71 | 0.02 | met | met |
| Work after the prompt (H2) | target 96 (main0, main1) | 0.95 | 0.84 | 0.02 | met | met |
| Work after the prompt (H2) | fallback 72 (fall0, fall1) | 0.85 | 0.64 | 0.03 | not met | met |

Own rate: share of datasets in which the generating account is supported. Rival rate: the largest share of datasets in which any single other rival account is supported (rival accounts never share a supported pattern). The lowest own rate and the highest rival rate are taken over the family's generating accounts. Criteria: (a) own rate at least .80 with no scene-by-cell variation and at least .70 with scene-by-cell SD 0.10 of the share SD; (b) every rival at most .05. Compatible accounts (Office practice in H1) are classified and reported but never generate data and never count as rivals.

Run date 2026-10-27. Full run: 1000 datasets at main0 and main1, 500 at each other setting; 8 cores; 63.1 minutes. B1 has no binary family, so there is no Laplace (nAGQ = 1) check.

Each generating account's own support rate in every setting:

| Family | Generating account | main0 | main1 | bound0 | bound1 | sens15 | fall0 | fall1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Neither prompting nor iterating earns credit | 0.96 | 0.87 | 0.96 | 0.83 | 0.61 | 0.87 | 0.71 |
| H1 | Work after the prompt counts; prompting does not | 0.98 | 0.92 | 0.92 | 0.84 | 0.78 | 0.92 | 0.82 |
| H1 | Initiator credit | 0.98 | 0.94 | 0.92 | 0.82 | 0.78 | 0.94 | 0.84 |
| H1 | Scoped credit | 1.00 | 1.00 | 0.89 | 0.83 | 0.98 | 1.00 | 0.98 |
| H2 | Office practice | 0.95 | 0.84 | 0.95 | 0.84 | 0.52 | 0.85 | 0.64 |
| H2 | Time | 0.97 | 0.89 | 0.93 | 0.82 | 0.63 | 0.89 | 0.75 |
| H2 | Selection | 0.96 | 0.87 | 0.92 | 0.82 | 0.60 | 0.89 | 0.71 |
| H2 | Revision | 0.97 | 0.89 | 0.91 | 0.83 | 0.65 | 0.88 | 0.74 |
| H2 | Scoped credit | 0.98 | 0.93 | 0.87 | 0.80 | 0.77 | 0.93 | 0.84 |
| H2 | Work | 1.00 | 1.00 | 0.85 | 0.78 | 0.97 | 0.99 | 0.98 |

Highest support rate of any other rival account, by generating account and setting:

| Family | Generating account | main0 | main1 | bound0 | bound1 | sens15 | fall0 | fall1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Neither prompting nor iterating earns credit | 0.01 | 0.01 | 0.01 | 0.02 | 0.03 | 0.01 | 0.01 |
| H1 | Work after the prompt counts; prompting does not | 0.01 | 0.02 | 0.04 | 0.03 | 0.02 | 0.01 | 0.01 |
| H1 | Initiator credit | 0.01 | 0.01 | 0.05 | 0.04 | 0.03 | 0.02 | 0.01 |
| H1 | Scoped credit | 0.00 | 0.00 | 0.04 | 0.04 | 0.00 | 0.00 | 0.00 |
| H2 | Office practice | 0.01 | 0.01 | 0.01 | 0.02 | 0.01 | 0.02 | 0.02 |
| H2 | Time | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0.00 | 0.00 |
| H2 | Selection | 0.01 | 0.01 | 0.04 | 0.04 | 0.01 | 0.01 | 0.03 |
| H2 | Revision | 0.01 | 0.01 | 0.04 | 0.04 | 0.01 | 0.02 | 0.01 |
| H2 | Scoped credit | 0.01 | 0.02 | 0.05 | 0.04 | 0.01 | 0.01 | 0.02 |
| H2 | Work | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0.00 | 0.00 |

## Settings

| Setting | N | Nonzero contrasts | Scene-by-cell SD | Participant-by-cell SD | Datasets |
| --- | --- | --- | --- | --- | --- |
| main0 | 96 | 12 | 0.0 |  7 | 1000 |
| main1 | 96 | 12 | 2.8 |  7 | 1000 |
| bound0 | 96 |  8 | 0.0 |  7 |  500 |
| bound1 | 96 |  8 | 2.8 |  7 |  500 |
| sens15 | 96 | 12 | 0.0 | 15 |  500 |
| fall0 | 72 | 12 | 0.0 |  7 |  500 |
| fall1 | 72 | 12 | 2.8 |  7 |  500 |

Nonzero contrasts are 1.5 times the bound (12 points) except in bound0 and bound1, where they equal the bound (8). Scene-by-cell SD 2.8 is 0.10 of the share SD. sens15 raises the participant-by-cell SD from 7 to 15 points. Seeds: 41000000 + 100000 x setting index (1 to 7, in the order above) + dataset number; the shift check uses 41000999.

## Design

Target 96 analyzable participants (24 lists of 6), fallback 72 (24 lists of 5); Design Specification 4.5 as kept by 12.5 (N fixed at 10 hours in cells r, b, c and d, which does not enter the simulation). One within-participant factor with six cells (o found, a prompt only, r routine hours, b re-roll, c revise, d tool iterates), two trials each, twelve trials, one scene per trial. 24 lists: 12 rotations x 2 compositions (V1 in lists 0-11, I2 in lists 12-23). In rotation q, trial position j shows scene (j + q) mod 12 (scenes ordered SB-P1, SB-N1, ..., SB-P6, SB-N6) and positions 2i and 2i + 1 hold cell i, so within a list each cell falls on one scene with a person and one without; across the 24 lists every scene appears in every cell four times. Participant p gets list (p - 1) mod 24.

Generating model (1.10 and plan_sim_v2.py, B1 section): share has total SD 28, split into participant intercept SD 22.05 (62 percent), scene intercept SD 6.86 (6 percent) and residual SD 15.84 (32 percent), plus independent participant-by-cell deviations (SD in the settings table) and scene-by-cell deviations (SD in the settings table). Share is generated as normal and not clipped to 0-100, as in the planning simulation. Composition has no generating effect. Each rival account's true contrasts are +effect where its only allowed state is positive and 0 otherwise; contrasts outside the family are 0.

Each dataset is simulated once with every contrast at zero, fitted once, and read under every generating account of both families by adding that account's true values to the estimates. Under REML the variance estimates, standard errors, df and the random terms removed do not depend on the cell means (the shift lies in the span of the fixed effects), so this equals fitting each account's dataset directly, up to the optimizer's tolerance.
Check on one dataset, direct fit of the shifted data against the shifted base fit (largest absolute difference over the five contrasts): estimates 1.5e-13, standard errors 0.00031, df 0.016; same random terms removed: yes.

## Model

Linear mixed model (lmerTest::lmer, REML, lme4's default optimizer and convergence checks) on share, with Helmert codes h1-h5 over cells o, a, r, b, c, d (the columns of `contr.helmert(6)`) and composition (V1 -0.5, I2 +0.5) as fixed effects. Crossed random intercepts for participant and scene; uncorrelated (`||`) by-participant and by-scene slopes for all five Helmert codes (1.8: two trials per cell make the by-participant slopes estimable); composition is a counterbalancing factor and gets no slope. With independent cell deviations of SD s, code hk carries generating variance s^2 / (k (k + 1)), and the Helmert codes are orthogonal, so uncorrelated slopes on them represent independent cell deviations exactly. Each contrast is a linear combination of the fixed effects, with Satterthwaite df (lmerTest::contest). Codes:

| Cell | h1 | h2 | h3 | h4 | h5 |
| --- | --- | --- | --- | --- | --- |
| o | -1 | -1 | -1 | -1 | -1 |
| a |  1 | -1 | -1 | -1 | -1 |
| r |  0 |  2 | -1 | -1 | -1 |
| b |  0 |  0 |  3 | -1 | -1 |
| c |  0 |  0 |  0 |  4 | -1 |
| d |  0 |  0 |  0 |  0 |  5 |

| Contrast | Cells | Weights on (Intercept, h1, h2, h3, h4, h5, comp) |
| --- | --- | --- |
| PR | a - o |     0,     2,     0,     0,     0,     0,     0 |
| H | r - a |     0,    -1,     3,     0,     0,     0,     0 |
| Sel | b - r |     0,     0,    -2,     4,     0,     0,     0 |
| R | c - b |     0,     0,     0,    -3,     5,     0,     0 |
| A | c - d |     0,     0,     0,     0,     4,    -6,     0 |

Model fitted first (the same for both families; one fit per dataset serves H1 and H2):

`share ~ h1 + h2 + h3 + h4 + h5 + comp + (1 + h5 + h4 + h3 + h2 + h1 || pid) + (1 + h5 + h4 + h3 + h2 + h1 || scene)`

Removal rule and convergence (1.8 as revised; `fit_registered()` in sim_common.R, called with slopes scene:h5, scene:h4, scene:h3, scene:h2, scene:h1, pid:h5, pid:h4, pid:h3, pid:h2, pid:h1, no interaction slopes, groups pid and scene, scene intercept removed last). A fit fails when it stops with an error, fails to converge (the optimizer returns a nonzero code, or lme4 or lmerTest warns that the model "failed to converge") or is singular. After a failed fit one random term is removed and the model refitted: the slope with the smallest estimated variance in the failed fit (there are no interaction slopes); when no slope is left, the scene intercept. The model left after the last removal is accepted as it is. Ties (several variances at zero) and a fit that stops with an error remove slopes in the order listed, smallest generating variance first: by-scene before by-participant, h5 to h1. A dataset has no usable fit when no model could be fitted or a contrast could not be computed; its contrasts are undetermined.

## Fit diagnostics

Datasets fitted, datasets dropped by an error outside the fit, datasets without a usable fit, share of all removals that followed a convergence failure that was not also a singular fit, share of datasets with at least one such removal, and share of datasets with 0, 1, ..., 11 random terms removed:

| Setting | N | Datasets | Dropped | No usable fit | Removals after a convergence failure (share of removals) | Datasets with such a removal | removed 0 | removed 1 | removed 2 | removed 3 | removed 4 | removed 5 | removed 6 | removed 7 | removed 8 | removed 9 | removed 10 | removed 11 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main0 | 96 | 1000 | 0 | 0 | 0.05 | 0.14 | 0.02 | 0.12 | 0.26 | 0.22 | 0.25 | 0.11 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| main1 | 96 | 1000 | 0 | 0 | 0.04 | 0.05 | 0.21 | 0.36 | 0.28 | 0.09 | 0.04 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| bound0 | 96 |  500 | 0 | 0 | 0.06 | 0.16 | 0.02 | 0.11 | 0.23 | 0.25 | 0.26 | 0.10 | 0.03 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| bound1 | 96 |  500 | 0 | 0 | 0.05 | 0.05 | 0.21 | 0.39 | 0.25 | 0.08 | 0.04 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sens15 | 96 |  500 | 0 | 0 | 0.05 | 0.14 | 0.03 | 0.14 | 0.29 | 0.22 | 0.21 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| fall0 | 72 |  500 | 0 | 0 | 0.04 | 0.12 | 0.01 | 0.13 | 0.21 | 0.27 | 0.24 | 0.11 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| fall1 | 72 |  500 | 0 | 0 | 0.04 | 0.07 | 0.10 | 0.29 | 0.33 | 0.17 | 0.07 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Share of datasets in which each random term is kept in the accepted model (participant intercepts are always kept):

| Setting | pid h1 | pid h2 | pid h3 | pid h4 | pid h5 | scene h1 | scene h2 | scene h3 | scene h4 | scene h5 | scene_intercept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main0 | 0.98 | 0.97 | 0.97 | 0.97 | 0.96 | 0.47 | 0.43 | 0.42 | 0.43 | 0.43 | 1.00 |
| main1 | 0.97 | 0.97 | 0.97 | 0.97 | 0.98 | 0.76 | 0.71 | 0.73 | 0.75 | 0.74 | 1.00 |
| bound0 | 0.98 | 0.97 | 0.98 | 0.96 | 0.96 | 0.48 | 0.44 | 0.36 | 0.41 | 0.42 | 1.00 |
| bound1 | 0.98 | 0.97 | 0.98 | 0.98 | 0.96 | 0.78 | 0.73 | 0.72 | 0.74 | 0.74 | 1.00 |
| sens15 | 1.00 | 1.00 | 1.00 | 1.00 | 0.99 | 0.48 | 0.45 | 0.43 | 0.43 | 0.45 | 1.00 |
| fall0 | 0.96 | 0.95 | 0.97 | 0.95 | 0.95 | 0.46 | 0.43 | 0.44 | 0.44 | 0.41 | 1.00 |
| fall1 | 0.96 | 0.95 | 0.94 | 0.96 | 0.96 | 0.72 | 0.68 | 0.67 | 0.62 | 0.63 | 1.00 |

## Full table

### Prompting and delegation (H1)

Support rate of every account; for each contrast the true value, mean estimate, mean model standard error and the standard deviation of the estimates across datasets, and the share of datasets in each state (zero / positive / negative / undetermined).

| Setting | N | Generating | Datasets | Neither prompting nor iterating earns credit | Work after the prompt counts; prompting does not | Initiator credit | Scoped credit | Office practice (compatible) | PR: true, mean est (mean SE; SD of est) | PR: 0 / + / - / u | A: true, mean est (mean SE; SD of est) | A: 0 / + / - / u |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main0 | 96 | Neither prompting nor iterating earns credit | 1000 | 0.96 | 0.01 | 0.01 | 0.00 | 0.97 | 0, 0.01 (2.02; 1.86) | 0.98 / 0.01 / 0.00 / 0.01 | 0, 0.01 (2.02; 1.93) | 0.98 / 0.01 / 0.01 / 0.01 |
| main0 | 96 | Work after the prompt counts; prompting does not | 1000 | 0.00 | 0.98 | 0.00 | 0.01 | 0.98 | 0, 0.01 (2.02; 1.86) | 0.98 / 0.01 / 0.00 / 0.01 | 12, 12.01 (2.02; 1.93) | 0.00 / 1.00 / 0.00 / 0.00 |
| main0 | 96 | Initiator credit | 1000 | 0.00 | 0.00 | 0.98 | 0.01 | 0.00 | 12, 12.01 (2.02; 1.86) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.01 (2.02; 1.93) | 0.98 / 0.01 / 0.01 / 0.01 |
| main0 | 96 | Scoped credit | 1000 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 12, 12.01 (2.02; 1.86) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.01 (2.02; 1.93) | 0.00 / 1.00 / 0.00 / 0.00 |
| main1 | 96 | Neither prompting nor iterating earns credit | 1000 | 0.87 | 0.01 | 0.01 | 0.00 | 0.88 | 0, 0.04 (2.22; 2.24) | 0.92 / 0.02 / 0.02 / 0.05 | 0, -0.05 (2.26; 2.15) | 0.94 / 0.01 / 0.01 / 0.03 |
| main1 | 96 | Work after the prompt counts; prompting does not | 1000 | 0.00 | 0.92 | 0.00 | 0.02 | 0.92 | 0, 0.04 (2.22; 2.24) | 0.92 / 0.02 / 0.02 / 0.05 | 12, 11.95 (2.26; 2.15) | 0.00 / 1.00 / 0.00 / 0.00 |
| main1 | 96 | Initiator credit | 1000 | 0.00 | 0.00 | 0.94 | 0.01 | 0.00 | 12, 12.04 (2.22; 2.24) | 0.00 / 1.00 / 0.00 / 0.00 | 0, -0.05 (2.26; 2.15) | 0.94 / 0.01 / 0.01 / 0.03 |
| main1 | 96 | Scoped credit | 1000 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 12, 12.04 (2.22; 2.24) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.95 (2.26; 2.15) | 0.00 / 1.00 / 0.00 / 0.00 |
| bound0 | 96 | Neither prompting nor iterating earns credit |  500 | 0.96 | 0.01 | 0.01 | 0.00 | 0.97 | 0, -0.06 (2.02; 1.87) | 0.98 / 0.01 / 0.01 / 0.01 | 0, -0.06 (2.04; 1.94) | 0.98 / 0.01 / 0.01 / 0.01 |
| bound0 | 96 | Work after the prompt counts; prompting does not |  500 | 0.04 | 0.92 | 0.00 | 0.01 | 0.96 | 0, -0.06 (2.02; 1.87) | 0.98 / 0.01 / 0.01 / 0.01 | 8, 7.94 (2.04; 1.94) | 0.04 / 0.94 / 0.00 / 0.02 |
| bound0 | 96 | Initiator credit |  500 | 0.05 | 0.00 | 0.92 | 0.01 | 0.05 | 8, 7.94 (2.02; 1.87) | 0.05 / 0.94 / 0.00 / 0.01 | 0, -0.06 (2.04; 1.94) | 0.98 / 0.01 / 0.01 / 0.01 |
| bound0 | 96 | Scoped credit |  500 | 0.00 | 0.04 | 0.04 | 0.89 | 0.05 | 8, 7.94 (2.02; 1.87) | 0.05 / 0.94 / 0.00 / 0.01 | 8, 7.94 (2.04; 1.94) | 0.04 / 0.94 / 0.00 / 0.02 |
| bound1 | 96 | Neither prompting nor iterating earns credit |  500 | 0.83 | 0.02 | 0.01 | 0.00 | 0.86 | 0, -0.00 (2.22; 2.30) | 0.91 / 0.01 / 0.02 / 0.06 | 0, 0.08 (2.27; 2.41) | 0.91 / 0.03 / 0.01 / 0.05 |
| bound1 | 96 | Work after the prompt counts; prompting does not |  500 | 0.03 | 0.84 | 0.00 | 0.01 | 0.87 | 0, -0.00 (2.22; 2.30) | 0.91 / 0.01 / 0.02 / 0.06 | 8, 8.08 (2.27; 2.41) | 0.04 / 0.92 / 0.00 / 0.04 |
| bound1 | 96 | Initiator credit |  500 | 0.04 | 0.00 | 0.82 | 0.02 | 0.04 | 8, 8.00 (2.22; 2.30) | 0.04 / 0.91 / 0.00 / 0.05 | 0, 0.08 (2.27; 2.41) | 0.91 / 0.03 / 0.01 / 0.05 |
| bound1 | 96 | Scoped credit |  500 | 0.00 | 0.04 | 0.04 | 0.83 | 0.04 | 8, 8.00 (2.22; 2.30) | 0.04 / 0.91 / 0.00 / 0.05 | 8, 8.08 (2.27; 2.41) | 0.04 / 0.92 / 0.00 / 0.04 |
| sens15 | 96 | Neither prompting nor iterating earns credit |  500 | 0.61 | 0.03 | 0.02 | 0.00 | 0.64 | 0, -0.10 (2.77; 2.68) | 0.79 / 0.02 / 0.02 / 0.17 | 0, 0.23 (2.80; 2.66) | 0.79 / 0.03 / 0.01 / 0.17 |
| sens15 | 96 | Work after the prompt counts; prompting does not |  500 | 0.00 | 0.78 | 0.00 | 0.02 | 0.78 | 0, -0.10 (2.77; 2.68) | 0.79 / 0.02 / 0.02 / 0.17 | 12, 12.23 (2.80; 2.66) | 0.00 / 0.99 / 0.00 / 0.00 |
| sens15 | 96 | Initiator credit |  500 | 0.00 | 0.00 | 0.78 | 0.03 | 0.00 | 12, 11.90 (2.77; 2.68) | 0.00 / 0.99 / 0.00 / 0.01 | 0, 0.23 (2.80; 2.66) | 0.79 / 0.03 / 0.01 / 0.17 |
| sens15 | 96 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 0.98 | 0.00 | 12, 11.90 (2.77; 2.68) | 0.00 / 0.99 / 0.00 / 0.01 | 12, 12.23 (2.80; 2.66) | 0.00 / 0.99 / 0.00 / 0.00 |
| fall0 | 72 | Neither prompting nor iterating earns credit |  500 | 0.87 | 0.01 | 0.01 | 0.00 | 0.88 | 0, 0.15 (2.31; 2.13) | 0.92 / 0.01 / 0.01 / 0.06 | 0, 0.01 (2.34; 2.09) | 0.94 / 0.02 / 0.01 / 0.04 |
| fall0 | 72 | Work after the prompt counts; prompting does not |  500 | 0.00 | 0.92 | 0.00 | 0.01 | 0.92 | 0, 0.15 (2.31; 2.13) | 0.92 / 0.01 / 0.01 / 0.06 | 12, 12.01 (2.34; 2.09) | 0.00 / 1.00 / 0.00 / 0.00 |
| fall0 | 72 | Initiator credit |  500 | 0.00 | 0.00 | 0.94 | 0.02 | 0.00 | 12, 12.15 (2.31; 2.13) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.01 (2.34; 2.09) | 0.94 / 0.02 / 0.01 / 0.04 |
| fall0 | 72 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 12, 12.15 (2.31; 2.13) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.01 (2.34; 2.09) | 0.00 / 1.00 / 0.00 / 0.00 |
| fall1 | 72 | Neither prompting nor iterating earns credit |  500 | 0.71 | 0.01 | 0.01 | 0.00 | 0.71 | 0, -0.09 (2.51; 2.57) | 0.82 / 0.01 / 0.03 / 0.15 | 0, -0.13 (2.52; 2.49) | 0.86 / 0.01 / 0.04 / 0.09 |
| fall1 | 72 | Work after the prompt counts; prompting does not |  500 | 0.00 | 0.82 | 0.00 | 0.01 | 0.82 | 0, -0.09 (2.51; 2.57) | 0.82 / 0.01 / 0.03 / 0.15 | 12, 11.87 (2.52; 2.49) | 0.00 / 0.99 / 0.00 / 0.01 |
| fall1 | 72 | Initiator credit |  500 | 0.00 | 0.00 | 0.84 | 0.01 | 0.00 | 12, 11.91 (2.51; 2.57) | 0.00 / 0.99 / 0.00 / 0.01 | 0, -0.13 (2.52; 2.49) | 0.86 / 0.01 / 0.04 / 0.09 |
| fall1 | 72 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 0.98 | 0.00 | 12, 11.91 (2.51; 2.57) | 0.00 / 0.99 / 0.00 / 0.01 | 12, 11.87 (2.52; 2.49) | 0.00 / 0.99 / 0.00 / 0.01 |

### Work after the prompt (H2)

Support rate of every account; for each contrast the true value, mean estimate, mean model standard error and the standard deviation of the estimates across datasets, and the share of datasets in each state (zero / positive / negative / undetermined).

| Setting | N | Generating | Datasets | Office practice | Time | Selection | Revision | Scoped credit | Work | H: true, mean est (mean SE; SD of est) | H: 0 / + / - / u | Sel: true, mean est (mean SE; SD of est) | Sel: 0 / + / - / u | R: true, mean est (mean SE; SD of est) | R: 0 / + / - / u |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main0 | 96 | Office practice | 1000 | 0.95 | 0.01 | 0.00 | 0.01 | 0.00 | 0.00 | 0, -0.00 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 0, 0.10 (2.03; 1.93) | 0.99 / 0.01 / 0.00 / 0.01 | 0, -0.07 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.00 |
| main0 | 96 | Time | 1000 | 0.00 | 0.97 | 0.00 | 0.00 | 0.00 | 0.00 | 12, 12.00 (2.03; 1.90) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.10 (2.03; 1.93) | 0.99 / 0.01 / 0.00 / 0.01 | 0, -0.07 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.00 |
| main0 | 96 | Selection | 1000 | 0.00 | 0.00 | 0.96 | 0.00 | 0.01 | 0.00 | 0, -0.00 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 12, 12.10 (2.03; 1.93) | 0.00 / 1.00 / 0.00 / 0.00 | 0, -0.07 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.00 |
| main0 | 96 | Revision | 1000 | 0.00 | 0.00 | 0.00 | 0.97 | 0.01 | 0.00 | 0, -0.00 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 0, 0.10 (2.03; 1.93) | 0.99 / 0.01 / 0.00 / 0.01 | 12, 11.93 (2.03; 1.90) | 0.00 / 1.00 / 0.00 / 0.00 |
| main0 | 96 | Scoped credit | 1000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.98 | 0.01 | 0, -0.00 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 12, 12.10 (2.03; 1.93) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.93 (2.03; 1.90) | 0.00 / 1.00 / 0.00 / 0.00 |
| main0 | 96 | Work | 1000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 12, 12.00 (2.03; 1.90) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.10 (2.03; 1.93) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.93 (2.03; 1.90) | 0.00 / 1.00 / 0.00 / 0.00 |
| main1 | 96 | Office practice | 1000 | 0.84 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 | 0, 0.04 (2.24; 2.24) | 0.93 / 0.02 / 0.01 / 0.04 | 0, 0.03 (2.25; 2.20) | 0.94 / 0.01 / 0.01 / 0.03 | 0, -0.07 (2.27; 2.23) | 0.93 / 0.01 / 0.01 / 0.04 |
| main1 | 96 | Time | 1000 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 | 0.00 | 12, 12.04 (2.24; 2.24) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.03 (2.25; 2.20) | 0.94 / 0.01 / 0.01 / 0.03 | 0, -0.07 (2.27; 2.23) | 0.93 / 0.01 / 0.01 / 0.04 |
| main1 | 96 | Selection | 1000 | 0.00 | 0.00 | 0.87 | 0.00 | 0.01 | 0.00 | 0, 0.04 (2.24; 2.24) | 0.93 / 0.02 / 0.01 / 0.04 | 12, 12.03 (2.25; 2.20) | 0.00 / 1.00 / 0.00 / 0.00 | 0, -0.07 (2.27; 2.23) | 0.93 / 0.01 / 0.01 / 0.04 |
| main1 | 96 | Revision | 1000 | 0.00 | 0.00 | 0.00 | 0.89 | 0.01 | 0.00 | 0, 0.04 (2.24; 2.24) | 0.93 / 0.02 / 0.01 / 0.04 | 0, 0.03 (2.25; 2.20) | 0.94 / 0.01 / 0.01 / 0.03 | 12, 11.93 (2.27; 2.23) | 0.00 / 1.00 / 0.00 / 0.00 |
| main1 | 96 | Scoped credit | 1000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.93 | 0.02 | 0, 0.04 (2.24; 2.24) | 0.93 / 0.02 / 0.01 / 0.04 | 12, 12.03 (2.25; 2.20) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.93 (2.27; 2.23) | 0.00 / 1.00 / 0.00 / 0.00 |
| main1 | 96 | Work | 1000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 12, 12.04 (2.24; 2.24) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.03 (2.25; 2.20) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.93 (2.27; 2.23) | 0.00 / 1.00 / 0.00 / 0.00 |
| bound0 | 96 | Office practice |  500 | 0.95 | 0.01 | 0.00 | 0.01 | 0.00 | 0.00 | 0, -0.06 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 0, 0.07 (2.01; 1.88) | 0.98 / 0.01 / 0.00 / 0.01 | 0, -0.05 (2.02; 1.92) | 0.98 / 0.01 / 0.01 / 0.00 |
| bound0 | 96 | Time |  500 | 0.04 | 0.93 | 0.00 | 0.00 | 0.00 | 0.00 | 8, 7.94 (2.03; 1.90) | 0.04 / 0.95 / 0.00 / 0.01 | 0, 0.07 (2.01; 1.88) | 0.98 / 0.01 / 0.00 / 0.01 | 0, -0.05 (2.02; 1.92) | 0.98 / 0.01 / 0.01 / 0.00 |
| bound0 | 96 | Selection |  500 | 0.04 | 0.00 | 0.92 | 0.01 | 0.00 | 0.00 | 0, -0.06 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 8, 8.07 (2.01; 1.88) | 0.04 / 0.95 / 0.00 / 0.01 | 0, -0.05 (2.02; 1.92) | 0.98 / 0.01 / 0.01 / 0.00 |
| bound0 | 96 | Revision |  500 | 0.04 | 0.00 | 0.00 | 0.91 | 0.00 | 0.00 | 0, -0.06 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 0, 0.07 (2.01; 1.88) | 0.98 / 0.01 / 0.00 / 0.01 | 8, 7.95 (2.02; 1.92) | 0.05 / 0.94 / 0.00 / 0.01 |
| bound0 | 96 | Scoped credit |  500 | 0.00 | 0.00 | 0.05 | 0.04 | 0.87 | 0.01 | 0, -0.06 (2.03; 1.90) | 0.98 / 0.01 / 0.01 / 0.01 | 8, 8.07 (2.01; 1.88) | 0.04 / 0.95 / 0.00 / 0.01 | 8, 7.95 (2.02; 1.92) | 0.05 / 0.94 / 0.00 / 0.01 |
| bound0 | 96 | Work |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 | 0.85 | 8, 7.94 (2.03; 1.90) | 0.04 / 0.95 / 0.00 / 0.01 | 8, 8.07 (2.01; 1.88) | 0.04 / 0.95 / 0.00 / 0.01 | 8, 7.95 (2.02; 1.92) | 0.05 / 0.94 / 0.00 / 0.01 |
| bound1 | 96 | Office practice |  500 | 0.84 | 0.01 | 0.01 | 0.02 | 0.00 | 0.00 | 0, 0.06 (2.24; 2.13) | 0.95 / 0.01 / 0.01 / 0.03 | 0, -0.13 (2.25; 2.15) | 0.93 / 0.01 / 0.01 / 0.05 | 0, 0.08 (2.26; 2.21) | 0.93 / 0.02 / 0.02 / 0.03 |
| bound1 | 96 | Time |  500 | 0.03 | 0.82 | 0.00 | 0.00 | 0.00 | 0.00 | 8, 8.06 (2.24; 2.13) | 0.04 / 0.93 / 0.00 / 0.02 | 0, -0.13 (2.25; 2.15) | 0.93 / 0.01 / 0.01 / 0.05 | 0, 0.08 (2.26; 2.21) | 0.93 / 0.02 / 0.02 / 0.03 |
| bound1 | 96 | Selection |  500 | 0.04 | 0.00 | 0.82 | 0.00 | 0.02 | 0.00 | 0, 0.06 (2.24; 2.13) | 0.95 / 0.01 / 0.01 / 0.03 | 8, 7.87 (2.25; 2.15) | 0.04 / 0.91 / 0.00 / 0.04 | 0, 0.08 (2.26; 2.21) | 0.93 / 0.02 / 0.02 / 0.03 |
| bound1 | 96 | Revision |  500 | 0.04 | 0.00 | 0.00 | 0.83 | 0.00 | 0.00 | 0, 0.06 (2.24; 2.13) | 0.95 / 0.01 / 0.01 / 0.03 | 0, -0.13 (2.25; 2.15) | 0.93 / 0.01 / 0.01 / 0.05 | 8, 8.08 (2.26; 2.21) | 0.04 / 0.92 / 0.00 / 0.04 |
| bound1 | 96 | Scoped credit |  500 | 0.00 | 0.00 | 0.04 | 0.04 | 0.80 | 0.00 | 0, 0.06 (2.24; 2.13) | 0.95 / 0.01 / 0.01 / 0.03 | 8, 7.87 (2.25; 2.15) | 0.04 / 0.91 / 0.00 / 0.04 | 8, 8.08 (2.26; 2.21) | 0.04 / 0.92 / 0.00 / 0.04 |
| bound1 | 96 | Work |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.78 | 8, 8.06 (2.24; 2.13) | 0.04 / 0.93 / 0.00 / 0.02 | 8, 7.87 (2.25; 2.15) | 0.04 / 0.91 / 0.00 / 0.04 | 8, 8.08 (2.26; 2.21) | 0.04 / 0.92 / 0.00 / 0.04 |
| sens15 | 96 | Office practice |  500 | 0.52 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0, 0.16 (2.81; 2.54) | 0.79 / 0.01 / 0.02 / 0.18 | 0, 0.04 (2.81; 2.60) | 0.81 / 0.02 / 0.02 / 0.15 | 0, -0.03 (2.80; 2.82) | 0.76 / 0.01 / 0.02 / 0.21 |
| sens15 | 96 | Time |  500 | 0.00 | 0.63 | 0.00 | 0.00 | 0.00 | 0.00 | 12, 12.16 (2.81; 2.54) | 0.00 / 0.99 / 0.00 / 0.00 | 0, 0.04 (2.81; 2.60) | 0.81 / 0.02 / 0.02 / 0.15 | 0, -0.03 (2.80; 2.82) | 0.76 / 0.01 / 0.02 / 0.21 |
| sens15 | 96 | Selection |  500 | 0.00 | 0.00 | 0.60 | 0.00 | 0.01 | 0.00 | 0, 0.16 (2.81; 2.54) | 0.79 / 0.01 / 0.02 / 0.18 | 12, 12.04 (2.81; 2.60) | 0.00 / 0.99 / 0.00 / 0.01 | 0, -0.03 (2.80; 2.82) | 0.76 / 0.01 / 0.02 / 0.21 |
| sens15 | 96 | Revision |  500 | 0.00 | 0.00 | 0.00 | 0.65 | 0.01 | 0.00 | 0, 0.16 (2.81; 2.54) | 0.79 / 0.01 / 0.02 / 0.18 | 0, 0.04 (2.81; 2.60) | 0.81 / 0.02 / 0.02 / 0.15 | 12, 11.97 (2.80; 2.82) | 0.00 / 0.98 / 0.00 / 0.01 |
| sens15 | 96 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.77 | 0.01 | 0, 0.16 (2.81; 2.54) | 0.79 / 0.01 / 0.02 / 0.18 | 12, 12.04 (2.81; 2.60) | 0.00 / 0.99 / 0.00 / 0.01 | 12, 11.97 (2.80; 2.82) | 0.00 / 0.98 / 0.00 / 0.01 |
| sens15 | 96 | Work |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.97 | 12, 12.16 (2.81; 2.54) | 0.00 / 0.99 / 0.00 / 0.00 | 12, 12.04 (2.81; 2.60) | 0.00 / 0.99 / 0.00 / 0.01 | 12, 11.97 (2.80; 2.82) | 0.00 / 0.98 / 0.00 / 0.01 |
| fall0 | 72 | Office practice |  500 | 0.85 | 0.01 | 0.02 | 0.01 | 0.00 | 0.00 | 0, -0.13 (2.33; 2.16) | 0.94 / 0.01 / 0.01 / 0.04 | 0, 0.00 (2.34; 2.27) | 0.93 / 0.02 / 0.01 / 0.03 | 0, 0.02 (2.34; 2.10) | 0.95 / 0.01 / 0.01 / 0.03 |
| fall0 | 72 | Time |  500 | 0.00 | 0.89 | 0.00 | 0.00 | 0.00 | 0.00 | 12, 11.87 (2.33; 2.16) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.00 (2.34; 2.27) | 0.93 / 0.02 / 0.01 / 0.03 | 0, 0.02 (2.34; 2.10) | 0.95 / 0.01 / 0.01 / 0.03 |
| fall0 | 72 | Selection |  500 | 0.00 | 0.00 | 0.89 | 0.00 | 0.01 | 0.00 | 0, -0.13 (2.33; 2.16) | 0.94 / 0.01 / 0.01 / 0.04 | 12, 12.00 (2.34; 2.27) | 0.00 / 1.00 / 0.00 / 0.00 | 0, 0.02 (2.34; 2.10) | 0.95 / 0.01 / 0.01 / 0.03 |
| fall0 | 72 | Revision |  500 | 0.00 | 0.00 | 0.00 | 0.88 | 0.02 | 0.00 | 0, -0.13 (2.33; 2.16) | 0.94 / 0.01 / 0.01 / 0.04 | 0, 0.00 (2.34; 2.27) | 0.93 / 0.02 / 0.01 / 0.03 | 12, 12.02 (2.34; 2.10) | 0.00 / 1.00 / 0.00 / 0.00 |
| fall0 | 72 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.93 | 0.01 | 0, -0.13 (2.33; 2.16) | 0.94 / 0.01 / 0.01 / 0.04 | 12, 12.00 (2.34; 2.27) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.02 (2.34; 2.10) | 0.00 / 1.00 / 0.00 / 0.00 |
| fall0 | 72 | Work |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.99 | 12, 11.87 (2.33; 2.16) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.00 (2.34; 2.27) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 12.02 (2.34; 2.10) | 0.00 / 1.00 / 0.00 / 0.00 |
| fall1 | 72 | Office practice |  500 | 0.64 | 0.01 | 0.01 | 0.02 | 0.00 | 0.00 | 0, 0.09 (2.53; 2.62) | 0.84 / 0.02 / 0.02 / 0.11 | 0, 0.02 (2.53; 2.43) | 0.86 / 0.02 / 0.02 / 0.10 | 0, -0.05 (2.52; 2.44) | 0.86 / 0.03 / 0.02 / 0.09 |
| fall1 | 72 | Time |  500 | 0.00 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 | 12, 12.09 (2.53; 2.62) | 0.00 / 0.99 / 0.00 / 0.01 | 0, 0.02 (2.53; 2.43) | 0.86 / 0.02 / 0.02 / 0.10 | 0, -0.05 (2.52; 2.44) | 0.86 / 0.03 / 0.02 / 0.09 |
| fall1 | 72 | Selection |  500 | 0.00 | 0.00 | 0.71 | 0.00 | 0.03 | 0.00 | 0, 0.09 (2.53; 2.62) | 0.84 / 0.02 / 0.02 / 0.11 | 12, 12.02 (2.53; 2.43) | 0.00 / 1.00 / 0.00 / 0.00 | 0, -0.05 (2.52; 2.44) | 0.86 / 0.03 / 0.02 / 0.09 |
| fall1 | 72 | Revision |  500 | 0.00 | 0.00 | 0.00 | 0.74 | 0.01 | 0.00 | 0, 0.09 (2.53; 2.62) | 0.84 / 0.02 / 0.02 / 0.11 | 0, 0.02 (2.53; 2.43) | 0.86 / 0.02 / 0.02 / 0.10 | 12, 11.95 (2.52; 2.44) | 0.00 / 0.99 / 0.00 / 0.01 |
| fall1 | 72 | Scoped credit |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.84 | 0.02 | 0, 0.09 (2.53; 2.62) | 0.84 / 0.02 / 0.02 / 0.11 | 12, 12.02 (2.53; 2.43) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.95 (2.52; 2.44) | 0.00 / 0.99 / 0.00 / 0.01 |
| fall1 | 72 | Work |  500 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.98 | 12, 12.09 (2.53; 2.62) | 0.00 / 0.99 / 0.00 / 0.01 | 12, 12.02 (2.53; 2.43) | 0.00 / 1.00 / 0.00 / 0.00 | 12, 11.95 (2.52; 2.44) | 0.00 / 0.99 / 0.00 / 0.01 |

## Timing

| Setting | Datasets | Seconds per dataset | Minutes |
| --- | --- | --- | --- |
| main0 | 1000 | 9.0 | 18.9 |
| main1 | 1000 | 8.4 | 17.5 |
| bound0 |  500 | 8.1 | 8.6 |
| bound1 |  500 | 4.3 | 4.5 |
| sens15 |  500 | 5.5 | 5.9 |
| fall0 |  500 | 3.9 | 4.0 |
| fall1 |  500 | 3.4 | 3.6 |

Mean seconds per dataset over this run (8 cores in parallel; one fit serves both families): 6.66. Estimated full run at the default numbers of datasets (1,000 at main0 and main1, 500 at each of the five other settings: 4500 datasets; no Laplace check) on 11 cores: 45 minutes. Elapsed time of this run: 63.1 minutes.

## Software and checksums

- R version 4.5.2 (2025-10-31); aarch64-apple-darwin20; macOS Tahoe 26.6.2
- Attached packages: lme4 2.0-1, lmerTest 3.2-1, Matrix 1.7-5
- Loaded packages: boot 1.3-32, cli 3.6.6, compiler 4.5.2, dplyr 1.2.1, farver 2.1.2, generics 0.1.4, ggplot2 4.0.3, glue 1.8.1, grid 4.5.2, gtable 0.3.6, lattice 0.22-9, lifecycle 1.0.5, magrittr 2.0.5, MASS 7.3-65, minqa 1.2.8, nlme 3.1-169, nloptr 2.2.1, numDeriv 2016.8-1.1, pillar 1.11.1, pkgconfig 2.0.3, R6 2.6.1, rbibutils 2.4.1, RColorBrewer 1.1-3, Rcpp 1.1.1-1.1, Rdpack 2.6.6, reformulas 0.4.4, rlang 1.2.0, S7 0.2.2, scales 1.4.0, splines 4.5.2, tibble 3.3.1, tidyselect 1.2.1, tools 4.5.2, vctrs 0.7.3
- Run date: 2026-10-27
- sim_B1.R SHA-256: f62f8a90036433fde474d5c68536222fda445354d1e8f0d085d8a10ea7402d3d
- sim_common.R SHA-256: 1fa301a67ad0c2a00dbfb3d3560297414294770e8768df52f3051d9484e896a2

