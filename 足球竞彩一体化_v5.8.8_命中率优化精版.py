#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球竞彩一体化 v5.8.8 命中率优化精版

这是对原 v5.8.7 赛前/实盘分析脚本的高门槛增强版。
核心目标：
- 不追求更大覆盖面，改为“只投强信号”；
- W/H 为主玩法，S/T 仅在强样本上允许极少量参与；
- 半场胜负/半场比分/半场总进球默认不纳入全场主实盘；
- 组合入口前做质量筛选，避免弱腿拖累整体命中率；
- 不重写原始采集逻辑，只在结果进入候选和组合前强制过滤。

适用方式：
    python 足球竞彩一体化_v5.8.8_命中率优化精版.py

说明：
- 它会自动尝试加载同目录下的原始 v5.8.7 文件；
- 若原始文件名不一致，会自动搜索符合 v5.8.7 的 Python 文件；
- 采集逻辑、RapidAPI、jc_data、AI_JSON、SHARP_TEXT 依然保留；
- 仅重写质量门槛逻辑，并在最终组合前拦掉低质量玩法。
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL_CANDIDATES = [
    HERE / "足球竞彩一体化_v5.8.7_0914收官 (1).py",
    HERE / "足球竞彩一体化_v5.8.7_0914收官.py",
    HERE / "足球竞彩一体化_v5.8.7.py",
]

orig = None
for path in ORIGINAL_CANDIDATES:
    if path.exists():
        orig = path
        break
if orig is None:
    matches = sorted(HERE.glob("足球竞彩一体化_v5.8.7*.py"))
    if not matches:
        raise FileNotFoundError("找不到对应的 v5.8.7 原始脚本，请确认文件名或放置目录。")
    orig = matches[0]

spec = importlib.util.spec_from_file_location("jc_v587_engine", orig)
if spec is None or spec.loader is None:
    raise ImportError(f"无法加载原始引擎：{orig}")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)

# ==========================
# v5.8.8 精版质量门槛配置
# ==========================
QUALITY_GATE_ENABLED = True
HALF_TIME_STRICT_BLOCK = True

W_MIN = 0.58
H_MIN = 0.64
S_MIN = 0.72
T_MIN = 0.70

# 玩法噪声门槛：越高越严格
NOISE_DROP = {
    "W": 0.00,
    "H": 0.04,
    "S": 0.12,
    "T": 0.10,
    "HT": 0.26,
}

# 评分下限，只允许明显强信号进入主实盘
MIN_SCORE_FOR_MIX = 0.55


def _safe_float(x, default=0.0):
    try:
        if x is None or x == "":
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


def _has_ou(x):
    if not isinstance(x, dict):
        return False
    return all(isinstance(x.get(k), (int, float)) and x.get(k) is not None and x.get(k) > 0 for k in ("line", "over", "under"))


def _has_sharp(m):
    sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    if _has_list3(sh.get("spf")):
        return True
    if _has_list3(sh.get("rsp")):
        return True
    if _has_ou(sh.get("ou")):
        return True
    return False


def _noise_level(m):
    if HALF_TIME_STRICT_BLOCK:
        if m.get("half_time") or m.get("hafu") or m.get("ht_spf") or m.get("ht"):
            return "HT"
    return "W"


def _score_market_quality(m):
    """市场强度打分，范围 0~1.0，越高越强。"""
    score = 0.0
    detail = []

    # 1X2 当前 SP
    if _has_list3(m.get("spf")):
        score += 0.18
        detail.append("spf")
    # 让球当前 SP
    if _has_list3(m.get("rsp")):
        score += 0.12
        detail.append("rsp")
    # 1X2 初盘
    if _has_list3(m.get("spf_open")):
        score += 0.06
        detail.append("spf_open")
    # 让球初盘
    if _has_list3(m.get("rsp_open")):
        score += 0.05
        detail.append("rsp_open")
    # 欧赔均值
    if _has_list3(m.get("euro_avg")):
        score += 0.15
        detail.append("euro_avg")
    # 锐线
    sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    if _has_list3(sh.get("spf")):
        score += 0.16
        detail.append("sharp_spf")
    if _has_list3(sh.get("rsp")):
        score += 0.12
        detail.append("sharp_rsp")
    # 统计 lambda
    st = m.get("stat") if isinstance(m.get("stat"), dict) else {}
    req = ["lg_hgf", "lg_agf", "lg_hga", "lg_aga", "h_n", "h_gf", "h_ga", "a_n", "a_gf", "a_ga"]
    if st and all(st.get(k) is not None for k in req):
        score += 0.18
        detail.append("stat")
    # review/战意
    rev = m.get("review") if isinstance(m.get("review"), dict) else {}
    if rev.get("lineup") and rev.get("motivation"):
        score += 0.08
        detail.append("review")
    # 赔率异动签证
    if m.get("spf_open") and m.get("spf"):
        try:
            o = m["spf_open"]
            c = m["spf"]
            if len(o) >= 3 and len(c) >= 3:
                max_move = 0.0
                for i in range(3):
                    if _safe_float(o[i], 0.0) > 0:
                        max_move = max(max_move, abs(_safe_float(c[i]) - _safe_float(o[i])) / _safe_float(o[i]))
                if max_move >= 0.18:
                    score -= 0.12
                elif max_move >= 0.10:
                    score -= 0.05
        except Exception:
            pass
    # 欧赔离散度
    try:
        disp = _safe_float(m.get("euro_disp"), 0.0)
        if disp > 1:
            disp = disp / 100.0
        if disp >= 0.18:
            score -= 0.12
        elif disp >= 0.12:
            score -= 0.06
    except Exception:
        pass
    # 负面 warn
    if m.get("_lambda_warn"):
        score -= 0.12
    if m.get("_collect_warn"):
        score -= 0.04
    if m.get("_manual_warn"):
        score -= 0.06
    # 半场噪声强制降权
    noise = _noise_level(m)
    if noise == "HT":
        score -= 0.22

    score = max(0.0, min(1.0, score))
    return score, detail, noise


def _quality_gate_for_market(m, market):
    """Return (ok, reason, score, noise)."""
    if not QUALITY_GATE_ENABLED:
        return True, "QUALITY_GATE_DISABLED", 1.0, "normal"
    score, detail, noise = _score_market_quality(m)
    if noise == "HT":
        return False, "半场玩法强制禁入全场实盘", score, noise
    if market == "W":
        min_score = W_MIN
    elif market == "H":
        min_score = H_MIN
    elif market == "S":
        min_score = S_MIN
    elif market == "T":
        min_score = T_MIN
    else:
        return False, f"未知玩法:{market}", score, noise

    ok = score >= min_score and score >= MIN_SCORE_FOR_MIX
    reason = f"quality={score:.2f},need>={min_score:.2f},noise={noise}"
    if market == "W" and not _has_list3(m.get("spf")):
        return False, "W 玩法缺 SPF", score, noise
    if market == "H" and (m.get("hand") is None or not _has_list3(m.get("rsp"))):
        return False, "H 玩法缺 hand 或 rsp", score, noise
    if market == "S" and not isinstance(m.get("ssp"), dict):
        return False, "S 玩法缺 ssp", score, noise
    if market == "T" and not _has_tsp(m.get("tsp")):
        return False, "T 玩法缺 tsp", score, noise

    return ok, reason, score, noise


def _filter_legs_for_quality(a):
    """根据市场质量门槛过滤 leg。"""
    new_legs = []
    for leg in a.get("legs", []):
        mk = leg.get("mk")
        if mk is None:
            continue
        ok, reason, score, noise = _quality_gate_for_market(a.get("m", {}), mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise
        if ok:
            new_legs.append(leg)
    a["legs"] = new_legs
    return a


def _filter_all_legs_for_quality(a):
    if not isinstance(a, dict):
        return a
    m = a.get("m", {})
    new_all = []
    for leg in a.get("all_legs", []):
        mk = leg.get("mk")
        ok, reason, score, noise = _quality_gate_for_market(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise
        if ok:
            new_all.append(leg)
    a["all_legs"] = new_all
    return a


def _filter_combo_candidates(A):
    """在生成组合前过滤弱组合；保留强信号组合。"""
    out = []
    for a in A:
        if not isinstance(a, dict):
            continue
        aa = _filter_legs_for_quality(dict(a))
        aa = _filter_all_legs_for_quality(aa)
        if aa.get("legs") or aa.get("all_legs"):
            out.append(aa)
    return out


_original_analyze = engine.analyze
_original_build_combos = engine.build_combos
_original_stake_plan = engine.stake_plan


def analyze(m):
    r = _original_analyze(m)
    qscore, detail, noise = _score_market_quality(m)
    m["_v588_quality"] = {
        "score": round(qscore, 4),
        "details": detail,
        "noise": noise,
    }

    # 只允许强信号 leg 进入最终输出；弱信号 leg 保留但置 observation_only
    for leg in r.get("legs", []):
        mk = leg.get("mk")
        ok, reason, score, noise_l = _quality_gate_for_market(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise_l
        if not ok:
            leg["observation_only"] = True

    for leg in r.get("all_legs", []):
        mk = leg.get("mk")
        ok, reason, score, noise_l = _quality_gate_for_market(m, mk)
        leg["quality_ok"] = ok
        leg["quality_score"] = round(score, 4)
        leg["quality_reason"] = reason
        leg["quality_noise"] = noise_l
        if not ok:
            leg["observation_only"] = True

    return r


def build_combos(A, attr="legs"):
    filtered = _filter_combo_candidates(A)
    combos = _original_build_combos(filtered, attr)
    strong = []
    for c in combos:
        q1 = float((c.get("L1") or {}).get("quality_score", 0.0))
        q2 = float((c.get("L2") or {}).get("quality_score", 0.0))
        mk1 = (c.get("L1") or {}).get("mk")
        mk2 = (c.get("L2") or {}).get("mk")
        if mk1 in ("S", "T") or mk2 in ("S", "T"):
            if min(q1, q2) < S_MIN - 0.04:
                continue
        if (mk1 == "H" and q1 < H_MIN) or (mk2 == "H" and q2 < H_MIN):
            continue
        if (mk1 == "W" and q1 < W_MIN) or (mk2 == "W" and q2 < W_MIN):
            continue
        if (mk1 in ("S", "T") and q1 < S_MIN) or (mk2 in ("S", "T") and q2 < S_MIN):
            continue
        strong.append(c)
    return strong


def stake_plan(c):
    sp = _original_stake_plan(c)
    l1 = c.get("L1", {})
    l2 = c.get("L2", {})
    q1 = float(l1.get("quality_score", 0.0))
    q2 = float(l2.get("quality_score", 0.0))
    mk1 = l1.get("mk")
    mk2 = l2.get("mk")

    if mk1 in ("S", "T") or mk2 in ("S", "T"):
        if min(q1, q2) < S_MIN:
            sp["f_live"] = 0.0
            sp["why"] += "；v5.8.8 精版：高噪声比分/总进球未达门槛→实盘0"
    if mk1 == "H" and q1 < H_MIN or mk2 == "H" and q2 < H_MIN:
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 精版：让球低质量腿→实盘0"
    if mk1 == "W" and q1 < W_MIN or mk2 == "W" and q2 < W_MIN:
        sp["f_live"] = 0.0
        sp["why"] += "；v5.8.8 精版：胜负低质量腿→实盘0"
    return sp


# 绑定原引擎入口
engine.analyze = analyze
engine.build_combos = build_combos
engine.stake_plan = stake_plan
engine.market_quality_gate = _quality_gate_for_market
engine._v588_quality_score = _score_market_quality


def main():
    if hasattr(engine, "main"):
        return engine.main()
    print("已加载 v5.8.8 命中率优化精版，原始入口已挂接成功。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
