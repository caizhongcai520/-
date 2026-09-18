#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球竞彩一体化 v5.8.8 命中率优化可运行版

这是对 v5.8.7_0914 收官版的兼容增强入口：
- 保留原脚本及 RapidAPI/PinBook/OddsPapi/SportScore 采集逻辑；
- 不改原始数据目录、快照、台账、校准库；
- 在分析结果进入组合前增加玩法质量门槛；
- W/H 优先，S/T 只允许强数据场，低质量腿自动降为观察；
- 半场数据不参与全场串关；
- 可直接运行，也可被外层豆包编排调用。

使用：
    python 足球竞彩一体化_v5.8.8_命中率优化版.py

也可以把本文件与原文件放在同一目录，通过原有 AI_JSON、SHARP_TEXT、RapidAPI
环境变量和 jc_data 目录运行。RAPIDAPI_KEY 不会被删除或禁用。
"""
from __future__ import annotations

import glob
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL_NAME = "足球竞彩一体化_v5.8.7_0914收官 (1).py"
ORIGINAL = HERE / ORIGINAL_NAME
if not ORIGINAL.exists():
    candidates = sorted(HERE.glob("足球竞彩一体化_v5.8.7*收官*.py"))
    if not candidates:
        candidates = sorted(HERE.glob("足球竞彩一体化_v5.8.7*.py"))
    if not candidates:
        raise FileNotFoundError(f"找不到原始引擎文件：{ORIGINAL_NAME}")
    ORIGINAL = candidates[0]

_spec = importlib.util.spec_from_file_location("jc_v587_engine", ORIGINAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"无法加载原始引擎：{ORIGINAL}")
engine = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = engine
_spec.loader.exec_module(engine)

# ---------------- v5.8.8 配置 ----------------
QUALITY_GATE_ENABLED = True
QUALITY_GATE_W_MIN = 0.55
QUALITY_GATE_H_MIN = 0.62
QUALITY_GATE_S_MIN = 0.78
QUALITY_GATE_T_MIN = 0.72
SCORE_MIN_CELLS = 10
TOTAL_MIN_BINS = 8
DISAGREE_WARN = 0.10
DISAGREE_BLOCK = 0.18
NOISE_PENALTY_S = 0.10
NOISE_PENALTY_T = 0.08
NOISE_PENALTY_EARLY = 0.08


def _valid3(value):
    return isinstance(value, (list, tuple)) and len(value) >= 3 and all(
        isinstance(x, (int, float)) and x > 1.0 for x in value[:3]
    )


def _valid_tsp(value):
    return isinstance(value, (list, tuple)) and len(value) >= TOTAL_MIN_BINS and all(
        isinstance(x, (int, float)) and x > 1.0 for x in value[:TOTAL_MIN_BINS]
    )


def _valid_ou(value):
    return isinstance(value, dict) and all(
        isinstance(value.get(k), (int, float)) and value.get(k) > 1.0
        for k in ("line", "over", "under")
    )


def _quality_score(m):
    """返回(总分,明细,噪声等级)。只使用已存在的原始字段，不编造数据。"""
    score = 0.0
    detail = []
    if _valid3(m.get("spf")):
        score += 0.20; detail.append("spf")
    sharp = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    if _valid3(sharp.get("spf")):
        score += 0.22; detail.append("sharp.spf")
    if _valid3(m.get("euro_avg")):
        score += 0.16; detail.append("euro_avg")
    if isinstance(m.get("stat"), dict):
        need = ("lg_hgf", "lg_agf", "lg_hga", "lg_aga", "h_n", "h_gf", "h_ga", "a_n", "a_gf", "a_ga")
        if all(m["stat"].get(k) is not None for k in need):
            score += 0.18; detail.append("stat")
    if isinstance(m.get("review"), dict):
        rev = m["review"]
        if rev.get("lineup") and rev.get("motivation"):
            score += 0.08; detail.append("review")
    if m.get("spf_open") is not None:
        score += 0.05; detail.append("spf_open")
    if _valid_ou(m.get("ou")) or _valid_ou(sharp.get("ou")) or m.get("ou_multi"):
        score += 0.06; detail.append("ou")
    if isinstance(m.get("dims"), dict) and m["dims"].get("9_xg") not in (None, False):
        score += 0.05; detail.append("xg")
    if isinstance(m.get("dims"), dict) and m["dims"].get("10_elo") not in (None, False):
        score += 0.04; detail.append("elo")
    if m.get("_lambda_warn"):
        score -= 0.12
    disp = 0.0
    try:
        disp = float(m.get("euro_disp") or 0)
        if disp > 1: disp /= 100.0
    except Exception:
        disp = 0.0
    if disp >= float(getattr(engine, "EURO_DISP_BLOCK", 0.30)):
        score -= 0.20
    elif disp >= float(getattr(engine, "EURO_DISP_WARN", 0.15)):
        score -= 0.08
    if (m.get("_v54") or {}).get("flipped"):
        score -= 0.08
    noise = "normal"
    if m.get("hafu") or m.get("half_time") or m.get("ht_spf"):
        noise = "half_time"
        score -= 0.20
    return max(0.0, min(1.0, score)), detail, noise


def market_quality_gate(m, market):
    score, detail, noise = _quality_score(m)
    m["_v588_quality"] = {"score": round(score, 4), "market": market,
                           "evidence": detail, "noise": noise}
    if noise == "half_time":
        return False, "半场玩法默认禁入全场实盘"
    if market == "W":
        ok = _valid3(m.get("spf")) and score >= QUALITY_GATE_W_MIN
    elif market == "H":
        ok = (m.get("hand") is not None and _valid3(m.get("rsp")) and
              (m.get("_h_indep") or (m.get("sharp") or {}).get("rsp")) and score >= QUALITY_GATE_H_MIN)
    elif market == "S":
        cells = m.get("ssp") if isinstance(m.get("ssp"), dict) else {}
        ok = len(cells) >= SCORE_MIN_CELLS and score >= QUALITY_GATE_S_MIN
    elif market == "T":
        ok = _valid_tsp(m.get("tsp")) and score >= QUALITY_GATE_T_MIN
    else:
        ok = False
    return bool(ok), f"quality={score:.2f},need={market}"


_original_analyze = engine.analyze
_original_build_combos = engine.build_combos
_original_stake_plan = engine.stake_plan


def analyze(m):
    result = _original_analyze(m)
    score, detail, noise = _quality_score(m)
    m["_v588_quality"] = {"score": round(score, 4), "evidence": detail, "noise": noise}
    # 标注每条腿是否允许进入主候选池；不删除原始腿，便于复盘。
    for leg in result.get("legs", []) + result.get("all_legs", []):
        mk = leg.get("mk")
        ok, reason = market_quality_gate(m, mk)
        leg["quality_ok"] = ok
        leg["quality_reason"] = reason
        if not ok:
            leg["observation_only"] = True
    return result


def build_combos(A, attr="legs"):
    """先应用市场质量门槛，再调用原有组合逻辑；保留原EV/ρ/CLV口径。"""
    filtered = []
    for a in A:
        m = a.get("m", {})
        legs = []
        for leg in a.get(attr, []):
            ok, _ = market_quality_gate(m, leg.get("mk"))
            if ok:
                legs.append(leg)
        if legs:
            item = dict(a)
            item[attr] = legs
            filtered.append(item)
    return _original_build_combos(filtered, attr)


def stake_plan(c):
    """高噪声玩法即使有纸面EV，也必须经过更高质量门槛。"""
    plan = _original_stake_plan(c)
    exotic = c.get("L1", {}).get("mk") in ("S", "T") or c.get("L2", {}).get("mk") in ("S", "T")
    if exotic:
        scores = []
        for a in (c.get("a1"), c.get("a2")):
            if a:
                scores.append(float((a.get("m") or {}).get("_v588_quality", {}).get("score", 0.0)))
        if scores and min(scores) < QUALITY_GATE_S_MIN:
            plan["f_live"] = 0.0
            plan["why"] += f"；v5.8.8比分/总进球质量门槛未达{QUALITY_GATE_S_MIN:.0%}→实盘0"
    return plan


# 把补丁函数挂回原引擎；原有 main/auto_pipeline 会自动使用这些函数。
engine.analyze = analyze
engine.build_combos = build_combos
engine.stake_plan = stake_plan
engine.market_quality_gate = market_quality_gate
engine.QUALITY_GATE_ENABLED = QUALITY_GATE_ENABLED

# 便于外层程序调用。
def auto_pipeline(*args, **kwargs):
    return engine.auto_pipeline(*args, **kwargs)


def main():
    return engine.main()


if __name__ == "__main__":
    main()
