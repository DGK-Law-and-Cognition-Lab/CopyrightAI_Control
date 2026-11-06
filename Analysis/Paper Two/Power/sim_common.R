# Shared helpers for the Paper A and Paper B sample-size simulations.
#
# Each study script (sim_A1.R, sim_A2.R, sim_B1.R, sim_B2.R, sim_B3.R) sources this file. The
# scripts simulate trial-level data under each rival account, fit the registered mixed model to
# every dataset, give each confirmatory contrast one state under the state rule, and count how
# often each account is supported. The design and every generating value are in
# Docs/Paper Two/_internal_notes/Design_Specification_2026-10-26.md (Parts 0, 1.8 and 1.10).

suppressPackageStartupMessages({
  library(lme4)
  library(lmerTest)
  library(parallel)
})

# ---------------------------------------------------------------- paths and arguments

# Folder of the running script, so every path is relative to it.
script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", args[grep("^--file=", args)])
  if (length(f)) dirname(normalizePath(f)) else getwd()
}

# Command-line options: --reps N (main settings), --reps_small N (settings at the bound and
# sensitivity runs), --reps_laplace N (Laplace check of the logistic fits), --cores N, --quick.
parse_args <- function(defaults = list(reps = 1000, reps_small = 500, reps_laplace = 200,
                                       cores = max(1, detectCores() - 1), quick = FALSE)) {
  a <- commandArgs(trailingOnly = TRUE)
  out <- defaults
  i <- 1
  while (i <= length(a)) {
    key <- sub("^--", "", a[i])
    if (key == "quick") {
      out$quick <- TRUE
      i <- i + 1
      next
    }
    out[[key]] <- type.convert(a[i + 1], as.is = TRUE)
    i <- i + 2
  }
  if (isTRUE(out$quick)) {
    out$reps <- 20
    out$reps_small <- 10
    out$reps_laplace <- 5
  }
  out
}

# ---------------------------------------------------------------- the state rule

# Part 0: zero if the 90 percent interval lies inside plus or minus the bound (zero takes
# precedence); otherwise positive or negative if the two-sided p is below .05; otherwise
# undetermined. df = Inf uses the normal distribution (logistic contrasts).
state_of <- function(est, se, df, bound, alpha = .05, level = .90) {
  if (!is.finite(est) || !is.finite(se) || se <= 0) return("undetermined")
  q <- if (is.finite(df)) qt(1 - (1 - level) / 2, df) else qnorm(1 - (1 - level) / 2)
  if (est - q * se > -bound && est + q * se < bound) return("zero")
  p <- 2 * (if (is.finite(df)) pt(-abs(est / se), df) else pnorm(-abs(est / se)))
  if (p < alpha) return(if (est > 0) "positive" else "negative")
  "undetermined"
}

# An account is a named list: contrast name -> states it allows. Supported when every contrast
# is in an allowed state; contradicted when any contrast is in a signed or zero state it
# excludes; inconclusive otherwise.
classify <- function(states, allowed) {
  s <- states[names(allowed)]
  ok <- mapply(function(x, a) x %in% a, s, allowed)
  if (all(ok)) return("supported")
  bad <- mapply(function(x, a) x != "undetermined" && !(x %in% a), s, allowed)
  if (any(bad)) "contradicted" else "inconclusive"
}

# ---------------------------------------------------------------- linear contrasts

# Estimate, standard error and Satterthwaite df of the contrast L %*% beta in an lmer fit.
lin_contrast <- function(m, L) {
  ct <- lmerTest::contest(m, matrix(L, nrow = 1), joint = FALSE)
  c(est = ct$Estimate, se = ct$`Std. Error`, df = ct$df)
}

# ---------------------------------------------------------------- logistic contrasts

GH <- local({
  # 30-point Gauss-Hermite nodes and weights (for integrals against exp(-x^2)).
  n <- 30
  i <- seq_len(n - 1)
  b <- sqrt(i / 2)
  J <- matrix(0, n, n)
  J[cbind(i, i + 1)] <- b
  J[cbind(i + 1, i)] <- b
  e <- eigen(J, symmetric = TRUE)
  list(x = e$values, w = sqrt(pi) * e$vectors[1, ]^2)
})

# Population-averaged probability: the mean of plogis(eta + b) over b ~ Normal(0, tau2).
pa_prob <- function(eta, tau2) {
  z <- sqrt(2 * tau2) * GH$x
  sum(GH$w * plogis(eta + z)) / sqrt(pi)
}

# Its derivative with respect to eta.
pa_deriv <- function(eta, tau2) {
  z <- sqrt(2 * tau2) * GH$x
  sum(GH$w * dlogis(eta + z)) / sqrt(pi)
}

# Linear predictor that gives population-averaged probability p, used to build generating values.
eta_for_pa <- function(p, tau2) {
  uniroot(function(e) pa_prob(e, tau2) - p, c(-15, 15), tol = 1e-10)$root
}

# Random-effect variance that applies to one cell of a glmer fit with uncorrelated terms
# (the || syntax with numeric codes). codes: named numeric vector giving the cell's value on each
# slope variable; intercept terms always count.
cell_tau2 <- function(m, codes) {
  vc <- as.data.frame(VarCorr(m))
  vc <- vc[is.na(vc$var2), ]
  tau2 <- 0
  for (k in seq_len(nrow(vc))) {
    term <- vc$var1[k]
    if (is.na(term)) next   # residual row of an lmer fit
    x <- if (term == "(Intercept)") 1 else if (term %in% names(codes)) codes[[term]] else 0
    tau2 <- tau2 + vc$vcov[k] * x^2
  }
  tau2
}

# Population-averaged contrast in a glmer fit. cells: list of cells, each with X (row of the
# fixed-effects design, named like fixef(m)), codes (for cell_tau2) and weight (its weight in the
# contrast). Standard error by the delta method with the random-effect variances held fixed.
pa_contrast <- function(m, cells) {
  beta <- fixef(m)
  V <- as.matrix(vcov(m))
  est <- 0
  grad <- numeric(length(beta))
  for (cl in cells) {
    x <- cl$X[names(beta)]
    eta <- sum(x * beta)
    t2 <- cell_tau2(m, cl$codes)
    est <- est + cl$weight * pa_prob(eta, t2)
    grad <- grad + cl$weight * pa_deriv(eta, t2) * x
  }
  c(est = est, se = sqrt(drop(t(grad) %*% V %*% grad)), df = Inf)
}

# Fixed-effects design row for one cell. Every fixed predictor in these scripts is a numeric
# code (effect or contrast coding), so newrow is a one-row data frame of those codes.
design_row <- function(m, newrow) {
  tt <- delete.response(terms(formula(m, fixed.only = TRUE)))
  X <- model.matrix(tt, model.frame(tt, newrow))
  setNames(drop(X[1, ]), colnames(X))
}

# ---------------------------------------------------------------- fitting with the registered fallback

# The registered rule (specification 1.8), shared by every study. The full model is fitted with
# lme4's default settings (unless `control` says otherwise). A fit fails when it stops with an error, fails to converge (the
# optimizer returns a nonzero code, or lme4 or lmerTest warns that the model "failed to
# converge"), or is singular. After a failed fit, one random term is removed and the model is
# refitted: first any interaction slope (in the order given), then the slope with the smallest
# estimated variance in the failed fit, then the scene intercept. The model left after the last
# removal is accepted as it is.
#
# fixed:   fixed part as a string, e.g. "share ~ fid * cho + prac".
# slopes:  random slopes as "group:variable" strings, e.g. c("pid:fid", "scene:exE1"), every
#          variable a numeric code; terms use the uncorrelated || syntax. The order breaks ties
#          and chooses the slope to remove when a fit stops with an error and has no estimates.
# inter:   the slopes in `slopes` that are interaction slopes, removed first in this order.
# groups:  grouping factors with random intercepts; `drop_int` is the one whose intercept is
#          removed last (the scene).
# control: an lmerControl() or glmerControl() object passed to every fit. NULL (the default) uses
#          lme4's default settings. A1's logistic models pass glmerControl(optimizer = "bobyqa"):
#          lme4's default second stage for glmer (Nelder-Mead) stops short of the optimum on them
#          (results/A1_convergence_note.md).
# max_sd:  a fit whose largest random-effect standard deviation exceeds max_sd also fails to
#          converge: the variance estimate is running off toward infinity, which lme4 does not
#          always flag. Inf (the default) turns the check off; A1's logistic models use 10 (log-odds).
# Returns the model (NULL if even the last model fails with an error), the number of removals,
# the slopes kept, whether the scene intercept was kept, how many removals followed a
# convergence failure that was not also a singular fit, whether the accepted model carried lme4's
# absolute-gradient warning (grad_warn; possible only for the last model, accepted as it is), and
# a trace of every fit tried: formula, error, singular, optimizer code, lme4's absolute-gradient
# warning, lme4's degenerate-Hessian warning, the relative gradient (logistic fits; rel_grad()),
# the largest random-effect SD, and whether the fit failed. The trace is a record only; the
# relative gradient plays no part in the rule.
fit_registered <- function(fixed, slopes, data, family = NULL, nAGQ = 0, inter = character(0),
                           groups = c("pid", "scene"), drop_int = "scene",
                           control = NULL, max_sd = Inf) {
  keep <- slopes
  int_kept <- TRUE
  removed <- 0
  conv_removed <- 0
  trace <- list()
  repeat {
    rhs <- character(0)
    for (g in groups) {
      if (g == drop_int && !int_kept) next
      v <- sub("^[^:]*:", "", keep[sub(":.*$", "", keep) == g])
      rhs <- c(rhs, if (length(v)) sprintf("(1 + %s || %s)", paste(v, collapse = " + "), g)
                    else sprintf("(1 | %s)", g))
    }
    f <- as.formula(paste(fixed, "+", paste(rhs, collapse = " + ")))
    notes <- character(0)
    m <- withCallingHandlers(
      tryCatch(
        if (is.null(family)) {
          if (is.null(control)) lmerTest::lmer(f, data = data, REML = TRUE)
          else lmerTest::lmer(f, data = data, REML = TRUE, control = control)
        } else {
          if (is.null(control)) glmer(f, data = data, family = family, nAGQ = nAGQ)
          else glmer(f, data = data, family = family, nAGQ = nAGQ, control = control)
        },
        error = function(e) NULL),
      warning = function(w) {
        notes <<- c(notes, conditionMessage(w))
        invokeRestart("muffleWarning")
      },
      message = function(msg) {
        notes <<- c(notes, conditionMessage(msg))
        invokeRestart("muffleMessage")
      })
    last <- !int_kept || (!length(keep) && !(drop_int %in% groups))
    grad_warn <- any(grepl("failed to converge with max\\|grad\\|", notes, ignore.case = TRUE))
    rg <- NA_real_
    msd <- NA_real_
    code <- NA
    if (is.null(m)) {
      failed <- TRUE
      singular <- FALSE
      no_conv <- FALSE
    } else {
      singular <- isSingular(m)
      code <- m@optinfo$conv$opt
      code_bad <- length(code) && !is.na(code) && code != 0
      if (!is.null(family)) rg <- rel_grad(m)   # recorded only
      msd <- max_re_sd(m)
      no_conv <- any(grepl("failed to converge", notes, ignore.case = TRUE)) || code_bad ||
        (is.finite(max_sd) && !is.na(msd) && msd > max_sd)
      failed <- singular || no_conv
    }
    trace[[length(trace) + 1]] <- data.frame(
      formula = paste(deparse(f, width.cutoff = 500L), collapse = ""), error = is.null(m),
      singular = singular, code = if (length(code)) as.numeric(code[1]) else NA_real_,
      grad_warn = grad_warn, degenerate = any(grepl("degenerate", notes, ignore.case = TRUE)),
      rel_grad = rg, max_sd = msd, failed = failed,
      stringsAsFactors = FALSE)
    if (!failed || last) {
      return(list(model = m, removed = removed, keep = keep, scene_int = int_kept,
                  conv_removed = conv_removed, grad_warn = !is.null(m) && grad_warn,
                  trace = do.call(rbind, trace)))
    }
    if (no_conv && !singular) conv_removed <- conv_removed + 1
    if (length(keep)) {
      first <- intersect(inter, keep)
      drop <- if (length(first)) first[1] else keep[1]
      if (!length(first) && !is.null(m)) {
        vc <- as.data.frame(VarCorr(m))
        vc <- vc[!is.na(vc$var1) & is.na(vc$var2), ]
        v <- setNames(vc$vcov, paste(sub("\\..*$", "", vc$grp), vc$var1, sep = ":"))
        v <- v[intersect(keep, names(v))]
        if (length(v)) drop <- names(v)[which.min(v)]
      }
      keep <- setdiff(keep, drop)
    } else {
      int_kept <- FALSE
    }
    removed <- removed + 1
  }
}

# Relative gradient of a fit, the check lme4's help page ?convergence suggests: the largest
# absolute element of solve(Hessian, gradient), from the derivatives lme4 stored at the optimum
# (for a glmer fit with nAGQ = 1, over the variance parameters and the fixed effects; with
# nAGQ = 0, over the variance parameters). NA when lme4 stored no derivatives; Inf when the
# Hessian cannot be solved.
rel_grad <- function(m) {
  d <- m@optinfo$derivs
  if (is.null(d) || is.null(d$Hessian) || is.null(d$gradient)) return(NA_real_)
  r <- tryCatch(solve(d$Hessian, d$gradient), error = function(e) NULL)
  if (is.null(r) || any(!is.finite(r))) return(Inf)
  max(abs(r))
}

# Largest random-effect standard deviation of a fit (residual excluded).
max_re_sd <- function(m) {
  vc <- as.data.frame(VarCorr(m))
  vc <- vc[is.na(vc$var2) & vc$grp != "Residual", ]
  if (nrow(vc)) max(vc$sdcor) else NA_real_
}

# Earlier fixed-list version, kept for reference; the study scripts use fit_registered().
# Fit the first formula in `formulas` that converges without a singular fit, following the
# registered removal order (the list is already in that order). Returns the fit and the index of
# the formula used; the last formula is accepted even if singular.
fit_fallback <- function(formulas, data, family = NULL, nAGQ = 0) {
  for (k in seq_along(formulas)) {
    m <- tryCatch(
      suppressWarnings(suppressMessages(
        if (is.null(family)) {
          lmerTest::lmer(formulas[[k]], data = data, REML = TRUE,
                         control = lmerControl(calc.derivs = FALSE))
        } else {
          glmer(formulas[[k]], data = data, family = family, nAGQ = nAGQ,
                control = glmerControl(calc.derivs = FALSE))
        })),
      error = function(e) NULL)
    if (is.null(m)) next
    if (k < length(formulas) && isSingular(m)) next
    return(list(model = m, used = k))
  }
  list(model = NULL, used = NA_integer_)
}

# ---------------------------------------------------------------- running and summarizing

# Run `one_rep(rep_id)` for reps 1..n in parallel. Each call must set its own seed from rep_id
# and return a one-row data frame (or NULL on failure).
run_reps <- function(n, one_rep, cores) {
  res <- mclapply(seq_len(n), function(r) tryCatch(one_rep(r), error = function(e) NULL),
                  mc.cores = cores, mc.preschedule = FALSE)
  do.call(rbind, Filter(Negate(is.null), res))
}

# Given per-dataset states for one family (columns named by contrast), the account table
# (list of accounts, each a list with $allowed and $status "rival" or "compatible"), and the
# generating account, return the share of datasets in which each account is supported.
support_rates <- function(states_df, accounts) {
  sapply(accounts, function(acc) {
    mean(apply(states_df[, names(acc$allowed), drop = FALSE], 1, function(row) {
      classify(as.list(row), acc$allowed) == "supported"
    }))
  })
}

# SHA-256 checksum of a file (shasum ships with macOS and most Linux systems).
sha256 <- function(path) {
  out <- tryCatch(system2("shasum", c("-a", "256", shQuote(path)), stdout = TRUE),
                  error = function(e) NA_character_)
  sub(" .*", "", out[1])
}
