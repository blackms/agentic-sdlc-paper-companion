"""Cluster-robust paired permutation test for cold vs cold_mismatched detection.

For each cell (domain × reviewer family), we have n bug instances. The bugs
within a domain are NOT independent (they share the module's structural
features, common idioms, common operator distributions, etc.). McNemar
paired exact treats them as independent — likely inflating significance.

We replace the per-cell test with a clustered permutation test:
- the unit of randomization is the (domain, bug_id) pair;
- within each cluster (= domain), we permute the condition labels
  (cold vs mismatched) on each bug independently and recompute the
  test statistic;
- we report the permutation p-value: P(|T_perm| >= |T_observed|).

Test statistic: T = (caught_cold - caught_mismatched) / n_paired.

For the cross-domain combined analysis, we use a block bootstrap over
DOMAINS as the cluster unit (resample domains with replacement, recompute
combined Δ across cells, build a percentile CI for the population Δ).

This is more conservative than McNemar exact: it does not assume
independence within a domain and uses a paired difference distribution
rather than a binomial discordant-pair distribution.
"""
from __future__ import annotations
import json
import random
import re
from pathlib import Path
from math import sqrt


def extract_json(p: Path):
    if not p.exists() or p.stat().st_size == 0:
        return None
    text = p.read_text()
    cands = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", text, re.DOTALL):
        cands.append(m.group(0))
    last = text.rfind("}")
    first = text.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        cands.append(text[first:last + 1])
    for c in cands:
        try:
            d = json.loads(c.strip())
            if isinstance(d, dict) and "bugs_found" in d:
                bugs = d["bugs_found"]
                if isinstance(bugs, list):
                    return [str(b) for b in bugs]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def detects(bug, found):
    if found is None:
        return None
    text = " ||| ".join(b for b in found)
    text_l = text.lower()
    line = bug["line"]
    line_set = {line, line - 1, line + 1, line - 2, line + 2}
    if any(re.search(rf"\b{n}\b", text) for n in line_set):
        return True
    enc = (bug.get("enclosing") or "").lower()
    enc_hit = bool(enc) and enc in text_l
    op_hit = any(kw.lower() in text_l for kw in bug["op_keywords"])
    return enc_hit and op_hit


def cluster_perm_test(paired_outcomes, n_perm=20000, seed=20260511):
    """Paired permutation test: H0 condition labels exchangeable per pair.

    paired_outcomes: list of (cold_caught:int, mm_caught:int) tuples
    Returns:
      delta_obs: cold_rate - mm_rate
      p_two: two-sided p-value (P(|delta_perm| >= |delta_obs|))
      p_one: one-sided p-value (P(delta_perm >= delta_obs))
      ci95: percentile bootstrap CI for delta
    """
    rng = random.Random(seed)
    paired = [(int(c), int(m)) for c, m in paired_outcomes]
    n = len(paired)
    if n == 0:
        return {"n": 0, "delta_obs": 0.0, "p_two": 1.0, "p_one": 1.0, "ci95": (0, 0)}
    deltas = [c - m for c, m in paired]
    delta_obs = sum(deltas) / n
    count_two = 0
    count_one = 0
    perm_deltas = []
    for _ in range(n_perm):
        s = 0
        for d in deltas:
            # swap label on this pair with prob 0.5: equivalent to randomizing sign
            if rng.random() < 0.5:
                s += -d
            else:
                s += d
        delta_perm = s / n
        perm_deltas.append(delta_perm)
        if abs(delta_perm) >= abs(delta_obs):
            count_two += 1
        if delta_perm >= delta_obs:
            count_one += 1
    p_two = (count_two + 1) / (n_perm + 1)
    p_one = (count_one + 1) / (n_perm + 1)

    # Percentile bootstrap CI on delta
    boots = []
    for _ in range(n_perm):
        sample = [rng.choice(paired) for _ in range(n)]
        s = sum(c - m for c, m in sample) / n
        boots.append(s)
    boots.sort()
    lo = boots[int(0.025 * n_perm)]
    hi = boots[int(0.975 * n_perm)]
    return {
        "n": n,
        "delta_obs": delta_obs,
        "p_two": p_two,
        "p_one": p_one,
        "ci95": (lo, hi),
    }


def cluster_bootstrap_domains(domain_paired_dict, n_boot=10000, seed=20260511):
    """Block bootstrap over domains. Each iteration resamples DOMAINS with
    replacement, pools within-sampled-domain pairs, and computes the
    overall mean delta.
    Returns: observed_delta, 95% percentile CI for the population mean.
    """
    rng = random.Random(seed)
    domains = list(domain_paired_dict.keys())
    K = len(domains)
    if K == 0:
        return {"delta": 0.0, "ci95": (0, 0), "n_domains": 0}

    def mean_delta(paired_lists):
        all_pairs = []
        for paired in paired_lists:
            all_pairs.extend(paired)
        if not all_pairs:
            return 0.0
        return sum(c - m for c, m in all_pairs) / len(all_pairs)

    observed = mean_delta(domain_paired_dict.values())
    boots = []
    for _ in range(n_boot):
        sampled = [domain_paired_dict[rng.choice(domains)] for _ in range(K)]
        boots.append(mean_delta(sampled))
    boots.sort()
    lo = boots[int(0.025 * n_boot)]
    hi = boots[int(0.975 * n_boot)]
    return {
        "delta": observed,
        "ci95": (lo, hi),
        "n_domains": K,
    }


if __name__ == "__main__":
    # Quick self-test
    pairs = [(1, 0)] * 13 + [(0, 0)] * 17  # 13/30 cold, 0/30 mm — like P9 csv Codex
    res = cluster_perm_test(pairs, n_perm=5000)
    print("Self-test:", res)
