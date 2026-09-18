#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球竞彩一体化 v5.8.8 命中率优化最终实盘版

目标：
- 只投强信号，绝不追求大覆盖；
- 胜负/让球优先；
- 比分/总进球仅在极强样本与强市场一致时少量参与；
- 半场打法默认禁入全场实盘；
- 组合前二次过滤弱腿，避免低质量门槛拖垮命中率；
- 保留原始 v5.8.7 采集逻辑与数据目录结构，增强的是筛选与门槛。

说明：
- 本文件会尝试自动加载同目录下的 v5.8.7 原始脚本；
- 若原文件名不同，会自动搜索同目录 v5.8.7 相关文件；
- 仅增强过滤逻辑与实盘门槛，不摧毁原始数据链路。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 只要能命中最接近的原脚本即可
CANDIDATES = [
    HERE / "足球竞彩一体化_v5.8.7_0914收官 (1).py",
    HERE / "足球竞彩一体化_v5.8.7_0914收官.py",
    HERE / "足球竞彩一体化_v5.8.7.py",
]

orig = None
for p in CANDIDATES:
    if p.exists():
        orig = p
        break
if orig is None:
    matches = sorted(HERE.glob("足球竞彩一体化_v5.8.7*.py"))
    if not matches:
        raise FileNotFoundError("找不到同目录下的 v5.8.7 原始脚本，无法执行最终实盘版。")
    orig = matches[0]

spec = importlib.util.spec_from_file_location("jc_v587_engine_final", orig)
if spec is None or spec.loader is None:
    raise ImportError(f"无法加载原脚本：{orig}")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)

# ========================== 
# 最终实盘版严格门槛
# ==========================
QUALITY_GATE_ENABLED = True
HALF_TIME_STRICT_BLOCK = True

# 玩法最小质量阈值（0~1.0）
W_MIN = 0.62
H_MIN = 0.68
S_MIN = 0.78
T_MIN = 0.76

# 合并后流量门槛
FINAL_MIN_SCORE = 0.60

# 更严厉的高噪声惩罚
NOISE_PENALTY = {
    "W": 0.00,
    "H": 0.02,
    "S": 0.14,
    "T": 0.12,
    "HT": 0.30,
}

# ===== HELPER =====

def _safe_f(x, default=0.0):
    try:
        if x in (None, "", "-"):
            return default
        if isinstance(x, bool):
            return float(int(x))
        return float(x)
    except Exception:
        return default


def _has_list3(x):
    return isinstance(x, (list, tuple)) and len(x) >= 3 and all(
        isinstance(v, (int, float)) and v > 1.0 for v in x[:3]
    )


def _has_tsp(x):
    return isinstance(x, (list, tuple)) and len(x) >= 8 and all(
        isinstance(v, (int, float)) and v > 0 for v in x[:8]
    )


def _is_ht_noise(m):
    if not HALF_TIME_STRICT_BLOCK:
        return False
    return bool(
        m.get("half_time") or m.get("hafu") or m.get("ht_spf") or m.get("ht")
    )


def _market_noise(m):
    return "HT" if _is_ht_noise(m) else "normal"


def _quality_score(m):
    """实时评估每场的整体质量分。越高越稳。"""
    score = 0.0
    detail = []

    if _has_list3(m.get("spf")):
        score += 0.18; detail.append("spf")
    if _has_list3(m.get("rsp")):
        score += 0.14; detail.append("rsp")
    if _has_list3(m.get("spf_open")):
        score += 0.06; detail.append("spf_open")
    if _has_list3(m.get("rsp_open")):
        score += 0.05; detail.append("rsp_open")
    if _has_list3(m.get("euro_avg")):
        score += 0.16; detail.append("euro_avg")

    sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    if _has_list3(sh.get("spf")):
        score += 0.16; detail.append("sharp_spf")
    if _has_list3(sh.get("rsp")):
        score += 0.12; detail.append("sharp_rsp")

    st = m.get("stat") if isinstance(m.get("stat"), dict) else {}
    stat_keys = [
        "lg_hgf", "lg_agf", "lg_hga", "lg_aga",
        "h_n", "h_gf", "h_ga",
        "a_n", "a_gf", "a_ga",
    ]
    if st and all(st.get(k) is not None for k in stat_keys):
        score += 0.18; detail.append("stat")

    rev = m.get("review") if isinstance(m.get("review"), dict) else {}
    if rev.get("lineup") and rev.get("motivation"):
        score += 0.08; detail.append("review")

    if m.get("_lambda_warn"):
        score -= 0.14
    if m.get("_collect_warn"):
        score -= 0.04
    if m.get("_manual_warn"):
        score -= 0.06

    # odds drift / dispersion
    try:
        disp = _safe_f(m.get("euro_disp"), 0.0)
        if disp > 1:
            disp = disp / 100.0
        if disp >= 0.18:
            score -= 0.12
        elif disp >= 0.12:
            score -= 0.06
    except Exception:
        pass

    # half_time noise
    noise = _market_noise(m)
    if noise == "HT":
        score -= 0.26

    score = max(0.0, min(1.0, score))
    return score, detail, noise


def _quality_gate(m, market):
    if not QUALITY_GATE_ENABLED:
        return True, "QUALITY_GATE_DISABLED", 1.0, "normal"

    score, details, noise = _quality_score(m)
    if noise == "HT":
        return False, "半场玩法强制禁入全场实盘", score, noise

    if market == "W":
        min_score = W_MIN
        if not _has_list3(m.get("spf")):
            return False, "W 缺 SPF", score, noise
    elif market == "H":
        min_score = H_MIN
        if m.get("hand") is None or not _has_list3(m.get("rsp")):
            return False, "H 缺 hand/rsp", score, noise
    elif market == "S":
        min_score = S_MIN
        if not isinstance(m.get("ssp"), dict):
            return False, "S 缺 ssp", score, noise
    elif market == "T":
        min_score = T_MIN
        if not _has_tsp(m.get("tsp")):
            return False, "T 缺 tsp", score, noise
    else:
        return False, f"未知玩法:{market}", score, noise

    ok = score >= min_score and score >= FINAL_MIN_SCORE
    reason = f"quality={score:.2f},need>={min_score:.2f},noise={noise}"
    return ok, reason, score, noise


def _filter_legs_quality(a):
    m = a.get("m", {})
    out_legs = []
    for leg in a.get("legs", []):
        mk = leg.get("mk")
        ok, reason, score, noise = _quality_gate(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise
        if ok:
            out_legs.append(leg)
    a["legs"] = out_legs
    return a


def _filter_all_legs_quality(a):
    m = a.get("m", {})
    out_all = []
    for leg in a.get("all_legs", []):
        mk = leg.get("mk")
        ok, reason, score, noise = _quality_gate(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise
        if ok:
            out_all.append(leg)
    a["all_legs"] = out_all
    return a


def _filter_combo_pool(A):
    filtered = []
    for a in A:
        if not isinstance(a, dict):
            continue
        aa = _filter_legs_quality(dict(a))
        aa = _filter_all_legs_quality(aa)
        if aa.get("legs") or aa.get("all_legs"):
            filtered.append(aa)
    return filtered


# ===== HOOK TO ORIGINAL ENGINE =====
_original_analyze = engine.analyze
_original_build_combos = engine.build_combos
_original_stake_plan = engine.stake_plan


def analyze(m):
    r = _original_analyze(m)
    score, details, noise = _quality_score(m)
    m["_v588_final_quality"] = {
        "score": round(score, 4),
        "details": details,
        "noise": noise,
    }

    for leg in r.get("legs", []):
        mk = leg.get("mk")
        ok, reason, score_l, noise_l = _quality_gate(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score_l, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise_l
        if not ok:
            leg["observation_only"] = True

    for leg in r.get("all_legs", []):
        mk = leg.get("mk")
        ok, reason, score_l, noise_l = _quality_gate(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score_l, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise_l
        if not ok:
            leg["observation_only"] = True

    return r


def build_combos(A, attr="legs"):
    filtered = _filter_combo_pool(A)
    combos = _original_build_combos(filtered, attr)
    strong = []
    for c in combos:
        l1 = c.get("L1", {})
        l2 = c.get("L2", {})
        q1 = float(l1.get("quality_score", 0.0))
        q2 = float(l2.get("quality_score", 0.0))
        m1 = l1.get("mk")
        m2 = l2.get("mk")

        # 最终拆强门槛：任何一腿低分直接剔除
        if m1 in ("S", "T") or m2 in ("S", "T"):
            if min(q1, q2) < S_MIN:
                continue
        if (m1 == "H" and q1 < H_MIN) or (m2 == "H" and q2 < H_MIN):
            continue
        if (m1 == "W" and q1 < W_MIN) or (m2 == "W" and q2 < W_MIN):
            continue
        if min(q1, q2) < FINAL_MIN_SCORE:
            continue
        strong.append(c)
    return strong


def stake_plan(c):
    sp = _original_stake_plan(c)
    l1 = c.get("L1", {})
    l2 = c.get("L2", {})
    q1 = float(l1.get("quality_score", 0.0))
    q2 = float(l2.get("quality_score", 0.0))
    m1 = l1.get("mk")
    m2 = l2.get("mk")

    if (m1 in ("S", "T") or m2 in ("S", "T")) and min(q1, q2) < S_MIN:
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 最终实盘版：比分/总进球低质量腿→实盘0"
    if (m1 == "H" and q1 < H_MIN) or (m2 == "H" and q2 < H_MIN):
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 最终实盘版：让球低质量腿→实盘0"
    if (m1 == "W" and q1 < W_MIN) or (m2 == "W" and q2 < W_MIN):
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 最终实盘版：胜负低质量腿→实盘0"
    if min(q1, q2) < FINAL_MIN_SCORE:
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 最终实盘版：组合总质量不足→实盘0"
    return sp

# bind
engine.analyze = analyze
engine.build_combos = build_combos
engine.stake_plan = stake_plan
engine.QUALITY_GATE_ENABLED = QUALITY_GATE_ENABLED
engine.market_quality_gate = _quality_gate
engine.v588_final_gate = True


def main():
    if hasattr(engine, "main"):
        return engine.main()
    print("已加载：足球竞彩一体化 v5.8.8 命中率优化最终实盘版")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
