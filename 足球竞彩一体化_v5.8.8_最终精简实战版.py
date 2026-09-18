#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""足球竞彩一体化 v5.8.8 最终精简实战版

保留原 v5.8.7 引擎及 RapidAPI/PinBook/AI_JSON/jc_data；只增加最终实盘筛选：
W/H 主力，S/T 强样本覆盖，半场禁入，同联赛组合禁用，质量不足自动空仓。
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
_candidates = [
    BASE / "足球竞彩一体化_v5.8.7_0914收官 (1).py",
    BASE / "足球竞彩一体化_v5.8.7_0914收官.py",
    BASE / "足球竞彩一体化_v5.8.7.py",
]
_source = next((p for p in _candidates if p.exists()), None)
if _source is None:
    _source = next(iter(sorted(BASE.glob("足球竞彩一体化_v5.8.7*.py"))), None)
if _source is None:
    raise FileNotFoundError("未找到同目录下的 v5.8.7 原始脚本。")

_spec = importlib.util.spec_from_file_location("jc_original_v587", _source)
if _spec is None or _spec.loader is None:
    raise ImportError(f"无法加载原始脚本：{_source}")
_engine = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _engine
_spec.loader.exec_module(_engine)

# 最终精简门槛
W_MIN, H_MIN, S_MIN, T_MIN = 0.60, 0.66, 0.76, 0.74
COMBO_MIN = 0.58
ALLOW_HALF_TIME = False
ALLOW_SAME_LEAGUE = False


def _v3(x):
    return isinstance(x, (list, tuple)) and len(x) >= 3 and all(
        isinstance(v, (int, float)) and v > 1 for v in x[:3]
    )


def _vt(x):
    return isinstance(x, (list, tuple)) and len(x) >= 8 and all(
        isinstance(v, (int, float)) and v > 0 for v in x[:8]
    )


def _half(m):
    return bool(m.get("half_time") or m.get("hafu") or m.get("ht_spf") or m.get("ht"))


def _score(m):
    s = 0.20 * _v3(m.get("spf")) + 0.06 * _v3(m.get("spf_open"))
    s += 0.10 * _v3(m.get("rsp")) + 0.15 * _v3(m.get("euro_avg"))
    sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    s += 0.18 * _v3(sh.get("spf")) + 0.12 * _v3(sh.get("rsp"))
    st = m.get("stat") if isinstance(m.get("stat"), dict) else {}
    keys = ("lg_hgf","lg_agf","lg_hga","lg_aga","h_n","h_gf","h_ga","a_n","a_gf","a_ga")
    s += 0.16 * bool(st and all(st.get(k) is not None for k in keys))
    rv = m.get("review") if isinstance(m.get("review"), dict) else {}
    s += 0.08 * bool(rv.get("lineup") and rv.get("motivation"))
    try:
        d = float(m.get("euro_disp") or 0); d = d / 100 if d > 1 else d
        s -= 0.12 if d >= .18 else .06 if d >= .12 else 0
    except Exception:
        pass
    s -= .10 if m.get("_lambda_warn") else 0
    s -= .05 if m.get("_manual_warn") else 0
    s -= .22 if _half(m) else 0
    return max(0.0, min(1.0, s))


def _ok(m, mk):
    if _half(m) and not ALLOW_HALF_TIME:
        return False, "半场玩法禁入", _score(m)
    q = _score(m)
    if mk == "W":
        good, need = _v3(m.get("spf")), W_MIN
    elif mk == "H":
        sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
        good = m.get("hand") is not None and _v3(m.get("rsp")) and (_v3(sh.get("rsp")) or m.get("_h_indep"))
        need = H_MIN
    elif mk == "S":
        good = isinstance(m.get("ssp"), dict) and len(m["ssp"]) >= 10 and (m.get("stat") or _v3((m.get("sharp") or {}).get("spf")))
        need = S_MIN
    elif mk == "T":
        good = _vt(m.get("tsp")) and (m.get("ou") or (m.get("sharp") or {}).get("ou") or m.get("stat"))
        need = T_MIN
    else:
        return False, "未知玩法", q
    return bool(good and q >= need and q >= COMBO_MIN), f"quality={q:.2f}", q


_orig_analyze = _engine.analyze
_orig_combos = _engine.build_combos
_orig_stake = _engine.stake_plan


def analyze(m):
    a = _orig_analyze(m)
    m["_v588_final_quality"] = round(_score(m), 4)
    for key in ("legs", "all_legs"):
        keep = []
        for leg in a.get(key, []):
            ok, reason, q = _ok(m, leg.get("mk"))
            leg.update(quality_ok=ok, quality_score=round(q, 4), quality_reason=reason)
            if ok:
                keep.append(leg)
        a[key] = keep
    return a


def build_combos(A, attr="legs"):
    pool = [analyze(a["m"]) if not (isinstance(a, dict) and "legs" in a) else a for a in A]
    pool = [a for a in pool if a.get(attr)]
    out = []
    for c in _orig_combos(pool, attr):
        l1, l2 = c.get("L1", {}), c.get("L2", {})
        q1, q2 = l1.get("quality_score", 0), l2.get("quality_score", 0)
        if min(q1, q2) < COMBO_MIN or c.get("same_lg") and not ALLOW_SAME_LEAGUE:
            continue
        if l1.get("mk") in ("S", "T") and q1 < S_MIN - .03:
            continue
        if l2.get("mk") in ("S", "T") and q2 < S_MIN - .03:
            continue
        out.append(c)
    return out


def stake_plan(c):
    p = _orig_stake(c)
    l1, l2 = c.get("L1", {}), c.get("L2", {})
    if c.get("same_lg") and not ALLOW_SAME_LEAGUE:
        p["f_live"] = 0.0
        p["why"] += "；同联赛组合禁用"
    if l1.get("mk") in ("S", "T") or l2.get("mk") in ("S", "T"):
        if min(l1.get("quality_score", 0), l2.get("quality_score", 0)) < S_MIN:
            p["f_live"] = 0.0
            p["why"] += "；S/T仅强样本覆盖"
    return p


_engine.analyze = analyze
_engine.build_combos = build_combos
_engine.stake_plan = stake_plan
_engine.BALANCED_WH_ST = True


def main():
    return _engine.main()


def auto_pipeline(*args, **kwargs):
    return _engine.auto_pipeline(*args, **kwargs)


if __name__ == "__main__":
    raise SystemExit(main())
