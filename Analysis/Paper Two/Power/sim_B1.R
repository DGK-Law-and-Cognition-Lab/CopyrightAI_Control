# Sample-size simulation for Study B1 (Design Specification 4.5, as kept by 12.5).
#
# B1's design is unchanged by the within-subjects redesign of 27 October 2026 (Part 12): one
# within-participant factor with six cells (o, a, r, b, c, d), two trials each, twelve trials, one
# scene per trial, and composition (V1 or I2) as a counterbalancing factor across lists. 24 lists
# (12 rotations x 2 compositions). Target 144 analyzable participants (6 per list); fallback 120
# (5 per list). Every dataset is fitted with the registered linear mixed model (share on the cell
# codes and composition; crossed random intercepts for participant and scene; uncorrelated
# by-participant and by-scene slopes for the five cell codes) through fit_registered() in
# sim_common.R, and each contrast of the two families is given a state under the state rule (bound
# 8 points):
#   H1 prompting and delegation: PR = a - o, A = c - d
#   H2 work after the prompt:    H = r - a, Sel = b - r, R = c - b
# Generating values mirror planning/plan_sim_v2.py (B1 section). Share is generated as normal and
# not clipped to 0-100, as in the planning simulation. B1 has no binary family, so there is no
# Laplace check; --reps_laplace is accepted and not used.
#
# Usage (from this folder):
#   VECLIB_MAXIMUM_THREADS=1 Rscript sim_B1.R [--reps 1000] [--reps_small 500] [--cores N]
#                                             [--quick] [--date YYYY-MM-DD]
# Writes results/B1_sim.csv and results/B1_sim.md.

# sim_common.R also defines script_dir(); this copy is needed to find sim_common.R first.
script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", args[grep("^--file=", args)])
  if (length(f)) dirname(normalizePath(f)) else getwd()
}
source(file.path(script_dir(), "sim_common.R"))

opt <- parse_args()
run_date <- if (!is.null(opt$date)) as.character(opt$date) else as.character(Sys.Date())
out_dir <- file.path(script_dir(), "results")
dir.create(out_dir, showWarnings = FALSE)
t_start <- Sys.time()
SEED_BASE <- 41000000

# ---------------------------------------------------------------- generating values

SD_TOTAL <- 28
SD_P <- sqrt(.62) * SD_TOTAL   # participant intercept
SD_S <- sqrt(.06) * SD_TOTAL   # scene intercept
SD_E <- sqrt(.32) * SD_TOTAL   # residual
GRAND <- 50                    # grand mean; any value gives the same contrasts
BOUND <- 8

N_TARGET <- 96                 # 24 lists of 4: the smallest candidate meeting the criteria (results/B1_search.md)
N_FALLBACK <- 72               # 24 lists of 3: the candidate below the target (12.12)
# Smallest-sample search (12.12): --n_target and --n_fallback override these, --only limits the
# run to the named settings (for example main0,main1), and --tag adds a suffix to the output files.
if (!is.null(opt$n_target)) N_TARGET <- as.integer(opt$n_target)
if (!is.null(opt$n_fallback)) N_FALLBACK <- as.integer(opt$n_fallback)
TAG <- if (!is.null(opt$tag)) paste0("_", opt$tag) else ""
N_LISTS <- 24
N_SCENES <- 12
CELLS <- c("o", "a", "r", "b", "c", "d")

# Registered contrasts as rows over the six cells.
CONTRASTS <- rbind(
  PR  = c(-1, 1, 0, 0, 0, 0),   # a - o
  H   = c(0, -1, 1, 0, 0, 0),   # r - a
  Sel = c(0, 0, -1, 1, 0, 0),   # b - r
  R   = c(0, 0, 0, -1, 1, 0),   # c - b
  A   = c(0, 0, 0, 0, 1, -1)    # c - d
)
colnames(CONTRASTS) <- CELLS

# Cell means that give a vector of true contrast values (the five contrasts are linearly
# independent, so this is exact): mu = GRAND + CELL_SHIFT %*% true.
CELL_SHIFT <- t(CONTRASTS) %*% solve(CONTRASTS %*% t(CONTRASTS))

# Fixed and random cell codes: Helmert codes over o, a, r, b, c, d. Orthogonal codes let the
# uncorrelated (||) slopes represent the generating model's independent participant-by-cell and
# scene-by-cell deviations exactly; each registered contrast is a linear combination of them.
# With independent cell deviations of SD s, code hk carries variance s^2 / (k (k + 1)), so h5 has
# the smallest generating variance and h1 the largest.
CODES <- contr.helmert(6)
colnames(CODES) <- paste0("h", 1:5)
rownames(CODES) <- CELLS

# Lists: list k (0-23) uses rotation k mod 12 and composition V1 (k < 12) or I2. In rotation q,
# trial position j shows scene (j + q) mod 12 (scenes ordered SB-P1, SB-N1, ..., SB-P6, SB-N6) and
# positions 2i and 2i + 1 hold cell i, so within a list each cell falls on one scene with a person
# and one without. Participant p (1-n) gets list (p - 1) mod 24: six per list at 144, five at 120.
# Across the 24 lists every scene appears in every cell four times. Trial order is randomized in
# the study and plays no part here.
make_design <- function(n) {
  pid <- rep(seq_len(n), each = 12)
  pos <- rep(0:11, times = n)
  k <- (pid - 1) %% N_LISTS
  scene <- (pos + k %% 12) %% N_SCENES
  cell <- pos %/% 2 + 1
  d <- data.frame(pid = factor(pid), scene = factor(scene), cell = cell,
                  comp = ifelse(k < 12, -0.5, 0.5))
  cbind(d, CODES[cell, , drop = FALSE])
}
DESIGNS <- list(make_design(N_TARGET), make_design(N_FALLBACK))
names(DESIGNS) <- c(N_TARGET, N_FALLBACK)

# One dataset with every contrast zero. Components follow plan_sim_v2.py: participant intercept,
# participant-by-cell deviation, scene intercept, scene-by-cell deviation, residual. Composition
# has no effect, as in the planning simulation.
sim_share <- function(design, pc_sd, scene_sd) {
  n <- nlevels(design$pid)
  pid <- as.integer(design$pid)
  sc <- as.integer(design$scene)
  cell <- design$cell
  u <- rnorm(n, 0, SD_P)
  upc <- matrix(rnorm(n * 6, 0, pc_sd), n, 6)
  v <- rnorm(N_SCENES, 0, SD_S)
  vsc <- matrix(rnorm(N_SCENES * 6, 0, scene_sd), N_SCENES, 6)
  e <- rnorm(nrow(design), 0, SD_E)
  GRAND + u[pid] + upc[cbind(pid, cell)] + v[sc] + vsc[cbind(sc, cell)] + e
}

# ---------------------------------------------------------------- the registered model

# Fitted by fit_registered() in sim_common.R (1.8 as revised; 12.1, rule 7) with lme4's default
# settings. Slopes are listed smallest generating variance first: the by-scene slopes (scene-by-cell
# SD 0 or 2.8) before the by-participant slopes (participant-by-cell SD 7), and within each group h5
# to h1. There are no interaction slopes. Composition is a counterbalancing factor and gets no slope.
FIXED <- "share ~ h1 + h2 + h3 + h4 + h5 + comp"
SLOPES <- c(paste0("scene:h", 5:1), paste0("pid:h", 5:1))
GROUPS <- c("pid", "scene")

# The model fit_registered() tries first, written the way it builds it.
registered_formula <- function(slopes = SLOPES) {
  rhs <- vapply(GROUPS, function(g) {
    v <- sub("^[^:]*:", "", slopes[sub(":.*$", "", slopes) == g])
    if (length(v)) sprintf("(1 + %s || %s)", paste(v, collapse = " + "), g) else sprintf("(1 | %s)", g)
  }, "")
  paste(FIXED, "+", paste(rhs, collapse = " + "))
}

# Contrast vectors over the fixed effects (Intercept, h1-h5, comp).
L_VEC <- lapply(rownames(CONTRASTS), function(k) {
  c(0, drop(CONTRASTS[k, ] %*% CODES), 0)
})
names(L_VEC) <- rownames(CONTRASTS)

# Fit one dataset and return estimate, standard error and Satterthwaite df of every contrast, and
# the random terms kept. A dataset whose model cannot be fitted or whose contrasts cannot be
# computed keeps NA estimates, which the state rule reads as undetermined.
fit_contrasts <- function(d) {
  f <- fit_registered(FIXED, SLOPES, d)
  gone <- c(setdiff(SLOPES, f$keep), if (!f$scene_int) "scene:(Intercept)")
  out <- list(failed = is.null(f$model), n_removed = f$removed, conv_removals = f$conv_removed,
              removed = paste(gone, collapse = " "))
  for (s in SLOPES) out[[paste0("keep_", sub(":", "_", s))]] <- s %in% f$keep
  out$keep_scene_intercept <- f$scene_int
  for (k in names(L_VEC)) {
    ct <- if (is.null(f$model)) NULL else tryCatch(lin_contrast(f$model, L_VEC[[k]]), error = function(e) NULL)
    if (is.null(ct)) {
      ct <- c(est = NA, se = NA, df = NA)
      out$failed <- TRUE
    }
    out[[paste0("est_", k)]] <- ct[["est"]]
    out[[paste0("se_", k)]] <- ct[["se"]]
    out[[paste0("df_", k)]] <- ct[["df"]]
  }
  out
}

# ---------------------------------------------------------------- families and accounts (4.5)

FAMILIES <- list(
  H1 = list(
    label = "Prompting and delegation (H1)",
    contrasts = c("PR", "A"),
    accounts = list(
      neither = list(label = "Neither prompting nor iterating earns credit", status = "rival",
                     allowed = list(PR = "zero", A = "zero")),
      after = list(label = "Work after the prompt counts; prompting does not", status = "rival",
                   allowed = list(PR = "zero", A = "positive")),
      initiator = list(label = "Initiator credit", status = "rival",
                       allowed = list(PR = "positive", A = "zero")),
      scoped = list(label = "Scoped credit", status = "rival",
                    allowed = list(PR = "positive", A = "positive")),
      office = list(label = "Office practice", status = "compatible",
                    allowed = list(PR = "zero", A = c("zero", "positive")))
    )
  ),
  H2 = list(
    label = "Work after the prompt (H2)",
    contrasts = c("H", "Sel", "R"),
    accounts = list(
      office = list(label = "Office practice", status = "rival",
                    allowed = list(H = "zero", Sel = "zero", R = "zero")),
      time = list(label = "Time", status = "rival",
                  allowed = list(H = "positive", Sel = "zero", R = "zero")),
      selection = list(label = "Selection", status = "rival",
                       allowed = list(H = "zero", Sel = "positive", R = "zero")),
      revision = list(label = "Revision", status = "rival",
                      allowed = list(H = "zero", Sel = "zero", R = "positive")),
      scoped = list(label = "Scoped credit", status = "rival",
                    allowed = list(H = "zero", Sel = "positive", R = "positive")),
      work = list(label = "Work", status = "rival",
                  allowed = list(H = "positive", Sel = "positive", R = "positive"))
    )
  )
)

# True contrast values under a generating account, as in plan_sim_v2.py: a contrast whose only
# allowed state is positive (negative) is set to +effect (-effect); every other contrast is 0.
# Only rival accounts generate data; the compatible account is classified but never generates.
true_values <- function(acc, effect) {
  v <- setNames(numeric(nrow(CONTRASTS)), rownames(CONTRASTS))
  for (k in names(acc$allowed)) {
    a <- acc$allowed[[k]]
    if (identical(a, "positive")) v[k] <- effect
    if (identical(a, "negative")) v[k] <- -effect
  }
  v
}

# ---------------------------------------------------------------- settings

# main0 and main1 at the target with --reps datasets; bound0, bound1 and sens15 at the target and
# fall0 and fall1 at the fallback with --reps_small. Scene-by-cell SD 2.8 is 0.10 of the share SD.
SETTINGS <- data.frame(
  setting  = c("main0", "main1", "bound0", "bound1", "sens15", "fall0", "fall1"),
  n        = c(N_TARGET, N_TARGET, N_TARGET, N_TARGET, N_TARGET, N_FALLBACK, N_FALLBACK),
  effect   = c(1.5, 1.5, 1, 1, 1.5, 1.5, 1.5) * BOUND,
  scene_sd = c(0, 2.8, 0, 2.8, 0, 0, 2.8),
  pc_sd    = c(7, 7, 7, 7, 15, 7, 7),
  reps     = c(opt$reps, opt$reps, rep(opt$reps_small, 5)),
  stringsAsFactors = FALSE
)
if (!is.null(opt$only)) SETTINGS <- SETTINGS[SETTINGS$setting %in% strsplit(opt$only, ",")[[1]], ]

# ---------------------------------------------------------------- one dataset

# Adding cell means to y moves only the fixed effects: the REML variance estimates, the terms
# removed, the standard errors and the Satterthwaite df are unchanged, and every estimate moves by
# exactly its true contrast. So each dataset is simulated once with every contrast zero, fitted
# once, and read under each generating account (of both families) by adding that account's true
# values to the estimates. check_shift() below confirms this on one dataset by fitting the shifted
# data directly. Seed: SEED_BASE + 1e5 * setting index + rep.
one_dataset <- function(rep, s, i) {
  set.seed(SEED_BASE + 1e5 * i + rep)
  t0 <- proc.time()[["elapsed"]]
  d <- DESIGNS[[as.character(s$n)]]
  d$share <- sim_share(d, s$pc_sd, s$scene_sd)
  out <- fit_contrasts(d)
  data.frame(rep = rep, out, secs = proc.time()[["elapsed"]] - t0)
}

check_shift <- function() {
  s <- SETTINGS[SETTINGS$setting == "main1", ]
  set.seed(SEED_BASE + 999)
  d <- DESIGNS[[as.character(s$n)]]
  d$share <- sim_share(d, s$pc_sd, s$scene_sd)
  base <- fit_contrasts(d)
  true <- setNames(c(12, -12, 12, 8, 12), rownames(CONTRASTS))
  d$share <- d$share + drop(CELL_SHIFT %*% true)[d$cell]
  direct <- fit_contrasts(d)
  k <- names(L_VEC)
  c(est = max(abs(unlist(direct[paste0("est_", k)]) - unlist(base[paste0("est_", k)]) - true)),
    se = max(abs(unlist(direct[paste0("se_", k)]) - unlist(base[paste0("se_", k)]))),
    df = max(abs(unlist(direct[paste0("df_", k)]) - unlist(base[paste0("df_", k)]))),
    same_terms = as.numeric(identical(direct$removed, base$removed) &&
                              identical(direct$n_removed, base$n_removed)))
}

# ---------------------------------------------------------------- summaries

# States of a family's contrasts in every dataset under true values `true`.
family_states <- function(raw, fam, true) {
  st <- lapply(fam$contrasts, function(k) {
    mapply(state_of, raw[[paste0("est_", k)]] + true[[k]], raw[[paste0("se_", k)]],
           raw[[paste0("df_", k)]], MoreArgs = list(bound = BOUND))
  })
  as.data.frame(setNames(st, fam$contrasts), stringsAsFactors = FALSE)
}

summarize_setting <- function(raw, s, minutes) {
  rows <- list()
  for (fid in names(FAMILIES)) {
    fam <- FAMILIES[[fid]]
    for (g in names(fam$accounts)) {
      acc <- fam$accounts[[g]]
      if (acc$status != "rival") next
      true <- true_values(acc, s$effect)
      st <- family_states(raw, fam, true)
      sup <- support_rates(st, fam$accounts)
      rivals <- setdiff(names(Filter(function(a) a$status == "rival", fam$accounts)), g)
      row <- list(study = "B1", family = fid, setting = s$setting, n = s$n, effect = s$effect,
                  scene_sd = s$scene_sd, pc_sd = s$pc_sd, generating = g,
                  generating_label = acc$label,
                  n_requested = s$reps, n_datasets = nrow(raw), n_dropped = s$reps - nrow(raw),
                  n_failed = sum(raw$failed),
                  own_rate = sup[[g]], max_rival_rate = max(sup[rivals]))
      for (a in names(fam$accounts)) row[[paste0("support_", fid, "_", a)]] <- sup[[a]]
      for (k in rownames(CONTRASTS)) {
        inside <- k %in% fam$contrasts
        for (state in c("zero", "positive", "negative", "undetermined")) {
          row[[paste0(k, "_", state)]] <- if (inside) mean(st[[k]] == state) else NA
        }
        row[[paste0(k, "_true")]] <- if (inside) true[[k]] else NA
        row[[paste0(k, "_mean_est")]] <-
          if (inside) mean(raw[[paste0("est_", k)]] + true[[k]], na.rm = TRUE) else NA
        row[[paste0(k, "_mean_se")]] <- if (inside) mean(raw[[paste0("se_", k)]], na.rm = TRUE) else NA
        row[[paste0(k, "_sd_est")]] <- if (inside) sd(raw[[paste0("est_", k)]], na.rm = TRUE) else NA
      }
      # Random terms: share of datasets with 0, 1, ..., 11 terms removed, share with each term
      # kept, share of all removals that followed a convergence failure (not a singular fit), and
      # share of datasets with at least one such removal.
      for (j in 0:(length(SLOPES) + 1)) row[[paste0("fit_removed_", j)]] <- mean(raw$n_removed == j)
      for (v in grep("^keep_", names(raw), value = TRUE)) row[[paste0("fit_", v)]] <- mean(raw[[v]])
      row$fit_conv_share_of_removals <-
        if (sum(raw$n_removed) > 0) sum(raw$conv_removals) / sum(raw$n_removed) else NA
      row$fit_conv_any <- mean(raw$conv_removals > 0)
      row$mean_secs_per_dataset <- mean(raw$secs)
      row$setting_minutes <- minutes
      rows[[length(rows) + 1]] <- row
    }
  }
  rows
}

# Rows with different family columns are filled with NA so they bind into one table.
bind_rows_fill <- function(rows) {
  cols <- unique(unlist(lapply(rows, names)))
  do.call(rbind, lapply(rows, function(r) {
    r[setdiff(cols, names(r))] <- NA
    as.data.frame(r[cols], stringsAsFactors = FALSE, check.names = FALSE)
  }))
}

# ---------------------------------------------------------------- run

cat("B1 simulation:", if (opt$quick) "quick run," else "", "cores", opt$cores, "\n")
shift <- check_shift()
cat(sprintf("Shift check (direct fit minus shifted base fit): est %.2g, se %.2g, df %.2g, same terms removed %s\n",
            shift[["est"]], shift[["se"]], shift[["df"]], shift[["same_terms"]] == 1))

all_rows <- list()
raw_all <- list()
for (i in seq_len(nrow(SETTINGS))) {
  s <- SETTINGS[i, ]
  t0 <- Sys.time()
  raw <- run_reps(s$reps, function(r) one_dataset(r, s, i), opt$cores)
  mins <- as.numeric(difftime(Sys.time(), t0, units = "mins"))
  raw_all[[s$setting]] <- raw
  all_rows <- c(all_rows, summarize_setting(raw, s, mins))
  cat(sprintf("  %-7s n %3d  %4d of %4d datasets  %d without a usable fit  %.1f min\n", s$setting, s$n,
              nrow(raw), s$reps, sum(raw$failed), mins))
}
res <- bind_rows_fill(all_rows)
res$mode <- if (opt$quick) "quick" else "full"
write.csv(res, file.path(out_dir, paste0("B1_sim", TAG, ".csv")), row.names = FALSE)
if (!is.null(opt$only)) {
  cat("Wrote results/B1_sim", TAG, ".csv (search run: no report)\n", sep = "")
  quit(save = "no")
}

# Seconds per dataset (one fit serves both families) and the full run at the default numbers of
# datasets on 11 cores. B1 has no Laplace check.
secs_all <- unlist(lapply(raw_all, `[[`, "secs"))
sec_per <- mean(secs_all)
n_full <- 2 * 1000 + 5 * 500
full_min <- n_full * sec_per / 11 / 60

# ---------------------------------------------------------------- report

f2 <- function(x) ifelse(is.na(x), "", formatC(x, format = "f", digits = 2))
md_table <- function(df) {
  c(paste("|", paste(names(df), collapse = " | "), "|"),
    paste("|", paste(rep("---", ncol(df)), collapse = " | "), "|"),
    apply(df, 1, function(r) paste("|", paste(r, collapse = " | "), "|")))
}
acc_label <- function(fid, g) FAMILIES[[fid]]$accounts[[g]]$label

crit_row <- function(fid, s0, s1, sample) {
  r <- res[res$family == fid, ]
  m0 <- min(r$own_rate[r$setting == s0])
  m1 <- min(r$own_rate[r$setting == s1])
  rv <- max(r$max_rival_rate[r$setting %in% c(s0, s1)])
  data.frame(Family = FAMILIES[[fid]]$label, Sample = sample,
             `Lowest own rate, scene-by-cell SD 0` = f2(m0),
             `Lowest own rate, scene-by-cell SD 0.10` = f2(m1),
             `Highest rival rate` = f2(rv),
             `(a) >= .80 and >= .70` = ifelse(m0 >= .80 && m1 >= .70, "met", "not met"),
             `(b) every rival <= .05` = ifelse(rv <= .05, "met", "not met"), check.names = FALSE)
}
criteria <- do.call(rbind, lapply(names(FAMILIES), function(fid) {
  rbind(crit_row(fid, "main0", "main1", sprintf("target %d (main0, main1)", N_TARGET)),
        crit_row(fid, "fall0", "fall1", sprintf("fallback %d (fall0, fall1)", N_FALLBACK)))
}))

own_table <- do.call(rbind, lapply(names(FAMILIES), function(fid) {
  r <- res[res$family == fid, ]
  do.call(rbind, lapply(unique(r$generating), function(g) {
    x <- r[r$generating == g, ]
    v <- setNames(f2(x$own_rate), x$setting)
    out <- data.frame(Family = fid, `Generating account` = acc_label(fid, g), check.names = FALSE)
    for (st in SETTINGS$setting) out[[st]] <- v[[st]]
    out
  }))
}))

rival_table <- do.call(rbind, lapply(names(FAMILIES), function(fid) {
  r <- res[res$family == fid, ]
  do.call(rbind, lapply(unique(r$generating), function(g) {
    x <- r[r$generating == g, ]
    w <- setNames(f2(x$max_rival_rate), x$setting)
    out <- data.frame(Family = fid, `Generating account` = acc_label(fid, g), check.names = FALSE)
    for (st in SETTINGS$setting) out[[st]] <- w[[st]]
    out
  }))
}))

support_tables <- lapply(names(FAMILIES), function(fid) {
  fam <- FAMILIES[[fid]]
  r <- res[res$family == fid, ]
  tab <- data.frame(Setting = r$setting, N = r$n,
                    Generating = vapply(r$generating, function(g) acc_label(fid, g), ""),
                    Datasets = r$n_datasets, check.names = FALSE)
  for (a in names(fam$accounts)) {
    nm <- paste0(fam$accounts[[a]]$label, if (fam$accounts[[a]]$status == "compatible") " (compatible)" else "")
    tab[[nm]] <- f2(r[[paste0("support_", fid, "_", a)]])
  }
  for (k in fam$contrasts) {
    tab[[paste0(k, ": true, mean est (mean SE; SD of est)")]] <-
      sprintf("%g, %s (%s; %s)", r[[paste0(k, "_true")]], f2(r[[paste0(k, "_mean_est")]]),
              f2(r[[paste0(k, "_mean_se")]]), f2(r[[paste0(k, "_sd_est")]]))
    tab[[paste0(k, ": 0 / + / - / u")]] <- paste(f2(r[[paste0(k, "_zero")]]), f2(r[[paste0(k, "_positive")]]),
                                                f2(r[[paste0(k, "_negative")]]), f2(r[[paste0(k, "_undetermined")]]), sep = " / ")
  }
  tab
})

first <- res[!duplicated(res$setting), ]
fit_table <- local({
  tab <- data.frame(Setting = first$setting, N = first$n, Datasets = first$n_datasets,
                    Dropped = first$n_dropped, `No usable fit` = first$n_failed,
                    `Removals after a convergence failure (share of removals)` = f2(first$fit_conv_share_of_removals),
                    `Datasets with such a removal` = f2(first$fit_conv_any), check.names = FALSE)
  for (j in 0:(length(SLOPES) + 1)) tab[[paste0("removed ", j)]] <- f2(first[[paste0("fit_removed_", j)]])
  tab
})
keep_table <- local({
  tab <- data.frame(Setting = first$setting, check.names = FALSE)
  for (v in c(rev(SLOPES), "scene_intercept")) {
    tab[[sub(":", " ", v)]] <- f2(first[[paste0("fit_keep_", sub(":", "_", v))]])
  }
  tab
})
timing_table <- data.frame(Setting = first$setting, Datasets = first$n_datasets,
                           `Seconds per dataset` = formatC(first$mean_secs_per_dataset, format = "f", digits = 1),
                           Minutes = formatC(first$setting_minutes, format = "f", digits = 1),
                           check.names = FALSE)
code_table <- data.frame(Cell = CELLS, check.names = FALSE)
for (k in colnames(CODES)) code_table[[k]] <- CODES[, k]
contrast_table <- data.frame(Contrast = names(L_VEC),
                             Cells = c("a - o", "r - a", "b - r", "c - b", "c - d"),
                             `Weights on (Intercept, h1, h2, h3, h4, h5, comp)` =
                               vapply(L_VEC, function(l) paste(formatC(l, format = "g", digits = 4), collapse = ", "), ""),
                             check.names = FALSE)

si <- sessionInfo()
pkg_line <- function(pkgs) {
  paste(vapply(sort(names(pkgs)), function(p) paste(p, pkgs[[p]]$Version), ""), collapse = ", ")
}
script_path <- file.path(script_dir(), "sim_B1.R")

md <- c(
  sprintf("# Study B1 sample-size simulation%s", if (opt$quick) " (quick run, not for filing)" else ""),
  "",
  "## Criteria (1.10)",
  "",
  md_table(criteria),
  "",
  "Own rate: share of datasets in which the generating account is supported. Rival rate: the largest share of datasets in which any single other rival account is supported (rival accounts never share a supported pattern). The lowest own rate and the highest rival rate are taken over the family's generating accounts. Criteria: (a) own rate at least .80 with no scene-by-cell variation and at least .70 with scene-by-cell SD 0.10 of the share SD; (b) every rival at most .05. Compatible accounts (Office practice in H1) are classified and reported but never generate data and never count as rivals.",
  "",
  sprintf("Run date %s. %s: %d datasets at main0 and main1, %d at each other setting; %d cores; %.1f minutes. B1 has no binary family, so there is no Laplace (nAGQ = 1) check.",
          run_date, if (opt$quick) "Quick run (--quick): too few datasets for any conclusion; it checks that the code runs" else "Full run",
          opt$reps, opt$reps_small, opt$cores, as.numeric(difftime(Sys.time(), t_start, units = "mins"))),
  "",
  "Each generating account's own support rate in every setting:",
  "",
  md_table(own_table),
  "",
  "Highest support rate of any other rival account, by generating account and setting:",
  "",
  md_table(rival_table),
  "",
  "## Settings",
  "",
  md_table(data.frame(Setting = SETTINGS$setting, N = SETTINGS$n,
                      `Nonzero contrasts` = SETTINGS$effect,
                      `Scene-by-cell SD` = SETTINGS$scene_sd, `Participant-by-cell SD` = SETTINGS$pc_sd,
                      Datasets = SETTINGS$reps, check.names = FALSE)),
  "",
  sprintf("Nonzero contrasts are 1.5 times the bound (%g points) except in bound0 and bound1, where they equal the bound (%d). Scene-by-cell SD 2.8 is 0.10 of the share SD. sens15 raises the participant-by-cell SD from 7 to 15 points. Seeds: %d + 100000 x setting index (1 to %d, in the order above) + dataset number; the shift check uses %d.",
          1.5 * BOUND, BOUND, SEED_BASE, nrow(SETTINGS), SEED_BASE + 999),
  "",
  "## Design",
  "",
  sprintf("Target %d analyzable participants (24 lists of 6), fallback %d (24 lists of 5); Design Specification 4.5 as kept by 12.5 (N fixed at 10 hours in cells r, b, c and d, which does not enter the simulation). One within-participant factor with six cells (o found, a prompt only, r routine hours, b re-roll, c revise, d tool iterates), two trials each, twelve trials, one scene per trial. 24 lists: 12 rotations x 2 compositions (V1 in lists 0-11, I2 in lists 12-23). In rotation q, trial position j shows scene (j + q) mod 12 (scenes ordered SB-P1, SB-N1, ..., SB-P6, SB-N6) and positions 2i and 2i + 1 hold cell i, so within a list each cell falls on one scene with a person and one without; across the 24 lists every scene appears in every cell four times. Participant p gets list (p - 1) mod 24.",
          N_TARGET, N_FALLBACK),
  "",
  sprintf("Generating model (1.10 and plan_sim_v2.py, B1 section): share has total SD %d, split into participant intercept SD %.2f (62 percent), scene intercept SD %.2f (6 percent) and residual SD %.2f (32 percent), plus independent participant-by-cell deviations (SD in the settings table) and scene-by-cell deviations (SD in the settings table). Share is generated as normal and not clipped to 0-100, as in the planning simulation. Composition has no generating effect. Each rival account's true contrasts are +effect where its only allowed state is positive and 0 otherwise; contrasts outside the family are 0.",
          SD_TOTAL, SD_P, SD_S, SD_E),
  "",
  "Each dataset is simulated once with every contrast at zero, fitted once, and read under every generating account of both families by adding that account's true values to the estimates. Under REML the variance estimates, standard errors, df and the random terms removed do not depend on the cell means (the shift lies in the span of the fixed effects), so this equals fitting each account's dataset directly, up to the optimizer's tolerance.",
  sprintf("Check on one dataset, direct fit of the shifted data against the shifted base fit (largest absolute difference over the five contrasts): estimates %.2g, standard errors %.2g, df %.2g; same random terms removed: %s.",
          shift[["est"]], shift[["se"]], shift[["df"]], if (shift[["same_terms"]] == 1) "yes" else "no"),
  "",
  "## Model",
  "",
  "Linear mixed model (lmerTest::lmer, REML, lme4's default optimizer and convergence checks) on share, with Helmert codes h1-h5 over cells o, a, r, b, c, d (the columns of `contr.helmert(6)`) and composition (V1 -0.5, I2 +0.5) as fixed effects. Crossed random intercepts for participant and scene; uncorrelated (`||`) by-participant and by-scene slopes for all five Helmert codes (1.8: two trials per cell make the by-participant slopes estimable); composition is a counterbalancing factor and gets no slope. With independent cell deviations of SD s, code hk carries generating variance s^2 / (k (k + 1)), and the Helmert codes are orthogonal, so uncorrelated slopes on them represent independent cell deviations exactly. Each contrast is a linear combination of the fixed effects, with Satterthwaite df (lmerTest::contest). Codes:",
  "",
  md_table(code_table),
  "",
  md_table(contrast_table),
  "",
  "Model fitted first (the same for both families; one fit per dataset serves H1 and H2):",
  "",
  paste0("`", registered_formula(), "`"),
  "",
  sprintf("Removal rule and convergence (1.8 as revised; `fit_registered()` in sim_common.R, called with slopes %s, no interaction slopes, groups pid and scene, scene intercept removed last). A fit fails when it stops with an error, fails to converge (the optimizer returns a nonzero code, or lme4 or lmerTest warns that the model \"failed to converge\") or is singular. After a failed fit one random term is removed and the model refitted: the slope with the smallest estimated variance in the failed fit (there are no interaction slopes); when no slope is left, the scene intercept. The model left after the last removal is accepted as it is. Ties (several variances at zero) and a fit that stops with an error remove slopes in the order listed, smallest generating variance first: by-scene before by-participant, h5 to h1. A dataset has no usable fit when no model could be fitted or a contrast could not be computed; its contrasts are undetermined.",
          paste(SLOPES, collapse = ", ")),
  "",
  "## Fit diagnostics",
  "",
  "Datasets fitted, datasets dropped by an error outside the fit, datasets without a usable fit, share of all removals that followed a convergence failure that was not also a singular fit, share of datasets with at least one such removal, and share of datasets with 0, 1, ..., 11 random terms removed:",
  "",
  md_table(fit_table),
  "",
  "Share of datasets in which each random term is kept in the accepted model (participant intercepts are always kept):",
  "",
  md_table(keep_table),
  "",
  "## Full table",
  ""
)
for (i in seq_along(FAMILIES)) {
  md <- c(md, paste0("### ", FAMILIES[[i]]$label), "",
          "Support rate of every account; for each contrast the true value, mean estimate, mean model standard error and the standard deviation of the estimates across datasets, and the share of datasets in each state (zero / positive / negative / undetermined).", "",
          md_table(support_tables[[i]]), "")
}
md <- c(md,
        "## Timing",
        "",
        md_table(timing_table),
        "",
        sprintf("Mean seconds per dataset over this run (%d cores in parallel; one fit serves both families): %.2f. Estimated full run at the default numbers of datasets (1,000 at main0 and main1, 500 at each of the five other settings: %d datasets; no Laplace check) on 11 cores: %.0f minutes. Elapsed time of this run: %.1f minutes.",
                opt$cores, sec_per, n_full, full_min, as.numeric(difftime(Sys.time(), t_start, units = "mins"))),
        "",
        "## Software and checksums",
        "",
        paste0("- ", si$R.version$version.string, "; ", si$platform, "; ", si$running),
        paste0("- Attached packages: ", pkg_line(si$otherPkgs)),
        paste0("- Loaded packages: ", pkg_line(si$loadedOnly)),
        paste0("- Run date: ", run_date),
        paste0("- sim_B1.R SHA-256: ", sha256(script_path)),
        paste0("- sim_common.R SHA-256: ", sha256(file.path(script_dir(), "sim_common.R"))),
        "")
writeLines(md, file.path(out_dir, paste0("B1_sim", TAG, ".md")))
cat(sprintf("Seconds per dataset %.2f; estimated full run on 11 cores %.0f minutes\n", sec_per, full_min))
cat("Wrote results/B1_sim.csv and results/B1_sim.md\n")
