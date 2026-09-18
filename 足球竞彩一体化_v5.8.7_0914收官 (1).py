#!/usr/bin/env python3
"""
================================================================================
足球竞彩【采集→研究验证→选串→投注单→赛后锁存结算】一体化主控（v5.5.2 = v5.5.1审计修复版 + 赛前首选快照锁存/赛后只读锁存结算 + 实际购票台账结算：只发编号/分析全部即端到端出单 + 国内全量影响因子采集清单 + 21点早盘 + 500元每期固定打满的容错覆盖 + 盈亏情景诚实量化 + 漏场/采集自校验修复 + 赛后对账不被赔率漂移污染）
整合来源：《数据采集口令v1.4》+《预测口令v38.4》+《选串器v4.7》，一份文件走完三阶段，人不手算λ/EV/CLV/仓位。

────────────────────────── v5.8.8 让球两源分歧并列警示 + 净胜球逐档人话分布（2026-09-15；纯呈现增量，概率/融合/校准/选注/结算口径与v5.8.7逐字节一致）──────────────────────────
 [背景] 复盘0914报告三问：①"赢球输盘"场模型τ首选让平、实盘却锚Pinnacle锐线锁让胜/让负，用户看不到分叉；
   ②用户要把-0.5/-1穿盘概率翻译成"赢1球/赢2球/赢3球…各多少"(互斥、和=100%)；③需讲清净胜球档/总进球/比分同源于一张矩阵。
 [改动1·analyze只读留档] 恒算自有矩阵让球三项 matrix_hcap=handicap(M,hand) 存 m['_hcap_matrix_raw']（选源逻辑一字未动，
   实盘仍按 SHARP_HCAP_ANCHOR 决定锚锐线还是矩阵）；有锐线时另存 m['_hcap_diverge']={两源三项/各自首选/让平概率差/客观分歧warn}。
 [改动2·专项报告 print_asian_goaldiff_report] 新增"让球方逐档(互斥,和100%)：赢5+/赢4/…/赢1◆/平/输1/输2+"，并显式写出
   让胜=赢≥n+1各档累加、让平=◆恰好赢n(=亚盘走盘)、让负=其余累加；并列打印[模型τ让胜/平/负]vs[锐线让胜/平/负](首选★)，
   首选不同或让平差≥HCAP_DIVERGE_DRAW_GAP(8pp)打⚠让平分歧。开关 HCAP_DIVERGE_SHOW/WARN，默认开；关闭逐字节回到v5.8.7展示。
 [不改] 不覆盖锐线、不改τ、不改最终hcap/hd/legs/EV/凯利/结算、不写任何样本；jc_data既有172条样本零触碰。
────────────────────────── v5.8.7 价值优先+概率兜底双档（2026-09-14；纯增量，默认开；概率/校准/结算口径与v5.8.6逐字节一致）──────────────────────────
 [需求] 多数夜晚无正EV/CLV价值注，用户希望此时仍给2注"兼顾价值与概率"的方案，并允许W胜负×H让球混搭(v5.8.6后H腿已独立可信)。
 [两档结构] S价值档(v5.8.5:EV>0+两腿CLV>0,EV降序,TOP2,正常凯利实盘) 优先；S档为空时才启动 F兜底档：
   联合命中≥FALLBACK_JP_MIN(55%)、单腿首选≥55%、组合EV≥FALLBACK_EV_FLOOR(-12%出血上限)，按联合命中降序取前2，允许v5.8.6独立H混搭。
 [资金纪律·关键] 兜底档本质是【负EV娱乐档】：强制has_edge=False→只走NO_EDGE_FUN_FRACTION娱乐小仓、打印负期望警示，
   绝不按价值实盘配仓；熔断锁仓时上层仍一票否决→空仓。0913回测：兜底TOP2为020客×022客/022客×023主(均含022,当晚022走平皆黑)，
   证明它不制造盈利、只把参与成本框在小仓。关FALLBACK_ENABLED即回到v5.8.6纯空仓。
 [权衡前沿(0913实测)] 出血上限-10%→最高联合P仅0.48；-12%→0.57；-15%→0.65：高命中与少出血不可兼得，默认取-12%折中。
────────────────────────── v5.8.6 H让球腿独立数据源硬门槛+H独立校准（2026-09-14；纯增量，默认开；W链/概率融合/S,T玩法/结算口径与v5.8.5逐字节一致）──────────────────────────
 [动机] 用户要求：让球H腿必须有独立数据源、独立校准，杜绝F3批判的"胜平负反演矩阵×让球SP"跨市场伪价值。
 [证据] 99条H样本中86条来自Pinnacle3WayH(命中48.8%)、13条matrix回退仅命中30.8%——换皮样本既不可信又污染让球校准。
 [改动] ①CONFIG：H_LEG_INDEP_GATE/H_CALIB_INDEP_ONLY/H_INDEP_SRCS；②analyze给每条H腿盖hindep戳
   (=hcap_src∈{Pinnacle3WayH} 或 模型λ来自stat/手填/锐线_model_indep)；③build_combos的_leg_trusted对H腿只认hindep，
   非独立H腿→ev_trusted=False，经既有F3链路降"⊗伪EV观察"，禁入价值榜/投注单/实盘(投资/W×H混搭同理，H腿必须独立)；
   ④load_calibrators的H校准器(含分层)只用独立源H样本训练，W口径不变。关两开关即逐字节回到v5.8.5。
────────────────────────── v5.8.5 TOP2实盘锁定（2026-09-14；纯增量，默认开；选串/概率/结算口径与v5.8.4逐字节一致）──────────────────────────
 [动机] 用户反馈引擎终选与纯命中榜/分类玩法榜不一致、候选太多易纠结。结论：实盘只认"价值+硬闸门"排序，纯命中榜仅复盘。
 [规则] ①CONFIG：TOP2_LOCK_MODE(默认True,False即回到v5.8.4)+TOP2_KEEP=2+TOP2_MIN_EV=0+TOP2_REQUIRE_CLV_POS=True；
   ②print_betting_slip在v5.8.4分层硬闸门之后再加一道：EV>0且两腿CLV>0→按组合EV降序(并列取两腿首选概率大者)→只留前2注；
   ③被滤掉的候选不打印、不落实盘额，仅后台留存校准；④熔断锁仓时上层仍直接空仓，本闸门叠加不破坏资金纪律。
   实盘一句话：价值+硬闸门后TOP2；纯命中率榜只复盘不投注。
────────────────────────── v5.8.4 锐线分层硬闸门（2026-09-14；纯增量，默认开；概率引擎/融合/校准/结算口径与v5.8.3逐字节一致）──────────────────────────
 [依据] 0913全24场真实赛果回测：W方向过[|Δλ|≥1.0且首选概率≥55%]的12场命中9=75%(Brier0.333/LL0.581)，未过12场仅5=41.7%(Brier0.710/LL1.151)。
 [改动] ①CONFIG：SHARP_STRATUM_GATE总开关(默认True,False即回到v5.8.3)+SHARP_GATE_DL_MIN=1.0+SHARP_GATE_PROB_MIN=0.55+SHARP_GATE_MARKETS=("W",)
   (H让球0913回测0场过线，维持原Pinnacle三维锐线/CLV闸门，不在此卡)；②sharp_stratum_leg_ok/sharp_stratum_combo_ok单腿/组合判定
   (非卡控玩法、缺分析、缺λ一律放行交既有闸门，不凭空杀注)；③print_betting_slip在diversify前剔除不过闸组合并逐注打印原因，
   不过闸只留程序终选/对照作观察、不进实盘单不落台账实盘额；④decision_briefing硬闸门清单同步显示；⑤stake_plan纵深拦截，上层漏过滤也f_live=0。
────────────────────────── v5.8.3 攻守风格画像+ρ自适应+分层校准+双变量泊松预留（2026-09-13；默认配置与v5.8.2逐字节等价，已验证analyze全数值字段最大差=0）──────────────────────────
 [背景] 代码审查后按"λ与各玩法概率校准应充分考虑主客实力悬殊/均衡、双方攻强守弱·攻守平衡·攻弱守强组合"落地四项能力。
   共同铁律：纯增量、每个新能力都有总开关且【默认关闭/等价】、参数靠真实赛果LOO定标(样本不足只提示不硬开)、main新调用try自容错。
 [零风险清理] ①删 asian_ladder 未使用死变量lo(pyflakes归零)；②删真失效常量 EARLY_CONF_DROP(早盘已改为不降置信等级)、
   SCORE_MAX_GOAL(已被REG_SCORE 16合规格取代)；③给 BUY_HOUR/DEFAULT_CONF/BANK_COEFF/DYN_COEFF/AUX_RECORD_KEYS/FREE_SOURCE_LADDER
   统一标注[文档性·不接线/内嵌资料]，说明逻辑已内联、改常量不生效，避免日后误调。
 [建议②·攻守风格画像(默认开,纯只读不改概率)] style_profile(lh,la,m)：L1纯λ层给实力差档strength(对齐GAP_NEAR/BIG=均衡/胶着/悬殊)、
   节奏档tempo(总λ<2闷战/2-3中性/>3对攻)、强弱倾向favor、综合style_class、分层键stratum；L2有stat时 attack_defense_indices
   复算atk/def四相对指数(口径同stat_lambda)，给主/客各自 攻强守弱·攻强守强·攻守平衡·攻弱守强… 及对阵组合matchup。analyze返回新增style字段。
 [建议①·Dixon-Coles ρ自适应(默认关RHO_ADAPTIVE_ENABLED=False)] 原ρ=-0.08全局固定；实测ρ 0→-0.15对平局率影响：均衡闷战+4.0pp、
   对攻+2.4pp、悬殊仅+1.7pp，故新增 rho_of_match：rho_eff=clip(RHO_DC×g_tempo×g_diff)，低总λ/小实力差更负、对攻/悬殊趋0。
   analyze主链(one0/最终M)与_final_matrix统一改用rho_of_match，关闭时恒=RHO_DC。新增 rho_adaptive_report 真实1X2赛果回测
   (固定ρ vs 自适应 vs 网格最优；带λW样本<15不结论)，已挂main赛后(try自容错)。
 [建议③·实力差分层校准(默认关CALIB_STRATIFY_ENABLED=False)] 赛后W/H样本统一补攒 lh/la/lt/dl/stratum；load_calibrators 按均衡/胶着/悬殊
   各训ProbCalibrator，某层样本<CALIB_STRAT_MIN_N(30)不建桶、calib_apply应用时整层回退全局(杜绝小桶过拟合/双重收缩，且桶isotonic
   仍受CALIB_W_CAP=0约束，全局isotonic证据未转正前分层也不贸然改概率)。新增 calib_stratified_report 留一LOO对比全局vs分层，挂main赛后。
 [建议④·双变量泊松(研究开关,默认关BIVARIATE_POISSON_ENABLED=False且mode='zero')] bivariate_matrix用共享共变项λ3建模主客进球正相关
   (X=X1+X3,Y=X2+X3；边际期望仍严格=λh/λa、协方差=λ3)，补独立模型/DC只修最低4格对悬殊局尾部依赖刻画不足；统一矩阵入口base_matrix，
   analyze主链改用之。双保险等价：关闭走matrix；即便开启zero模式λ3=0时bivariate_matrix逐字节返回matrix(已验证逐格差=0)；auto模式λ3由总λ
   节奏保守估计并以较弱队λ的12%封顶保证λ1/λ2非负。λ3须真实样本定标后才可启用，现阶段仅预留。
 [验证] py_compile+pyflakes(0告警)；五类对阵(悬殊主让2/均衡无盘/客让1/对攻/铁桶)在默认及三开关分别/同时开启下1X2/让球/总进球/净胜球/
   亚盘全档概率和恒=1；双泊松λ3=0逐字节=独立、边际=λh/λa、协方差=λ3；默认配置v5.8.3对v5.8.2 analyze全数值字段(含gdiff递归/全部腿概率)最大差=0。
────────────────────────── v5.8.2 净胜球分布×亚盘全档拆解（2026-09-13；纯增量只读派生层，概率引擎/融合/校准/选串/结算口径与v5.8.1逐字节一致）──────────────────────────
 [动机] 把"赢球输盘/穿盘"从定性标签升级为可计算概率：强队赢球但只赢一球(赢球输盘)的概率有多大、各档亚盘(-0.5/-1/-1.5/-1.75…)
   穿盘概率多少，原先只有官方整数让球线三项，缺净胜球粒度与亚盘半球/quarter盘视角。
 [新增1·核心函数](均为只读、不改动matrix/onextwo/handicap/tg_from_matrix/dixon_coles任何一个现有函数)：
   · goal_diff_dist(M)：最终比分矩阵按 d=i-j 聚合主队视角净胜球分布；
   · asian_handicap_breakdown(M,line,favorite)：任意亚盘线(0/0.25/…/3.0)拆 W全赢/HW赢半/P走盘/HL输半/L全输 五档(五项和=1)，
     统一判据 margin=让球方净胜-让球数：≥.5全赢/=.25赢半/=0走盘/=-.25输半/≤-.5全输；cover=W+0.5HW穿盘当量；
   · asian_ladder：围绕官方整数线n按0.25步长向两侧各扩ASIAN_LADDER_AROUND档；
   · asian_ev：亚盘十进制赔率下 EV=W(b-1)+HW(b-1)/2-HL/2-L（走盘退本=0），令EV=0反解盈亏平衡价；
   · goal_diff_snapshot：analyze一次性挂载结构(净胜球分布+让球方赢球率+恰好赢n球率+整数线W/P/L+邻近全档+形态量化)。
 [新增2·挂载] analyze()返回字典新增 gdiff 字段(开关ASIAN_GOALDIFF_ENABLED)；整数线W/P/L与现有handicap()让胜/让平/让负
   严格同源于同一最终矩阵M，因此天然守恒一致(让球对角线补偿τ后仍一致)；快照_json_safe递归兜底，兼容赛前锁存。
 [新增3·报告] print_asian_goaldiff_report 接入main()(开关ASIAN_REPORT_ENABLED，try自容错)，在单场候选后打印每场净胜球分布与亚盘全档。
 [新增4·τ分档预留] 让平对角线系数τ支持按让球档配置：新增handicap_tau_of()+CONFIG的HANDICAP_DIAG_TAU_BY(默认{}=全档2.0、
   与v5.8.1逐字节一致，验证矩阵最大差<1e-15)；赛后校准H样本补攒hand/hand_abs/lh/la字段(老样本缺省None)，为日后分让球档τ的
   赛果LOO攒原料。2026-09-13回测：市场基准下τ=1最贴合Pinnacle(市场自身低估让平)、赛果基准下τ≈2贴近实际让平38.5%，
   故默认维持2.0不分档，待让2/让3每档攒≥20-30场赛果再定，届时只改HANDICAP_DIAG_TAU_BY一个字典即可分档、无需改代码。
 [新增5·分档τ赛果回测器] tau_by_handicap_report()：按让球档用λ重建矩阵源让球三项(非样本融合probs)，对τ网格1.0..3.0做
   ①全样本最优 ②LOO留一(其余选τ评留出,与固定2.0对照) ③LOBO按batch留批同向确认；改档须过三重门：样本≥TAU_BY_MIN_N(15)、
   LOO的Brier相对改善≥TAU_BY_IMPROVE(2%)且LogLoss同向改善、LOBO不反向，任一不过维持2.0；输出可直接拷给HANDICAP_DIAG_TAU_BY
   的建议字典，已接入main赛后流程(try自容错,样本不足只提示)。老种子缺λ会被跳过并计数，v5.8.2起新样本自动带λ方可回测。
   落盘两份(均在DATA_DIR、save可关、IO失败自容错)：tau_by_handicap_log.csv滚动台账(每次赛后每档追加1行,utf-8-sig,
   Excel可看证据随样本量演变)；tau_by_handicap_latest.json覆盖写最新各档LOO指标+copy_paste_CONFIG(整行拷给HANDICAP_DIAG_TAU_BY)。
 [新增6·收敛可视化] tau_by_convergence_report()读台账画各档"建议τ/LOO改善%随样本量n"双面板PNG(Agg后端、缺matplotlib纯文本降级),
   并按状态机自动判档：不足(n<TAU_STABLE_MIN_N=30)/抖动未收敛(最近TAU_STABLE_WINDOW=3次建议不一致或临门指标不达标)/稳定维持
   (收敛回2.0=无需分档)/可定档(n≥30+近3次一致收敛到非2.0+末次改善达标+LOBO不反向)；赛后自动更新(开关TAU_CONV_AUTO_AFTER_SETTLE)。
   另配独立命令行脚本 tau_convergence_plot.py(同目录,薄封装复用引擎函数)：python tau_convergence_plot.py [台账.csv] [--png x.png]。
 [守恒与回退] 不新增任何投注/选注/校准副作用，gdiff仅作分析展示；两开关置False即逐字节回到v5.8.1行为。
────────────────────────── v5.8.1 持久化目录+队名词典扩充+stat补强固化（2026-09-10；只动数据落盘/队名匹配/研究清单三处，概率引擎与v5.8.0逐字节一致）──────────────────────────
 [升级点3·持久化] 新增统一 DATA_DIR：所有跨日积累(calib_store/elo/h2h/snapshots/journal/pinbook_history/research_todo/team_alias_todo)
   默认落"脚本同目录/jc_data/"，可用环境变量 JC_DATA_DIR 指向固定盘/网盘；首次运行自动从旧运行目录迁移已有积累(只补缺、不删原件)。
   解决"每次会话临时容器换目录、攒下的校准样本/快照丢失、越用越准无法兑现"的问题。
 [升级点2·队名] ①TEAM_ALIAS_CN2EN 补 2026-09-10 实测缺失(斯拉维亚/萨巴赫/阿马多拉/德尔瓦耶)+欧战/葡超/南美/澳超常客；
   ②_cn_en_aliases 精确未中时对中文键做"最长包含+相似度≥0.82"兜底(译名带城市后缀也能命中，仍受主客双阈值把关防错配)；
   ③新增 export_team_alias_todo：每轮仍匹配不上的中文队名自动导出 jc_data/team_alias_todo_<批次>.json，形成
   未命中→补词典→下次自动命中的闭环，自动锐线率逐晚提升。
 [升级点4·stat] 把 stat 统计λ原料从"尽力抓"升为与 euro_avg 并列的【P0必补】：RESEARCH_BRIEF写清主客拆分10字段口径与取数页、
   research_todo 分 P0/P1 并把 stat 主客战绩提为第一搜索词、AGENT_SOP/AUTO_RUN_SOP 同步强调"缺stat=只能纯市场λ复读赔率"。
 [升级点5·种子样本] 内置用户累计52条历史校准样本(2026-09-08/09,W26/H26,均已过isotonic 15场门槛)：本地库缺失即用它起步、
   已存在则按(batch,no,market)去重补齐,用户赛后真实样本优先、永不被种子覆盖;新装环境一上来W/H即进入渐进保序校准而非从零收缩。
 [升级点6·赛后自动备份] 新增 auto_backup_data_dir + 开关 AUTO_BACKUP_AFTER_SETTLE：赛后锁存结算/台账/校准样本全部写完后,
   自动把 jc_data 打包成带时间戳zip到脚本旁 jc_backup/(与 jc_data_backup.py 同口径),免手动backup;异常不影响主流程。
 [升级点7·启动自动接续] 新增 auto_restore_on_start + 开关 AUTO_RESTORE_ON_START(默认开)：main最开头、装载校准器之前,自动从
   jc_backup 找最新备份【只补缺、绝不覆盖】还原到 jc_data——新会话/新容器把备份zip放进 jc_backup(或用环境变量 JC_BACKUP_DIR 指定目录)
   即可免手动restore;已有更新数据永不被旧备份覆盖,只还原 jc_data/ 数据部分、拦截../越界,找不到备份静默跳过,任何异常不阻断启动。
────────────────────────── v5.8.0 让球对角线补偿（2026-09-10；基于70条样本+三批次36场离线定参，只动比分矩阵层，采集/融合/选串/结算/校准层口径不变）──────────────────────────
 [问题诊断] 让球H两源都系统性低估让平：实际让平频率43%，Pinnacle3WayH只给26%、自有DC矩阵更只给22.5%；Pinnacle源21场13个错单里9个是漏让平。根因=独立泊松假设进球独立，低估"净胜球差恰好等于整数让球线"的聚集（让1球时1-0/2-1/3-2整条对角线），Dixon-Coles只修了0-0/1-0/0-1/1-1四格，没修让球对角线。
 [升级] 在比分矩阵M生成后(dixon_coles+draw_boost)、派生四玩法前，对满足 i-j==-hand 的让平对角线格子乘经验抬升系数τ后全矩阵归一。τ=2.0由35场LOO选定(让平从22%抬到~36%，留余地不过冲)。这是源头修：W/S/T与matrix源H全部来自M因此同步受益；Pinnacle源H仍直取锐线不变(遵守锐线优先，不随意改外部源)。
 [离线验证(三批次36场)] 固定τ=2.0：W命中66%→69%、Brier0.463→0.441、LogLoss0.817→0.786；H Brier0.647→0.624、LogLoss1.071→1.029(Pinnacle源不变、matrix源14场改善)；比分S命中14%→17%；总进球T命中14%→29%。四玩法概率仍严格守恒(同源于一个M)。关HANDICAP_DIAG_BOOST_ENABLED即逐字节回退v5.7.9。
 [边界] 让2/3球仅6场样本不足，统一用τ=2.0(标注待回测)；无让球盘(hand=None)的场次不补偿、保持v5.7.9。τ为可调常量，攒更多样本后可重估。
────────────────────────── v5.7.9 概率校准层正则化增强（2026-09-10；基于累计70条校准样本，只动校准层，采集/融合/选串/结算口径逐字节不变）──────────────────────────
 [问题诊断] v5.7.8硬PAVA在35场小样本上过拟合：留一法W对数损失0.875→2.914、13~18/35场输出近0/1极端概率；留批交叉验证下校准反而略劣于原始概率。
 [四项升级] ①PAVA块拟合改Beta(α=1)拉普拉斯先验平滑(h+α)/(n+2α)，消除0/1硬输出；
   ②isotonic进入阈值30→15，但[15,60]场按w=(n-15)/45与原始概率渐进混合、60场才全信，消除阈值硬跳变，小样本轻校准；
   ③输出统一过[0.02,0.98]概率地板再归一，杜绝押反方向时对数损失灾难；
   ④新增 calib_quality_report：留一法交叉验证 raw vs 校准后 Brier/LogLoss/命中/极端率+首选翻转净对错，长期客观监控校准是否真有效。
 [定参依据] LOBO留批+LOO留一双交叉验证：选定α=1/full_n=60/floor=0.02，两套验证下LogLoss均不劣化且略降、零极端、方向翻转以改对为主。关CALIB_ENABLED即回到v5.7原始概率。
────────────────────────── v5.7.8 接入RapidAPI「SportScore(sportscore1,Tipsters同账号)」赛前结构化补强（2026-09-08；只补不覆盖，概率/选串/结算口径不变）──────────────────────────
 [接入·同一把RAPIDAPI_KEY] host=sportscore1.p.rapidapi.com(实测根路径即API根,官方文档的/api/v1前缀在本账号404)。
   ①在线H2H:/teams/{h}/h2h-events/{a}取历史交锋→按本场主队视角算胜平负/不败率,≥3场才填6_h2h(样本不足不凑维),
     优先级 AI研究>SS在线>本地自积累;实测当晚4场达标自动点亮、不达标7场诚实留空。
   ②预测阵容:/events/{id}/lineups取预测阵型/预计首发/is_confirmed(临场约1小时转官宣);【注意免费档missing_players
     伤停名单为空,伤停仍需豆包联网检索回填,不能省】。
   ③积分战意:/seasons/{id}/standings-tables取总排名+fields.points_total真实积分(顶层points不可靠,已修正),辅助战意。
   全程双阈值队名对齐(实测11/11全对齐)、单端点失败只跳过不崩、SS_MAX_CALLS=70请求上限省免费额度(实测每晚约30次)。
 [终审修正] start_at显式按UTC解析(旧版按容器本地时区)、ko_ts去掉多减的8h(旧版两处偏置恰好抵消才未错配,换部署环境会暴露);
   积分取fields.points_total(顶层points为不可靠值);杯赛刚开赛0分排名不展示防误导;删只写不读的h2h_raw冗余;ss_info/h2h_online锁入快照供复盘。
────────────────────────── v5.7.7 新增免费自积累H2H交锋维6_h2h（2026-09-08；在v5.7.6基础上只加一维多存储，概率/选串/结算口径不变）──────────────────────────
 [新增·H2H交锋往绩维] 与Elo同构的免费自积累引擎:键复用Pinnacle英文规范名,本地h2h_store.json持久化,赛后结算自动追加
        交锋、赛前取近10次(≈近5赛季)按"本场主队视角"换算胜平负与不败率(主客互换时正确翻转,单元测试验证),≥3次才填
        6_h2h(样本不足不凑维、不编造);AI研究在dims["6_h2h"]回填时只补不覆盖。odds-api1为纯赔率聚合无h2h端点,在线h2h
        需另订同账号RapidAPI产品(如sportscore1),故默认走"赛后自积累+AI联网回填"双免费通道。实测AI回填后10/11场C→B(5维/辅2)。
────────────────────────── v5.7.6 OddsPortal百家欧均 + 免费自算Elo维 + 市场锚伤停门控（2026-09-08；概率口径更稳、置信度可累积）──────────────────────────
 [新增1·OddsPortal百家欧均] 复用已订阅的odds-api1(357书商聚合),在原pinnacle/betfair-ex锐线之外增拉10家主流软盘书商,
        跨7-8家(≥4家才有效,不足留空不编造)算术均赔→euro_avg、各家去水概率跨家标准差→euro_disp并填辅助维5_dispersion;
        软盘共识只做低抽水全球主锚/离散风控,绝不进sharp锐线主锚。实测10/11场取到、离散0.3%-0.8%(高度一致)。
 [新增2·免费自算Elo维10_elo] 标准Elo(K20/主场+65/净胜球边际封顶×2),本地elo_store.json持久化;键统一到竞彩中文→
        Pinnacle英文规范名(12场映射全通过);analyze前自动挂维,主/客各≥5场才填(杜绝初始1500虚假凑维);赛后settle自动
        滚动积累、越用越准;另留elo_bootstrap_football_data()供可访问football-data.co.uk的网络一键预热(本容器503)。
 [修正3·市场锚伤停不重复计入] 新增_inj_addons门控(INJ_SKIP_IF_MARKET_ANCHOR=True):有市场锚(竞彩SP/市场反演λ)时伤停
        早已被price in,不再叠加inj加性球数(修正2026-09-08首跑011/012把0-0概率冲到41-51%的double-count);纯统计/纯手填
        且无市场价时伤停仍是AI独有增量、照常叠加。review伤停文字保留做方向核查/红灯。单元测试:门控ON λ1.785/OFF 1.485。
 [健壮4] AI纯review补充包在官方已移除该场(已开赛)时不再建无队名空壳;_match_en/op_resolve/b365_resolve缺队名安全跳过;
        候选等距时sorted只按时间差、不再比较dict崩溃。
────────────────────────── v5.7.5 销售批次+单场健壮（2026-09-08；在v5.7.4基础上只改两处运行边界，概率/选串/结算口径不变）──────────────────────────
 [修复1·批次锁定] collect_sporttery主批次由"按matchDate真实开球日取最早自然日"改为"按businessDate竞彩销售日锁定
        最早未开赛场所在批次"。竞彩同一销售批次=当天傍晚场(matchDate今天)+次日凌晨场(matchDate明天),旧逻辑在傍晚
        (如17点)运行时会只锁到当天傍晚仅剩的1场、漏掉同批次次日凌晨的全部主赛;新版按销售日整批保留(实测17:55正确
        纳入12场而非1场),21点/凌晨/上午各时点也均锁定正确批次。main_batch_only=False的48h全量补齐池行为不变。
 [修复2·单场健壮] 可计算场次<2(单场/全部缺λ被跳过)、组不出任何跨场2串1时,F类by_p[0]旧版IndexError直接崩溃;
        新版对空组合加保护,改为打印"不足2场、无合法跨场组合"并让维度二/终选/投注单自动留空,仍保留单场概率与快照。
 （v5.7.4已修：让球出票SP恒用竞彩rsp、Dixon-Coles两格主客λ系数归正，详见对应注释。）

────────────────────────── v5.7.3 三源锐线融合（2026-09-08 真实密钥逐接口实测；概率引擎/选串/结算一字未动，只升级采集对齐层）──────────────────────────
 [三层架构] 第一层 PinBook+巅峰投注(Pinnacle Betting Odds) 孪生host热备：两host同schema、同一把key；_pb_get按顺序故障转移
        (每host两试、空壳判定、成功host本轮优先、全败回退本地缓存)，任一源宕机自动切另一个，锐线不中断。
        第二层 OddsPapi(odds-api1,357书商)：只取 pinnacle(与PinBook同上游,做同源互验/热备) 与 betfair-ex(交易所,第二锐线,src=2)；
        三维让球取 spreads-european(主队视角整数线,与竞彩hand同号)。对齐【优先 externalProviders.pinnacleId == PinBook event_id 精确对齐】
        (同场实测两源ID完全相等=1635267534,绕开队名模糊匹配=零张冠李戴风险)，无ID才退回队名双阈值+开赛时间消歧。
        同源互验：两路Pinnacle 1X2最大相对差>OP_XDIFF_WARN(5%)告警、>OP_XDIFF_DROP(15%)该场OddsPapi弃用(主客颠倒时差必达100%,天然拦截错套)。
        第三层 Bet365 Inplay(bet365-api-inplay)：软盘共识/偏离度参考，结果只挂 r["soft_b365"]，【绝不进sharp主锚、不改λ/EV】；
        并做主客热门方向交叉校验(锐线热门与软盘热门相反即告警人工核对)。48h窗口过滤(列表跨2个月)、剔isCyber虚拟赛与U系/女足/预备队。
 [时间对齐修复] _op_time_pick 目标epoch改为 replace(tzinfo=UTC).timestamp()，修复机器为UTC+8时naive .timestamp()被本地时区二次+8h、
        导致OddsPapi/Bet365队名匹配后全部因"时差8h>3h"被误弃的隐患(PinBook走naive对naive不受影响；ID精确对齐也不受影响)。
 [让球链] 手动 > PinBook-3WayH(同event_id) > OddsPapi-Pinnacle(spreads-european,同hand整数线) > OddsPapi-BetfairEx > AI；
        全部要求与竞彩hand同整数线、主队视角同号，仍禁止-h反线兜底、禁止2维亚盘合成3维。
 [审计输出] assemble末尾新增"三源对齐审计表"：每场列出 PinBook(event_id)/OddsPapi(ID精确|队名|✗)/Bet365/让球是否取到/同源价差，逐场可追溯。
 [结论·四问] ①一一对齐：竞彩每场→PinBook按队名+时间消歧、OddsPapi再按Pinnacle原生ID精确锁死同一场，Bet365队名+时间，三层互相印证；
        ②汉译：程序从不做英→中翻译，方向恒为"竞彩中文名→词典英文别名→与各源英文键比对"，未入词典且双阈值不过=拒绝套线，绝不猜译；
        ③主客：各源均实测 participant1/team1=主队，按位置对齐不换序，让球统一主队视角，另有热门方向交叉校验兜底；
        ④赔率：只取全场十进制、1X2按主/平/客固定槽位、让球按竞彩hand整数线取同线、同源价差与主客翻转双拦截。

────────────────────────── v5.7.2 RapidAPI锐线防错配加固（2026-09-08 用真实密钥+当晚23场实测；概率引擎/选串/结算一字未动）──────────────────────────
 [实测背景] 内置RapidAPI「PinBook Odds」BASIC密钥实测可达(550次/月,每次运行耗2次)：markets返回1045事件、special-markets
        返回1140条3-Way Handicap；1140条让球盘100%以【主队视角】命名(主让为负)，与竞彩hand符号一致；足球feed主队字段100% Team1。
 [fix-1·剔非正赛] PinBook feed含 resulting_unit=Corners(角球盘86个)/Bookings(牌盘27个) 的同名1X2，旧版混入候选池；
        现只收 resulting_unit=="Regular" 的正赛。
 [fix-2·同队名多赛事消歧【核心】] 实测同晚23场竞彩中4场(布鲁日/皇马/里尔/波尔图)在PinBook同时存在【成年欧冠】与
        【UEFA Youth League U19青年欧冠】两条同对阵事件，旧版只按队名取dict最后一条→把U19赔率错套成年场(如布鲁日主胜取1.917而正赛2.54)。
        现：全部候选留 PB_CAND 并打青年/女足/预备队标记，assemble 时 _pb_resolve 按竞彩开赛时间(北京↔UTC)就近选同一场，
        时间差>3h/两候选同近/仅青年候选 → 宁可不套锐线也不套错；让球3WayH只取与选定赛事 event_id 一致的三项。
 [fix-3·让球方向] 删除 lines.get(-h) 反线兜底(实测99%赛事±线并存,-h是相反的另一个盘口,错套会翻转让胜/让负方向)。
 [fix-4·开盘注入主客] inject_open_sharp 删除 (客,主) 反向键兜底(旧版遇两回合/男女足同名会对调主胜/客胜概率)。
 [fix-5·队名词典] TEAM_ALIAS_CN2EN 支持一中文对多英文别名(list)；修正 国际米兰→Internazionale(Pinnacle实际名,
        旧值"Inter Milan"匹配分仅0.56会漏配)、济州SK；按当晚实测+主流联赛补到约260队。
 [fix-6·匹配透明化] 旧版只打印被拒匹配、采用场看不到对应了哪个英文赛事；现每场打印 ✓中文→英文键+匹配分，
        任一侧模糊命中(分<1.0)额外打⚠提示人工核对(近似队名如Man City/Man Utd=0.81的残余风险靠此+时间消歧双保险)。
 [结论] 程序从不做"英文→中文翻译"，方向恒为【竞彩中文名→查词典得英文→与PinBook英文键比对】；未入词典的中文名
        规范化后为空、必被双阈值(两侧各≥0.6且总≥2.2)拒绝，不会乱套；主客按位置对齐(主对主/客对客)，不交换顺序。

────────────────────────── v5.7.1 相对 v5.7 的增强（P1概率校准层 + P2自动攒样本闭环 + 实盘第二确认；全部总开关可一键回退）──────────────────────────
 [P2·赛后自动攒校准样本] 新增 parse_results_text 健壮解析"001 1:0；002 1:1…"自然语言比分(兼容全角/分号/空格/短横、不误吃日期)；
        collect_results_sporttery 预留官方完场比分自动通道(当前环境403即优雅降级,绝不编造)；赛后三通道取比分优先级
        POST_RESULTS手填 > RESULTS_TEXT比分串 > 官方自动。结算时 calib_append_from_snapshot 把每场【W=1X2/H=让球 三方向锁存概率+实际方向】
        自动写入 calib_store.json，按(批次,编号,市场)去重、跨日累积；赛前快照补锁 hcap/tg/概率源，旧快照无hcap则用λ矩阵重算降级。
 [P1-4·概率校准层(手写PAVA,零依赖)] ProbCalibrator 对W/H各做三方向 one-vs-rest：样本≥CALIB_MIN_ISOTONIC(30)上保序回归isotonic、
        不足则向1/3温和收缩(强度随样本衰减)，治"锁高自信却打出反向"(如005锁主胜77%实际客胜)；analyze最终对外 one/hcap 统一过 calib_apply，
        关 CALIB_ENABLED 即逐字节回到 v5.7。赛后 calib_report 滚动输出样本量/命中/Brier/当前校准方式。
 [P1-5·实盘第二确认(收盘线不反向)] inject_open_sharp 用本批次最早PinBook快照注入开盘去水概率(18/21/临场多跑即逼近开盘→临场,零额外请求)；
        stake_plan 实盘闸门新增：腿方向去水概率相对早盘反向移动≥LINE_REVERSE_PP(8pp)则拦实盘，缺早快照不拦(不误伤)。
 [健壮性修复] 修掉让球段局部变量 _rsp 被锐线覆盖、导致"竞彩有让球但锐线无对齐3WayH"时让球腿崩溃的隐患(票面锐线优先、竞彩兜底)。
 闭环：赛前出单(概率已被历史样本校准)→赛后结算自动攒样本→样本≥30自动升级为isotonic→下一晚出单更准；样本库是纯JSON可人工审计。

────────────────────────── v5.5.2 相对 v5.5.1 的增强（概率引擎与 settle_review 口径一字未改，只加"锁存层+实际票结算"）──────────────────────────
 [G·赛前快照锁存·堵赛后重算漂移(审计级)] 旧版赛后结算 settle_review 的首选来自"赛后重跑 analyze 现场重算"，若赛后重新采集，
        竞彩SP/欧赔/λ已漂移(甚至收盘)，重算出的"首选"已不是21点购彩那一刻真正推荐/购买的首选→命中率回测会被结果污染。
        现新增：赛前出单后 save_pre_match_snapshot 把每场【四玩法首选腿(mk/选项/方向d/概率p/即时SP)+hand+λ+1X2】、
        程序终选注、v5.5投注单(每注金额/总赔)、实际购票台账，序列化成 snapshots/snapshot_批次_北京时间戳.json(同时写latest指针)；
        JSON可人工审计、跨容器不丢(替代易失的pkl)，且永不覆盖、每次赛前出单都留档。
 [H·赛后只读锁存结算] settle_from_snapshot / settle_snapshot_file：赛后填 POST_RESULTS={编号:"主:客"}即只【读取赛前快照】对账，
        全程不调 analyze、不重算λ/首选——赛后赔率怎么变都不影响"当时推荐了什么"。输出：四玩法锁存首选命中、程序终选注兑现盈亏、
        v5.5投注单(真实金额)兑现、实际购票台账返还/净盈亏、胜平负锁存概率vs实际校准。main检测到POST_RESULTS非空即进入赛后模式、
        绝不覆盖快照；POST_RESULTS为空的赛前流程才写新快照。旧 settle_review(当场重算快速回测)与 calibrate_from_history 保留不变。
 [I·实际购票台账] 每日输入区新增 ACTUAL_TICKETS：录你真金白银买下、可能与程序推荐不完全一致的票(每注腿[(编号,玩法,选项)]+本金+
        票面理论返还)，赛后按同一套规则结算"实际买的票中没中、亏赚多少"(对应021-024那两张48/52元娱乐覆盖单)，而非只算"程序推荐准不准"。
────────────────────────── v5.5.1 全面代码审计后的修复（对7项审计问题逐条落地）──────────────────────────
 [A·取错批次/漏场bug·二次彻底修复] 竞彩接口 businessDate=【销售轮次日】(如"周日021"),matchDate=【真实开球自然日】,
        凌晨场销售日比开球日早一天。旧代码(含v5.5.1第一版)用 businessDate+matchTime 当开球时间,会把当天凌晨临近开赛的
        周末轮场次(021-024)误判成"昨天已开赛"过滤掉,反错取成后一天凌晨的下一批(006-009)。现统一:①kickoff_dt一律以
        matchDate为准(businessDate仅销售分组标识,缺失才回退);②北京时间统一_bj_now_naive;③auto默认锁定"最近开球日"主批次
        (21点只买次日凌晨那批,不与后天凌晨场跨天串关),指定后批编号时自动从48h全量池补齐;④按真实开球时间升序。
        matchStatus接口滞后(已开赛仍Selling)一律不信,只认开球时间。
 [B·每期固定打满] cover_staking/proportional_staking 取整后用_fill_to_bankroll把2元零头回填，每期合计严格=500(无优势娱乐档=100)。
 [C·每日最优性增强] 投注单候选池从"终选5注"扩大到 build_combos('all_legs') 全结果合格池(ρ<0.3/同源可信/概率≥阈值/有SP,去重),
        容错覆盖在大池上优选；并真正输出被多注共用的腿(该腿错多注同黑)。
 [D·采集信息自校验] 新增百家欧赔overround越界校验：正常1.03-1.10，>12%提示复核是否取成单家、>20%或<1判定采集错误直接不参与融合,
        防止豆包抓错的欧赔污染概率；配合既有双锚交叉/市场统计背离/λ边界/队名匹配阈值/quality_audit构成多层采集准确性校验。
 [E·健壮性] slip_scenario加2^n枚举上限保护；清理死变量；异常输入fuzz(缺spf/rsp/tsp/euro非法/极端λ/单场/空池)全部不崩。
 [F·校正闭环补全] AGENT_SOP增"赛后回流"步：次日豆包自动查比分填res→calibrate_from_history反推ρ/总λ乘子+命中率/Brier校准、
        settle_review核对推荐注盈亏。★赛前只有内部一致性校验、赛后比分回流才是检验与提升真实命中率的唯一客观途径。

────────────────────────── v5.5 相对 v5.4 的升级（面向"只发编号、零手填、21点买、每晚500元、要自带金额"）──────────────────────────
 [U1·全自动入口] auto_pipeline(nos='all'|['001',...], ai_json_text=..., bankroll=500)：用户只发编号或"分析全部"，豆包按 AGENT_SOP
        (show_sop()打印)自动 采集骨架→浏览器补全量数据→回填→选串→直接打印【今晚投注单】，全程不再向用户追问、无需改源码。
 [U2·国内全量数据清单] RESEARCH_BRIEF 扩为 A赔率市场族/B实力状态族/C环境外部族 共20项(欧赔均值离散/初盘移动/亚盘大小球/必发成交/
        凯利指数/大众热度/xG/Elo/H2H/伤停首发/赛程密度/战意/裁判/天气/默契球/突发)，逐项给来源、取不到填null、禁止编造。
 [U3·21点购彩] 购彩时刻统一为21:00(买次日00:30-07:00凌晨赛,距开球约3.5-10h,几乎全部判早盘,早盘仓位×0.7的逻辑不变)。
 [U4·500元容错覆盖投注单(核心)] cover_staking 求"命中任意1注即净赚≥5%"的金额分配(数学充要条件Σ(1/sp)≤1/(1+g),自动取最大可覆盖
        注数、金额取整到2元)；覆盖不可行时按凯利/概率比例分配。print_betting_slip 输出每注金额+中了可得+合计。
 [U5·盈亏情景诚实量化] slip_scenario 枚举2^n命中组合，给出"中0/1/2…注"各自概率与净盈亏、全黑概率、当晚盈利概率、期望ROI；
        并做单场复用上限分散(SLIP_MATCH_CAP)与同联赛相关提示。★用数字讲清:覆盖买法只提高"小赚"概率,无法做到每晚必盈,
        约1/3的晚仍会全黑,长期期望由各注EV决定(全负EV时任何分配都不能扭亏)——这是数学事实,不是程序不够努力。
 [U6·空仓诚实化] 无任何满足[有SP/联合概率≥18%/ρ<0.3/同源可信]的注时,投注单明确建议空仓,绝不为了"每晚都要买"硬凑注。

────────────────────────── v5.4 相对 v5.3.6 的升级（面向"零人工·国内网络·21点前买次日凌晨赛"现实约束）──────────────────────────
 [现实] 用户不手填/不核验任何数据、国内无Pinnacle、21:00前买00:30-07:00凌晨赛(拿不到临场首发与临场赔率)。实测国内网络：
        竞彩官方webapi(带Referer)稳定可达；500/澳客/足彩网首页可达但欧赔页JS反爬→由豆包【浏览器】读取；Pinnacle/Betfair不可达。
 [G1·全球共识主锚(核心提精度)] 新增 euro_avg=[主,平,客]百家欧赔平均赔率(overround≈1.05,远低于竞彩1.13)。概率从"复读竞彩"改为
        三源融合：竞彩去水(权.25,仅作价格/情绪)+欧赔均值去水(权.55,主锚)+统计泊松(权.20)，再以共识概率反推一致比分矩阵
        (总λ仅允许±5%微调,守住比分/总进球锚定)。竞彩只作为下注价格，首次具备相对竞彩定价的独立判断(可纠正竞彩方向偏差)。
 [G2·欧赔静态价值] 无Pinnacle时，用欧赔均值去水公允赔率对竞彩SP算静态价值(仅同源胜平负W,门槛+5%严于锐线CLV+3%)；
        让球/比分/总进球不跨源定价(无对应市场锐线则clv=None)，杜绝v5.3.6批判的跨源伪EV。
 [G3·21点早盘模式] ①自动按businessDate+matchTime算距开球小时,>3h判早盘；②早盘用"预计首发(expected)+伤停已核/战意数学形势"
        即可过H10语义核查(block类真风险仍绝不放宽,全部留warn)；③早盘风险统一由仓位折扣EARLY_STAKE_MULT=0.7承载,不重复降置信；
        ④置信分层:真锐线要求S+、仅欧赔准锐线放宽到S且S+封顶S；⑤初盘→即时SP漂移>12%降置信。
 [G4·离散度风控] euro_disp百家欧赔离散度>15%降档、>30%降到C禁实盘(庄家严重分歧不投)。
 [G5·采集与指令] collect_sporttery补businessDate/matchTime(早盘判定)/排名/队名全称/matchId；RESEARCH_BRIEF重写为21点早盘版,
        明确要求豆包用浏览器读500/澳客/足彩网的"百家平均欧赔+离散度"与近10场战绩填euro_avg/stat,取不到填null不编造。
 [天花板·务必知悉] 竞彩返奖率约88.5%(overround1.13)，平均每注相对全球公允价先亏约11.5%；只有竞彩某方向SP比欧赔均值公允价
        高出门槛(锐线+3%/欧赔+5%)才是真价值，这种机会稀缺，多数场次最诚实结论仍是"空仓/极小娱乐"。本版让方向不劣于全球共识、
        并只在出现真实背离价值时出注，但【不能把负期望变成稳定盈利】，请长期用≥30场Brier/ROI校准、量力而行。
────────────────────────── v5.3.6 相对 v5.3.5 的精度修复（8场已赛样本回归：修复前1X2命中3/8、Brier0.710差于均匀猜测0.667）──────────────────────────
 [精度诊断] 回测发现：当一场只有竞彩胜平负spf(+avg)、没有stat统计原料/锐线/手填λ时，λ由spf反演、再聚合回1X2，
            模型概率≈spf去水概率(逐场仅差1.4~4.2pp)，泊松外壳不产生任何超越市场的信息增量；而竞彩overround≈1.13，
            自锚买回天生EV≈-11.5%。本版四处修复，让"模型到底有没有独立判断、EV是不是真的"一眼可见、且不再自欺：
 [F1·总λ不被1X2带偏] 无大小球ou/总进球tsp锚时，退化反演总λt【固定=avg】(走invert_fixed_lt)，不再用1X2-KL在
            avg±20%网格里自由漂移总λ(旧版常把λt顶到±20%边界，如avg3.0→λt3.6，污染比分/总进球，这两类首选命中仅25%)。
 [F2·关闭拍脑袋平局增强] draw_boost(平赔3.20-3.50就把对角线×1.10)改为CONFIG开关DRAW_BOOST_ENABLED，【默认False】；
            它作用在已≈市场的矩阵上纯属加噪(回归：关闭后Brier0.710→0.706)。需要旧行为设True即可。
 [F3·跨源伪EV识别·关键] 纯市场反演时矩阵只是spf的重参数化：用它给【让球/比分/总进球】(SP来自rsp/ssp/tsp=另一个市场)
            算EV会因两套抽水/定价不同而结构性虚高(旧主推荐榜首SP4.33却标EV+24.6%、命中仅28.8%)。本版：
            ①每场标 indep=概率是否有独立来源(stat统计/手填λ/锐线sharp任一)；②非胜平负腿标cross=跨市场；
            ③一注若含"跨市场腿 且 该场无独立概率来源"→ev_trusted=False，维度二硬过滤直接剔除、主推荐把它降到
            '⊗伪EV观察'层不得进前列；④无锐线且无独立概率时主推荐明确输出"无正EV注、最优动作空仓"，不再用伪+EV误导。
 [F4·信息增量透明化] 体检表逐场打印 模型1X2 vs spf去水 的最大偏差igain与【=市场/有增量】标签；体检后给汇总：
            平均信息增量、有独立判断场数，并对带res已赛场【首页即显示】累计1X2命中率与Brier(不用翻到末尾校准)。
 [F5·校准闭环轻增强] calibrate_from_history维持"≥30场才建议改参数防过拟合"，建议文案直接给出可粘贴的CONFIG赋值行。
 [边界·务必知悉] 本版只修"自我欺骗/总λ污染/伪EV排序"，不改变足球固有方差：没有stat/锐线等独立数据时模型在数学上
            仍不可能跑赢市场——此时最诚实的输出就是"=市场、EV为负、空仓"。要真正提精度必须喂stat统计原料或Pinnacle锐线。
────────────────────────── v5.3.4 相对 v5.3.3 的审核修复（终审挑刺后）──────────────────────────
 [P1修复] ①assemble_matches 合并字段表 QUAL 漏 review——导致"官方自动采集+豆包回填"混合模式下
		        AI语义核查review丢失、H10永远拦实盘；已补入，混合模式review正确合并。
	        ②战意 dual 兼容真布尔/字符串'true'/1/'是'等(_as_bool)，AI回填不再因类型被误判单确认；
	        ③战意核心门槛收紧为【严格双确认】：仅数学形势(单确认)不再算核心已核查，dual与math缺一即core_done=False、H10拦实盘；
	        ④首发status扩同义词(ok/available/齐整/已出/官宣)、未识别天气词不再静默当晴(转warn提示人工核对)、
	          默契球/突发红灯缺note时补默认拦截理由；amer_to_dec补"≥100整数固有歧义"注释。
 [桥接]   新增 run_from_ai_text(ai_json,sharp_text) 一键喂入豆包结果直接跑全流程(免改CONFIG)。
────────────────────────── v5.3.3 相对 v5.3.2 的升级（均经实测回归）──────────────────────────
 [λ校正] ①λ校正链全程留痕并输出『λ校正链审计』：统计λ(联赛标准化+贝叶斯收缩)/竞彩ttg锚/锐线ou锚/
	        双锚交叉偏差/融合权重/战意伤停天气调整前→最终λ，逐场可核；②竞彩ttg锚与锐线ou锚【双锚交叉校正】，
	        偏差≥0.35留痕告警；③市场+统计融合权重随统计样本量自适应(样本≥10用0.6/0.4，6-9用0.75，<6用0.85)，
	        市场/统计背离≥30%红标强制以市场为准；④λ合理性边界校正(总λt>5.6/单队>3.7/触底→告警)；
	        ⑤新增总λ系统校准乘子 LAMBDA_TLT_MULT(由滚动回测反推)。
 [AI语义] 把原需人工的『首发/战意双确认/默契球/突发利空/临场天气』交给联网AI在 review 块核查(必带src证据)：
	        程序自动量化(天气→节奏系数、核心缺阵→加性λ、战意→乘子)，并新增实盘闸门 H10——
	        REQUIRE_AI_REVIEW_LIVE=True 时，任一场AI语义红灯、或首发/战意核心未核查，该场相关注单 f_live=0 禁止实盘。
 [锐线通道] 境外博彩站程序无法直连(JS渲染+地区限制)，新增 SHARP_TEXT 紧凑文本通道：豆包读回页面后每场一行
	        『编号|spf 主 平 客|ou 线 大 小|rsp ...』，美式(-138/+301)/十进制混写自动换算、按编号回填(只补不覆盖)；
	        _coerce_record 对 sharp 美式赔率自动转十进制。
 [滚动校准] 新增 calibrate_from_history：对带 res 的已赛场用最大似然反推 Dixon-Coles ρ 与总λ乘子，
	        并给1X2命中率/Brier/概率分桶校准表(合成600场验证可找回真值)；只建议、样本≥30才改参数防过拟合。
────────────────────────── v5.3.2 相对 v5.3.1 的修复（均经实测回归）──────────────────────────
 [P0-1] 零配置不再崩：新增『竞彩总进球ttg8档SP反推总λt』，官方接口只有spf+ttg也能自动反演λ；
        main 对 analyze 逐场容错，坏场跳过并汇总，绝不再因单场缺λ整场 Traceback 退出。
 [P0-2] parse_ai_json 修复比分SP键：ssp 的 "i-j" 字符串键统一转 (i,j) 元组键，纯AI_JSON路径比分EV不再全丢。
 [P0-3] SP缺档保护：spf/rsp 不足3项、tsp 不足8档一律按 None 安全降级，不再 IndexError。
 [P1-4] 组合层联合凯利上界 = min(玩法硬顶, 逐注分数凯利 f_theory)，联合配仓不再把1/8分数凯利放大数十倍。
 [P1-5] 概率口径统一：EV/Kelly/联合配仓一律用未折减的真实联合概率 pc_raw=p1*p2；同联赛×0.95 只作
        维度一保守展示与排序(RHO_SAME_LG)，不再污染期望值，消除"仅联赛标签不同EV就差4.7pp"。
 [P1-6] 手填λ不再跳过六步：同样叠加⑤战意⑥伤停；并与市场去水概率做一致性校验、超阈值亮⚠(不静默)。
 [P2-7] 终选5注不再纳入 ρ≥0.3 自己判禁组的注(移除 allow_block 漏洞)。
 [P2-8] 英文队名模糊匹配加严：主客两队都要命中、打印『中文→英文+匹配分』对照供人工确认，防张冠李戴。
 [P2-9] AUTO_COLLECT 联网失败/当日无场时回退内置示例并明示，不再直接 return 空跑。
 [P2-10]全局EV终选缓存 stake_plan（20万组合提速）；并将『全局EV最优模式』升为【主推荐】，角色覆盖降为参考。
 [新增] settle_review 赛果结算：填 res("x:y")即自动核对各玩法首选/终选注命中，做命中率回测小结(主动校正基础)。
 [新增] 美式赔率↔十进制换算 amer_to_dec（Pinnacle加拿大镜像等给美式线时用）；RESEARCH_BRIEF 更新为实测可达源。
──────────────────────────────────────────────────────────────────────────────────

【零手填闭环·怎么用这一份文件】
  第1步 把本文件 §A 的 RESEARCH_BRIEF（show_brief()可打印）整块发给【联网AI】：
         它自动联网检索(国内官网优先+全力找Pinnacle级锐线)、交叉验证、深度研究12维/伤停/战意，
         并按本文件 MATCHES schema 直接输出一个 JSON 数组——你不用手填任何字段。
  第2步 把联网AI输出的 JSON 粘贴到本文件 §B 的 AI_JSON 里(或存成文件用load_ai_file读取)，运行本文件；
         parse_ai_json 自动解析成 MATCHES，引擎自动完成 λ六步/概率/CLV/置信度/EV/G5/分型/组合枚举。
  第3步 看输出：自动验证红绿灯(可算项全检)+赛前人工语义清单+终选5注+凯利仓位，只对 f_live>0 的注实盘。

【能力边界·务必知悉(为何不写成.py自动爬Pinnacle)】
  · 联网检索/读网页/语义研究由【联网AI】执行：Pinnacle等境外锐线站在大陆常规网络不可直连(被墙+强反爬+地区限制)，
    程序化直爬既不稳定也不合规(本运行环境的安全策略同样拦截对博彩站的直连)；故"全力搜锐线"由联网AI走
    Pinnacle→Betfair→OddsPortal三级回退，不可达时用国内可及的等值锐利盘(必发成交价/澳门/平博等)并标注来源。
  · 本.py是【确定性精算引擎】：只做可复算的数学(λ六步/概率/CLV/EV/凯利/组合最优化)，不内置脆弱且无法验证的爬虫；
    拿不到的数据一律 None 并自动降级(无锐线→实盘=0、仅纸面)，【绝不编造赔率/数据】。
  · 首发官宣/默契球/突发利空等语义判断无法代码化，由 §D 赛前人工清单逐项勾选，核心4维任一缺失即不进实盘。

————————————————————以下为选串精算引擎(源自选串器v4.7,数学逻辑零改动)————————————————————
每日竞彩 2串1 选串器（方案甲 v4.7 六分类·两维度·终选5注·凯利仓位·全采集接入·场次分型·λ六步全自动校准）
——严格对齐《足球预测口令 v38.4》第十五章「单日2串1组合最优筛选(v37.3)」、§9.1λ六步与§9.3凯利七步
——v4.7：λ六步全自动(无需人手算λ)——照采集卡填原始数即可：①统计λ(stat:Atk/Def联赛标准化+9.4小样本收缩k12/升班马k20)
         →②统计乘弱增量(weak_coeff默认1.0,连乘封顶0.90-1.15)→③市场λ(ou大小球锚总λ→1X2定差,有锐线0.6竞彩+0.4锐线)
         →④0.6市场+0.4统计融合(背离>15%以市场为准并标注)→⑤结构性战意motiv分乘各队λ→⑥加性伤停inj球数最后叠加。
         优先级：手填lh/la > 六步融合 > 纯市场/纯统计；体检表标注每场λ链路。12维定级/G5/EV本就内建自动。
——v4.6：大小球两步反演(半球/整数/split盘自动锚总λ,免手填avg)。
——v4.5：场次分型(Δλ×方向一致性→悬殊一致/相近分歧/均衡过渡)与选法指引(只加提示不改概率/排序)。
——v4.4：①输入结构完整承接《数据采集口令v1.4》单场数据卡全部字段(见每日输入区字段模板,无需另做对照表)；
         ②锐线三级(Pinnacle/Betfair/OddsPortal)自动去水→每腿CLV；③置信度按核心4+辅助8自动定级(S+/S/A/B/C)；
         ④资金档/L连输/W连赢/回撤DD/赛季系数接入凯利动态层；⑤实盘比例f_live在“双锐线+每腿CLV≥+3%+S+”全过闸时才非0；
         ⑥新增采集完整度/置信度回显与输入格式校验。缺省(简填)行为与v4.3完全一致：无锐线→恒A级、实盘=0。
——v4.3：①终选5注每注给“占总资金比例”(全凯利×A级1/8→玩法/单场/组仓封顶,与本金绝对额无关)；
         ②终选全局降相关(共用1条已用腿扣5pp当量,单腿最多绑2注)；③维度二补Pareto非支配标注+极端点
——v4.2：从三榜自动收敛“终选5注(核心-卫星)”，并如实计算当晚整体盈利概率(不保证单次盈利)
——v4.1：维度二价值榜改全结果枚举(32076组合)，修正首选枚举漏掉次选高价值结果的盲区
================================================================================
【相对 v3 的升级（概率引擎一字未改，只重构“选腿/枚举/排序”层）】
  1. 六分类：A=胜平负2串 / B=让球2串 / C=比分2串(单选) / D=总进球2串(单选)
     / E=混合2串(跨玩法·必须跨场) / F=全场最高(A-E最优)。旧版“策略A/B”被A、B替代，
     旧版“比分top4复式(每场4选、2串16注)”违反红灯㉘“三选复式禁止”，v4改为C类单选2串。
  2. 两维度：维度一【中奖概率最高】结构性合法组合按 P_combo=p1×p2 降序，全局Top5+六分类各Top1，
     EV/ρ/无锐线只“标注可投状态”不提前剔除（v38.4 15.5.3）；维度二【概率×价值最优】硬过滤
     组合EV≥0.15+单腿EV(胜负平让球≥0.08/比分总进球≥0.05)+ρ上限<0.3 后按 S=P×EV 降序Top5。
  3. 合规红线落地：⑤同场不同玩法禁串（枚举只跨场）；⑩比分只取每队≤3球的16个常规比分；
     ⑪总进球只取0-4档；⑱ρ按“联赛×玩法×方向”对照ρ值表取上限，上限≥0.3判⚠️禁组；
     同联赛概率保守×0.95（≠ρ，二者并列显示）；半全场③禁飞不计算。
  4. 比分/总进球SP为可选字段(ssp/tsp)：采集口令P0已要求全量采集；不填则C/D/E只算命中概率、
     不算EV（与旧版一致），维度二在无SP/无锐线时如实输出空，绝不凑数。
【概率引擎顺序（v38.4 §9.2，不可调换）】独立泊松矩阵 → Dixon-Coles 只修(0,0)(0,1)(1,0)(1,1)
   四格并全矩阵归一（ρDC默认−0.08，CONFIG设RHO_DC=0退化为独立泊松）→ 平局增强(平赔3.20-3.50
   区间对角线×1.10)并再次归一 → 最后才聚合1X2/让球/比分/总进球。DC/增强后总进球只能矩阵聚合。
【口径边界】本工具无锐线输入：按v38.4，无锐线仅G8/G9单关可投、禁串关，故本器所有2串1在补到
   锐线并满足每腿CLV≥+3%前，一律是“概率参考/纸面跟踪”，不是投注建议（红灯㉚）。单日实盘≤2组(红灯⑫)。
【每日用法】只改下方 MATCHES：字段同v3，另可选 ssp={(i,j):SP}比分SP、tsp=[0..7+共8档]总进球SP。
================================================================================
"""
import itertools
import json
import math
import re
import os as _ospath
import os.path as _pp
import shutil as _shutil
from datetime import datetime, timedelta
from math import exp, factorial, log

# ==================== v5.8.1 统一持久化数据目录 DATA_DIR（跨会话/跨容器不丢的关键）====================
# 旧版所有跨日积累文件(calib_store/elo/h2h/snapshots/journal/pinbook_history/research_todo)都写在"当前运行目录",
# 每次豆包会话若是全新临时容器、运行目录又不固定，攒下的样本/快照就会丢，"越用越准"无法兑现。
# 现统一落到固定 DATA_DIR：①默认=本脚本所在目录/jc_data（跟着文件走，最稳）；
# ②设环境变量 JC_DATA_DIR 可指向固定挂载盘/网盘同步目录（多容器共享同一积累）；③首次运行自动迁移旧目录已有文件。
def _resolve_data_dir():
    d = (_ospath.environ.get("JC_DATA_DIR") or "").strip()
    if not d:
        try:
            base = _pp.dirname(_pp.abspath(__file__)) if "__file__" in globals() else _ospath.getcwd()
        except Exception:
            base = _ospath.getcwd()
        d = _pp.join(base, "jc_data")
    d = _pp.abspath(d)
    try:
        _ospath.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d
DATA_DIR = _resolve_data_dir()
def _data_path(*parts):
    """统一拼出 DATA_DIR 下的持久化路径，并惰性确保其父目录存在。"""
    p = _pp.join(DATA_DIR, *parts)
    try:
        _ospath.makedirs(_pp.dirname(p), exist_ok=True)
    except Exception:
        pass
    return p
def _bootstrap_data_dir():
    """预建子目录 + 从旧版当前工作目录平滑迁移已有积累文件(只在新位置缺失时拷贝，绝不覆盖、不删除原件)。
    注意：join/abspath/exists/isdir/isfile 走 os.path(=_pp)，makedirs/getcwd/listdir 才是 os 顶层。"""
    for _sd in ("snapshots", "journal", "pinbook_history"):
        try:
            _ospath.makedirs(_data_path(_sd), exist_ok=True)
        except Exception:
            pass
        try:
            dst = _data_path(_sd)
            src = _pp.join(_ospath.getcwd(), _sd)
            if _pp.isdir(src) and _pp.abspath(src) != _pp.abspath(dst):
                for _fn in _ospath.listdir(src):   # 目录内逐文件补缺，避免 copytree 对已存在目录报错
                    _s, _d = _pp.join(src, _fn), _pp.join(dst, _fn)
                    if _pp.isfile(_s) and not _pp.exists(_d):
                        _shutil.copy2(_s, _d)
        except Exception:
            pass
    for _sf in ("calib_store.json", "elo_store.json", "h2h_store.json"):
        try:
            dst = _data_path(_sf); src = _pp.join(_ospath.getcwd(), _sf)
            if (not _pp.exists(dst)) and _pp.isfile(src) \
                    and _pp.abspath(src) != _pp.abspath(dst):
                _shutil.copy2(src, dst)   # 保住升级前已攒的校准/Elo/H2H样本
        except Exception:
            pass
_bootstrap_data_dir()

def auto_backup_data_dir(tag="自动备份", verbose=True):
    """v5.8.1：把 DATA_DIR 整体打包成带时间戳 zip（默认存到 DATA_DIR 同级的 jc_backup/，与 jc_data_backup.py 同口径）。
    赛后结算+样本入库后自动调用，固化当晚全部记忆；自包含(函数内 import zipfile)、不依赖外部脚本、任何异常都不影响主流程。
    返回 zip 路径或 None。注意输出目录在 DATA_DIR 之外，walk 不会把备份自身递归打进去。"""
    import zipfile as _zf
    try:
        if not _pp.isdir(DATA_DIR):
            return None
        files = []
        for _dp, _, _fns in _ospath.walk(DATA_DIR):
            for _fn in _fns:
                if _fn.endswith((".tmp", ".lock")):
                    continue
                files.append((_pp.join(_dp, _fn), _pp.relpath(_pp.join(_dp, _fn), DATA_DIR)))
        if not files:
            return None
        out_dir = _pp.join(_pp.dirname(DATA_DIR), "jc_backup")   # 与独立备份脚本默认输出一致
        _ospath.makedirs(out_dir, exist_ok=True)
        zp = _pp.join(out_dir, "jc_data_%s_%s.zip" % (tag, datetime.now().strftime("%Y%m%d_%H%M%S")))
        with _zf.ZipFile(zp, "w", _zf.ZIP_DEFLATED) as _z:
            for _ap, _rel in files:
                _zi = _zf.ZipInfo.from_file(_ap, _pp.join("jc_data", _rel))
                _zi.compress_type = _zf.ZIP_DEFLATED; _zi.flag_bits |= 0x800   # UTF-8 文件名，中文不乱码
                with open(_ap, "rb") as _fh:
                    _z.writestr(_zi, _fh.read())
        if verbose:
            print(f"  · v5.8.1 已自动备份积累数据：{zp}（{len(files)}个文件）。请下载/回传留存；"
                  f"新会话用 jc_data_backup.py restore 接续即可无缝衔接。")
        return zp
    except Exception as _e:
        if verbose:
            print(f"  · 自动备份跳过(不影响主流程)：{_e}")
        return None

# ---- v5.8.1 启动自动接续：新会话/新容器自动从 jc_backup 最新备份把记忆补回来（只补缺、绝不覆盖；开关见下方 CONFIG）----
def _backup_search_dirs():
    """备份zip候选目录：环境变量 JC_BACKUP_DIR > 脚本旁 jc_backup > DATA_DIR 同级 jc_backup。"""
    dirs = []
    _e = _ospath.environ.get("JC_BACKUP_DIR", "").strip()
    if _e:
        dirs.append(_pp.abspath(_pp.expanduser(_e)))
    try:
        _base = _pp.dirname(_pp.abspath(__file__)) if "__file__" in globals() else _ospath.getcwd()
    except Exception:
        _base = _ospath.getcwd()
    dirs.append(_pp.join(_base, "jc_backup"))
    dirs.append(_pp.join(_pp.dirname(DATA_DIR), "jc_backup"))
    out = []
    for d in dirs:
        if d and d not in out:
            out.append(d)
    return out

def _latest_backup_zip():
    """在候选目录里找最新备份：正常赛后/手动备份优先于'恢复前安全备份'，同类按修改时间取最新。返回路径或None。"""
    cands = []
    for d in _backup_search_dirs():
        if not _pp.isdir(d):
            continue
        for z in _ospath.listdir(d):
            fp = _pp.join(d, z)
            if z.lower().endswith(".zip") and _pp.isfile(fp):
                cands.append((z, fp))
    if not cands:
        return None
    def _rank(name):
        if "恢复前安全备份" in name:
            return 2                      # 中间安全网，最低优先
        return 0 if ("赛后自动备份" in name or "备份" in name) else 1
    cands.sort(key=lambda t: (_rank(t[0]), -_pp.getmtime(t[1])))
    return cands[0][1]

def auto_restore_on_start(verbose=True):
    """新会话启动时自动接续记忆。安全策略（保证绝不旧盖新）：
    ①只把 zip 里【DATA_DIR 当前缺失】的文件补回，已存在的文件一律跳过，因此持久盘/本会话已更新的数据永不被覆盖；
    ②只还原 jc_data/ 数据部分，_script_snapshot/ 程序快照不动；③拦截 ../ 越界路径；
    ④找不到备份/无需补缺则静默跳过；⑤任何异常都不影响主程序启动。"""
    if not AUTO_RESTORE_ON_START:
        return None
    import zipfile as _zf, shutil as _sh
    try:
        zp = _latest_backup_zip()
        if not zp:
            return None
        n = skip = 0; base_abs = _pp.abspath(DATA_DIR)
        with _zf.ZipFile(zp, "r") as _z:
            for info in _z.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                if name.startswith("_script_snapshot/"):
                    continue
                rel = name[len("jc_data/"):] if name.startswith("jc_data/") else name
                if not rel:
                    continue
                target = _pp.join(DATA_DIR, *rel.split("/"))
                t_abs = _pp.abspath(target)
                if not (t_abs == base_abs or t_abs.startswith(base_abs + _pp.sep)):
                    continue                             # zip-slip 防护
                if _pp.exists(target):
                    skip += 1; continue                  # 只补缺、绝不覆盖
                _ospath.makedirs(_pp.dirname(target), exist_ok=True)
                with _z.open(info) as _src, open(target, "wb") as _dst:
                    _sh.copyfileobj(_src, _dst)
                n += 1
        if verbose and n:
            print(f"  · v5.8.1 启动自动接续：从最新备份 {_pp.basename(zp)} 补缺还原 {n} 个文件"
                  f"（已有 {skip} 个文件保持不动、未覆盖任何现有数据）。")
        return zp if n else None
    except Exception as _e:
        if verbose:
            print(f"  · 启动自动恢复跳过(不影响运行)：{_e}")
        return None

# ------------------------- CONFIG（每日可调阈值） -------------------------
RHO_DC = -0.08        # Dixon-Coles参数(通常-0.15~-0.05；设0=独立泊松)
# ---- v5.8.3 建议①：ρ按"总λ节奏×主客实力差"自适应（默认关闭=全局RHO_DC，逐字节等价v5.8.2）----
# 机理：ρ刻画低比分(0-0/1-0/0-1/1-1)相关；均衡闷战(低总λ+小实力差)低分聚集更强应更负，
#       对攻/悬殊局比分更接近独立应趋0。实测ρ 0→-0.15对平局率：均衡闷战+4.0pp、对攻+2.4pp、悬殊仅+1.7pp。
# 公式：rho_eff = clip(RHO_DC * g_tempo * g_diff, RHO_ADAPT_LO, RHO_ADAPT_HI)
#   g_tempo = 1 - SLOPE_LT*(lt-ANCHOR)（lt低于锚→g>1更负；高于锚→g<1趋0）
#   g_diff  = 1 - SLOPE_DL*dl（实力差越大越趋0）。系数须用 rho_adaptive_sweep 真实赛果LOO定标，勿拍脑袋。
RHO_ADAPTIVE_ENABLED = False   # 总开关：False=恒用RHO_DC(等价旧版)；True=按对阵类型自适应
RHO_ADAPT_LT_ANCHOR = 2.5      # 总λ中性锚(此节奏下g_tempo=1)
RHO_ADAPT_SLOPE_LT = 0.22      # 总λ每偏离锚1，g_tempo变化量(低λ增强/高λ减弱)
RHO_ADAPT_SLOPE_DL = 0.18      # 实力差|λh-λa|每+1，g_diff减弱量
RHO_ADAPT_G_MIN, RHO_ADAPT_G_MAX = 0.5, 1.6   # 综合乘子g上下限(防极端)
RHO_ADAPT_LO, RHO_ADAPT_HI = -0.16, 0.0       # rho_eff取值边界(不超过DC经验区间、不允许变正)
# ---- v5.8.3 建议④：双变量泊松(共享共变项λ3,建模主客进球正相关)【研究开关·默认关闭】----
# 独立泊松假设主客进球相互独立；双变量泊松 X=X1+X3、Y=X2+X3，λ3=共同节奏项(>0=两队倾向同时多进,刻画对攻共振,
# 补独立模型/Dixon-Coles只修最低4格对"悬殊局尾部依赖"刻画不足)。这是概率引擎核心替换,启用即改变全部下游口径、
# 且λ3必须真实样本定标,故双保险默认等价：①ENABLED=False ②即便开启,默认mode='zero'使λ3=0、数学上严格退化为独立泊松。
BIVARIATE_POISSON_ENABLED = False
BP_LAMBDA3_MODE = "zero"     # zero=λ3恒0(=独立泊松)；auto=按总λ节奏给保守正相关(经验式,待bp回测定标后再用)
BP_LAMBDA3_MAXFRAC = 0.12    # λ3≤此比例×较弱队λ，保证 λ1=lh-λ3、λ2=la-λ3 非负
BP_AUTO_MIN_LT = 2.6         # auto：总λ超过此值才开始给正相关(低比分闷战不共振)
BP_AUTO_COEF = 0.06          # auto：λ3=COEF×max(0,lt-MIN_LT)，再被MAXFRAC封顶
# v5.3.6 F2：拍脑袋平局增强开关。旧版平赔3.20-3.50就把所有平局格×1.10，作用在已≈市场的矩阵上纯属加噪
# (8场回归Brier0.710→0.706)，故【默认关闭】；要复现v5.3.5旧行为设True。是否抬平局应交给≥30场滚动校准而非写死。
DRAW_BOOST_ENABLED = False
DRAW_BOOST_LO, DRAW_BOOST_HI, DRAW_BOOST_MULT = 3.20, 3.50, 1.10  # 仅在DRAW_BOOST_ENABLED=True时生效
# v5.3.6 F3：跨源伪EV识别。一场概率若仅由竞彩spf反演(无stat/手填λ/锐线)，则其让球/比分/总进球腿的raw-EV
# 因"概率来自spf、SP来自另一市场"而结构性不可信；igain低于此值即判"模型=市场、无独立判断"。
IGAIN_FLAT = 0.05
# ==================== v5.4 21点早盘模式 + 国内多源欧赔均值融合 ====================
# 现实约束：用户零人工、靠豆包联网取数；国内无Pinnacle；21点前买次日凌晨赛(距开球常3-9h,拿不到临场首发/临场赔率)。
# 核心提精度思路：把概率主锚从"竞彩自己(抽水13%)"换成"低抽水的百家欧赔均值全球共识(overround≈1.05)"，
# 竞彩只作为【下注价格】；三源(竞彩去水/欧赔均值去水/统计泊松)融合出共识概率，再反推一致比分矩阵。
EARLY_BET_MODE = True      # 启用21点早盘适配
EARLY_HOURS = 3.0          # 距开球>3h即按早盘处理(21点买00:30-07:00凌晨赛典型落在3.5-10h,几乎全部判早盘)
# v5.8.3清理：旧 EARLY_CONF_DROP(早盘置信降档)已删除——现行设计早盘不降置信等级(等级只反映数据/价值源质量),
#   早盘信息不完整统一由 EARLY_STAKE_MULT 仓位折扣承载(见confidence()注释),避免降档+卡门+减仓三重惩罚。
EARLY_STAKE_MULT = 0.70    # 早盘凯利仓位折扣(信息不完整,仓位再打7折)
ODDS_DRIFT_WARN = 0.12     # 初盘spf_open→当前spf相对漂移>12%=已显著变盘,早盘降置信
FUSE_W_CN = 0.25           # 三源融合权重:竞彩去水(高抽水市场,只作价格与情绪参照)
FUSE_W_EURO = 0.55         # 百家欧赔均值去水(全球共识、低抽水,主锚,权重最高)
FUSE_W_STAT = 0.20         # 统计/模型泊松(stat战绩或手填λ,独立判断)
# ==================== v5.7 锐线主锚（配 PinBook/Pinnacle 密钥后启用；总开关 False=逐字节回退 v5.6 三源行为）====================
# 赛后实证(v5.6批次2026-09-07)：PinBook已9/9全自动拿到1X2+3WayH+多线totals，但v5.6只拿它锚λt/算CLV，
# 没把【Pinnacle去水概率本身】当主锚，概率主锚仍是豆包手填euro_avg；且让球用自有矩阵推(5/9走让平、锁的让胜全灭)、
# 总进球只被单主盘锚(0/9、λt高估)。v5.7对症：有真锐线时改以Pinnacle去水为概率/让球/总λ主锚，竞彩只作下注价格。
SHARP_ANCHOR_ENABLED = True   # v5.7总开关。False=完全回退v5.6；True=检测到sharp.spf的场启用下列锐线主锚逻辑
SHARP_W_1X2   = 0.70          # P0-1 有锐线时1X2四源权重:Pinnacle去水(最锐,主锚)
EURO_W_V57    = 0.15          #   百家欧均去水(次共识)
CN_W_V57      = 0.10          #   竞彩去水(高抽水,仅保留少量情绪/价格信息)
MODEL_W_V57   = 0.15          #   自有泊松模型(stat/λ,独立增量)；缺源时fuse_probs按在场源动态归一,无需手动配平
SHARP_HCAP_ANCHOR = True      # P0-2 让球首选/概率直取Pinnacle 3WayH去水三项(精确对齐竞彩hand那条线)；缺则矩阵兜底
SHARP_HCAP_MARGIN = 0.03      # P0-2 锐线方向优势门：3WayH最大两方向概率差<3pp=方向不明,不硬覆盖矩阵(回退矩阵并标模糊),防0.x pp级脆弱argmax把对的改错
# ============ v5.8.6 H让球腿独立数据源硬门槛 + H独立校准（2026-09-14；默认开；W链/概率融合/S,T玩法口径不变）============
H_LEG_INDEP_GATE = True       # H腿必须独立数据源：概率直取Pinnacle3WayH锐线让球，或模型λ来自stat/手填/锐线(_model_indep)；
#                             # 仅由竞彩胜平负spf(+欧赔1X2)反演矩阵得到的H腿=跨市场换皮，ev_trusted=False禁入价值/实盘(降⊗伪EV观察)
H_CALIB_INDEP_ONLY = True     # H校准器只用独立源(hcap_src=Pinnacle3WayH)H样本训练，剔除matrix回退换皮样本，防污染让球校准
H_INDEP_SRCS = ("Pinnacle3WayH",)   # 历史样本中视为"让球市场独立"的hcap_src白名单(老样本未存_model_indep,以记录在案的来源为准)
SHARP_OU_MULTI = True         # P0-3 用Pinnacle多档totals(1.5/2.5/3.5...)联立拟合总λt,替代单主盘锚,治总进球系统性偏差
OU_MULTI_LO, OU_MULTI_HI = 1.25, 4.25   # 参与联立拟合的大小球线范围(剔除1.25以下/4.25以上极端线,样本太少反噪)
# ===== v5.7.1 P1+P2 自动校准闭环（赛后自动攒样本 → 概率校准层；实盘第二确认）=====
CALIB_ENABLED = True          # 概率校准层总开关：对1X2/让球最终概率做经验校准(False=恒等,完全不校准,逐字节回到v5.7)
# —— v5.7.9 校准正则化增强（70条样本 LOBO留批+LOO留一 双交叉验证定参；治v5.7.8硬PAVA小样本过拟合：
#    实测35场硬PAVA的W对数损失0.875→2.914、13~18/35场输出近0/1极端概率）——
CALIB_MIN_ISOTONIC = 15       # 进入正则化保序回归的样本下限(原30→15)；小样本不再硬切,改由blend权重w做轻校准
CALIB_ISO_FULL_N = 60         # 样本达60场时blend权重w=1(全信保序)；[15,60]之间w线性0→1平滑过渡,杜绝阈值跳变
CALIB_W_CAP = 0.00            # 2026-09-13按75场/玩法 LOO留一+LOBO留批双交叉扫参(0/0.15/0.30/0.45/0.67/1.0)再定档：
                              #   任一正CAP都使Brier/LogLoss单调劣化(W:LOO +0.004~+0.042、LOBO +0.009~+0.071；H同向更差)；
                              #   CAP=0.30在LOO的W命中+2.7pp(2次翻转全改对)在LOBO(新比赛日泛化,更相关)中增益消失，H在LOO净翻错2次。
                              #   结论：75样本下isotonic仍在拟合噪声，封顶到0=isotonic混合关闭(w=0,等价原始概率;<15场的shrink分支仍保留)。
                              #   复评窗口：W/H各≥120场或台账≥30注时扫参重估，证据转好再逐步放开。回退：改回0.30。
CALIB_ISO_PRIOR = 1.0         # PAVA块Beta(α,α)拉普拉斯先验伪计数:拟合率(h+α)/(n+2α),消除0/1硬输出(α=1标准平滑)
CALIB_FLOOR = 0.02            # 单方向概率地板(同时封顶1-地板)后再归一:杜绝近0概率押反方向时的对数损失灾难
CALIB_SHRINK_BASE = 0.35      # 样本<CALIB_MIN_ISOTONIC时向1/3均匀收缩强度；随样本线性衰减,到下限归零
# ---- v5.8.3 建议③：按实力差分层校准（默认关闭=全局一个校准器，逐字节等价v5.8.2）----
# 机理：全局isotonic假设"预测p→经验频率"对所有对局同一映射；但悬殊局模型常过度自信、均衡局易低估平局,
#       单一映射会把不同实力差层的偏差互相抵消。按 style_profile 的 stratum(均衡/胶着/悬殊)各训校准器。
# 防过拟合铁律：某层样本<CALIB_STRAT_MIN_N 整层回退全局(绝不对小桶再做一次shrink造成双重收缩)；
#       且桶isotonic同样受 CALIB_W_CAP 封顶约束——在全局isotonic都因证据不足关闭(CAP=0)的当下,分层也不会贸然改概率。
CALIB_STRATIFY_ENABLED = False  # 总开关：False=恒走全局；True=优先该实力差层校准器、不足回退全局
CALIB_STRAT_MIN_N = 30          # 每实力差层进入分层校准的最小样本(比全局15更严,分层更易过拟合)；不足回退全局
CALIB_STORE = _data_path("calib_store.json")   # 校准样本库(v5.8.1统一落DATA_DIR持久目录,跨日累积/跨会话不丢,(批次,编号,市场)去重,可人工审计)
# ===== v5.8.0 让球对角线补偿（比分矩阵源头修；治让球两源系统性低估让平）=====
HANDICAP_DIAG_BOOST_ENABLED = True   # 总开关：对让球线对应的净胜差对角线(i-j==-hand)做经验抬升后归一；False=逐字节回退v5.7.9
HANDICAP_DIAG_TAU = 2.0              # 让平对角线抬升系数(τ>1抬升让平)。70条样本+36场LOO选定2.0(让平22%→~36%，留余地不过冲)；可调，攒样本后重估
# v5.8.2 τ分让球档配置：默认{}=所有让球档统一用HANDICAP_DIAG_TAU(=2.0，与v5.8.1逐字节一致)；要分档时按【让球数绝对值】覆盖，
#   如 {2:1.5,3:1.5}=让2/让3用1.5、让1仍2.0。2026-09-13 22场τ敏感性回测：以Pinnacle市场为基准τ=1最贴合(市场本身低估让平)，
#   以真实赛果为基准τ≈2把让平从~22%抬到~36%、贴近种子库实际让平38.5%(Pinnacle源42.9%)；让2/让3分档赛果样本不足(个位数)前
#   不贸然分档，先靠校准样本补攒hand/λ(HANDICAP_DIAG_TAU_BY改值即分档)，每档≥20-30场再做分档LOO定τ。
HANDICAP_DIAG_TAU_BY = {}
# v5.8.2 分让球档τ【真实赛果】回测参数（tau_by_handicap_report 用；只在赛后样本上评估，不参与赛前概率）
TAU_GRID_BY_HCAP = [round(1.0 + 0.25 * k, 2) for k in range(9)]  # τ候选网格 1.0..3.0 步长0.25
TAU_BY_MIN_N = 15            # 每让球档最少赛果样本：低于此只报告不建议改τ(让2/让3小样本防过拟合)
TAU_BY_IMPROVE = 0.02        # LOO下最优τ相对固定2.0的Brier【相对】改善需≥2%且LOBO不反向才建议改档(噪声容限)
TAU_BY_HCAP_LOG_CSV = _data_path("tau_by_handicap_log.csv")     # v5.8.2 分档τ回测滚动台账：每次赛后追加一行/档快照(utf-8-sig,Excel可审计,看证据随样本演变)
TAU_BY_HCAP_LATEST = _data_path("tau_by_handicap_latest.json")  # v5.8.2 分档τ最新建议：覆盖写(各档LOO指标+可直接拷给HANDICAP_DIAG_TAU_BY的suggest)
TAU_STABLE_MIN_N = 30         # 收敛定档最低赛果样本：某档n≥此值才允许判"可定档"(低于只继续攒,让2/让3尤其要等)
TAU_STABLE_WINDOW = 3         # 最近连续K次赛后回测的建议τ一致才算收敛(抗在改档阈值附近来回抖动)
TAU_BY_HCAP_CONV_PNG = _data_path("tau_by_handicap_convergence.png")  # v5.8.2 各档τ随样本量收敛图(读台账出图)
TAU_CONV_AUTO_AFTER_SETTLE = True  # 赛后跑完分档τ回测后是否自动更新收敛轨迹文本+PNG(False=只手动用tau_convergence_plot.py)
# ===== v5.8.2 净胜球分布 × 亚盘全档拆解（纯增量；只从【最终比分矩阵M】只读派生，不改任何现有概率/融合/选注口径）=====
# 用途：把"赢球输盘/穿盘"从定性标签升级为可计算概率——由M按净胜球d=i-j聚合，再对任意亚盘线(0/0.25/.../3.0)
#       拆出 W全赢/HW赢半/P走盘/HL输半/L全输 五档。整数线W/P/L与现有handicap()让胜/让平/让负严格同源守恒。
ASIAN_GOALDIFF_ENABLED = True   # analyze()是否挂载 gdiff(净胜球分布+让球方关键概率+官方整数线邻近亚盘全档)；False=逐字节回到v5.8.1
ASIAN_REPORT_ENABLED  = True    # main()是否打印"净胜球分布×亚盘全档"专项报告(只读取analyze已算好的gdiff，不重复计算)
ASIAN_LADDER_AROUND   = 2       # 围绕官方整数让球线n，按0.25步长向两侧各扩几档(=2→覆盖 n-0.5 到 n+0.5 共5档)
ASIAN_DIFF_LO, ASIAN_DIFF_HI = -3, 4   # 专项报告里净胜球分布只打印[LO,HI]区间(尾部概率极低不刷屏)
# ===== v5.8.8 让球"模型τ口径 vs Pinnacle锐线"分歧并列警示 + 净胜球逐档人话分布（纯呈现增量，不改概率/选注/结算）=====
# 背景：实盘H首选默认锚Pinnacle3WayH(SHARP_HCAP_ANCHOR)，而自有矩阵经让平对角线τ=2抬升后让平常更高；两源在
#   "赢球输盘"场会出现"模型选让平、锐线锁让胜/让负"的分叉。默认只并列展示+打警示，绝不覆盖任一源、不改最终hcap。
HCAP_DIVERGE_SHOW     = True   # 专项报告是否并列打印[模型τ让胜/平/负] vs [Pinnacle锐线让胜/平/负]，各自首选标★
HCAP_DIVERGE_WARN     = True   # 两源首选方向不同，或让平概率差≥下阈值时，是否打⚠让平分歧警示
HCAP_DIVERGE_DRAW_GAP = 0.08   # 让平概率分歧警示阈值(8pp)：|模型让平-锐线让平|≥此值即提示(即便首选碰巧相同)
HCAP_TIER_WIN_MERGE   = 5      # 净胜球逐档分布：让球方赢≥此球数合并为"赢N+球"档(尾部概率极低不刷屏)
HCAP_TIER_LOSE_MERGE  = 2      # 净胜球逐档分布：让球方输≥此球数合并为"输N+球"档
LINE_MOVE_CONFIRM = True      # P1-5 实盘第二确认：腿方向的Pinnacle去水概率相对早快照反向移动≥阈值则拦实盘
LINE_REVERSE_PP = 0.08        # 反向移动阈值(去水概率8pp)：如当前锁主胜但其去水概率较早盘掉≥8pp=资金在反向,拦
AUTO_RESULTS_ENABLED = True   # P2 赛后先尝试自动拉完场比分；官方接口不可达时优雅降级到POST_RESULTS/比分串解析
AUTO_BACKUP_AFTER_SETTLE = True  # v5.8.1 赛后锁存结算+校准样本入库后，自动把 jc_data 打包成带时间戳zip(脚本旁jc_backup/)，免手动备份；设False关闭
AUTO_RESTORE_ON_START     = True  # v5.8.1 启动时自动从 jc_backup 找最新备份【只补缺、绝不覆盖】还原(新会话免手动restore)；备份所在目录可用环境变量 JC_BACKUP_DIR 指定
RESULTS_TEXT = ""             # 可选：直接粘贴"001 1:0；002 1:1…"自然语言比分，赛后自动解析(与POST_RESULTS等价)
EURO_EDGE_MIN = 0.05       # 无Pinnacle时:竞彩SP相对欧赔均值fair的静态价值门槛(比锐线CLV+3%从严,取+5%)
EURO_DISP_WARN = 0.15      # 百家欧赔离散度>15%=公司分歧偏大,降置信一档
EURO_DISP_BLOCK = 0.30     # 离散度>30%=严重分歧/数据可疑,该场腿禁入实盘
EURO_OV_WARN = 0.12        # 百家欧赔均值overround(Σ1/赔率-1)>12%=可能不是均值/混入高抽水,降置信并提示复核
EURO_OV_BAD  = 0.20        # >20%或<0=采集明显错误(抓错公司/录入错),该euro不参与融合,防错误数据污染概率
# ==================== v5.5 每晚固定额度·容错覆盖投注单（用户21点购彩、每晚约500元、要自带金额）====================
NIGHT_BANKROLL = 500.0     # 每晚购彩总额度(元)；只应用可承受的娱乐资金,不追号不补仓
BUY_HOUR = 21              # [文档性·不接线]用户购彩时刻仅作SOP提示；早盘判定按运行时now自动算,改此常量不影响逻辑
COVER_TARGET = 0.05        # 覆盖模式目标:命中任意1注即净赚≥5%(相对总投入)
SLIP_MAX_BETS = 2          # 一张投注单最多纳入的2串1注数(2026-09-12用户偏好：只推荐最优2注；旧值5)
FINAL_MAX_BETS = 2         # 终选/主推荐最多输出注数(2026-09-12用户偏好：只看最优2注；旧值5)
# ============ v5.8.5 TOP2实盘锁定（2026-09-14；用户偏好：只看价值+硬闸门后的最优2注，其余候选不打印以免纠结）============
TOP2_LOCK_MODE = True       # 总开关：True=实盘投注单只输出价值排序后前TOP2_KEEP注；其余候选后台留存校准、不打印
TOP2_KEEP = 2               # 实盘只给这几注2串1
TOP2_MIN_EV = 0.0           # 进TOP2硬门槛：组合EV>0(负期望直接淘汰)
TOP2_REQUIRE_CLV_POS = True # 进TOP2硬门槛：两腿CLV均>0(无正锐线漂移的不进实盘)
TOP2_SORT_KEY = "EV"        # 排序：组合EV降序为主；并列时取两腿首选概率大者(命中面更高)
# ============ v5.8.7 稳健兜底档（仅当TOP2价值档为空时启动；概率优先的【负EV娱乐档】，与价值实盘严格区分）============
FALLBACK_ENABLED = True      # 总开关：无正EV/CLV价值注时，是否仍给概率优先的兜底2注(False=纯空仓=v5.8.6行为)
FALLBACK_KEEP = 2            # 兜底档最多给几注
FALLBACK_JP_MIN = 0.55       # 兜底：组合联合命中率下限(概率优先,要的就是常中)
FALLBACK_LEG_PMIN = 0.55     # 兜底：每条腿首选概率下限
FALLBACK_EV_FLOOR = -0.12    # 兜底：组合EV出血上限(负EV再深不碰)；0913前沿实测 -10%最高P0.48/-12%可达0.57/-15%达0.65
# 兜底档资金：强制走既有 NO_EDGE_FUN_FRACTION 娱乐小仓(无独立优势)，熔断锁仓时上层仍一票否决→空仓
SLIP_MIN_PROB = 0.18       # 纳入投注单的2串1最低联合概率(过滤极小概率博冷,提高当晚命中面)
SLIP_MATCH_CAP = 2         # 同一场比赛在整张投注单中最多出现次数(降同场聚集/一起黑,使容错覆盖更真实)
NO_EDGE_FUN_FRACTION = 0.2 # 无任何独立价值源(无欧赔均值/锐线、全负EV)时,投注单降级为娱乐参考,额度压到当晚预算的20%
BET_UNIT = 2               # 竞彩2元/注,建议金额向下取整到2的整数倍
RHO_SAME_LG = 0.95    # 同联赛"都中概率"保守折减(v5.3.2:仅用于维度一概率展示/排序；EV/Kelly/联合配仓用真实pc_raw,不再折减)
MANUAL_LG_WARN = 0.12 # v5.3.2 手填λ模型1X2 vs 市场去水1X2 最大方向偏差≥此值→亮⚠(手填仍优先,但不再静默背离)
STAKE_UNIT = 2.0      # 每注金额(竞彩2元/注)
TOPN = 5              # 每个维度输出的最优组合数（用户要求每次给5个）
EV_COMBO_MIN = 0.15   # 维度二：组合EV硬门槛(v38.4 2串1≥0.15)
EV_LEG_WDL = 0.08     # 维度二：胜平负/让球单腿EV门槛
EV_LEG_EXOTIC = 0.05  # 维度二：比分/总进球单腿EV门槛(G6/G7)
RHO_BLOCK = 0.30      # ρ上限≥此值=可能超限，维度二硬过滤、维度一标⚠️
# ============ v5.8.4 锐线分层硬闸门（2026-09-14；依据0913全24场真实赛果回测）============
# 回测证据(W方向)：过[|Δλ|≥1.0 且 首选概率≥55%]的12场 9中=75%、Brier0.333/LogLoss0.581；
#                 未过的12场仅5中=41.7%、Brier0.710/LogLoss1.151。故把该规则固化为【实盘投注单】前置硬闸门，
#                 不过闸的腿只保留在程序终选/对照里观察，不进实盘串、不落台账实盘额。
SHARP_STRATUM_GATE = True     # 总开关；False=完全回到v5.8.3行为(逐字节等价)
SHARP_GATE_DL_MIN = 1.0       # |Δλ|=|主λ-客λ|下限，取值=GAP_BIG实力悬殊阈值(下方定义,此处用字面量避免前向引用)
SHARP_GATE_PROB_MIN = 0.55    # 腿锁存首选概率下限55%
SHARP_GATE_MARKETS = ("W",)   # 只卡胜平负W腿：H让球0913回测0场过此线，维持原Pinnacle三维锐线/CLV闸门，避免被误杀(要扩展改这里)
# v5.8.3清理：旧 SCORE_MAX_GOAL=3 已删除——比分"每队≤3球"由下方 REG_SCORE(16合规格)唯一实现,旧常量从未被读取。
TG_MAX_GOAL = 4       # 红灯⑪总进球5球+禁：只取0-4档
# ---- v4.5 场次分型：Δλ实力差 × 方向一致性（只做选法指引，不改概率/排序，全局P最优仍成立）----
GAP_BIG = 1.0         # |主λ-客λ|≥此值且方向一致=实力悬殊
GAP_NEAR = 0.8        # |主λ-客λ|≤此值=实力相近；0.8-1.0为均衡过渡灰区
# ---------------- v4.3 凯利七步仓位（v38.4 §9.3；“不考虑资金多少”=统一标准档）----------------
CONF_BASE = {"S+": 0.25, "S": 0.167, "A": 0.125}  # 第2步部分凯利:S+=.25/S=.167/A=.125(1/8)
# v4.4起置信度/资金档/动态系数均由每场字段(sharp/dims/bankroll_tier/L/W/DD/season_stage)自动算；
# v5.8.3清理标注：下列三值【仅作文档性默认值留档，代码逻辑已内联(confidence内base="A"、stake_plan用BANK_MAP.get(.,1.0)、
#   dyn_coeff内部自算)，改这三个常量不会改变运行结果】；保留是为说明"全缺省=标准档/A级/无回撤"。
DEFAULT_CONF = "A"          # [文档性·不接线]兜底置信度，实际见confidence()内联 base="A"
BANK_COEFF = 1.0            # [文档性·不接线]兜底资金档系数，实际见stake_plan的BANK_MAP
DYN_COEFF = 1.0             # [文档性·不接线]兜底动态系数，实际见dyn_coeff()
CAP_PLAY_WH = 0.02          # 第6步玩法上限:纯胜平负/让球2串1 f≤2%
CAP_PLAY_EXOTIC = 0.005     # 第6步含比分/总进球腿 f≤0.5%(G6/G7)
CAP_MATCH = 0.015           # 第7步单场硬顶:标准档1.5%(单笔2串1计入两场,就严取此值)
CAP_GROUP = 0.03            # 第5步关联组仓:标准3%
DAILY_CAP = 0.10            # 日仓上限:标准档10%
COMBO_RATIO = 0.25          # 2串1 f总和≤当日全部f总和25%(且单关≥60%)
MAX_PARLAY_LIVE = 2         # 红灯⑫单日实盘2串1≤2组
DIV_PENALTY = 0.05          # 终选降相关：每共用1条已用腿扣5pp概率当量再排序(越大越分散)
# ============ v4.4 采集表全量接入：锐线/CLV/置信度/动态仓位（对齐v38.4 §2.5/§7.2/§9.3/§11）============
SHARP_RETURN = {1: 0.98, 2: 0.97, 3: 0.96, 9: 0.95}   # ①Pinnacle/②Betfair/③OddsPortal；9=国内等值锐利盘(必发/澳门等,近似从严)
CLV_MIN = 0.03             # H2 每腿CLV≥+3%（2串1强制无例外）
AUX_DIM_KEYS = ["4_volume", "5_dispersion", "6_h2h", "8_public",
                "9_xg", "10_elo", "11_euasian"]  # 辅助7维(均为外部数据,参与置信度计数;12维编号体系不变)
# v5.7.7终审清理:原首位"3_kelly"移出——凯利是选串/资金的【内生计算输出】(见f_kelly/凯利仓位),不是要外部采集的数据维,
# 旧版它从不被填充却让每场缺项清单都误报"缺3_kelly"、且永远凑不到;凯利仍照常参与选串与仓位,只是不计入"有效数据维"。
AUX_RECORD_KEYS = ["12_referee"]  # [文档性·不接线]裁判维只采集留档(v38.4经验弱信号),不计入置信度；采集逻辑内联,改此清单不影响计数
BANK_MAP = {"small": 1.0, "std": 1.0, "5w": 0.80, "10w": 0.72}  # 资金档bank_coeff(就高不叠加)
SEASON_COEFF = {"early1_3": 0.5, "r4_5": 0.7, "summer": 0.9,
                "normal": 1.0, "last2": 0.7}     # §9.3第4步赛季系数
CONF_ORDER = {"C": 0, "B": 1, "A": 2, "S": 3, "S+": 4}  # 置信度高低序（2串1取两场较低者）

# ============ v5.5.2 赛前首选快照锁存 + 赛后只读锁存结算（堵"赛后重算首选被赔率漂移污染"的审计漏洞）============
SNAPSHOT_DIR = _data_path("snapshots")   # 赛前快照目录(v5.8.1统一落DATA_DIR；JSON可人工审计、跨会话/跨容器不丢，替代易失的内存/pkl)
SAVE_SNAPSHOT = True         # 赛前出单后是否自动锁存快照(永不覆盖，文件名带批次+北京时间戳，并刷新latest指针)
SETTLE_STAKE_UNIT = STAKE_UNIT  # 赛后锁存结算时，程序【终选注】每注本金(元)；与 settle_review 一致=2元/注

# ------------------------- v38.4 概率引擎（与v3完全一致，勿改） -------------------------
def pois(k, lam):
    return exp(-lam) * lam**k / factorial(k)


def matrix(lh, la, N=12):
    return [[pois(i, lh) * pois(j, la) for j in range(N + 1)]
            for i in range(N + 1)]


def bp_lambda3(lh, la):
    """v5.8.3建议④ 双变量泊松共享共变项λ3(≥0)。未启用/zero模式恒0(=独立泊松)；
    auto按总λ节奏保守给正相关，并以较弱队λ的BP_LAMBDA3_MAXFRAC封顶，保证边际λ仍为lh/la且λ1/λ2非负。"""
    if not BIVARIATE_POISSON_ENABLED or BP_LAMBDA3_MODE == "zero":
        return 0.0
    lh, la = float(lh), float(la)
    raw = BP_AUTO_COEF * max(0.0, (lh + la) - BP_AUTO_MIN_LT)
    cap = BP_LAMBDA3_MAXFRAC * min(lh, la)
    return max(0.0, min(raw, cap))


def bivariate_matrix(lh, la, N=12, lam3=None):
    """v5.8.3建议④ 双变量泊松联合比分矩阵(Karlis-Ntzoufras 2003)：
    P(i,j)=e^{-(λ1+λ2+λ3)} Σ_{k=0}^{min(i,j)} λ1^(i-k)/(i-k)! · λ2^(j-k)/(j-k)! · λ3^k/k!，
    其中 λ1=lh-λ3、λ2=la-λ3(边际期望仍分别=lh、la)。λ3=0 时严格退化为独立泊松 matrix。截断N×N后统一归一。"""
    lh, la = float(lh), float(la)
    if lam3 is None:
        lam3 = bp_lambda3(lh, la)
    lam3 = max(0.0, min(float(lam3), min(lh, la) - 1e-9))   # 保证λ1/λ2严格为正
    if lam3 <= 1e-12:
        return matrix(lh, la, N)     # λ3=0严格等价独立泊松(逐字节，不额外归一，与matrix同构)
    l1, l2 = lh - lam3, la - lam3
    base = exp(-(l1 + l2 + lam3))
    M = [[0.0] * (N + 1) for _ in range(N + 1)]
    for i in range(N + 1):
        for j in range(N + 1):
            s = 0.0
            for k in range(min(i, j) + 1):
                s += (l1 ** (i - k) / factorial(i - k)) * (l2 ** (j - k) / factorial(j - k)) \
                     * (lam3 ** k / factorial(k))
            M[i][j] = base * s
    return M   # 与matrix同构不在此归一(截断质量≈1)，统一交由下游dixon_coles/onextwo归一


def base_matrix(lh, la, N=12):
    """v5.8.3 概率引擎统一比分矩阵源：默认(BIVARIATE_POISSON_ENABLED=False)走独立泊松matrix、逐字节等价v5.8.2；
    开启且λ3>0才走双变量泊松。赔率反演(invert/consensus)与τ/ρ回测刻意仍用独立matrix，以隔离单一评估变量。"""
    if not BIVARIATE_POISSON_ENABLED:
        return matrix(lh, la, N)
    l3 = bp_lambda3(lh, la)
    return matrix(lh, la, N) if l3 <= 1e-12 else bivariate_matrix(lh, la, N, l3)


def _renorm(M):
    z = sum(sum(r) for r in M)
    return [[v / z for v in r] for r in M]


def onextwo(M):
    H = sum(M[i][j] for i in range(len(M)) for j in range(len(M)) if i > j)
    D = sum(M[i][j] for i in range(len(M)) for j in range(len(M)) if i == j)
    A = sum(M[i][j] for i in range(len(M)) for j in range(len(M)) if i < j)
    z = H + D + A
    return H / z, D / z, A / z


def handicap(M, h):
    H = D = A = 0.0
    for i in range(len(M)):
        for j in range(len(M[0])):
            s = i + h - j
            H += M[i][j] if s > 0 else 0
            D += M[i][j] if s == 0 else 0
            A += M[i][j] if s < 0 else 0
    z = H + D + A
    return H / z, D / z, A / z


def tg_from_matrix(M, maxg=6):
    # 总进球分布只能从最终矩阵按 i+j 聚合；末档7+吸收截断，严格8档和=1
    t = [0.0] * (maxg + 2)
    for i in range(len(M)):
        for j in range(len(M[0])):
            t[min(i + j, maxg + 1)] += M[i][j]
    z = sum(t)
    return [x / z for x in t]


def dixon_coles(M, lh, la, rho=RHO_DC):
    # 仅修正(0,0)(0,1)(1,0)(1,1)四格后全矩阵归一；rho=0即独立泊松
    if not rho:
        return M
    M = [r[:] for r in M]
    # v5.7.4终审修复：按Dixon-Coles(1997)标准τ，行i=主队进球(λ=lh)、列j=客队进球(μ=la)：
    # (0,1)=主0客1 用主λ；(1,0)=主1客0 用客λ。旧版两者la/lh写反(ρ=-0.08时1X2偏差<1pp,方向不变,此次归正)。
    M[0][0] *= 1 - lh * la * rho
    M[0][1] *= 1 + lh * rho
    M[1][0] *= 1 + la * rho
    M[1][1] *= 1 - rho
    return _renorm(M)


def _rho_adaptive_value(lh, la):
    """自适应ρ核心计算(不看总开关，供rho_of_match与回测rho_adaptive_report共用)。"""
    lh, la = float(lh), float(la)
    lt, dl = lh + la, abs(lh - la)
    g_t = 1.0 - RHO_ADAPT_SLOPE_LT * (lt - RHO_ADAPT_LT_ANCHOR)
    g_d = 1.0 - RHO_ADAPT_SLOPE_DL * dl
    g = max(RHO_ADAPT_G_MIN, min(RHO_ADAPT_G_MAX, g_t * g_d))
    return max(RHO_ADAPT_LO, min(RHO_ADAPT_HI, RHO_DC * g))


def rho_of_match(lh, la):
    """v5.8.3建议①：按对阵类型给Dixon-Coles的ρ。默认 RHO_ADAPTIVE_ENABLED=False 时恒返回全局RHO_DC，
    与v5.8.2逐字节一致；开启后：均衡闷战(低总λ/小实力差)ρ更负、对攻/悬殊趋0。纯函数、不改输入。"""
    return RHO_DC if not RHO_ADAPTIVE_ENABLED else _rho_adaptive_value(lh, la)


def draw_boost(M, draw_sp):
    # v5.3.6 F2：默认关闭(DRAW_BOOST_ENABLED=False)。平赔黄金区间×1.10是无统计依据的人为抬平局，
    # 在矩阵已≈市场去水概率时只会加噪；仅当显式打开且平赔落区间才做对角线加权并全矩阵归一。
    if not DRAW_BOOST_ENABLED:
        return M
    if draw_sp is not None and DRAW_BOOST_LO <= draw_sp <= DRAW_BOOST_HI:
        M = [r[:] for r in M]
        for i in range(len(M)):
            M[i][i] *= DRAW_BOOST_MULT
        M = _renorm(M)
    return M


def handicap_diag_boost(M, hand, tau=HANDICAP_DIAG_TAU):
    """v5.8.0 让球对角线补偿：对比分矩阵M中满足 i-j==-hand 的格子(让平=净胜差恰好等于让球线)乘τ后全矩阵归一。
    治独立泊松/DC低估'净胜差在整数让球线附近聚集'的结构性偏差(让1球时1-0/2-1/3-2整条对角线)。
    这是源头修：W=onextwo、S=格子、T=tg_from_matrix、matrix源H=handicap 全部由M派生因此同步受益且严格守恒；
    Pinnacle源H直取锐线三项不受影响(遵守锐线优先)。τ=1即恒等；hand=None时调用方应跳过。"""
    if not HANDICAP_DIAG_BOOST_ENABLED or tau is None or abs(tau - 1.0) < 1e-12 or hand is None:
        return M
    h = int(hand); M = [r[:] for r in M]; z = 0.0
    for i in range(len(M)):
        for j in range(len(M[0])):
            if i - j == -h:
                M[i][j] *= tau
            z += M[i][j]
    return [[v / z for v in r] for r in M]


def handicap_tau_of(hand):
    """v5.8.2 按让球档取让平对角线τ：HANDICAP_DIAG_TAU_BY 按|让球线|覆盖，缺省/hand=None 时回退统一 HANDICAP_DIAG_TAU。
    HANDICAP_DIAG_TAU_BY={}（默认）时对任何盘口都返回2.0，与v5.8.1逐字节一致；这是'预留分档能力、不提前过拟合'的唯一入口。"""
    if hand is None:
        return HANDICAP_DIAG_TAU
    return HANDICAP_DIAG_TAU_BY.get(abs(int(hand)), HANDICAP_DIAG_TAU)


def p_over_line(lt, line):
    """总进球~Poisson(lt)下，大小球盘口line的大球'有效概率'（含整数走水/split半盘）。
    line=2.5半球→P(N≥3)；line=2整数→P(N≥3)+0.5P(N=2)；2.25split→整数2与半球2.5各半；2.75同理。"""
    pn = [pois(k, lt) for k in range(13)]

    def half(i):                       # 半球盘 i.5：大球=P(N≥i+1)
        return 1 - sum(pn[:i + 1])

    def integer(i):                    # 整数盘：N>i全赢、N=i走水(计半)
        return 1 - sum(pn[:i + 1]) + 0.5 * pn[i]
    i = int(line)
    frac = round((line - i) * 100)
    if frac == 0:
        return integer(i)
    if frac == 50:
        return half(i)
    if frac == 25:   # split=整数i + 半球i.5，半球i.5的floor=i
        return 0.5 * integer(i) + 0.5 * half(i)
    if frac == 75:   # split=半球i.5 + 整数(i+1)
        return 0.5 * half(i) + 0.5 * integer(i + 1)
    raise ValueError(f"大小球盘口线{line}无法识别(支持半球x.5/整数/split x.25,x.75)")


# ==================== v5.8.2 净胜球分布 × 亚盘全档拆解（只读派生层，与onextwo/handicap/tg_from_matrix同源于M）====================
def goal_diff_dist(M):
    """从最终比分矩阵M按 d=i-j（主队净胜球）聚合净胜球分布，返回 {d:概率}(按d升序)。
    M在调用前已归一(DC/平局增强/让球对角线补偿后)，故各格概率和≈1。这是亚盘全档拆解唯一需要的中间量。"""
    gd = {}
    for i in range(len(M)):
        for j in range(len(M[0])):
            d = i - j
            gd[d] = gd.get(d, 0.0) + M[i][j]
    return dict(sorted(gd.items()))


def _ah_bucket(margin):
    """买[让球方]、让球后净胜差margin=让球方净胜d-让球数line时的结算档：
    margin≥+0.5全赢'W'；=+0.25赢半'HW'(只出现在.75盘)；=0走盘'P'(只出现在整数盘)；
    =-0.25输半'HL'(只出现在.25盘)；≤-0.5全输'L'。d为整数、line为0.25倍数，margin只落这5个离散格。"""
    if margin >= 0.5 - 1e-9:
        return "W"
    if abs(margin - 0.25) < 1e-9:
        return "HW"
    if abs(margin) < 1e-9:
        return "P"
    if abs(margin + 0.25) < 1e-9:
        return "HL"
    return "L"


def asian_handicap_breakdown(M, line, favorite="home"):
    """亚盘全档结算概率（买让球方 -line）。
    line=让球数(非负，支持 0/0.25/0.5/0.75/1.0...3.0 任意0.25档：平手/平半/半球/半一/一球/... )；
    favorite='home'让球方是主队(其净胜球d=i-j)，'away'让球方是客队(d=j-i，主视角镜像)。
    返回 {W,HW,P,HL,L,cover,fail}：全赢/赢半/走盘/输半/全输概率(五项和=1)；
      cover=W+0.5·HW=穿盘当量(赢半折半)，fail=L+0.5·HL=失盘当量。
    整数线line=n时：W=让球方净胜≥n+1(=竞彩让胜)、P=恰好净胜n(=竞彩让平/亚盘走盘退本格)、L=净胜≤n-1(=竞彩让负)。"""
    gd = goal_diff_dist(M)
    r = dict(W=0.0, HW=0.0, P=0.0, HL=0.0, L=0.0)
    for d_home, pr in gd.items():
        d_fav = d_home if favorite == "home" else -d_home
        r[_ah_bucket(d_fav - line)] += pr
    s = sum(r.values())
    if s > 0:   # 数值兜底再归一(M本已≈1，归一仅为消除截断尾差)
        r = {k: v / s for k, v in r.items()}
    r["cover"] = r["W"] + 0.5 * r["HW"]
    r["fail"] = r["L"] + 0.5 * r["HL"]
    return r


def asian_ladder(M, base_line, favorite="home", around=ASIAN_LADDER_AROUND):
    """围绕官方整数让球线base_line(让球数≥0)，按0.25步长向两侧各扩around档，
    返回[{line,W,HW,P,HL,L,cover,fail},...]按line升序，直观呈现盘口加深时穿盘概率如何衰减。
    不让球(base_line=0)时从平手0起算、不出现负盘。"""
    rows = []
    center = int(round(float(base_line) * 4))     # 以0.25(=1/4)为最小单位，避免浮点误差
    for k in range(center - around, center + around + 1):  # v5.8.3清理：移除未使用的lo变量(负盘由下方line<0 continue处理)
        line = k / 4.0
        if line < -1e-9:
            continue
        r = asian_handicap_breakdown(M, line, favorite)
        r["line"] = line
        rows.append(r)
    return rows


def asian_ev(dec_odds, W, HW=0.0, P=0.0, HL=0.0, L=0.0):
    """亚盘期望收益(每押1单位、十进制赔率dec_odds；走盘P退本贡献0)：
    EV=W·(b-1)+HW·(b-1)/2-HL·0.5-L。令EV=0可反解盈亏平衡赔率；纯整数/半球盘(无半档)简化为 b*=1/W。"""
    return W * (dec_odds - 1.0) + HW * (dec_odds - 1.0) / 2.0 - HL * 0.5 - L


def goal_diff_snapshot(M, hand, around=ASIAN_LADDER_AROUND):
    """供analyze()一次性挂载的只读结构。hand与引擎同号(主让为负-1/-2、客让为正+1/+2、无盘None)：
      · gd_home：主队视角净胜球分布{d:概率}
      · 有让球线时再给 fav(让球方home/away)、n(让球数)、fav_diff(让球方视角净胜球分布)、
        gd_peak(让球方净胜球众数档)、p_win(让球方赢球=其1X2方向概率)、p_exact_n(恰好赢够n球=走盘/让平格)、
        base_int(官方整数线W/P/L)、ladder(邻近亚盘全档)、morph(穿盘/赢球输盘/让不出 的形态量化)。
    形态判据(模型矩阵视角)：穿盘概率(W)三分区最大→'穿盘'；否则让球方赢球率≥0.5→'赢球输盘'；赢球率<0.5→'让不出'。"""
    gd = goal_diff_dist(M)
    out = {"gd_home": gd, "hand": hand}
    if hand is None:
        return out
    fav = "home" if float(hand) < 0 else "away"
    n = abs(int(hand))
    fd = {}
    for d_home, p in gd.items():
        d_fav = d_home if fav == "home" else -d_home
        fd[d_fav] = fd.get(d_fav, 0.0) + p
    fd = dict(sorted(fd.items()))
    peak = max(fd, key=lambda d: fd[d])
    p_win = sum(p for d, p in fd.items() if d >= 1)
    p_exact = fd.get(n, 0.0)
    base_int = asian_handicap_breakdown(M, n, fav)
    # 形态三分(模型矩阵视角；与analyze.cover的市场锐线视角并列、不互相覆盖)：穿盘=让球方净胜≥n+1(整数线W)且为
    # 三分区最大；否则若让球方赢球概率p_win≥0.5(更可能赢下来)→'赢球输盘'(会赢但大概率赢不够整数线)；
    # 若连赢球概率都不足一半(更可能平/负)→'让不出'。另给 p_cover/p_win_nocover/p_notwin 三客观概率供自行判断。
    p_cover = base_int["W"]
    p_win_nocover = sum(p for d, p in fd.items() if 1 <= d <= n)
    p_notwin = sum(p for d, p in fd.items() if d <= 0)
    if p_cover >= p_win_nocover and p_cover >= p_notwin:
        morph = "穿盘"
    elif p_win >= 0.5:
        morph = "赢球输盘"
    else:
        morph = "让不出"
    out.update(fav=fav, n=n, fav_diff=fd, gd_peak=peak, p_win=p_win, p_exact_n=p_exact,
               p_cover=p_cover, p_win_nocover=p_win_nocover, p_notwin=p_notwin,
               base_int=base_int, ladder=asian_ladder(M, n, fav, around), morph=morph)
    return out


def total_lambda_from_ou(ou):
    """大小球水位去水→大球概率→反解总λt（v38.4市场λ第一步：大小球锚总λ）。返回(λt,去水大球概率)。"""
    wo, wu = ou["over"], ou["under"]
    q = (1 / wo) / ((1 / wo) + (1 / wu))     # 两项水位去水归一
    line = float(ou["line"])
    lt, gap = None, 9.0
    x = 20
    while x <= 1200:                         # λt∈[0.10,6.00] 步长0.005 网格反解
        cand = x / 200
        g = abs(p_over_line(cand, line) - q)
        if g < gap:
            lt, gap = cand, g
        x += 1
    return lt, q


def total_lambda_from_ou_multi(ou_list, lo=OU_MULTI_LO, hi=OU_MULTI_HI):
    """v5.7 P0-3：用Pinnacle【多档totals】联立反演总λt。每条大小球线去水后各自反解一个λt，
    按'越接近主盘2.5越可信'加权平均（单主盘只用到一条线、易被该线水位噪声带偏；多线联立更稳，治总进球系统性偏差）。
    输入ou_list=[{"line","over","under"},...]；全部非法返回None。"""
    if not ou_list:
        return None
    lts = []
    for ou in ou_list:
        try:
            line = float(ou["line"]); wo, wu = ou.get("over"), ou.get("under")
            if wo is None or wu is None or not (lo <= line <= hi):
                continue
            lt, _ = total_lambda_from_ou({"line": line, "over": float(wo), "under": float(wu)})
            if lt is None:
                continue
            w = 1.0 / (1.0 + abs(line - 2.5) * 1.6)   # 2.5主线权重1；2.0/3.0≈0.76；1.5/3.5≈0.56
            lts.append((lt, w))
        except Exception:
            continue
    if not lts:
        return None
    sw = sum(w for _, w in lts)
    return sum(lt * w for lt, w in lts) / sw


def total_lambda_from_ttg(tsp):
    """v5.3.2 新增：竞彩总进球8档SP去水得分布，反解泊松总λt（零配置闭环关键——官方接口不卖大小球，
    但卖总进球ttg，其8档SP去水后即总进球经验分布，反解与之最匹配的Poisson λt，步长0.005）。
    返回 λt 或 None（档不全/全空时）。"""
    if not tsp:
        return None
    inv = []
    for k in range(8):
        v = tsp[k] if k < len(tsp) else None
        inv.append(1.0 / v if v not in (None, 0) else None)
    if sum(x is not None for x in inv) < 6:      # 至少6档有效才反解，避免残缺失真
        return None
    # 缺档按比例外的方式处理：有效档去水后在有效档内归一（末档7+ = 1-Σ0..6）
    s = sum(x for x in inv[:7] if x is not None)
    if s <= 0:
        return None
    tgt = [0.0] * 8
    for k in range(7):
        tgt[k] = (inv[k] / s) if inv[k] is not None else 0.0
    tgt[7] = max(0.0, 1.0 - sum(tgt[:7]))
    best_lt, best_gap = None, 1e9
    x = 20
    while x <= 1200:                            # λt∈[0.10,6.00] 步长0.005
        lt = x / 200
        pn = [pois(k, lt) for k in range(7)]
        p7 = max(0.0, 1.0 - sum(pn))
        gap = sum(abs(tgt[k] - pn[k]) for k in range(7)) + abs(tgt[7] - p7)
        if gap < best_gap:
            best_lt, best_gap = lt, gap
        x += 1
    return best_lt


def amer_to_dec(x):
    """v5.3.2 新增：美式赔率(如 -138 / +301)→十进制(1.725 / 4.01)；已是十进制(1<x<=60)原样返回。
    【固有歧义，v5.3.4注明】美式正赔(+100起,对应十进制≥2.0)与十进制整数赔率在'≥100的整数'处无法区分：
    本函数仅用于锐线 1X2/让球/大小球主流市场，这些市场赔率实际不会≥100，故按美式换算；
    切勿把竞彩比分(tsp/ssp)等可能出现百倍长冷的赔率传进来(那些走_dec不走本函数)。"""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if -1.0 < v < 1.0:        # 0.x 无意义
        return None
    if v > 1.0 and abs(v - round(v)) > 1e-9 and v <= 60:
        return v              # 已经是十进制小数赔率
    if v <= -100:
        return 1.0 + 100.0 / (-v)
    if v >= 100:
        return 1.0 + v / 100.0
    return v if v > 1.0 else None


# v5.3.3 Pinnacle等锐线【紧凑赔率文本】通道：境外博彩站程序无法直连(JS渲染+地区限制)，
# 由豆包用联网/浏览器读到页面后，把每场一行抄进 SHARP_TEXT，程序自动解析、美式自动换算，免手算。
# 每行格式：编号|spf 主 平 客|ou 盘口线 大 小|rsp 让胜 让平 让负  （赔率可混写美式-138/+301或十进制1.72，#开头注释）
SHARP_TEXT = r""""""
def _odds_tokens(s):
    """从一段文本抽全部赔率并换算为十进制（美式/十进制混写均可）。"""
    out = []
    for tok in re.findall(r'[-+]?\d+(?:\.\d+)?', str(s)):
        d = amer_to_dec(float(tok))
        if d:
            out.append(round(d, 3))
    return out
def parse_sharp_text(text, src=1, name="Pinnacle.ca文本"):
    """解析 SHARP_TEXT → {编号: sharp}。spf三项/ou(线+大小)/rsp三项，缺段不报错、取不到不编造。"""
    res = {}
    if not text:
        return res
    for ln in str(text).splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = [p.strip() for p in ln.split("|")]
        ids = re.findall(r'\d+', parts[0])
        if not ids:
            continue
        no = ids[0].zfill(3); sharp = {"src": src, "name": name}
        for p in parts[1:]:
            head = p.lower()[:3]
            if head.startswith("spf"):
                t = _odds_tokens(p[3:])
                if len(t) >= 3: sharp["spf"] = t[:3]
            elif head.startswith("ou"):
                toks = re.findall(r'[-+]?\d+(?:\.\d+)?', p[2:])
                if len(toks) >= 3:
                    line = float(toks[0]); ov = amer_to_dec(float(toks[1])); un = amer_to_dec(float(toks[2]))
                    if line and ov and un: sharp["ou"] = {"line": line, "over": ov, "under": un}
            elif head.startswith("rsp"):
                t = _odds_tokens(p[3:])
                if len(t) >= 3: sharp["rsp"] = t[:3]
        if set(sharp) - {"src", "name"}:
            res[no] = sharp
    return res
def merge_sharp_text(matches, text=None, src=1):
    """把 SHARP_TEXT 解析结果按编号回填到比赛记录（已有sharp只补缺失键，不覆盖AI/API更全的值）。"""
    parsed = parse_sharp_text(SHARP_TEXT if text is None else text, src=src)
    n = 0
    for m in matches:
        no = str(m.get("no", "")).zfill(3)
        if no in parsed:
            add = parsed[no]; cur = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
            for k, v in add.items():
                if k in ("src", "name"):
                    continue
                if not cur.get(k):
                    cur[k] = v
            cur.setdefault("src", add["src"]); cur.setdefault("name", add["name"])
            m["sharp"] = cur; n += 1
    return n


def invert_fixed_lt(sp3, lt):
    """v38.4市场λ第二步：固定总λt，用胜平负SP去水概率KL匹配定主/客λ（主λ步长0.005）。"""
    inv = [1 / x for x in sp3]
    s = sum(inv)
    tgt = [x / s for x in inv]
    best = None
    for lh200 in range(10, int(lt * 200) - 9):
        lh = lh200 / 200
        la = lt - lh
        if min(lh, la) <= 0.05:
            continue
        f = onextwo(matrix(lh, la))
        d = sum(tgt[k] * log(tgt[k] / f[k]) for k in range(3) if f[k] > 1e-9)
        if best is None or d < best[0]:
            best = (d, lh, la)
    if best is None:
        raise ValueError(f"两步反演定主客差失败(spf={sp3},λt={lt})")
    return best[1], best[2]


# ==================== v5.4 多源融合 + 21点早盘 工具函数 ====================
def consensus_lambda(q3, lt, lt_rel=0.05):
    """把目标1X2概率q3(和为1)KL拟合为(主λ,客λ)。总λt仅允许在base锚定值±lt_rel内微调(默认±5%,
    远小于旧版±20%自由漂移→守住比分/总进球锚定),叠加主客差共2自由度,使融合1X2(尤其平局)精确还原。"""
    best = None
    for ti in range(-2, 3):  # -5%/-2.5%/0/+2.5%/+5% 五档总λ
        ltt = lt * (1 + ti * lt_rel / 2.0)
        for lh200 in range(10, int(ltt * 200) - 9):
            lh = lh200 / 200
            la = ltt - lh
            if min(lh, la) <= 0.05:
                continue
            f = onextwo(matrix(lh, la))
            d = sum(q3[k] * log(q3[k] / f[k]) for k in range(3) if f[k] > 1e-9)
            if best is None or d < best[0]:
                best = (d, lh, la)
    if best is None:  # 兜底：严格固定总λ
        return invert_fixed_lt([1.0 / max(x, 1e-9) for x in q3], lt)
    return best[1], best[2]


def euro_fair_probs(m):
    """百家欧赔均值[主,平,客]去水→(去水概率, overround)；缺/非法返回None。欧赔overround通常1.04-1.08,远低于竞彩1.13。"""
    e = m.get("euro_avg")
    if not e or len(e) < 3:
        return None
    try:
        sp = [float(e[0]), float(e[1]), float(e[2])]
    except (TypeError, ValueError):
        return None
    if min(sp) <= 1.0:
        return None
    inv = [1.0 / x for x in sp]
    s = sum(inv)
    return [x / s for x in inv], s


def fuse_probs(sources):
    """sources=[(概率3元组, 权重),...] 仅取非空源,按权重比例动态归一加权;返回融合概率与实际权重清单。"""
    ok = [(q, w) for q, w in sources if q]
    if not ok:
        return None, []
    sw = sum(w for _, w in ok)
    out = [0.0, 0.0, 0.0]
    used = []
    for q, w in ok:
        ww = w / sw
        used.append(ww)
        for k in range(3):
            out[k] += q[k] * ww
    z = sum(out)
    return [x / z for x in out], used


def kickoff_dt(m):
    """解析【真实开球时间】。★竞彩接口 businessDate=销售轮次日(如"周日021"),matchDate=真实开球自然日:
    凌晨场销售日比开球日早一天(周日轮次日凌晨踢)。必须用 matchDate+matchTime,用 businessDate 会把当天凌晨临近场
    误判成"昨天已开赛"而漏采、错取成后一批。matchDate缺失才回退businessDate;AI JSON兼容time/kickoff/date。"""
    s = None
    kd, mt = (m.get("matchDate") or m.get("businessDate")), m.get("matchTime")
    if kd and mt:
        s = f"{kd} {mt}"
    else:
        for k in ("time", "kickoff", "datetime", "date"):
            if m.get(k):
                s = str(m[k]); break
    if not s:
        return None
    s = str(s).strip().replace("T", " ").replace("/", "-")
    mm = re.search(r"(\d{4}-\d{1,2}-\d{1,2})[ ]+(\d{1,2}:\d{2})(:\d{2})?", s)
    if not mm:
        return None
    try:
        hh, mi = mm.group(2).split(":")
        y, mo, da = [int(x) for x in mm.group(1).split("-")]
        return datetime(y, mo, da, int(hh), int(mi))
    except (ValueError, TypeError):
        return None


def _bj_now_naive():
    """当前北京时间(naive,与kickoff_dt同口径),避免容器系统时区非UTC+8导致早盘/未开赛判定错位。"""
    return _dt.now(_tz(_td(hours=8))).replace(tzinfo=None)
def hours_to_kickoff(m, now=None):
    """距开球小时数(正=未开赛),统一用北京时间。无法解析返回None。"""
    ko = kickoff_dt(m)
    if ko is None:
        return None
    now = now or _bj_now_naive()
    return round((ko - now).total_seconds() / 3600.0, 2)


def is_early_bet(m, now=None):
    """v5.4 早盘判定：启用EARLY_BET_MODE且距开球>EARLY_HOURS(21点买凌晨赛典型3-9h,吃不到临场首发/临场赔率)。"""
    if not EARLY_BET_MODE:
        return False, None
    h = hours_to_kickoff(m, now)
    if h is None:
        return False, None
    return (h > EARLY_HOURS), h


def euro_dispersion(m):
    """百家欧赔离散度(0-1)。兼容传百分数(>1按/100)与'18%'字符串；缺/非法返回0。"""
    v = m.get("euro_disp")
    if v is None:
        return 0.0
    try:
        v = float(v)
    except (TypeError, ValueError):
        try:
            v = float(str(v).replace("%", "").strip())
        except (TypeError, ValueError):
            return 0.0
    return v / 100.0 if v > 1 else v


def odds_drift(m):
    """初盘spf_open→当前spf的最大相对漂移幅度(0-1)；缺初盘返回0。用于早盘'已显著变盘'预警。"""
    o, c = m.get("spf_open"), m.get("spf")
    if not o or not c or len(o) < 3 or len(c) < 3:
        return 0.0
    d = 0.0
    try:
        for k in range(3):
            a, b = float(o[k]), float(c[k])
            if a > 0:
                d = max(d, abs(b - a) / a)
    except (TypeError, ValueError):
        return 0.0
    return d


LAMBDA_FLOOR = 0.05
# v5.3.3 λ校正阈值
LAMBDA_ANCHOR_WARN = 0.35   # 竞彩ttg锚λt 与 锐线ou锚λt 偏差≥此值→交叉校正告警(仍0.6/0.4融合)
LAMBDA_LT_HI = 5.6          # 总λt>此值=异常(大概率采集错/极端对攻)，告警
LAMBDA_TEAM_HI = 3.7        # 单队λ>此值=异常，告警
LAMBDA_DIV_HARD = 0.30      # 市场λ与统计λ背离≥此值=严重背离，强制以市场为准并红标
LAMBDA_TLT_MULT = 1.0       # v5.3.3 总λ系统校准乘子(由calibrate_from_history滚动回测反推，默认1=不校正)
WEAK_KEYS = ("lsc", "ctc", "referee", "rest", "tactic", "coach")  # v5.3.3: weather移出,改在resolve末端对所有λ来源统一乘(避免纯市场路径吃不到天气)


def stat_lambda(m):
    """v38.4 §9.1(A) 统计λ：联赛标准化Atk/Def + §9.4小样本贝叶斯收缩(k=12；升班马前5轮k=20)。
    原料来自采集卡维度1的stat块，缺任一必需项返回None；②统计λ乘市场未定价弱增量(默认全1.0,S5防伪)。"""
    st = m.get("stat")
    if not st:
        return None
    need = ["lg_hgf", "lg_agf", "lg_hga", "lg_aga",
            "h_n", "h_gf", "h_ga", "a_n", "a_gf", "a_ga"]
    if any(st.get(k) is None for k in need):
        return None
    lg_hgf, lg_agf, lg_hga, lg_aga = st["lg_hgf"], st["lg_agf"], st["lg_hga"], st["lg_aga"]
    h_n, h_gf, h_ga = st["h_n"], st["h_gf"], st["h_ga"]
    a_n, a_gf, a_ga = st["a_n"], st["a_gf"], st["a_ga"]
    if min(h_n, a_n, lg_hgf, lg_agf, lg_hga, lg_aga) <= 0:
        return None
    atk_h = (h_gf / h_n) / lg_hgf          # 主队主场进攻指数
    def_a = (a_ga / a_n) / lg_aga          # 客队客场防守指数(>1防守差)
    atk_a = (a_gf / a_n) / lg_agf
    def_h = (h_ga / h_n) / lg_hga
    lh_raw = lg_hgf * atk_h * def_a
    la_raw = lg_agf * atk_a * def_h
    k = 20 if st.get("promoted_round") and st["promoted_round"] <= 5 else 12
    lh = h_n / (h_n + k) * lh_raw + k / (h_n + k) * lg_hgf   # 收缩向联赛主场场均
    la = a_n / (a_n + k) * la_raw + k / (a_n + k) * lg_agf
    wc = m.get("weak_coeff") or {}
    w = 1.0
    for key in WEAK_KEYS:                  # LSC/CTC/裁判/体能/天气/战术/换帅，无证据全1.0
        w *= wc.get(key, 1.0)
    w = min(1.15, max(0.90, w))             # S1(a) 弱信息连乘总偏离[0.90,1.15]封顶
    return lh * w, la * w, w


def _sharp_only_lambda(m):
    """v5.7：无竞彩1X2(接口故障/离线)但有Pinnacle锐线1X2+大小球时，纯锐线独立反演(主,客,tag)。
    总λt优先多档totals联立，主客差由锐线1X2去水KL定。正常有竞彩SP时不走此路(仍走竞彩+锐线融合)。"""
    sh = m.get("sharp") or {}
    sspf = sh.get("spf")
    if not (sspf and len(sspf) >= 3 and all(x is not None for x in sspf[:3])):
        return None
    sou = sh.get("ou"); oum = sh.get("ou_multi") or m.get("ou_multi")
    slt = total_lambda_from_ou_multi(oum) if (SHARP_OU_MULTI and oum) else None
    if slt is None and isinstance(sou, dict) and sou.get("over") is not None \
            and sou.get("under") is not None and sou.get("line") is not None:
        try:
            slt, _ = total_lambda_from_ou(sou)
        except Exception:
            slt = None
    if not slt:
        return None
    rh, ra = invert_fixed_lt(sspf, slt)
    aud = m.setdefault("_lambda_audit", {})
    aud.update(sh_lt=round(slt, 3), sh_h=round(rh, 3), sh_a=round(ra, 3))
    tag = "纯锐线λ·多线" if (SHARP_OU_MULTI and oum) else "纯锐线λ"
    return rh, ra, f"{tag}λt{slt:.2f}"


def market_lambda(m):
    """v38.4 §9.1(B) 市场λ两步反演：大小球/总进球锚总λ→1X2定差；竞彩为主，
    若锐线同时给了1X2+大小球则 0.6竞彩+0.4锐线。无任何市场SP返回None。
    v5.3.3：①竞彩ttg锚与锐线ou锚【双锚交叉校正】，偏差≥LAMBDA_ANCHOR_WARN留痕告警；
    ②各源λ(竞彩锚/锐线锚/融合)写入 m['_lambda_audit']，供λ校正报告透明核对。
    v5.7：竞彩1X2残缺但有Pinnacle锐线时，走_sharp_only_lambda纯锐线兜底(接口故障/离线也能出λ)。"""
    aud = m.setdefault("_lambda_audit", {})
    spf0 = m.get("spf")
    if not (spf0 and len(spf0) >= 3 and all(x is not None for x in spf0[:3])):
        if SHARP_ANCHOR_ENABLED:        # v5.7 纯锐线兜底；关开关=v5.6直接return None
            return _sharp_only_lambda(m)
        return None     # v5.3.2 胜平负三项残缺则不走市场反演(交由统计/手填),不崩
    ou = m.get("ou")
    try:
        lt_cn, cn_tag = None, None
        if ou and ou.get("over") is not None and ou.get("under") is not None and ou.get("line") is not None:
            lt_cn, _ = total_lambda_from_ou(ou); cn_tag = "大小球锚"
        elif m.get("tsp"):
            lt_cn = total_lambda_from_ttg(m["tsp"])    # v5.3.2 零配置：竞彩总进球8档SP反推总λt
            if lt_cn is None and m.get("avg"):
                # v5.3.6 F1：总λt固定=avg，只用1X2定主客差，不再让1X2-KL漂移总λ污染比分/总进球
                mh, ma = invert_fixed_lt(spf0, float(m["avg"])); return mh, ma, "avg固定总λ(F1)"
            cn_tag = "总进球SP锚"
        elif m.get("avg"):
            # v5.3.6 F1：旧invert会在avg±20%网格自由选总λ(常顶到±20%边界)，改为固定总λ=avg
            mh, ma = invert_fixed_lt(spf0, float(m["avg"])); return mh, ma, "avg固定总λ(F1)"
        else:
            return None
        if lt_cn is None:
            return None
        mh, ma = invert_fixed_lt(spf0, lt_cn)
        # v5.3.3 高λt时ttg聚合档分辨率下降(方法论上限)，留痕提示优先用大小球ou交叉
        if cn_tag == "总进球SP锚" and lt_cn >= 3.6:
            aud["ttg_hi"] = round(lt_cn, 2)
        aud.update(cn_lt=round(lt_cn, 3), cn_h=round(mh, 3), cn_a=round(ma, 3))
        tag = f"{cn_tag}λt{lt_cn:.2f}"
    except Exception:
        return None
    sh = m.get("sharp") or {}
    _sspf = sh.get("spf")
    _sou = sh.get("ou")
    # v5.7 P0-3：锐线总λt优先用【多档totals联立拟合】(更稳)，无多线再退回单主盘
    _ou_multi = sh.get("ou_multi") or m.get("ou_multi")
    slt = None
    if SHARP_ANCHOR_ENABLED and SHARP_OU_MULTI and _ou_multi:
        try:
            slt = total_lambda_from_ou_multi(_ou_multi)
        except Exception:
            slt = None
    if slt is None and isinstance(_sou, dict) and _sou.get("over") is not None \
            and _sou.get("under") is not None and _sou.get("line") is not None:
        try:
            slt, _ = total_lambda_from_ou(_sou)
        except Exception:
            slt = None
    if _sspf and len(_sspf) >= 3 and all(x is not None for x in _sspf[:3]) and slt:
        try:
            rh, ra = invert_fixed_lt(_sspf, slt)
            aud.update(sh_lt=round(slt, 3), sh_h=round(rh, 3), sh_a=round(ra, 3))
            gap = abs(lt_cn - slt)                       # v5.3.3 双锚交叉校正
            aud["anchor_gap"] = round(gap, 3)
            # v5.7：锐线主锚模式下λ融合改为0.4竞彩+0.6锐线(更信Pinnacle)；关闭开关仍=v5.6的0.6竞彩+0.4锐线
            _wsh = 0.6 if (SHARP_ANCHOR_ENABLED and SHARP_OU_MULTI) else 0.4
            if gap >= LAMBDA_ANCHOR_WARN:
                aud["anchor_warn"] = (f"竞彩锚λt{lt_cn:.2f}与锐线锚λt{slt:.2f}差{gap:.2f}"
                                      f"≥{LAMBDA_ANCHOR_WARN:.2f}，已{1-_wsh:.1f}/{_wsh:.1f}融合，请核对盘口线/抓取时间窗")
            mh, ma = (1 - _wsh) * mh + _wsh * rh, (1 - _wsh) * ma + _wsh * ra
            aud.update(fused_h=round(mh, 3), fused_a=round(ma, 3))
            tag += f"+锐线{_wsh:.1f}" + ("·多线" if (_ou_multi and SHARP_ANCHOR_ENABLED and SHARP_OU_MULTI) else "")
        except Exception:
            pass
    return mh, ma, tag


def _lambda_sanity(m, lh, la, aud):
    """v5.3.3 λ合理性边界校正：极端λ只告警不硬改(防采集错值被当成对攻/铁桶)，留痕到m['_lambda_warn']。"""
    warns = []
    if lh + la > LAMBDA_LT_HI:
        warns.append(f"总λt={lh+la:.2f}>{LAMBDA_LT_HI}异常高,请核对SP是否录错")
    if max(lh, la) > LAMBDA_TEAM_HI:
        warns.append(f"单队λ={max(lh,la):.2f}>{LAMBDA_TEAM_HI}异常高")
    if min(lh, la) <= LAMBDA_FLOOR + 1e-9:
        warns.append(f"一队λ已触底{LAMBDA_FLOOR},近乎0进球,请核对")
    if warns:
        m["_lambda_warn"] = "；".join(warns)
        aud["sanity"] = m["_lambda_warn"]
    return warns


INJ_SKIP_IF_MARKET_ANCHOR = True   # v5.7.6：有市场锚时伤停已被price in,默认不再叠加inj加性球数(防重复计入);False=回退旧逻辑
def _inj_addons(m, has_market):
    """伤停加性球数门控：存在市场锚(竞彩SP/市场反演λ)时,伤停早已被全球市场定价(price in),
    再叠加inj等于重复计入、会把总λ压低并制造虚高平局/0-0(2026-09-08首跑实证011/012的0-0概率冲到41-51%)。
    故市场锚下默认不叠加；仅纯统计/纯手填且无任何市场价时,伤停是AI独有增量才叠加。review伤停文字仍保留做方向核查/红灯。"""
    ih=float(m.get("inj_h",0.0) or 0.0); ia=float(m.get("inj_a",0.0) or 0.0)
    if INJ_SKIP_IF_MARKET_ANCHOR and has_market and (ih or ia):
        m["_inj_skipped_market"]=True
        return 0.0,0.0
    return ih,ia
def resolve_lambda(m):
    """v38.4 §9.1(C) λ六步固定顺序：①统计标准化+收缩→②统计乘弱增量→③市场两步反演
    →④市场+统计融合(背离>15%以市场为准)→⑤结构性战意分乘各队λ→⑥加性伤停球数。
    v5.3.2：手填同样叠加⑤⑥并做市场一致性校验。
    v5.3.3：①融合权重随统计样本量自适应(样本越不足越信市场:0.6/0.75/0.85)；
    ②背离≥LAMBDA_DIV_HARD红标强制以市场为准；③末尾λ合理性边界校正并全程留痕λ校正链。"""
    aud = m.setdefault("_lambda_audit", {})
    if m.get("lh") is not None and m.get("la") is not None:
        lh0, la0 = m["lh"], m["la"]
        warn = ""
        if m.get("spf"):                      # 手填λ vs 市场去水1X2 一致性校验(不静默背离)
            try:
                f = onextwo(matrix(lh0, la0))
                tgt = _norm3(m["spf"])
                if tgt:
                    d = max(abs(f[k] - tgt[k]) for k in range(3))
                    if d >= MANUAL_LG_WARN:
                        warn = f"手填λ与市场去水最大差{d*100:.0f}%≥{MANUAL_LG_WARN*100:.0f}%请核对"
                        m["_manual_warn"] = warn
            except Exception:
                pass
        lh = lh0 * m.get("motiv_h", 1.0)      # ⑤战意分乘(手填也走,不再跳过六步)
        la = la0 * m.get("motiv_a", 1.0)
        _ih,_ia=_inj_addons(m, bool(m.get("spf")))  # ⑥伤停加性(v5.7.6:有竞彩SP市场价=已price in,不重复叠加)
        lh += _ih; la += _ia
        _wc = m.get("_weather_coef", 1.0)     # v5.3.3 AI天气核查系数(对所有λ来源统一)
        lh *= _wc; la *= _wc
        lh, la = max(lh, LAMBDA_FLOOR), max(la, LAMBDA_FLOOR)
        if LAMBDA_TLT_MULT != 1.0:
            lh *= LAMBDA_TLT_MULT; la *= LAMBDA_TLT_MULT
        aud.update(source="手填", final_h=round(lh, 3), final_a=round(la, 3))
        _lambda_sanity(m, lh, la, aud)
        adj = (m.get("motiv_h", 1.0) != 1 or m.get("motiv_a", 1.0) != 1
               or m.get("inj_h", 0.0) != 0 or m.get("inj_a", 0.0) != 0 or _wc != 1.0)
        tag = "手填λ" + ("·叠加战意伤停" if adj else "") + (f"·⚠{warn}" if warn else "")
        sw = m.get("_lambda_warn")
        if sw: tag += "·⛔边界异常"
        return lh, la, tag
    mk, sk = market_lambda(m), stat_lambda(m)
    if mk and sk:
        mh, ma, mtag = mk
        sh, sa, _ = sk
        aud.update(stat_h=round(sh, 3), stat_a=round(sa, 3))
        diverge = max(abs(mh - sh) / max(mh, 1e-6), abs(ma - sa) / max(ma, 1e-6))
        # v5.3.3 自适应市场权重：统计主/客样本均值越大越可信(≥10→0.6；6-9→0.75；<6→0.85)
        st = m.get("stat") or {}
        try:
            nmean = (float(st.get("h_n", 0)) + float(st.get("a_n", 0))) / 2
        except (TypeError, ValueError):
            nmean = 0
        wm = 0.6 if nmean >= 10 else (0.75 if nmean >= 6 else 0.85)
        if diverge >= LAMBDA_DIV_HARD:        # 严重背离：红标、强制市场
            lh, la, note = mh, ma, f"市场/统计严重背离{diverge*100:.0f}%≥{LAMBDA_DIV_HARD*100:.0f}%→强制以市场为准"
            aud["hard_div"] = round(diverge, 3)
        elif diverge > 0.15:                  # 一般背离>15%→以市场为准并标注
            lh, la, note = mh, ma, f"市场/统计背离{diverge*100:.0f}%>15%→以市场为准"
        else:
            lh, la = wm * mh + (1 - wm) * sh, wm * ma + (1 - wm) * sa
            note = f"{wm:.2f}市场+{1-wm:.2f}统计(背离{diverge*100:.0f}%,样本{nmean:.0f}场)"
        lsrc = f"六步融合·{mtag}·{note}"
    elif mk:
        lh, la, lsrc = mk[0], mk[1], f"纯市场λ·{mk[2]}(无统计原料)"
    elif sk:
        lh, la, lsrc = sk[0], sk[1], "纯统计λ·无市场SP(降级)"
    else:
        raise ValueError(f'{m["no"]}: λ来源不足——需手填lh/la，或ou大小球，或spf+avg，或stat统计原料之一')
    aud.update(pre_h=round(lh, 3), pre_a=round(la, 3))
    lh *= m.get("motiv_h", 1.0)            # ⑤结构性战意(4.6.2/4.6.3/4.6.4)独立通道,分乘各队,默认1.0
    la *= m.get("motiv_a", 1.0)
    _ih,_ia=_inj_addons(m, bool(mk))       # ⑥伤停加性(v5.7.6:有市场锚mk=伤停已price in不叠加;纯统计λ才叠加)
    lh += _ih; la += _ia
    _wc = m.get("_weather_coef", 1.0)      # v5.3.3 AI天气核查系数(对所有λ来源统一,只乘一次)
    lh *= _wc; la *= _wc
    lh, la = max(lh, LAMBDA_FLOOR), max(la, LAMBDA_FLOOR)
    if LAMBDA_TLT_MULT != 1.0:             # v5.3.3 滚动回测反推的总λ系统校正
        lh *= LAMBDA_TLT_MULT; la *= LAMBDA_TLT_MULT
    aud.update(final_h=round(lh, 3), final_a=round(la, 3),
               source=("融合" if mk and sk else ("市场" if mk else "统计")))
    _lambda_sanity(m, lh, la, aud)
    if m.get("_lambda_warn"):
        lsrc += "·⛔λ边界异常"
    return lh, la, lsrc


def sharp_fair(sp3, src):
    """锐线去抽水公平赔率(basic method)：原始赔率÷返还率（v38.4 §2.5）。"""
    r = SHARP_RETURN.get(src, 0.98)
    return [x / r for x in sp3]


# ===================== v5.3.3 豆包AI语义核查（把原§D人工清单交给联网AI核查，程序自动量化+闸门）=====================
REQUIRE_AI_REVIEW_LIVE = True   # True=要f_live>0，两场都必须有合格AI语义核查(核心项已核查且无红灯)；False=仅提示不拦实盘
# 天气→总进球弱系数（雨雪大风压低节奏；只在AI带证据时启用，无证据恒1.0）
_WEATHER_COEF = {"晴": 1.0, "多云": 1.0, "阴": 1.0, "小雨": 0.97, "雨": 0.94, "大雨": 0.91,
                 "暴雨": 0.88, "雪": 0.88, "小雪": 0.95, "大雪": 0.88, "大风": 0.95}
_REVIEW_LABEL = {"pass": "✓通过", "warn": "⚠关注", "block": "⛔红灯", "todo": "？未核查"}


def _rev_get(rev, key):
    """安全取 review 子块（兼容dict缺失/None）。"""
    if not isinstance(rev, dict):
        return {}
    v = rev.get(key)
    return v if isinstance(v, dict) else {}
def _as_bool(x):
    """v5.3.4：把AI回填的布尔兼容成真bool——真布尔/1/'1'/'true'/'yes'/'y'/'是'/'已'/'双确认' 均为True，其余False。"""
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x != 0
    if x is None:
        return False
    return str(x).strip().lower() in ("1", "true", "yes", "y", "是", "已", "双确认", "confirmed", "ok")


def ai_review_check(m):
    """解析一场的 m['review']（豆包联网核查后回填），返回结论dict：
    level=pass/warn/block/todo；core_done=首发与战意双确认是否都已核查；blocks/warns=原因；
    adj=可量化调整(weather/motiv/inj，供注入λ引擎)；evid=各项证据来源。缺review=未核查(todo)。
    【只认带 src 证据的结论；AI没查到必须显式 unknown/none，绝不默认利好】。"""
    rev = m.get("review")
    res = dict(level="todo", core_done=False, blocks=[], warns=[],
               adj=dict(weather=1.0, motiv_h=None, motiv_a=None, inj_h=None, inj_a=None), evid={})
    if not isinstance(rev, dict):
        res["blocks"].append("无AI语义核查review块")
        return res
    levels = []
    LINEUP_OK = ("confirmed", "full", "confirmed_full", "ok", "available", "齐整", "已出", "官宣", "首发已确认", "已确认")
    # v5.4 早盘(21点买凌晨赛)通常拿不到1小时前才官宣的首发，但能拿到"预测/预计首发+已确定伤停名单"
    LINEUP_EXPECTED = ("expected", "predicted", "expected_full", "预计", "预计齐整", "预测首发", "预计首发")
    LINEUP_MISS = ("key_missing", "missing", "部分缺阵", "缺阵", "核心缺阵")
    _early, _hrs = is_early_bet(m)
    lineup_core = False
    # —— ① 首发/伤停 ——
    lu = _rev_get(rev, "lineup")
    st = str(lu.get("status", "unknown")).strip().lower()
    res["evid"]["lineup"] = lu.get("src", "")
    if st in LINEUP_EXPECTED and _early:
        # v5.4 早盘有限放行：预测首发齐整且伤停已核→核心算过，但留warn(临场可能变阵)；非早盘仍须官宣
        ih, ia = lu.get("impact_h"), lu.get("impact_a")
        if ih is not None or ia is not None:
            res["adj"]["inj_h"] = _fnum(ih) or 0.0
            res["adj"]["inj_a"] = _fnum(ia) or 0.0
        lineup_core = True
        res["warns"].append(f"早盘距开{_hrs}h为【预计首发】(未官宣),伤停已核;临场存在变阵风险,已以早盘仓位折扣对冲")
        levels.append("warn")
    elif st in LINEUP_OK:
        levels.append("pass"); lineup_core = True
        # v5.3.5修复:官宣首发≠无伤停——残阵常由替补/新人顶替进首发,只要给了带证据的impact就仍须量化注入λ
        ih, ia = lu.get("impact_h"), lu.get("impact_a")
        if ih is not None or ia is not None:
            res["adj"]["inj_h"] = _fnum(ih) or 0.0
            res["adj"]["inj_a"] = _fnum(ia) or 0.0
            if res["adj"]["inj_h"] != 0.0 or res["adj"]["inj_a"] != 0.0:
                res["warns"].append(f"首发已官宣,但带证据伤停/缺阵[{lu.get('missing','')}]按加性{res['adj']['inj_h']}/{res['adj']['inj_a']}计入λ")
    elif st in LINEUP_MISS:
        ih, ia = lu.get("impact_h"), lu.get("impact_a")
        if ih is not None or ia is not None:        # 核心缺阵但AI已给加性球数→已反映到λ=warn
            res["adj"]["inj_h"] = _fnum(ih) or 0.0
            res["adj"]["inj_a"] = _fnum(ia) or 0.0
            res["warns"].append(f"首发:核心缺阵[{lu.get('missing','')}]已按加性{res['adj']['inj_h']}/{res['adj']['inj_a']}计入λ")
            levels.append("warn"); lineup_core = True
        else:                                        # 核心缺阵却未量化→block（不可在未知影响下实盘）
            res["blocks"].append(f"首发:核心[{lu.get('missing','关键球员')}]缺阵但未给λ影响,无法定价")
            levels.append("block")
    else:                                            # unknown / 未给
        res["warns"].append("首发:未拿到确认首发名单(unknown)")
        levels.append("todo")
    # —— ② 战意双确认（数学形势 + 官宣轮换 两条证据都在才算dual；v5.3.4 dual兼容字符串/1，且严格要求双确认才算核心已核查）——
    mo = _rev_get(rev, "motivation")
    res["evid"]["motivation"] = mo.get("src", "")
    dual = _as_bool(mo.get("dual"))
    math_s = mo.get("math")
    motiv_core = False
    if dual and math_s:
        motiv_core = True
        if mo.get("motiv_h") is not None: res["adj"]["motiv_h"] = _fnum(mo.get("motiv_h"))
        if mo.get("motiv_a") is not None: res["adj"]["motiv_a"] = _fnum(mo.get("motiv_a"))
        levels.append("pass")
    elif math_s:                                     # 只有数学形势、无官宣=单确认
        if _early:
            # v5.4 早盘：轮换官宣常到临场才出，数学形势确定即算核心过，留warn（block类风险仍不放宽）
            motiv_core = True
            if mo.get("motiv_h") is not None: res["adj"]["motiv_h"] = _fnum(mo.get("motiv_h"))
            if mo.get("motiv_a") is not None: res["adj"]["motiv_a"] = _fnum(mo.get("motiv_a"))
            res["warns"].append(f"早盘距开{_hrs}h:战意以数学形势[{math_s}]为准、缺官宣轮换(临场复核)")
            levels.append("warn")
        else:
            res["warns"].append(f"战意:仅有数学形势[{math_s}]、缺官宣轮换确认(单确认,未达双确认)")
            levels.append("warn")
    else:
        res["warns"].append("战意:未完成数学形势+官宣双确认")
        levels.append("todo")
    # —— ③ 默契球/积分互利 ——
    co = _rev_get(rev, "collusion")
    res["evid"]["collusion"] = co.get("src", "")
    cl = str(co.get("level", "none")).strip().lower()
    if cl == "high":
        res["blocks"].append(f"默契球/积分互利高风险:{co.get('note','') or '存在互利/做球嫌疑,AI未排除'}")
        levels.append("block")
    elif cl == "watch":
        res["warns"].append(f"默契球关注:{co.get('note','')}")
        levels.append("warn")
    elif cl == "none":
        levels.append("pass")
    else:
        levels.append("todo"); res["warns"].append("默契球:未排查")
    # —— ④ 突发利空 ——
    bk = _rev_get(rev, "breaking")
    res["evid"]["breaking"] = bk.get("src", "")
    bl = str(bk.get("level", "none")).strip().lower()
    if bl == "block":
        why = ';'.join(str(x) for x in bk.get('items', []) if x) or bk.get('note', '') or "存在未消化的突发利空(伤退/罢训/换帅/舆情)"
        res["blocks"].append(f"突发利空:{why}")
        levels.append("block")
    elif bl == "watch":
        res["warns"].append(f"突发利空关注:{(';'.join(str(x) for x in bk.get('items',[])) or bk.get('note',''))}")
        levels.append("warn")
    elif bl == "none":
        levels.append("pass")
    else:
        levels.append("todo"); res["warns"].append("突发利空:未排查")
    # —— ⑤ 临场天气（自动映射弱系数并入λ）——
    wt = _rev_get(rev, "weather")
    res["evid"]["weather"] = wt.get("src", "")
    cond = str(wt.get("cond", "")).strip()
    if cond:
        if cond not in _WEATHER_COEF:                # v5.3.4 未识别天气词不静默当晴，提示人工核对
            res["warns"].append(f"天气:词'{cond}'未在系数表内,按1.0处理请人工核对")
            levels.append("warn")
        else:
            coef = _WEATHER_COEF[cond]
            res["adj"]["weather"] = coef
            if cond in ("大雨", "暴雨", "雪", "大雪"):
                res["warns"].append(f"天气:{cond}→总节奏系数{coef}已自动并入λ")
                levels.append("warn")
            elif coef < 1.0:
                res["warns"].append(f"天气:{cond}→系数{coef}")
                levels.append("warn")
            else:
                levels.append("pass")
    else:
        levels.append("todo"); res["warns"].append("天气:未核查")
    # —— 汇总：block>todo>warn>pass；v5.3.4核心两项=首发已确认/缺阵已量化 且 战意完成数学+官宣双确认，缺一不可实盘 ——
    order = {"block": 3, "todo": 2, "warn": 1, "pass": 0}
    res["level"] = max(levels, key=lambda x: order[x]) if levels else "todo"
    res["core_done"] = bool(lineup_core and motiv_core)
    return res


def apply_ai_review(m):
    """把AI语义核查的可量化调整注入一场记录：天气→weak_coeff.weather，
    首发加性→inj，战意→motiv（均为赋值、天然幂等，重复调用不叠加）；结论缓存到 m['_review']。
    不做"已处理就跳过"的短路——review可能在analyze后被更新，需每次按最新review重算。"""
    rv = ai_review_check(m)
    adj = rv["adj"]
    # v5.3.3 天气系数统一存 _weather_coef，在resolve末端对所有λ来源生效（不塞进只作用于统计λ的weak_coeff）
    if adj["weather"] and adj["weather"] != 1.0:
        m["_weather_coef"] = adj["weather"]
    if adj["inj_h"] is not None:
        m["inj_h"] = adj["inj_h"]
    if adj["inj_a"] is not None:
        m["inj_a"] = adj["inj_a"]
    if adj["motiv_h"] is not None:
        m["motiv_h"] = adj["motiv_h"]
    if adj["motiv_a"] is not None:
        m["motiv_a"] = adj["motiv_a"]
    m["_review"] = rv
    m["_review_applied"] = True
    return rv


def ai_review_report(A):
    """打印豆包AI语义核查表：五项状态 + 综合等级 + 证据是否齐备；并汇总红灯/未核查场。"""
    line(); print("§A++ 豆包AI语义核查（首发/战意双确认/默契球/突发利空/临场天气——原需人工，现由联网AI核查、程序量化并卡实盘）"); line()
    n_block = n_todo = n_warn = n_ok = 0
    keys = ["lineup", "motivation", "collusion", "breaking", "weather"]
    subs = ["status", "dual", "level", "level", "cond"]
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        m = a["m"]; rv = m.get("_review") or apply_ai_review(m)
        rev = m.get("review") or {}
        _hn = str(m.get("home") or m.get("lg") or "?")[:5]
        _an = str(m.get("away") or "?")[:5]
        cells = []
        for k, sb in zip(keys, subs):
            blk = _rev_get(rev, k); v = blk.get(sb, "")
            cells.append(str(v) if v not in (None, "") else "—")
        lv = rv["level"]
        n_block += (lv == "block"); n_todo += (lv == "todo"); n_warn += (lv == "warn"); n_ok += (lv == "pass")
        print(f'  {m["no"]} {_hn:<5}v{_an:<5} 综合[{_REVIEW_LABEL.get(lv,lv)}] '
              f'首发[{cells[0]}] 战意双确认[{cells[1]}] 默契[{cells[2]}] 利空[{cells[3]}] 天气[{cells[4]}] '
              f'核心已核查={"是" if rv["core_done"] else "否"}')
        for b in rv["blocks"]:
            print(f"      ⛔ {b}")
        for w in rv["warns"]:
            print(f"      ⚠ {w}")
    print(f"  ── 汇总：✓全过{n_ok}场、⚠关注{n_warn}场、？未核查{n_todo}场、⛔红灯{n_block}场。"
          + ("实盘要求每场综合非⛔且核心已核查（REQUIRE_AI_REVIEW_LIVE=True）。" if REQUIRE_AI_REVIEW_LIVE else
             "当前REQUIRE_AI_REVIEW_LIVE=False，语义核查仅提示不卡实盘。"))
    return n_block, n_todo


def clv_one(sp_bet, fair):
    """单方向CLV=(竞彩出票SP−锐线公平赔率)/锐线公平赔率；≥+3%才有价格优势。"""
    if sp_bet is None or fair is None or fair <= 0:
        return None
    return (sp_bet - fair) / fair


CONF_LADDER = ["S+", "S", "A", "B", "C"]


def drop_conf(lvl, n):
    if lvl not in CONF_LADDER:
        return lvl
    return CONF_LADDER[min(len(CONF_LADDER) - 1, CONF_LADDER.index(lvl) + n)]


def confidence(m):
    """v38.4 §7.2 置信度定级 + v5.4 早盘/离散度/变盘降档。
    价值源：真锐线sharp(Pinnacle/必发等) 或 百家欧赔均值euro(准锐线,无真锐线时S+封顶S)。
    无任何价值源→恒A级(2串1不可实盘)；有价值源：有效维≥10=S+/7-9=S/5-6=B/≤4=C，再叠加v5.4降档。
    返回(等级, 有效维数, 辅助维数, 是否有价值源)。降档原因写入m['_v54']['conf_note']。"""
    d = m.get("dims", {}) or {}
    sh = m.get("sharp")
    has_sharp = bool(sh and sh.get("spf"))
    v54 = m.get("_v54", {}) or {}
    has_euro = bool(v54.get("has_euro"))
    has_vsrc = has_sharp or has_euro
    core_poisson = d.get("1_poisson", True)                 # 有spf能反演即视为泊松维在
    core_move = d.get("2_oddsmove", m.get("spf_open") is not None)
    core_motiv = d.get("7_motivation", True)
    n_aux = sum(1 for k in AUX_DIM_KEYS if d.get(k) not in (None, False))
    n_dim = sum([bool(core_poisson), bool(core_move), bool(core_motiv), has_vsrc]) + n_aux
    notes = []
    if not has_vsrc:
        base = "A"
    elif n_dim >= 10:
        base = "S+"
    elif n_dim >= 7:
        base = "S"
    elif n_dim >= 5:
        base = "B"
    else:
        base = "C"
    # v5.4：仅靠欧赔均值(无Pinnacle真锐线)时，锐利度次一级，S+封顶S
    if has_euro and not has_sharp and base == "S+":
        base = "S"
        notes.append("欧赔均值为准锐线,S+封顶S")
    lvl = base
    # 注：早盘(21点买凌晨)不降低置信等级——等级反映数据/价值源质量，早盘信息不完整改由
    # stake_plan的EARLY_STAKE_MULT仓位折扣统一承载，避免"降档+卡门+减仓"三重惩罚导致永不出注。
    disp = v54.get("disp", 0) or 0
    if disp >= EURO_DISP_BLOCK:
        lvl = "C"
        notes.append(f"欧赔离散{disp*100:.0f}%严重分歧→C且禁实盘")
    elif disp >= EURO_DISP_WARN:
        lvl = drop_conf(lvl, 1)
        notes.append(f"欧赔离散{disp*100:.0f}%偏大降档")
    if (v54.get("drift", 0) or 0) >= ODDS_DRIFT_WARN:
        lvl = drop_conf(lvl, 1)
        notes.append(f"初盘至今漂移{v54['drift']*100:.0f}%降档")
    v54["conf_note"] = "；".join(notes)
    m["_v54"] = v54
    return lvl, n_dim, n_aux, has_vsrc


def dyn_coeff(m):
    """§9.3第3步动态系数=L×W×回撤×赛季（样本量/偏离无历史流默认1）。返回(总系数, 明细)。"""
    L, W, DD = m.get("L", 0), m.get("W", 0), m.get("DD", 0.0)
    idle = m.get("idle_days", 0)
    if L >= 4:
        l_c = 0.0
    elif L == 3:
        l_c = 0.0 if DD >= 5 else 0.5
    else:
        l_c = {0: 1.0, 1: 0.9, 2: 0.7}.get(L, 1.0)
    if 10 <= idle <= 30:                       # 连续未投10-30天，L系数再×0.8
        l_c *= 0.8
    if W >= 7:
        w_c = 0.7
    elif W >= 5:
        w_c = 0.8
    elif W >= 3:
        w_c = 0.9
    else:
        w_c = 1.0
    dd_c = 1.0 if DD < 5 else (0.8 if DD < 10 else (0.5 if DD < 20 else 0.0))
    s_c = SEASON_COEFF.get(m.get("season_stage", "normal"), 1.0)
    return l_c * w_c * dd_c * s_c, dict(L=l_c, W=w_c, DD=dd_c, season=s_c)


def kelly(p, sp):
    b = sp - 1
    return max(0.0, (b * p - (1 - p)) / b) if b > 0 else 0.0


def stake_plan(c):
    """v38.4 §9.3 凯利七步 → 该2串1占【总资金】比例（与本金绝对额无关）。
    f_star全凯利 → ×自动置信度base ×资金档bank ×动态系数 → 玩法/单场/组仓封顶=f_theory(理论参考)；
    f_live=当前可实盘比例：须同时过 H9双锐线/H2每腿CLV≥+3%/H3组合置信度≥S+/动态>0/红灯②非博冷，
    任一不过则 f_live=0（只作概率纸面参考，不投钱）。无锐线场置信度恒A，必被H3挡下，与v4.3一致。"""
    p, sp = c.get("pc_raw", c["pc"]), c["spc"]   # v5.3.2 凯利/EV用真实联合概率(同联赛0.95仅展示折减)
    m1, m2 = c["a1"]["m"], c["a2"]["m"]
    exotic = c["L1"]["mk"] in ("S", "T") or c["L2"]["mk"] in ("S", "T")
    cold = ((c["L1"]["sp"] or 0) > 2.50) or ((c["L2"]["sp"] or 0) > 2.50)
    conf1, nd1, _, sh1 = confidence(m1)
    conf2, nd2, _, sh2 = confidence(m2)
    conf_lo = min((conf1, conf2), key=lambda x: CONF_ORDER[x])  # 组合置信度取两场较低
    dyn1, det1 = dyn_coeff(m1)
    dyn2, det2 = dyn_coeff(m2)
    dyn = min(dyn1, dyn2)                                # 赛季/动态按更保守一场
    tier = m1.get("bankroll_tier", "std")
    bank = BANK_MAP.get(tier, 1.0)
    clv1, clv2 = c["L1"].get("clv"), c["L2"].get("clv")
    base_pack = dict(conf1=conf1, conf2=conf2, conf_lo=conf_lo, nd1=nd1, nd2=nd2,
                     dyn=dyn, det1=det1, det2=det2, bank=bank, clv1=clv1, clv2=clv2)

    def zero(reason):
        return dict(f_star=0.0, f_raw=0.0, f_theory=0.0, f_live=0.0, exotic=exotic,
                    cold=cold, why=reason, **base_pack)

    if sp is None:
        return zero("无SP无法算凯利→比例0(纯纸面)")
    f_star = kelly(p, sp)
    if f_star <= 0:
        return zero(f"EV={c['ev']*100:+.1f}%≤0，凯利拒绝下注→比例0(只作概率参考，不投钱)")
    if conf_lo in ("B", "C"):
        return zero(f"组合置信度{conf_lo}(有效维{nd1}/{nd2}<7)，有锐线场景B/C级禁止投注→比例0")
    base = CONF_BASE[conf_lo]
    f_raw = f_star * base * bank * dyn
    cap_play = CAP_PLAY_EXOTIC if exotic else CAP_PLAY_WH
    cap_match = 0.0135 if tier == "10w" else CAP_MATCH          # 单场硬顶:标准/5万1.5%,10万1.35%
    cap_group = CAP_GROUP * bank                                # 组仓:3%/2.4%/2.16%随档
    f_theory = min(f_raw, cap_play, cap_match, cap_group)
    # —— 实盘闸门（全过才把理论比例放为实盘）——
    block = []
    # v5.4 价值源分层：真锐线sharp(Pinnacle/必发,CLV≥+3%)；百家欧赔均值euro(准锐线,静态价值≥+5%)。
    # 欧赔均值仅对同源胜平负W有效；含让球/比分/总进球的串必须有对应市场sharp，否则该腿clv=None被挡。
    vs1, vs2 = c["L1"].get("vsrc"), c["L2"].get("vsrc")
    only_euro = not (vs1 == "sharp" and vs2 == "sharp") and (vs1 == "euro" or vs2 == "euro")

    def _vmin(L):
        return EURO_EDGE_MIN if L.get("vsrc") == "euro" else CLV_MIN

    if not (sh1 and sh2):
        block.append("含无价值源场(H9:既无锐线也无百家欧赔均值,恒A级)")
    else:
        for L, nn in ((c["L1"], c["n1"]), (c["L2"], c["n2"])):
            vmin = _vmin(L)
            lv = L.get("clv")
            if lv is None or lv < vmin:
                tag = "欧赔静态价值" if L.get("vsrc") == "euro" else "CLV"
                block.append(f"{nn}腿{tag}=" + ("无" if lv is None else f"{lv*100:+.1f}%") + f"<{vmin*100:.0f}%")
    # H3 v5.4：两场均真锐线要求S+；任一场仅靠欧赔准锐线放宽到S(欧赔置信已封顶S、CONF_BASE更低)
    h3_need = "S" if only_euro else "S+"
    if CONF_ORDER[conf_lo] < CONF_ORDER[h3_need]:
        block.append(f"组合置信度{conf_lo}<{h3_need}(H3,{'欧赔准锐线档' if only_euro else '真锐线档'};维{nd1}/{nd2})")
    if dyn <= 0:
        block.append("动态系数=0(L连输/DD回撤触发停投)")
    if cold:
        block.append("含SP>2.50博冷腿(红灯②,未证G5三条件)")
    if c["ev"] is not None and c["ev"] < EV_COMBO_MIN:
        block.append(f"组合EV{c['ev'] * 100:.1f}%<15%(H5)")
    if not leg_ev_ok(c["L1"]):
        block.append(f"{c['n1']}单腿EV未达H6/H7门槛")
    if not leg_ev_ok(c["L2"]):
        block.append(f"{c['n2']}单腿EV未达H6/H7门槛")
    if c["rho_hi"] >= RHO_BLOCK:
        block.append(f"ρ上限{c['rho_hi']:.2f}≥0.3(H1/红灯⑱)")
    # v5.6 时间熔断（连黑/回撤冷静期）：全局开关由 main 在出单前依据台账置位，锁仓期一切实盘比例强制为0，只留纸面
    if globals().get("_TILT_LOCK56"):
        block.append("v5.6时间熔断锁仓中(连黑≥5注或滚动ROI≤-20%,冷静期内不追损)")
    # v5.7.1 P1-5 实盘第二确认：腿方向的Pinnacle去水概率相对早快照反向移动≥阈值→拦(收盘线不反向才放行；缺早快照不拦)
    if LINE_MOVE_CONFIRM:
        for _m, _nm, _L in ((m1, c["n1"], c["L1"]), (m2, c["n2"], c["L2"])):
            _rev, _desc = sharp_leg_reversal(_m, _L)
            if _rev:
                block.append(f"{_nm}{_desc}")
    # H10 v5.3.3 豆包AI语义核查闸门：任一AI语义红灯、或核心(首发/战意)未核查→禁止实盘(用户无法人工审核,强制AI核全)
    if REQUIRE_AI_REVIEW_LIVE:
        for _m, _nm in ((m1, c["n1"]), (m2, c["n2"])):
            _rv = _m.get("_review") or apply_ai_review(_m)
            if _rv["level"] == "block":
                block.append(f"{_nm}AI语义红灯[{'；'.join(_rv['blocks'])}]")
            elif not _rv["core_done"]:
                block.append(f"{_nm}AI语义核心(首发/战意)未核查")
    # v5.8.4 锐线分层硬闸门（纵深拦截：即便上层漏过滤，这里也强制 f_live=0；非卡控玩法/缺λ自动放行）
    _sg_map = {str(c["n1"]): c.get("a1"), str(c["n2"]): c.get("a2")}
    for _nn, _LL in ((c["n1"], c["L1"]), (c["n2"], c["L2"])):
        _sok, _srs = sharp_stratum_leg_ok(_nn, _LL, _sg_map)
        if not _sok:
            block.append(f"v5.8.4分层闸门:{_nn}腿{_srs}")
    why = (f"全凯利f*={f_star*100:.2f}%×{conf_lo}级{base:g}×档{bank:g}×动态{dyn:g}"
           f"={f_raw*100:.3f}%，封顶[{'含比分/总进球0.5%' if exotic else '胜负让球2%'}"
           f"/单场{cap_match*100:.2f}%/组仓{cap_group*100:.2f}%]→理论{f_theory*100:.3f}%")
    # v5.4 早盘(21点买次日凌晨)：缺临场首发/临场赔率，闸门通过后仓位再打EARLY_STAKE_MULT折扣
    early2 = bool((m1.get("_v54") or {}).get("early") or (m2.get("_v54") or {}).get("early"))
    early_mult = EARLY_STAKE_MULT if early2 else 1.0
    f_live = 0.0 if block else f_theory * early_mult
    if not block and early2:
        why += f"；早盘(21点买凌晨,缺临场)仓位×{EARLY_STAKE_MULT:g}"
    why += "；实盘闸门：" + ("全部通过→可按实盘比例" if not block else "、".join(block) + "→实盘0")
    return dict(f_star=f_star, f_raw=f_raw, f_theory=f_theory, f_live=f_live, exotic=exotic,
                cold=cold, why=why, **base_pack)


DIR = {0: "主胜", 1: "平", 2: "客胜"}
HC_NAME = ["让胜", "让平", "让负"]
MK_LABEL = {"W": "胜平负", "H": "让球", "S": "比分", "T": "总进球"}

# 红灯⑩：剔除“比分4球+”后的16个可投常规比分（每队≤3球；平局仅到3-3）
_REG_HOME = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2)]
_REG_DRAW = [(0, 0), (1, 1), (2, 2), (3, 3)]
REG_SCORE = set(_REG_HOME + _REG_DRAW + [(j, i) for i, j in _REG_HOME])


def score_dir(i, j):
    # 比分方向映射（v38.4：主胜类/平局类/客胜类），混合ρ判定用
    return 0 if i > j else (1 if i == j else 2)


def rho_of(lg1, mk1, d1, lg2, mk2, d2):
    """对照v38.4 §7.9.3 ρ值表，返回(上限ρ,中值ρ)。多维同时命中取上限最大值(最保守)；
    区间上限用于ρ<0.3硬过滤判断。d为方向0/1/2，总进球腿d=None。"""
    rows = []
    same_lg = lg1 == lg2
    both_dir = d1 is not None and d2 is not None
    if same_lg:  # 同联赛当日同轮：同方向0.35-0.50/不同方向0.25-0.35
        if both_dir:
            rows.append((0.50, 0.425) if d1 == d2 else (0.35, 0.30))
        else:
            rows.append((0.50, 0.425))  # 含无方向腿(比分/总进球)无法判方向，按同方向最保守
    else:
        if both_dir:
            rows.append((0.25, 0.20) if d1 == d2 else (0.00, 0.00))  # 不同联赛同/异方向
        else:
            rows.append((0.25, 0.20))  # 跨联赛含无方向腿，保守按同方向档
    if mk1 == mk2:  # 同玩法同方向0.30-0.45（含同为比分/总进球）
        if not both_dir or d1 == d2:
            rows.append((0.45, 0.375))
    hi = max(r[0] for r in rows)
    mid = max(rows, key=lambda z: z[0])[1]
    return hi, mid


def match_type_of(dl, dir_ok):
    """v4.5 场次分型：Δλ=|主λ-客λ|实力差 × 1X2首选方向与最高比分格方向是否一致。
    相近分歧(方向不稳/实力接近) / 悬殊一致(方向明确) / 均衡过渡(灰区)。只用于选法指引。"""
    if (not dir_ok) or dl <= GAP_NEAR:
        return "相近分歧"
    if dl >= GAP_BIG and dir_ok:
        return "悬殊一致"
    return "均衡过渡"


# ===================== v5.8.3 建议②：主客攻守风格画像（纯只读派生，绝不改变任何概率）=====================
STYLE_PROFILE_ENABLED = True   # analyze是否挂style画像；关闭=不输出该字段，概率口径完全不变
STYLE_ATKDEF_BAND = 0.12       # 攻防指数相对1.0偏离阈值：|idx-1|≤此值=平衡，>则偏强(>1)/偏弱(<1)
STYLE_TEMPO_LOW = 2.0          # 总λ<此值=低比分闷战
STYLE_TEMPO_HIGH = 3.0         # 总λ>此值=对攻互爆，之间=中性节奏


def attack_defense_indices(m):
    """从stat块复算四相对指数(口径与stat_lambda完全一致)：atk_h主队主场进攻、def_h主队主场防守
    (>1=失球多于联赛=守弱)、atk_a客队客场进攻、def_a客队客场防守。stat缺失/字段不全/非正返回None。纯只读。"""
    st = m.get("stat") if isinstance(m, dict) else None
    if not st:
        return None
    need = ["lg_hgf", "lg_agf", "lg_hga", "lg_aga", "h_n", "h_gf", "h_ga", "a_n", "a_gf", "a_ga"]
    if any(st.get(k) is None for k in need):
        return None
    try:
        if min(st["h_n"], st["a_n"], st["lg_hgf"], st["lg_agf"], st["lg_hga"], st["lg_aga"]) <= 0:
            return None
        atk_h = (st["h_gf"] / st["h_n"]) / st["lg_hgf"]
        def_a = (st["a_ga"] / st["a_n"]) / st["lg_aga"]
        atk_a = (st["a_gf"] / st["a_n"]) / st["lg_agf"]
        def_h = (st["h_ga"] / st["h_n"]) / st["lg_hga"]
    except Exception:
        return None
    return dict(atk_h=atk_h, def_h=def_h, atk_a=atk_a, def_a=def_a)


def _side_atkdef_style(atk, deff, b):
    """单队攻防型：进攻指数atk、防守指数deff均相对联赛1.0(deff>1=失球多=守弱，<1=守强)。"""
    a_strong, a_weak = atk > 1 + b, atk < 1 - b
    d_weak, d_strong = deff > 1 + b, deff < 1 - b
    if a_strong and d_weak: return "攻强守弱"
    if a_strong and d_strong: return "攻强守强"
    if a_weak and d_weak: return "攻弱守弱"
    if a_weak and d_strong: return "攻弱守强"
    if not (a_strong or a_weak) and not (d_weak or d_strong): return "攻守平衡"
    if a_strong: return "攻强守中"
    if a_weak: return "攻弱守中"
    return "攻中守弱" if d_weak else "攻中守强"


def strength_band(dl):
    """实力差档，阈值对齐GAP_NEAR/GAP_BIG：≤0.8均衡 / 0.8-1.0胶着 / ≥1.0悬殊。建议①③共用此分层。"""
    if dl <= GAP_NEAR: return "均衡"
    if dl >= GAP_BIG: return "悬殊"
    return "胶着"


def tempo_band(lt):
    """节奏档(总λ)：<2.0闷战 / 2.0-3.0中性 / >3.0对攻。"""
    if lt < STYLE_TEMPO_LOW: return "闷战"
    if lt > STYLE_TEMPO_HIGH: return "对攻"
    return "中性"


def style_profile(lh, la, m=None):
    """v5.8.3 攻守风格画像（纯只读派生，不参与也不改变任何概率计算）。
    L1 纯λ层(任何路径都有)：实力差档strength(对齐GAP)、节奏档tempo(总λ)、强弱倾向favor、
       综合style_class、分层键stratum(建议①ρ自适应/建议③分层校准统一复用，保证口径一致)；
    L2 stat层(有stat块才有)：主/客各自 攻强守弱·攻守平衡·攻弱守强… 及 对阵组合matchup。
    """
    lh, la = float(lh), float(la)
    lt, dl = lh + la, abs(lh - la)
    sb, tb = strength_band(dl), tempo_band(lt)
    favor = "主强" if lh - la > 1e-9 else ("客强" if la - lh > 1e-9 else "均势")
    cls = f"{sb}·{tb}" if sb == "均衡" else f"{sb}·{favor}·{tb}"
    prof = dict(lt=round(lt, 4), dl=round(dl, 4), strength=sb, tempo=tb, favor=favor,
                style_class=cls, stratum=sb)
    idx = attack_defense_indices(m)
    if idx:
        hs = _side_atkdef_style(idx["atk_h"], idx["def_h"], STYLE_ATKDEF_BAND)
        aw = _side_atkdef_style(idx["atk_a"], idx["def_a"], STYLE_ATKDEF_BAND)
        prof.update(indices={k: round(v, 3) for k, v in idx.items()},
                    home_style=hs, away_style=aw, matchup=f"主{hs}×客{aw}")
    return prof


TYPE_ADVICE = {
    "悬殊一致": "实力悬殊且方向明确→主力走胜平负/让球(胜负方向)；比分/总进球仅作⑤号高赔小注覆盖",
    "相近分歧": (
        "实力接近/方向不稳→优先让球(受让覆盖,概率高于硬赌胜负)；慎用胜平负W；"
        "比分/总进球仅高赔小注,且同玩法2串ρ=0.45禁组、须跨玩法/跨方向拆"),
    "均衡过渡": "实力差居中→按维度一P排序正常选,让球与胜平负并重,比分/总进球仅高赔覆盖",
}


# ==================== v5.7.6 免费自算 Elo 维(10_elo)：本地持久化+赛后滚动+免费CSV引导，零订阅、不编造 ====================
# 设计：①键统一到"竞彩中文→Pinnacle英文规范名"(三源对齐已验证的同一空间),赛前查询/赛后滚动/CSV引导共用一套键,天然自洽;
#       ②标准Elo(K=20,主场优势+65,净胜球边际封顶×2,贴近ClubElo口径);③队历史<ELO_MIN_GAMES场视为未成型→不填维,
#         杜绝"全是初始1500"虚假凑维;④覆盖不到的联赛(韩职/沙特/解放者等)留null,靠每晚赛后结算自动滚动积累。
ELO_ENABLED = True
ELO_STORE_PATH = _data_path("elo_store.json")     # {规范英文队名键:{e评分,n已赛场次,lg最近联赛}}；v5.8.1统一落DATA_DIR长期保留(同calib_store)
ELO_DEFAULT = 1500.0; ELO_K = 20.0; ELO_HOME_ADV = 65.0; ELO_FLOOR = 800.0
ELO_MIN_GAMES = 5                     # 成型门槛：主/客各自历史场次≥N才填10_elo维
_ELO_STORE = None
def _elo_key(name):
    """任意队名(中/英)→统一英文规范键；中文靠TEAM_ALIAS_CN2EN,映射不到返回''(调用方据此留空,不编造)。"""
    if not name: return ""
    al=_cn_en_aliases(name)
    if al: return al[0].strip()
    k=_en_norm(name).strip()
    return k
def elo_load(force=False):
    global _ELO_STORE
    if _ELO_STORE is not None and not force: return _ELO_STORE
    s={}
    try:
        if _os.path.exists(ELO_STORE_PATH):
            with open(ELO_STORE_PATH,encoding="utf-8") as f: s=json.load(f)
    except Exception: s={}
    _ELO_STORE=s; return s
def elo_save():
    s=elo_load()
    try:
        with open(ELO_STORE_PATH,"w",encoding="utf-8") as f: json.dump(s,f,ensure_ascii=False)
    except Exception as e: print(f"  Elo库保存异常(不影响主流程):{e}")
def elo_expected(rh,ra):
    """主队期望得分(含主场优势ELO_HOME_ADV)。"""
    return 1.0/(1.0+10**((ra-(rh+ELO_HOME_ADV))/400.0))
def _elo_apply_keys(hk,ak,hg,ag,lg=None):
    """按规范键滚动一场,返回(nh,na)或None。"""
    if not hk or not ak or hk==ak or hg is None or ag is None: return None
    s=elo_load()
    rh=s.get(hk,{}).get("e",ELO_DEFAULT); ra=s.get(ak,{}).get("e",ELO_DEFAULT)
    we=elo_expected(rh,ra); wa=1-we
    wh=1.0 if hg>ag else (0.5 if hg==ag else 0.0); wa_=1-wh
    gd=abs(hg-ag); mult=(1.0+min(gd-1,2)*0.5) if gd>=2 else 1.0   # 净胜球边际:赢2球×1.5、3球×2封顶
    k=ELO_K*mult
    nh=max(rh+k*(wh-we),ELO_FLOOR); na=max(ra+k*(wa_-wa),ELO_FLOOR)
    for key,e in ((hk,nh),(ak,na)):
        d=s.get(key) or {}; d.update(e=round(e,1),n=int(d.get("n",0))+1,lg=lg or d.get("lg")); s[key]=d
    return nh,na
def elo_apply_result(home,away,hg,ag,lg=None):
    hk,ak=_elo_key(home),_elo_key(away)
    r=_elo_apply_keys(hk,ak,hg,ag,lg)
    return (hk,ak) if r else None
def _elo_canon_candidates():
    """TEAM_ALIAS_CN2EN 全部英文规范名(=Pinnacle名空间),供免费CSV缩写模糊归一。"""
    out=set()
    for v in TEAM_ALIAS_CN2EN.values():
        for x in ((v if isinstance(v,(list,tuple)) else [v])):
            k=_en_norm(x).strip()
            if k: out.add(k)
    return sorted(out)
def _elo_match_canon(raw, canon, th=0.62):
    """外部CSV队名→已知规范键:取模糊分最高且过阈值者,匹配不上返回None(不硬凑)。"""
    q=_en_norm(raw); best,bk=-1.0,None
    for c in canon:
        sc=_team_match_score(q,c)
        if sc>best: best,bk=sc,c
    return bk if best>=th else None
def elo_match_delta(m):
    """赛前:返回(主Elo,客Elo,含主场优势评分差)或None(任一队未成型/查无)。"""
    hk,ak=_elo_key(m.get("home")),_elo_key(m.get("away"))
    if not hk or not ak: return None
    s=elo_load(); H,A=s.get(hk),s.get(ak)
    if not H or not A or H.get("n",0)<ELO_MIN_GAMES or A.get("n",0)<ELO_MIN_GAMES: return None
    return H["e"],A["e"],round((H["e"]+ELO_HOME_ADV)-A["e"],1)
def attach_elo_dim(m):
    """analyze前调用:成型则填辅助维10_elo(数值=含主场优势评分差),取不到留空(不编造)。"""
    if not ELO_ENABLED: return
    try:
        d=elo_match_delta(m)
        if d: m.setdefault("dims",{})["10_elo"]=d[2]; m["_elo"]=(d[0],d[1],d[2])
    except Exception: pass
def elo_bootstrap_football_data(codes=("E0","E1","SP1","I1","D1","F1","N1","P1"),seasons=("2526","2425"),verbose=True):
    """免费无key历史引导:football-data.co.uk联赛CSV(E0英超/E1英冠/SP1西甲/I1意甲/D1德甲/F1法甲/N1荷甲/P1葡超;
    season如2526=25/26、2425=24/25)。CSV缩写经模糊归一到Pinnacle规范键后滚动,匹配不上跳过(不编造);
    覆盖不到的联赛留空,靠赛后滚动。返回(滚动场次,库内队数,今晚/当前库成型队数)。"""
    import csv as _csv, io as _io, urllib.request as _ur
    canon=_elo_canon_candidates(); n=0; miss=0
    for season in seasons:
        for code in codes:
            url=f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
            try:
                req=_ur.Request(url,headers={"User-Agent":"Mozilla/5.0"})
                txt=_ur.urlopen(req,timeout=30).read().decode("utf-8","ignore")
                for row in _csv.DictReader(_io.StringIO(txt)):
                    try: hg,ag=int(float(row.get("FTHG"))),int(float(row.get("FTAG")))
                    except Exception: continue
                    hk=_elo_match_canon(row.get("HomeTeam"),canon); ak=_elo_match_canon(row.get("AwayTeam"),canon)
                    if not hk or not ak: miss+=1; continue
                    if _elo_apply_keys(hk,ak,hg,ag,lg=code): n+=1
            except Exception as e:
                if verbose: print(f"  Elo引导 {code}/{season} 跳过:{type(e).__name__} {str(e)[:40]}")
    elo_save(); s=elo_load()
    ready=sum(1 for d in s.values() if d.get("n",0)>=ELO_MIN_GAMES)
    if verbose: print(f"Elo免费引导:滚动{n}场、未匹配{miss}场,库内{len(s)}队、成型(≥{ELO_MIN_GAMES}场){ready}队")
    return n,len(s),ready
# ==================== v5.7.7 免费自积累 H2H 交锋往绩维(6_h2h)：本地持久化+赛后滚动+AI回填优先，零订阅、不编造 ====================
# 与Elo同构:键复用Pinnacle英文规范名;赛后结算自动追加交锋、赛前取近10次(≈近5赛季)按本场主队视角算不败率;
# 样本<H2H_MIN不填(不凑维);AI研究在dims["6_h2h"]回填时只补不覆盖;odds-api1纯赔率无h2h,如需在线h2h可另订同账号RapidAPI产品。
H2H_ENABLED=True
H2H_STORE_PATH=_data_path("h2h_store.json")   # {"队A||队B(规范键排序)":[{d日期,h主,a客,hg,ag,lg}...]}；v5.8.1统一落DATA_DIR
H2H_MIN=3                         # 近N次交锋≥3场才填6_h2h(样本太少不具参考性)
H2H_LOOKBACK=10                   # 取近10次(≈近5赛季)
_H2H_STORE=None
def _h2h_pairkey(k1,k2):
    a=sorted([k1,k2]); return a[0]+"||"+a[1]
def h2h_load(force=False):
    global _H2H_STORE
    if _H2H_STORE is not None and not force: return _H2H_STORE
    s={}
    try:
        if _os.path.exists(H2H_STORE_PATH):
            with open(H2H_STORE_PATH,encoding="utf-8") as f: s=json.load(f)
    except Exception: s={}
    _H2H_STORE=s; return s
def h2h_save():
    try:
        with open(H2H_STORE_PATH,"w",encoding="utf-8") as f: json.dump(h2h_load(),f,ensure_ascii=False)
    except Exception as e: print(f"  H2H库保存异常(不影响主流程):{e}")
def h2h_apply_result(home,away,hg,ag,date=None,lg=None):
    """赛后追加一场交锋(主客按实际记录,查询时再换算到本场主队视角)。"""
    if hg is None or ag is None: return None
    hk,ak=_elo_key(home),_elo_key(away)
    if not hk or not ak or hk==ak: return None
    s=h2h_load(); pk=_h2h_pairkey(hk,ak)
    s.setdefault(pk,[]).append({"d":date,"h":hk,"a":ak,"hg":int(hg),"ag":int(ag),"lg":lg})
    s[pk]=s[pk][-30:]
    return pk
def h2h_summary(m,lookback=H2H_LOOKBACK):
    """返回(本场主队视角近lookback次的 胜,平,负, 不败率, 明细)或None(不足H2H_MIN/查无)。"""
    hk,ak=_elo_key(m.get("home")),_elo_key(m.get("away"))
    if not hk or not ak: return None
    games=(h2h_load().get(_h2h_pairkey(hk,ak)) or [])[-lookback:]
    if len(games)<H2H_MIN: return None
    w=d=l=0
    for g in games:
        gh,ga=(g["hg"],g["ag"]) if g["h"]==hk else (g["ag"],g["hg"])  # 历史hk打客则翻转到本场主队视角
        if gh>ga: w+=1
        elif gh==ga: d+=1
        else: l+=1
    return w,d,l,round((w+d)/len(games),3),games
def attach_h2h_dim(m):
    """analyze前调用:成型则填6_h2h(数值=本场主队历史不败率),AI已回填则不覆盖,取不到留空(不编造)。"""
    if not H2H_ENABLED: return
    try:
        dims=m.setdefault("dims",{})
        if dims.get("6_h2h") not in (None,False): return
        r=h2h_summary(m)
        if r:
            w,d,l,ub,games=r
            dims["6_h2h"]=ub
            m["_h2h"]=dict(w=w,d=d,l=l,unbeaten=ub,n=len(games))
    except Exception: pass
def analyze(m):
    # v5.7.6 先挂免费自算Elo维(成型才填10_elo,否则留空不编造)
    attach_elo_dim(m)
    # v5.7.8 SportScore在线H2H/阵容/积分(在线H2H先于本地自积累;AI回填仍最高优先,只补不覆盖)
    attach_ss(m)
    # v5.7.7 挂免费自积累H2H交锋维(SS在线/AI都无时本地自积累兜底,成型才填6_h2h)
    attach_h2h_dim(m)
    # v5.3.3 先把豆包AI语义核查(天气/首发加性/战意)量化注入，再走λ六步（幂等）
    apply_ai_review(m)
    # v4.7 λ六步自动引擎：手填>市场+统计融合>纯市场/纯统计；由采集字段驱动，无需人手算λ
    lh, la, lsrc = resolve_lambda(m)
    lt = lh + la
    _spf = m.get("spf")
    spf_ok = bool(_spf) and len(_spf) >= 3 and all(x is not None for x in _spf[:3])
    _rsp = m.get("rsp")   # 竞彩官方让球赔率(让球腿票面兜底源；是否三项齐全在_hsp处判)
    _shp_rsp = None   # 锐线Pinnacle 3WayH让球三项(与竞彩_rsp分开；让球腿票面锐线优先、竞彩兜底)
    draw_sp = _spf[1] if spf_ok else None
    # ===== v5.4 三源概率融合：竞彩去水 / 百家欧赔均值去水 / 统计(模型)泊松 → 共识概率 → 反推一致比分矩阵 =====
    # base λ 来自 resolve_lambda(已做市场+统计融合、总λ由ttg/ou/avg锚定)；其矩阵概率=模型源
    base_lh, base_la, base_lt = lh, la, lh + la
    one0 = list(onextwo(dixon_coles(base_matrix(base_lh, base_la), base_lh, base_la, rho_of_match(base_lh, base_la))))
    mkt_q = _norm3(_spf) if spf_ok else None              # 源①竞彩去水(高抽水,主要作下注价格)
    euro = euro_fair_probs(m)                             # 源②百家欧赔均值去水(低抽水全球共识)
    q_euro = euro[0] if euro else None
    euro_ov_raw = euro[1] if euro else None
    # v5.5.1 采集自校验：百家均值overround正常约1.03-1.10；越界=抓错/非均值/录错，BAD直接剔除不污染概率，WARN提示复核
    euro_ov_flag = None
    if euro:
        _margin = euro[1] - 1.0
        if euro[1] < 1.0 or _margin > EURO_OV_BAD:
            euro_ov_flag = f"百家欧赔overround={euro[1]:.3f}异常(正常1.03-1.10)→判定采集错误,该euro不参与融合"
            q_euro = None
        elif _margin > EURO_OV_WARN:
            euro_ov_flag = f"百家欧赔overround={euro[1]:.3f}偏高→请确认取的是'百家平均'而非单家高水公司"
    has_euro = q_euro is not None
    _has_stat = False
    try:
        _has_stat = stat_lambda(m) is not None
    except Exception:
        _has_stat = False
    _manual_lam = m.get("lh") is not None and m.get("la") is not None
    _shp = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
    _has_sharp = bool((_shp or {}).get("spf"))
    _model_indep = bool(_has_stat or _manual_lam or _has_sharp)   # 模型源是否含独立于竞彩的信息
    indep = bool(_model_indep or has_euro)               # v5.4: 欧赔均值同样是独立于竞彩的信源(F3放行依据)
    # v5.7 P0-1：Pinnacle去水概率作为1X2主锚。有真锐线(spf)时用四源权重(Pin0.70/欧0.15/竞彩0.10/模型0.15)，
    # 缺源由fuse_probs按在场源动态归一；无锐线或总开关关闭时，逐字节回退v5.6三源(竞彩0.25/欧0.55/模型0.20)。
    q_sharp = None
    if SHARP_ANCHOR_ENABLED and _has_sharp:
        q_sharp = _norm3(sharp_fair(_shp["spf"], _shp.get("src", 1)))   # fair赔率取倒归一=Pinnacle去水概率
    fuse_mode = "v5.6三源"
    _fsrc = []
    if q_sharp:
        _fsrc.append((q_sharp, SHARP_W_1X2))
        if q_euro:
            _fsrc.append((q_euro, EURO_W_V57))
        if mkt_q:
            _fsrc.append((mkt_q, CN_W_V57))
        if _model_indep:
            _fsrc.append((one0, MODEL_W_V57))
        fuse_mode = "v5.7锐线主锚"
    else:
        if mkt_q:
            _fsrc.append((mkt_q, FUSE_W_CN))
        if q_euro:
            _fsrc.append((q_euro, FUSE_W_EURO))
        if _model_indep:
            _fsrc.append((one0, FUSE_W_STAT))
    q_fuse, fuse_w = fuse_probs(_fsrc)
    if q_fuse is None:
        q_fuse = one0
    # 存在独立源才用共识概率反推主/客λ(总λ沿用base锚定,只调主客差)；纯竞彩则保持=市场(诚实复读,不制造伪增量)
    if has_euro or _model_indep:
        lh, la = consensus_lambda(q_fuse, base_lt)
        lt = lh + la
    M = dixon_coles(base_matrix(lh, la), lh, la, rho_of_match(lh, la))  # v5.8.3建议①④：默认关=独立泊松+RHO_DC等价旧版
    M = draw_boost(M, draw_sp)
    # v5.8.0 让球对角线补偿（源头修）：提前取hand，对M中i-j==-hand的让平对角线抬升τ后归一；
    # 此后onextwo(W)/sc(S)/tg_from_matrix(T)/handicap(matrix源H)全部基于补偿后M，四玩法严格守恒。hand=None时函数内恒等。
    hand = m.get("hand")
    M = handicap_diag_boost(M, hand, handicap_tau_of(hand))
    H, D, A = onextwo(M)
    one_raw = [H, D, A]                 # 校准前(融合/矩阵原始输出)，留档审计
    one = calib_apply("W", one_raw, lh, la)     # v5.7.1 P1-4 概率校准层(v5.8.3建议③携带λ供分层；关开关/默认恒等)
    # 信息增量igain=最终共识相对竞彩去水的最大偏离；≈0=模型仍是赔率复读，越大=独立判断越强
    igain = (max(abs(one[k] - mkt_q[k]) for k in range(3)) if mkt_q else None)
    # v5.4 早盘/离散度/变盘信号写入m，供confidence/stake_plan使用
    early, hrs = is_early_bet(m)
    _disp, _drift = euro_dispersion(m), odds_drift(m)
    _flipped = bool(mkt_q) and max(range(3), key=lambda k: q_fuse[k]) != max(range(3), key=lambda k: mkt_q[k])
    m["_v54"] = dict(early=early, hrs=hrs, disp=_disp, drift=_drift, q_cn=mkt_q, q_euro=q_euro,
                     q_model=one0, q_sharp=q_sharp, q_fuse=q_fuse, fuse_mode=fuse_mode,
                     base_lh=base_lh, base_la=base_la, fuse_w=fuse_w,
                     euro_ov=euro_ov_raw, euro_ov_flag=euro_ov_flag, has_euro=has_euro, flipped=_flipped)
    if euro_ov_flag:   # 采集自校验告警留痕(供信息增量/质量审计报告显示)
        m.setdefault("_collect_warn", []).append(euro_ov_flag)
    d1 = max(range(3), key=lambda k: one[k])
    n = len(M)
    sc = sorted(((M[i][j], i, j) for i in range(n) for j in range(n)), reverse=True)
    sc_dir = 0 if sc[0][1] > sc[0][2] else (1 if sc[0][1] == sc[0][2] else 2)
    dir_ok = d1 == sc_dir
    hcap_src = None
    if hand is not None:
        # v5.7 P0-2：让球首选/概率直取Pinnacle 3WayH去水三项(已在采集层精确对齐竞彩hand那条整数线)，
        # 治v5.6自有矩阵推让球系统性偏向让平(批次0907五次走让平、锁的让胜全灭)；无3WayH或关开关→矩阵兜底=v5.6。
        hcap_sharp = None
        if SHARP_ANCHOR_ENABLED and SHARP_HCAP_ANCHOR:
            _shp_rsp = _shp.get("rsp") if isinstance(_shp, dict) else None   # 锐线3WayH让球三项(独立变量,勿覆盖竞彩_rsp)
            if _shp_rsp and len(_shp_rsp) >= 3 and all(x is not None for x in _shp_rsp[:3]):
                hcap_sharp = _norm3(sharp_fair(_shp_rsp, _shp.get("src", 1)))
        # v5.7 锐线方向优势门：最大两方向差<SHARP_HCAP_MARGIN视为方向不明,不硬覆盖矩阵(回归实证0.3pp级argmax会把对的改错)
        sharp_ambiguous = False
        if hcap_sharp:
            _top = sorted(hcap_sharp, reverse=True)
            sharp_ambiguous = (_top[0] - _top[1]) < SHARP_HCAP_MARGIN
        matrix_hcap = tuple(handicap(M, hand))   # v5.8.8 自有矩阵(DC+让平对角线τ)让球三项：恒算留档，供与锐线并列，不参与下方选源
        if hcap_sharp and not sharp_ambiguous:
            hH, hD, hA = hcap_sharp
            hcap = list(hcap_sharp); hcap_src = "Pinnacle3WayH"
        else:
            hH, hD, hA = matrix_hcap
            hcap = list(matrix_hcap)
            hcap_src = "matrix(锐线方向不明回退)" if sharp_ambiguous else "matrix"
        m["_hcap_sharp"] = hcap_sharp; m["_hcap_ambiguous"] = sharp_ambiguous
        m["_hcap_matrix_raw"] = list(matrix_hcap)
        # v5.8.8 让球两源分歧(纯只读派生，绝不覆盖最终hcap/hd/选注)：模型τ首选 vs 锐线首选、让平概率差、客观是否分歧
        _div = None
        if hcap_sharp:
            _pm = int(max(range(3), key=lambda k: matrix_hcap[k]))
            _ps = int(max(range(3), key=lambda k: hcap_sharp[k]))
            _gap = float(matrix_hcap[1] - hcap_sharp[1])
            _div = dict(matrix=list(matrix_hcap), sharp=list(hcap_sharp), pick_m=_pm, pick_s=_ps,
                        draw_gap=_gap, warn=bool((_pm != _ps) or abs(_gap) >= HCAP_DIVERGE_DRAW_GAP))
        m["_hcap_diverge"] = _div
        hcap_raw = list(hcap)
        hcap = calib_apply("H", hcap, lh, la)     # v5.7.1 让球概率同步过校准层(v5.8.3建议③携带λ供分层)
        hd = max(range(3), key=lambda k: hcap[k])
        m["_hcap_raw"] = hcap_raw
        cover = None if d1 == 1 else ((d1 == 0 and hd == 0) or (d1 == 2 and hd == 2))
    else:
        # 让球盘口缺失：不崩，让球玩法H整体跳过(有rsp也无法定让球方向)，其余玩法照常
        hcap, hd, cover = None, None, None
        m["_hcap_matrix_raw"] = None; m["_hcap_diverge"] = None
    m["_hcap_src"] = hcap_src
    # v5.8.6 H腿独立数据源标记：概率直取Pinnacle3WayH锐线让球，或模型λ本身独立(stat/手填/锐线_model_indep)→独立；
    # 仅由竞彩spf(+欧赔1X2)反演矩阵(hcap_src=matrix*)且_model_indep=False→跨市场换皮、非独立(F3判伪EV)
    _h_indep = (hcap_src in H_INDEP_SRCS) or bool(_model_indep)
    m["_h_indep"] = _h_indep
    tg = tg_from_matrix(M)
    sc_k = sc[0][1] + sc[0][2]
    tg_peak = max(range(8), key=lambda k: tg[k])
    # v5.8.2 净胜球分布×亚盘全档（纯只读派生：从同一个最终矩阵M聚合，不改one/hcap/tg等任何现有结果；开关在CONFIG）
    gdiff = goal_diff_snapshot(M, hand) if ASIAN_GOALDIFF_ENABLED else None

    # —— 每场四玩法“首选腿”（单选；概率最大导向）——
    sh = m.get("sharp")
    _sh_spf = sh.get("spf") if isinstance(sh, dict) else None
    _sh_rsp = sh.get("rsp") if isinstance(sh, dict) else None
    sh_spf_ok = bool(_sh_spf) and len(_sh_spf) >= 3 and all(x is not None for x in _sh_spf[:3])
    sh_rsp_ok = bool(_sh_rsp) and len(_sh_rsp) >= 3 and all(x is not None for x in _sh_rsp[:3])
    fair_1x2 = sharp_fair(_sh_spf, sh.get("src", 1)) if sh_spf_ok else None
    vsrc_1x2 = "sharp" if fair_1x2 else ("euro" if has_euro else None)
    if fair_1x2 is None and has_euro:
        # v5.4 无Pinnacle时，用百家欧赔均值去水后的公允十进制赔率作1X2静态价值基准（仅对同源胜平负W有效，
        # 不覆盖让球/比分/总进球——那些是另一市场，混用会重蹈F3跨源伪EV）。
        fair_1x2 = [1.0 / max(q, 1e-9) for q in q_euro]
    fair_h = sharp_fair(_sh_rsp, sh.get("src", 1)) if sh_rsp_ok else None
    vsrc_h = "sharp" if fair_h else None
    legs = []
    # W 胜平负首选
    if spf_ok:
        legs.append(dict(mk="W", pick=DIR[d1], p=one[d1], sp=_spf[d1], d=d1, vsrc=vsrc_1x2,
                         clv=clv_one(_spf[d1], fair_1x2[d1]) if fair_1x2 else None))
    # H 让球首选（价值基准fair_h仅来自让球锐线sharp.rsp；欧赔均值是1X2市场，不跨源给让球定价）
    # v5.7.4终审修复：【出票SP恒取竞彩让球rsp】(用户在竞彩实际按此价买入,票面/EV/凯利/返还必须用竞彩价)；
    #   Pinnacle的_shp_rsp只用于让球概率主锚(hcap,见上)与公允基准fair_h。旧版锐线齐全时_hsp误用Pinnacle价,
    #   使 clv=pin/(pin/返还率)-1 恒≈-(1-返还率)(src1恒-2%),让球价值注被H2闸门永久误杀,且票面赔率并非竞彩可买价。
    _hsp = _rsp if (_rsp and len(_rsp) >= 3 and all(x is not None for x in _rsp[:3])) else None
    if hcap is not None and _hsp:
        _sp_h = _hsp[hd]
        legs.append(dict(mk="H", pick=HC_NAME[hd], p=hcap[hd], sp=_sp_h, d=hd, vsrc=vsrc_h, hindep=_h_indep,
                         clv=clv_one(_sp_h, fair_h[hd]) if (fair_h and _sp_h is not None) else None))
    # S 比分首选：红灯⑩合规16格里概率最高者（单选，非复式）
    ssp = m.get("ssp")
    for p_, i, j in sc:
        if (i, j) in REG_SCORE:
            sp_s = ssp.get((i, j)) if ssp else None
            legs.append(dict(mk="S", pick=f"{i}-{j}", p=p_, sp=sp_s, d=score_dir(i, j), clv=None, vsrc=None))
            break
    # T 总进球首选：红灯⑪只在0-4档取峰值（单选）
    tsp = m.get("tsp")
    k_tg = max(range(TG_MAX_GOAL + 1), key=lambda k: tg[k])
    sp_t = tsp[k_tg] if (tsp and k_tg < len(tsp)) else None
    legs.append(dict(mk="T", pick=f"{k_tg}球", p=tg[k_tg], sp=sp_t, d=None, clv=None, vsrc=None))

    # —— 全结果腿（仅维度二“价值最优”用：EV依赖SP，次选结果可能赔率更值，故全结果枚举）——
    ssp = m.get("ssp")
    all_legs = []
    if spf_ok:
        for k in range(3):
            all_legs.append(dict(mk="W", pick=DIR[k], p=one[k], sp=_spf[k], d=k, vsrc=vsrc_1x2,
                                 clv=clv_one(_spf[k], fair_1x2[k]) if fair_1x2 else None))
    if hcap is not None and _hsp:
        for k in range(3):
            all_legs.append(dict(mk="H", pick=HC_NAME[k], p=hcap[k], sp=_hsp[k], d=k, vsrc=vsrc_h, hindep=_h_indep,
                                 clv=clv_one(_hsp[k], fair_h[k]) if (fair_h and _hsp[k] is not None) else None))
    for i, j in sorted(REG_SCORE):  # 红灯⑩合规16个比分格全列（维度二按价值挑，非复式）
        all_legs.append(dict(mk="S", pick=f"{i}-{j}", p=M[i][j],
                             sp=ssp.get((i, j)) if ssp else None, d=score_dir(i, j), clv=None, vsrc=None))
    for k in range(TG_MAX_GOAL + 1):  # 红灯⑪总进球0-4共5档全列
        all_legs.append(dict(mk="T", pick=f"{k}球", p=tg[k],
                             sp=(tsp[k] if (tsp and k < len(tsp)) else None), d=None, clv=None, vsrc=None))

    # v5.3.6 F3：胜平负W的概率与spf同源(其负EV是"诚实的"，会被EV门槛自然过滤)；让球/比分/总进球(H/S/T)
    # 的概率来自矩阵、SP却来自另一个市场(rsp/ssp/tsp)=跨市场cross，纯市场反演时其raw-EV结构性不可信。
    for L in legs:
        L["cross"] = (L["mk"] != "W")
    for L in all_legs:
        L["cross"] = (L["mk"] != "W")
    style = None  # v5.8.3建议②：攻守风格画像(纯只读派生,try自容错,绝不影响概率)
    if STYLE_PROFILE_ENABLED:
        try:
            style = style_profile(lh, la, m)
        except Exception:
            style = None
    return {"m": m, "lh": lh, "la": la, "lt": lt, "one": one, "d1": d1, "sc": sc,
            "sc_k": sc_k, "tg_peak": tg_peak, "hcap": hcap, "hd": hd, "tg": tg,
            "gdiff": gdiff, "style": style,
            "dir_ok": dir_ok, "cover": cover, "dl": abs(lh - la),
            "mtype": match_type_of(abs(lh - la), dir_ok),
            "lsrc": lsrc, "indep": indep, "mkt1x2": mkt_q, "igain": igain,
            "base_lh": base_lh, "base_la": base_la, "fuse": m.get("_v54", {}),
            "legs": legs, "all_legs": all_legs}


def combo_category(mk1, mk2):
    if mk1 == mk2:
        return {"W": "A", "H": "B", "S": "C", "T": "D"}[mk1]
    return "E"


def leg_ev_min(mk):
    return EV_LEG_EXOTIC if mk in ("S", "T") else EV_LEG_WDL


def build_combos(A, attr="legs"):
    """枚举所有【跨场】腿对（红灯⑤同场禁串），产出六分类2串1组合。
    attr='legs'=每场每玩法首选(维度一概率最优，已证首选即全局概率最优)；
    attr='all_legs'=全结果(维度二价值最优，因EV依赖SP需枚举次选结果)。"""
    all_legs = []
    for a in A:
        for L in a[attr]:
            all_legs.append((a["m"]["no"], a["m"]["lg"], L, a))
    combos = []
    for (n1, lg1, L1, a1), (n2, lg2, L2, a2) in itertools.combinations(all_legs, 2):
        if n1 == n2:
            continue  # 红灯⑤同比赛多玩法禁串
        cat = combo_category(L1["mk"], L2["mk"])
        rho_hi, rho_mid = rho_of(lg1, L1["mk"], L1["d"], lg2, L2["mk"], L2["d"])
        same_lg = lg1 == lg2
        pc_raw = L1["p"] * L2["p"]                                   # v5.3.2 真实联合概率(EV/Kelly/联合配仓用)
        pc = pc_raw * (RHO_SAME_LG if same_lg else 1.0)             # 同联赛保守折减→仅维度一展示/排序
        spc = (L1["sp"] * L2["sp"]) if (L1["sp"] is not None and L2["sp"] is not None) else None
        ev = pc_raw * spc - 1 if spc is not None else None          # 期望值必须用真实概率,不被0.95污染
        # v5.3.6 F3：跨市场腿(H/S/T，概率来自spf矩阵、SP来自rsp/ssp/tsp)必须在该场有独立概率来源(indep)，
        # 否则其raw-EV只是两套抽水/定价错位造成的伪价值。胜平负W同源，恒视为可信(负EV会被门槛正常过滤)。
        def _leg_trusted(L, a):
            # v5.8.6 H让球腿独立数据源硬门槛：只认腿上hindep(3WayH锐线让球直取 或 stat/手填/锐线λ独立模型)；
            # 仅spf(+欧赔1X2)反演矩阵的H腿hindep=False→不可信。W同源恒可信；S/T维持原"场级indep"判据不变。
            if L.get("mk") == "H" and H_LEG_INDEP_GATE:
                return bool(L.get("hindep", False))
            return (not L.get("cross", False)) or bool(a.get("indep", False))
        t1, t2 = _leg_trusted(L1, a1), _leg_trusted(L2, a2)
        ev_trusted = t1 and t2
        bad_no = []
        if not t1: bad_no.append(n1)
        if not t2: bad_no.append(n2)
        combos.append(dict(cat=cat, pc=pc, pc_raw=pc_raw, spc=spc, ev=ev, rho_hi=rho_hi, rho_mid=rho_mid,
                           ev_trusted=ev_trusted, untrusted=("、".join(bad_no) if bad_no else ""),
                           a1=a1, a2=a2,
                           same_lg=same_lg, n1=n1, lg1=lg1, L1=L1, n2=n2, lg2=lg2, L2=L2))
    return combos


def leg_ev_ok(L):
    if L["sp"] is None:
        return False
    return (L["p"] * L["sp"] - 1) >= leg_ev_min(L["mk"])


def investable(c):
    # 维度二硬过滤：两腿都有SP + 组合EV≥0.15 + 各单腿EV达标 + ρ上限<0.3
    if c["spc"] is None or c["ev"] is None:
        return False, "无比分/总进球或胜平负SP"
    miss = []
    # v5.3.6 F3：跨市场腿无独立概率来源→raw-EV不可信，维度二直接剔除(不再让伪+EV进价值榜)
    if c.get("ev_trusted", True) is False:
        miss.append(f"raw-EV不同源不可信(场{c.get('untrusted','')}概率由胜平负反演却配让球/比分/总进球SP,且无stat/锐线/手填λ)")
    if c["ev"] < EV_COMBO_MIN:
        miss.append(f"组合EV={c['ev'] * 100:.1f}%<15%")
    if not leg_ev_ok(c["L1"]):
        miss.append(f"{c['n1']}单腿EV不足")
    if not leg_ev_ok(c["L2"]):
        miss.append(f"{c['n2']}单腿EV不足")
    if c["rho_hi"] >= RHO_BLOCK:
        miss.append(f"ρ上限{c['rho_hi']:.2f}≥0.3")
    return (len(miss) == 0), ("；".join(miss) if miss else "全部硬约束满足(仍需每腿CLV≥+3%/置信度S+)")


def fmt_leg(no, L):
    sp = f"@{L['sp']:.2f}" if L["sp"] is not None else "@SP待补"
    return f"{no}{MK_LABEL[L['mk']]}[{L['pick']}]({L['p'] * 100:.1f}%{sp})"


def line():
    print("=" * 108)


# ===================== §A 联网AI研究总指令（整块复制发给联网AI；show_brief()可再打印） =====================
RESEARCH_BRIEF = r'''
你是足球竞彩【联网数据研究分析员】。请自动联网检索并深度研究，用户不手填、不核验任何数据，全部由你用浏览器/检索取数。严格遵守：
【数据铁律】①每条赔率/战绩/伤停标注[来源+抓取时间]；②关键数据≥2个独立来源交叉，冲突如实标注；
③查不到的字段填 null，【绝不编造/插值/想当然】；④不点击任何"充值/下注/注册送彩金/山寨博彩"链接；
⑤境外站(Pinnacle/Betfair/OddsPortal)不翻墙：能开则取，不能开改用国内可及的等值源并在 sharp.src 标注。

【v5.4 21点早盘场景(最重要)】用户每天21:00前购买、比赛多在次日00:30-07:00凌晨，你取数时点就是21:00前，
读"当前时点"数据即可，【不要等也不要要求"出票前60分钟临场数据"——用户做不到】。因此：
(1) 首发通常未官宣：用跟队记者/赛前发布会的【预测/预计首发+已确定伤停名单】，lineup.status 填 "expected"(预计齐整)
    而非 unknown；只有真拿到官宣才填 confirmed；核心伤停必须量化 impact_h/impact_a。
(2) 赔率取21点前当前值，并尽量同时给最初初盘 spf_open(用于识别已发生的变盘方向/幅度)。
(3) 战意以"数学形势(积分/出线)+赛前发布会表态"为准，motivation.dual 在早盘允许 false 但 math 必填。

★【v5.4 必采核心：百家欧赔均值 euro_avg(免翻墙、比Pinnacle更现实的全球共识主锚)】
 竞彩官方SP抽水约13%(overround≈1.13)，必须用更低抽水(≈1.05)的【百家欧赔平均赔率】做独立锚，否则模型只是复读竞彩。
 请用浏览器打开下列【国内可直达】站点的该场"欧赔/欧洲指数"页，读取"百家平均/平均赔率"的[主胜,平,客胜]十进制赔率：
   · 500彩票网 odds.500.com（欧赔页"平均赔率"行；赛程从 trade.500.com/jczq 或 live.500.com 按队名找场次）
   · 澳客 okooo.com、足彩网 zgzcw.com、雪缘园/nowscore（任一可达即可，优先取到"百家平均"的两个源交叉）
   填 euro_avg=[主,平,客](与spf同一21点时点)；并填 euro_disp=百家公司赔率的离散度(标准差或最大偏离,用百分数如0.12表示12%,取不到null)。
   这些站欧赔页是JS渲染、程序直连会被反爬，【必须由你用浏览器渲染后读取页面数值】，不要因为接口报错就放弃。
   若所有欧赔站都打不开，euro_avg 填 null 并在 _warn 标注"缺百家欧赔均值"，此时模型只能复读竞彩、会建议空仓。
  ★【v5.8.1 必采核心②：stat 统计λ原料(与euro_avg并列P0；缺它引擎只能走'纯市场λ'=复读赔率、丧失独立统计判断)】
   stat 必须按【主/客场分开】给齐 10 个字段(用总战绩混算是错的)：
     · 联赛基准：lg_hgf 该联赛【主场】场均进球、lg_hga 主场场均失球；lg_agf【客场】场均进球、lg_aga 客场场均失球；
     · 主队(只算本赛季主场)：h_n 主场场次、h_gf 主场总进球、h_ga 主场总失球；
     · 客队(只算本赛季客场)：a_n 客场场次、a_gf 客场总进球、a_ga 客场总失球；另 promoted_round=当前轮次(升班马前5轮强收缩)。
   取数路径：500/澳客『战绩→主场/客场』分页与联赛统计页(主客拆分)，能开再用 FBref/SofaScore 的 home/away 表交叉；
   优先近10场口径，某队样本<5场则该队字段可 null 但联赛四基准尽量给；查不到整段 null，禁止用印象编场均。

■ 每场必须检索并给出下列字段(键名严格一致，单位：SP为十进制小数赔率，λ相关只给原始量、不要自己算λ/概率/EV)：
  no编号,lg联赛,time开赛,home主队,away客队,hand让球(【主让为负、客让为正】整数),
  season_stage(early1_3/r4_5/summer/normal/last2),round当前轮,promoted是否升班马,
  leg/cup/group_state/twoleg(杯赛/小组/两回合信息,无则null)。
  四玩法SP(当前+最初初盘都要)：spf=[主胜,平,客胜](当前),spf_open=[主,平,客](最初初盘,供赔率异动/降赔基准),
  rsp=[让胜,让平,让负](当前),rsp_open=[让胜,让平,让负](初盘)，
  ssp=比分SP对象【必须覆盖0-0,1-0,...到3-3共16个常规格,键如"1-2"；另可附胜其他/平其他/负其他】(缺格则该比分EV无法算),
  tsp=总进球0,1,2,3,4,5,6,7+八档列表，
  ou={"line":大小球盘口线,"over":大球水位,"under":小球水位},open_single各玩法是否单关,odds_move降赔/升赔方向与幅度。
  euro_avg=[百家欧赔平均主胜,平,客胜](v5.4全球共识主锚,见上,必尽力给),euro_disp=百家离散度(0-1小数,如0.12)。
  半全场只记录"是否在售"(红灯③禁飞、不采SP、不参与选串)。
  sharp锐线【全力搜索Pinnacle级】：优先 Pinnacle(src=1)→Betfair(src=2)→OddsPortal(src=3)；
  三者都不可达时，用国内可及的等值锐利盘(必发交易所成交价/澳门/平博/Pinnacle国内收录页,src=9并注明名称)；
  给 {"src":1/2/3/9,"spf":[主,平,客],"rsp":[...],"ou":{line,over,under},"kind":live/close,"time":时间}；完全无则null。
  stat统计λ原料(照维度1)：lg_hgf联赛主场场均进球,lg_agf联赛客场场均进球,lg_hga联赛主场场均失球,lg_aga联赛客场场均失球；
  h_n主队本赛季主场场次,h_gf主队主场进球,h_ga主队主场失球；a_n客队本赛季客场场次,a_gf/a_ga同理；promoted_round升班马轮次。
  dims十二维：核心 1_poisson/2_oddsmove/7_motivation(有证据true)；辅助 3_kelly/4_volume/5_dispersion/6_h2h/
  8_public/9_xg/10_elo/11_euasian(取到给数值/简述,取不到null)；12_referee裁判(留档)。
  ★v5.5【国内网络可及·全量影响因子采集清单(浏览器渲染读取,尽量找齐;每一项都要带来源,取不到显式null,禁止编造)】：
   A 赔率/市场族：①百家欧赔平均euro_avg[主,平,客]与最高/最低、②离散度euro_disp(公司分歧)、③初盘spf_open与
     即时盘的赔率移动方向/幅度(对应2_oddsmove)、④亚盘让球+大小球盘口及水位变化(11_euasian)、⑤必发/交易所
     主胜平负成交量占比与大单方向(4_volume)、⑥各家凯利指数(3_kelly)、⑦大众投注比例/热度(8_public,新浪/澳客/500彩票网)。
   B 实力/状态族：⑧近10场&主/客场近5场进失球、进失球xG/xGA(9_xg,FBref/understat若可及,否则null)、
     ⑨Elo评分或联赛排名与积分差(10_elo)、⑩近5个赛季交锋H2H(6_h2h)、⑪伤停/停赛/轮换名单与缺阵球员对攻防的权重影响、
     ⑫预计/已官宣首发(expected/confirmed)、⑬赛程密度:距上场休息天数与未来3天是否一周双赛/关键战、
     ⑭战意数学形势(7_motivation,见下)、⑮教练战术/换帅、⑯升班马/主客场龙虫。
   C 环境/外部族：⑰当值主裁及其主场胜率/判点/红黄牌倾向(12_referee)、⑱天气(雨/风/温度)与场地、
     ⑲默契球/积分互利/已出线轮换(collusion)、⑳赛前突发(罢训/欠薪/换帅/伤病反复,breaking)。
   优先保证 A①②⑦ 与 B⑪⑫⑭(对21点早盘最关键)；其余能取则取，取不到一律null并在src注明，不允许用印象填充。
  战意背景(用于判定motiv档位,请给客观事实)：双方排名/与争冠欧战保级线差距、小组出线形势(争净胜球/锁定第一/
  荣誉/必须赢/打平出线/已出线出局)、两回合首回合比分与客场进球、未来3天关键战/轮换官宣、默契球或积分互利(无则填无)。
  ★v5.3.3【语义核查review块(必做,替代人工审核;每子项必须带src来源链接,查不到显式unknown/none,禁止默认利好)】：
   "review":{
    "lineup":{"status":"confirmed(已官宣首发齐整)/expected(v5.4早盘:预测首发齐整+伤停已核)/key_missing(核心缺阵)/unknown(未拿到首发)",
              "missing":"缺阵球员与位置","impact_h":主队加性球数(核心缺阵-0.2~-0.4,无0),"impact_a":客队同,"src":"...","note":"..."},
    "motivation":{"dual":true/false(数学形势+官宣轮换两条证据都在才true),"math":"如保级必须赢/已出线无欲",
                  "official":"主帅/球队官宣的轮换或全主力表述","motiv_h":主队战意1.4/1.2/0.7/0.5/1.0,"motiv_a":客队同,"src":"..."},
    "collusion":{"level":"none/watch/high(默契球/积分互利风险)","note":"","src":"..."},
    "breaking":{"level":"none/watch/block(赛前24h训练伤退/罢训/换帅/财务舆情)","items":[],"time":"","src":"..."},
    "weather":{"cond":"晴/多云/阴/小雨/雨/大雨/暴雨/雪/大风","temp":温度,"wind":风速,"src":"开赛城市天气预报链接"}
   }。
   说明：核心缺阵且你能据近6场样本估出进球影响就给impact(引擎并入λ)、估不出impact_h/a也要把status设key_missing(引擎会拦实盘)；
   天气按实际选cond,引擎自动映射节奏系数(大雨0.91等),不要自己改λ。
  状态校准(只在有确凿证据时给,否则省略让引擎取默认)：weak_coeff弱信息乘子,可选键 weather(大雨0.91)/
  referee(裁判黄牌>4取0.95)/rest(少休≥3天0.93、多休1.03)/tactic(逼抢1.10、密集0.90)/coach(永久新帅前5场1.05)/lsc/ctc,
  连乘由引擎自动封顶[0.90,1.15]、无证据全部省略；
  motiv_h/motiv_a(结构性战意:拼命1.4/争取1.2/中游0.7/放假0.5,须保级争冠数学状态+首发官宣双确认,否则1.0)；
  inj_h/inj_a(核心伤停【加性球数】-0.2~-0.4,近6场样本已含其缺阵则0;无伤停0)。
  g5：仅当竞彩平赔∈[3.20,3.70]时给九项信号状态,否则null。
  资金档默认 bankroll_tier="std",L=0,W=0,DD=0.0,idle_days=0(用户另有要求再改)。
■ λ六步/概率/CLV/EV/凯利/组合【一律不要你计算】——全部由选串引擎用你给的原始量精确计算，避免双重口径。
■ v5.1免费锐线最大化（重点补让球3维）：配免费 RapidAPI「PinBook Odds」key 即全自动拿 Pinnacle 的1X2+大小球+3维让球；
  无key时1X2/大小球按 Pinnacle→Betfair→OddsPortal→国内等值(src9)回退；让球必须找 3-Way/European Handicap 且线与hand一致的【三项】，禁止2维水换算；取不到填null记来源。
■ 输出格式：【只输出一个 JSON 数组】，用 ```json 代码块包裹，每场一个对象，键名如上，缺项填 null，不要任何解释文字。
■ 输出前自检(对应采集口令30项)：四玩法SP是否齐、【euro_avg百家欧赔均值是否每场都给(缺则模型只能复读竞彩、会建议空仓)】、
  锐线是否尽力三级回退、stat四基准+双方主客样本是否齐、
  核心4维(泊松原料/赔率异动/战意/锐线或CLV前置)任一缺失请在该对象加 "_warn":["缺项名"] 显著标注；
  v5.3.3还须确认每场 review 块五子项(首发/战意双确认/默契球/突发利空/天气)都已联网核查并带src，未查到写unknown/none。
■ Pinnacle加拿大镜像(pinnacle.ca)页面给的是【美式赔率】(如-138/+301)，你可直接把美式数字填进sharp.spf/ou，引擎自动换算；
  也可按"编号|spf 主 平 客|ou 线 大 小|rsp 让胜 让平 让负"每行一场整理进文件SHARP_TEXT(美式十进制混写均可)。
'''


def show_brief():
    print(RESEARCH_BRIEF)


# ===================== §B AI回填区：把联网AI输出的JSON粘进 AI_JSON（无需手抄字段） =====================
AI_JSON = r""""""   # 粘贴形如：```json [ {"no":"001",...}, ... ] ```；也可用 load_ai_file("路径.json")


def _to_num(x):
    if x is None or isinstance(x, bool):
        return None if x is None else x
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace('%', '')
    if s in ('', '—', '-', 'None', 'null', '无', '未获取', 'N/A', 'na', 'NA'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_list(x):
    if isinstance(x, list):
        return [_to_num(v) for v in x]
    return None


def parse_ai_json(text):
    """把联网AI按RESEARCH_BRIEF输出的JSON解析成MATCHES(自动类型清洗/空值归一)，免手填。"""
    if not text or not text.strip():
        return []
    m = re.search(r'```(?:json)?\s*(.*?)```', text, re.S)
    raw = m.group(1) if m else text
    br = re.search(r'\[.*\]', raw, re.S)
    if br:
        raw = br.group(0)
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("AI回填必须是JSON数组(每场一个对象)")
    out = []
    for d in data:
        try:
            rec = dict(d)
            for k in ('spf', 'rsp', 'spf_open', 'rsp_open', 'tsp', 'euro_avg'):
                if k in rec:
                    rec[k] = _to_list(rec[k])
            for k in ('avg', 'lh', 'la', 'hand', 'motiv_h', 'motiv_a', 'inj_h', 'inj_a', 'euro_disp'):
                if k in rec:
                    rec[k] = _to_num(rec[k])
            if isinstance(rec.get('ou'), dict):
                rec['ou'] = {k: (_to_num(v) if k in ('line', 'over', 'under') else v)
                             for k, v in rec['ou'].items()}
            for dk in ('stat', 'weak_coeff'):
                if isinstance(rec.get(dk), dict):
                    rec[dk] = {k: _to_num(v) for k, v in rec[dk].items()}
            if isinstance(rec.get('sharp'), dict):
                sh = rec['sharp']
                for k in ('spf', 'rsp'):
                    if k in sh:
                        sh[k] = _to_list(sh[k])
                if isinstance(sh.get('ou'), dict):
                    sh['ou'] = {k: (_to_num(v) if k in ('line', 'over', 'under') else v)
                                for k, v in sh['ou'].items()}
            _coerce_record(rec)   # v5.3.2 出口统一：定长+ssp字符串键转元组，修比分SP丢失/缺档崩溃
            out.append(rec)
        except Exception as _e:
            print(f"⚠ parse_ai_json 跳过一条无法解析的记录: {_e}")
    return out


def load_ai_file(path):
    with open(path, encoding='utf-8') as fh:
        return parse_ai_json(fh.read())


# ===================== 每日输入区（只改这里） =====================
# ━━━━━━━━━━━━━ 单场字段填写模板（与《数据采集口令v1.4》单场数据卡逐项对应，照卡填即可，无需另做对照表）━━━━━━━━━━━━━
# 复制下面整块、去注释后填值；★=参与选串/仓位计算，☆=采集留档(用于置信度计数或体检回显，不改变概率)。
# 任何字段缺省都可省略：只填简填版(见下方MATCHES)也能跑，此时无锐线→只出概率与理论仓位、实盘比例=0。
#
# {  # ──【1.基础信息】──
#   "no":"001", "lg":"英超",                 # ★编号/联赛(跨场串关、同联赛折减、ρ判定用)
#   "time":"2026-09-05 21:00", "home":"主", "away":"客",  # ☆开赛时间/主客队(CLV时效与留档)
#   "hand":-1,                                # ★让球盘口带方向：主让1球填-1、客让1球填+1(与让球SP顺序一致)
#   "season_stage":"normal",   # ★赛季阶段系数:early1_3(初1-3轮×.5)/r4_5(4-5轮×.7)/summer(夏窗过渡×.9)/normal/last2(末2轮×.7)
#   "round":6, "promoted":None, "leg":None, "cup":None,    # ☆轮次/升班马(home/away/both)/互战(first/second)/杯赛阶段
#   "group_state":None, "twoleg":None, "future":None,      # ☆小组出线形势/两回合比分/未来留力·默契球(定性留档)
#   # ──【2.四玩法竞彩SP】（★全部参与概率/EV；初盘用于赔率异动留档，即时用于计算）──
#   "spf_open":[2.10,3.30,3.20],             # ☆胜平负【初盘】[主,平,客](降赔信号基准)
#   "spf":[2.00,3.40,3.30],                  # ★胜平负【即时】[主,平,客]；无则None并必须给lh/la
#   "rsp_open":[2.05,3.30,3.10],            # ☆让球【初盘】[让胜,让平,让负]
#   "rsp":[1.95,3.40,3.20],                  # ★让球【即时】[让胜,让平,让负]
#   "ssp":{(1,0):8.5,(2,1):8.0,...},         # ★比分即时SP，键(主队球,客队球)；可全抄31项,程序只聚合每队≤3球16格(红灯⑩)
#   "tsp":[11.0,5.2,3.6,4.2,6.5,11.0,19.0,26.0],  # ★总进球即时SP 8档[0,1,2,3,4,5,6,7+]；程序只用0-4(红灯⑪)
#   "ou":{"line":2.5,"type":"half","over":1.95,"under":1.85},  # ★大小球盘口线/类型/大小水位：v4.6起自动锚总λ(填了可免avg/lh/la)
#   "open_single":{"w":True,"h":False,"score":True,"tg":True}, # ☆单关开栓:胜平负/让球/比分/总进球 开售状态
#   "odds_move":{"drop":[],"rise":[],"draw_move":0.0},         # ☆降赔≥.10方向/升赔≥.15/平赔变动(红灯⑧/G5留档)
#   # ──【3.锐线】（★决定CLV与能否实盘；无则整段省略→该场无锐线、恒A级、2串1实盘=0）──
#   "sharp":{"src":1,                        # ★锐线来源:1=Pinnacle(÷.98)/2=Betfair(÷.97)/3=OddsPortal(÷.96)
#            "spf":[1.90,3.30,3.80],         # ★胜平负三项【原始】锐线赔率(去水/CLV程序自动算,勿自己除)
#            "rsp":None,                     # ☆让球锐线三项(尽力采,有则让球腿也计CLV)
#            "ou":None,                      # ☆大小球锐线(留档)
#            "kind":"live", "time":"20:05"}, # ☆性质live即时/close收盘 + 抓取时间(≤1h按收盘,缺时间戳无效)
#   # ──【4.十二维】（★前3核心+8辅助决定置信度；其余为λ/定性原料留档）──
#   "dims":{
#     "1_poisson":True, "2_oddsmove":True, "7_motivation":True,  # ★核心3维:泊松原料/赔率异动/战意(任一False→不可进投注计算)
#     # ★辅助8维:采到填True(或数值),缺省留None;核心4齐+辅助数→有锐线定级 10-12=S+/7-9=S/5-6=B/≤4=C
#     "3_kelly":None,"4_volume":None,"5_dispersion":None,"6_h2h":None,
#     "8_public":None,"9_xg":None,"10_elo":None,"11_euasian":None,
#     "12_referee":None,                     # ☆裁判(经验弱信号,只留档不计置信度)
#     "poisson_raw":None,                    # ☆λ原料:近6主客场进失/联赛4基准/赛季累计/近10与11-30滑窗(dict,留档)
#     "injuries":None,"weather":None,"rest_days":None,"tactic":None,"coach_change":None},  # ☆伤停/天气/休息/战术/换帅(留档)
#   # ──【5.G5平局专项】平赔∈[3.20,3.70]时把九信号状态填这里(☆留档) ──
#   "g5":None,
#   # ──【6.用户自填·仓位动态】（★驱动凯利base/资金档/动态系数；缺省=标准档/L0W0无回撤）──
#   "bankroll_tier":"std",     # ★资金档:small(<1万,按标准)/std(1-5万,×1.0)/5w(5-10万,×.8)/10w(≥10万,×.72)
#   "L":0, "W":0, "DD":0.0,    # ★连输日/连赢日/当前回撤%(L≥4或DD≥20停投;L3且DD≥5停投)
#   "idle_days":0,             # ☆连续未投注天数(10-30天L系数再×.8,>30重置)
#   "peak":None,"inflight":None,"used_f":None,  # ☆峰值资金/在途清单/2串已用f占比(组仓·日仓留档)
#   # ──λ与赛果 ──
#   "avg":2.75,                # ★总λ预期:仅当未填ou大小球、也未手填λ时才需要(退化反演);填了ou可省略
#   "lh":None, "la":None,      # ★手填主/客λ(最高优先级人工覆盖;不填则走下面六步自动)
#   # ──v4.7 λ六步自动校准(照采集卡维度1/维度7填原始数,无需手算λ)──
#   "stat":{  # 统计λ原料(Atk/Def联赛标准化+小样本收缩);整块不填=不做统计λ,只用市场λ
#     "lg_hgf":联赛主场场均进球,"lg_agf":联赛客场场均进球,"lg_hga":联赛主场场均失球,"lg_aga":联赛客场场均失球,
#     "h_n":主队本赛季主场场次,"h_gf":主队主场进球,"h_ga":主队主场失球,
#     "a_n":客队本赛季客场场次,"a_gf":客队客场进球,"a_ga":客队客场失球,
#     "promoted_round":None},  # 升班马当前轮次(1-5时小样本k=20,否则k=12;非升班马留None)
#   "weak_coeff":{},           # 弱信息乘子(无证据全留空=1.0):weather大雨0.91/referee0.95/rest/tactic/coach/lsc/ctc,连乘自动封顶[0.90,1.15]
#   "motiv_h":1.0,"motiv_a":1.0,  # 结构性战意分乘各队λ(4.6.2拼命1.4/争取1.2/中游0.7/放假0.5;需数学状态+首发双确认,否则1.0)
#   "inj_h":0.0,"inj_a":0.0,    # 加性伤停球数(核心缺阵-0.2~-0.4,最后叠加;近6场已含其缺阵则0)
#   "res":None},               # ☆已开赛果(复盘留档,不参与当晚计算)
#
# 【实盘比例 f_live 放开条件(全过, 缺一即0)】两场都有锐线；每腿CLV≥+3%；组合置信度≥S+(有效维≥10)；
#   组合EV≥15%且单腿EV达标(胜负让球8%/比分总进球5%)；ρ上限<0.3；无SP>2.50博冷腿；动态系数>0(L/W/DD/赛季)。
MATCHES = [
    {"no": "001", "lg": "荷甲", "avg": 3.00, "spf": [5.35, 4.95, 1.35], "hand": 1,
     "rsp": [2.25, 3.95, 2.32], "res": "1:6"},
    {"no": "002", "lg": "韩K1", "avg": 2.55, "spf": [3.65, 3.22, 1.84], "hand": 1,
     "rsp": [1.73, 3.40, 3.80], "res": "3:1"},
    {"no": "003", "lg": "韩K1", "avg": 2.55, "spf": [2.77, 3.00, 2.30], "hand": 1,
     "rsp": [1.46, 3.60, 5.50], "res": "1:1"},
    {"no": "004", "lg": "德乙", "avg": 2.95, "spf": [1.65, 3.72, 3.93], "hand": -1,
     "rsp": [3.00, 3.30, 1.94], "res": "1:2"},
    {"no": "005", "lg": "瑞超", "avg": 2.75, "spf": [7.05, 5.00, 1.27], "hand": 1,
     "rsp": [2.98, 3.50, 1.90], "res": "3:2"},
    {"no": "006", "lg": "荷甲", "avg": 3.00, "spf": None, "hand": -2,
     "rsp": [2.09, 4.20, 2.42], "lh": 3.05, "la": 0.70, "res": None},
    {"no": "007", "lg": "挪超", "avg": 3.05, "spf": [1.20, 5.85, 8.00], "hand": -1,
     "rsp": [1.63, 4.30, 3.53], "lh": 2.30, "la": 0.83, "res": None},
    {"no": "008", "lg": "英超", "avg": 2.75, "spf": [2.13, 3.15, 2.92], "hand": -1,
     "rsp": [5.10, 3.95, 1.47], "res": "1:0"},
    {"no": "009", "lg": "英超", "avg": 2.75, "spf": [2.80, 3.10, 2.23], "hand": -1,
     "rsp": [5.26, 4.25, 1.42], "res": "1:1"},
    {"no": "010", "lg": "法甲", "avg": 2.70, "spf": [1.77, 3.30, 3.85], "hand": -1,
     "rsp": [2.40, 3.30, 2.50], "res": "3:0"},
]

# ===================== v5.5.2 赛后回流输入区（赛前出单不用填；赛后只改这里即可锁存对账）=====================
# ① ACTUAL_TICKETS=你21点【真金白银买下】的票(可与程序推荐不同；不买就留空[])。每张票：
#    name=备注；stake=本注本金(元)；payout=命中时【票面理论返还】(含本金，元，=2串1总赔×本金；未中返还0)；
#    legs=两条腿列表，每条=(场次编号, 玩法, 选项)：玩法 W胜平负(选项 主胜/平/客胜)、H让球(让胜/让平/让负)、
#    S比分(选项形如"1-1")、T总进球(选项形如"2球")。让球方向以该场 hand 为准(主让为负、受让为正)，与引擎一致。
ACTUAL_TICKETS = [
    # —— 021-024 那批 100 元娱乐覆盖单示例（实战替换成你当晚实际买的票）——
    # {"name": "注A", "stake": 48, "payout": 128, "legs": [("023", "H", "让负"), ("024", "H", "让胜")]},
    # {"name": "注B", "stake": 52, "payout": 135, "legs": [("022", "W", "主胜"), ("023", "H", "让负")]},
]
# ② POST_RESULTS=赛后终场比分(仅算90分钟+伤停补时，不含加时/点球)：{"编号":"主队进球:客队进球"}。
#    ★留空{}=赛前正常出单并锁存快照；填非空=赛后锁存结算模式：程序【不会】用赛后数据重算/覆盖赛前首选，
#      只读取赛前快照里锁存的首选来对比分，从根上杜绝"赛后赔率漂移污染命中率"。
POST_RESULTS = {
}
# ③ 赛后对账要读的快照文件；留空""=按批次自动选最近一份(snapshots/latest_批次.json，没有则取时间最新snapshot_*.json)。
SNAPSHOT_TO_SETTLE = ""


def _full_dims():
    d = {"1_poisson": True, "2_oddsmove": True, "7_motivation": True}  # 核心3维齐
    for _k in AUX_DIM_KEYS:        # 辅助8维采到即填(可填数值/True)，凑齐→有效12维=S+
        d[_k] = True
    return d


# ━━━━━━━━━ 填好的样例 SAMPLE_MATCHES（两场全字段：基础/初盘+即时SP/锐线/十二维/资金档，可直接运行）━━━━━━━━━
# 用途：演示“补了锐线+辅助维后，实盘比例 f_live 如何从0变为非0”。切换方法：令 MATCHES = SAMPLE_MATCHES
#       （或把 main() 第一行的 for m in MATCHES 换成 SAMPLE_MATCHES），即可看到终选①实盘比例非0的完整效果。
# 数值已验证：T1强主(主胜)×T2强客(客胜)，跨联赛+方向相反→ρ=0；竞彩SP均高于Pinnacle去水公平赔率→两腿CLV≈+4%；
#       核心3+辅助8=12维→S+；组合EV/单腿EV均达标、非博冷 → 终选①实盘比例=1.500%(被单场硬顶1.5%封顶)。
SAMPLE_MATCHES = [
    # T1 强主队：手填λ主2.30/客0.55；竞彩主胜2.00，Pinnacle主胜1.88→去水公平1.918→CLV≈+4.3%
    {"no": "T1", "lg": "样例甲", "time": "2026-09-05 21:00", "home": "样例甲主", "away": "样例甲客",
     "hand": -1, "season_stage": "normal", "avg": 2.8, "lh": 2.30, "la": 0.55,
     "spf_open": [2.15, 3.30, 3.50], "spf": [2.00, 3.40, 3.80],          # 胜平负 初盘/即时[主,平,客]
     "rsp_open": [2.10, 3.30, 3.20], "rsp": [1.95, 3.40, 3.30],          # 让球 初盘/即时[让胜,让平,让负]
     # "ssp": {(2, 0): 7.5}, "tsp": [11, 5.2, 3.6, 4.2, 6.5, 11, 19, 26],  # 有比分/总进球SP时再填
     # "ou": {"line": 2.5, "type": "half", "over": 1.95, "under": 1.85},
     "sharp": {"src": 1, "spf": [1.88, 3.30, 3.60], "rsp": [1.82, 3.30, 3.40],
               "kind": "live", "time": "20:05"},                          # 1=Pinnacle,只填【原始】赔率
     "dims": _full_dims(),
     "bankroll_tier": "std", "L": 0, "W": 0, "DD": 0.0, "idle_days": 0, "res": None},
    # T2 强客队：手填λ主0.55/客2.30；竞彩客胜2.05，Pinnacle客胜1.92→去水公平1.959→CLV≈+4.6%
    {"no": "T2", "lg": "样例乙", "time": "2026-09-05 23:00", "home": "样例乙主", "away": "样例乙客",
     "hand": 1, "season_stage": "normal", "avg": 2.8, "lh": 0.55, "la": 2.30,
     "spf_open": [3.50, 3.30, 2.20], "spf": [3.80, 3.40, 2.05],
     "rsp_open": [3.20, 3.30, 2.10], "rsp": [3.30, 3.40, 1.98],
     "sharp": {"src": 1, "spf": [3.60, 3.30, 1.92], "rsp": [3.40, 3.30, 1.86],
               "kind": "live", "time": "20:06"},
     "dims": _full_dims(),
     "bankroll_tier": "std", "L": 0, "W": 0, "DD": 0.0, "idle_days": 0, "res": None},
]
CAT_NAME = {"A": "A类·胜平负2串", "B": "B类·让球2串", "C": "C类·比分2串(单选)",
            "D": "D类·总进球2串(单选)", "E": "E类·混合跨玩法2串", "F": "F类·全场最高"}


def print_combo(c, idx=None):
    pre = f"{idx}. " if idx else "   "
    sp = f"{c['spc']:.2f}" if c["spc"] is not None else " SP待补"
    ev = f"{c['ev'] * 100:+.1f}%" if c["ev"] is not None else "  —  "
    ok, why = investable(c)
    # 博冷腿(红灯②单腿SP>2.50从严)；本工具无锐线，EV门槛达标≠可实盘投
    cold = ((c["L1"]["sp"] is not None and c["L1"]["sp"] > 2.50)
            or (c["L2"]["sp"] is not None and c["L2"]["sp"] > 2.50))
    if c["spc"] is None:
        state = "⚠无SP仅概率"
    elif not ok:
        state = "⚠" + why
    else:
        has_sh = confidence(c["a1"]["m"])[3] and confidence(c["a2"]["m"])[3]
        state = ("EV门槛达标·实盘另须双锐线+每腿CLV≥+3%+S+(见终选闸门)" if not has_sh
                 else "EV门槛达标·再核每腿CLV≥+3%/置信度S+(见终选闸门)")
        if cold:
            state += "；含SP>2.50博冷腿(红灯②从严)"
    rho_flag = f"ρ上限{c['rho_hi']:.2f}{'⚠禁组' if c['rho_hi'] >= RHO_BLOCK else ''}"
    lg_flag = "[同联赛×0.95]" if c["same_lg"] else ""
    print(f"{pre}[{c['cat']}] P={c['pc'] * 100:5.1f}% SP={sp:>6} EV={ev:>7} "
          f"{rho_flag}{lg_flag}")
    print(f"     {fmt_leg(c['n1'], c['L1'])} × {fmt_leg(c['n2'], c['L2'])}  → {state}")


def ckey(c):
    return (c["n1"], c["L1"]["mk"], c["L1"]["pick"],
            c["n2"], c["L2"]["mk"], c["L2"]["pick"])


def llegs(c):
    return {(c["n1"], c["L1"]["mk"], c["L1"]["pick"]),
            (c["n2"], c["L2"]["mk"], c["L2"]["pick"])}


def final_five(by_p, pool2):
    """从 维度一Top5 ∪ 六分类Top1 ∪ 维度二Top5 三榜中，按“核心-卫星”结构确定性收敛5注。
    v4.3：全局降相关贪心——每选下一注都对“当前全部已选”最小化共用腿（候选取该榜前3留降相关空间）。
    注意：这是给定模型/输入下的结构化取舍，不保证单次盈利——高概率注EV常为负，
    盈利只可能来自正EV注+足够样本+凯利纪律的长期收敛（见末尾数学说明）。"""
    cat_list = {cat: [c for c in by_p if c["cat"] == cat] for cat in "ABCDE"}  # 各类已按P降序
    chosen, used = [], set()
    leg_use = {}  # 每条腿已被几注使用

    def pick(cands, role, allow_block=False, topn=None):
        """风险调整排序：adj=P − DIV_PENALTY×Σ(共用腿已用次数)，每重复1条已用腿扣5pp当量，
        同adj再按P降序。topn=None=全候选（惩罚本身已平衡分散与概率，不硬截前3）。"""
        def adj(c):
            return c["pc"] - DIV_PENALTY * sum(leg_use.get(leg, 0) for leg in llegs(c))

        pool = []
        for c in (cands if topn is None else cands[:topn]):
            if ckey(c) in used:
                continue
            if c["rho_hi"] >= RHO_BLOCK and not allow_block:
                continue
            pool.append(c)
        if not pool:
            return False
        pool.sort(key=lambda c: (-adj(c), -c["pc"]))
        c = pool[0]
        used.add(ckey(c))
        for leg in llegs(c):
            leg_use[leg] = leg_use.get(leg, 0) + 1
        chosen.append((role, c))
        return True

    pick(by_p, "①稳健首选·命中锚")                       # 槽1 概率锚(无已用腿→纯P最高)
    if len(chosen) < FINAL_MAX_BETS:
        pick(by_p, "②稳健分散·降相关")                   # 槽2 扣减共用腿后最优(主动绕开①的腿)
    if FINAL_MAX_BETS >= 3:
        pick(cat_list.get("B", []), "③让球均衡·攻守平衡")     # 槽3 B类让球全候选降相关
        pick(pool2, "④价值首选·正EV(无锐线仅纸面)")           # 槽4 维度二正EV
        for cat in ("D", "C"):                           # 槽5 高赔小注覆盖(v5.3.2:ρ≥0.3禁组注不再进终选)
            if pick(cat_list.get(cat, []), "⑤高赔覆盖·最小注", allow_block=False):
                break
    for c in by_p:                                       # 不足注数用维度一合规组合补齐
        if len(chosen) >= FINAL_MAX_BETS:
            break
        pick([c], "补充")
    return chosen[:FINAL_MAX_BETS]


def validate_one(m):
    """轻量格式校验：返回问题清单；SP长度/锐线结构等格式错误直接指出（缺数据不报错，按缺省降级）。"""
    errs = []
    for key, n in (("spf", 3), ("spf_open", 3), ("rsp", 3), ("rsp_open", 3)):
        v = m.get(key)
        if v is not None and (len(v) < n or any(x is None for x in v[:n])):
            errs.append(f"{key}应有{n}个有效数值,实际{[x for x in (v or [])][:n]}")
    if m.get("tsp") is not None and (len(m["tsp"]) != 8 or any(x is None for x in m["tsp"])):
        errs.append(f"tsp应8档齐全,有效{sum(x is not None for x in m['tsp'])}/8(缺档按None降级,不崩)")
    sh = m.get("sharp")
    if sh:
        if sh.get("src") not in (1, 2, 3, 9):
            errs.append("sharp.src须为1(Pinnacle)/2(Betfair)/3(OddsPortal)/9(国内等值锐利盘)")
        if not sh.get("spf") or len(sh["spf"]) != 3:
            errs.append("sharp.spf须为3项原始锐线赔率")
    if m.get("rsp") is not None and m.get("hand") is None:
        errs.append("给了让球SP(rsp)却缺让球盘口hand→让球玩法已自动跳过,请补hand(主让为负)")
    if m.get("lh") is None and m.get("la") is None and not m.get("spf"):
        errs.append("未给spf反演时必须手填lh/la")
    return errs


def information_gain_report(A):
    """v5.3.6 F4：信息增量透明化 + 已赛场首页滚动命中/Brier（不必翻到末尾校准才看到准不准）。"""
    line()
    print("信息增量与已赛校准（F4：模型相对赔率去水有没有独立判断；带res场当场累计1X2命中/Brier）")
    line()
    igs = [a["igain"] for a in A if a.get("igain") is not None]
    n_indep = sum(1 for a in A if a.get("indep"))
    # v5.4 三源融合/早盘 汇总
    n_euro = sum(1 for a in A if (a.get("fuse") or {}).get("has_euro"))
    n_flip = sum(1 for a in A if (a.get("fuse") or {}).get("flipped"))
    n_early = sum(1 for a in A if (a.get("fuse") or {}).get("early"))
    print(f"  v5.4信源：百家欧赔均值锚 {n_euro}/{len(A)} 场、其中融合后相对竞彩方向翻转 {n_flip} 场；"
          f"21点早盘(> {EARLY_HOURS:g}h,仓位×{EARLY_STAKE_MULT:g}) {n_early} 场。")
    if igs:
        near = sum(1 for a in A if a.get("igain") is not None and a["igain"] < IGAIN_FLAT and not a.get("indep"))
        print(f"  共{len(A)}场：共识1X2与竞彩去水概率平均最大偏差 {sum(igs)/len(igs)*100:.1f}pp；"
              f"有独立概率来源(欧赔均值/stat/手填λ/锐线){n_indep}场、纯赔率复读{len(A)-n_indep}场。")
        if near >= max(1, (len(A)+1)//2):
            print("  ⚠过半场次增量≈0且无独立来源：当前引擎只是把竞彩赔率翻译成泊松再翻回，不具备超越市场的预测力；")
            print("    方向命中率≈市场热门，且竞彩约13%抽水使EV天生为负。要真正提精度，必须让豆包用浏览器补 euro_avg百家欧赔均值 或 stat战绩原料。")
    rows = []
    for a in A:
        ij = _res_ij(a["m"].get("res"))
        if ij is None:
            continue
        i, j = ij
        d = 0 if i > j else (1 if i == j else 2)
        rows.append((a, d))
    if rows:
        n = len(rows)
        hit = sum(1 for a, d in rows if max(range(3), key=lambda k: a["one"][k]) == d)
        br = sum(sum((a["one"][k] - (1 if k == d else 0)) ** 2 for k in range(3)) for a, d in rows) / n
        print(f"  已填赛果 {n} 场：1X2首选命中 {hit}/{n}={hit/n*100:.0f}%，多分类Brier={br:.3f}"
              f"（均匀猜测基线0.667，越低越好；模型≈市场时此值不会优于市场）。")
    print("  说明：≥30场的Brier/命中才具统计意义，小样本波动大，单日黑红不构成模型优劣结论。")


def print_input_report(A):
    """采集完整度/锐线/CLV/自动置信度/动态系数回显——让用户一眼看清采集表数据是否被完整吃进。"""
    line()
    print("采集完整度与置信度（v4.4：锐线自动去水→每腿CLV→按核心4+辅助8自动定级；无锐线恒A级、2串1实盘=0）")
    line()
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        m = a["m"]
        conf, nd, n_aux, has_sh = confidence(m)
        sh = m.get("sharp")
        _has_e = bool((a.get("fuse") or {}).get("has_euro"))
        if sh and sh.get("spf"):
            sh_txt = f"锐线源{sh.get('src')}"
        elif _has_e:
            sh_txt = "欧赔准锐线"
        else:
            sh_txt = "无价值源"
        wleg = next((L for L in a["legs"] if L["mk"] == "W"), None)
        if wleg and wleg.get("clv") is not None:
            _lab = "静态价值" if wleg.get("vsrc") == "euro" else "CLV"
            clv_txt = f"首选{_lab}{wleg['clv'] * 100:+.1f}%"
        else:
            clv_txt = "价值—"
        sp_stat = ("胜" if m.get("spf") else "·") + ("让" if m.get("rsp") else "·") \
            + ("比" if m.get("ssp") else "·") + ("总" if m.get("tsp") else "·")
        dyn, _ = dyn_coeff(m)
        tier = m.get("bankroll_tier", "std")
        print(f'  {m["no"]} {m["lg"]:4} {sh_txt:6} 置信{conf}({nd}维/辅{n_aux}) {clv_txt:13} '
              f'动态{dyn:.2f} 资金档{tier:4} 四玩法SP[{sp_stat}]')


def print_type_guide(A):
    """v4.5 场次分型与选法指引：逐场标 悬殊一致/相近分歧/均衡过渡 + 四玩法首选概率，再按型给选法。"""
    line()
    print("场次分型与选法指引（Δλ实力差×方向一致性；只作选法提示，不改概率/排序，维度一P最优仍成立）")
    line()
    groups = {}
    for a in sorted(A, key=lambda x: (-x["dl"])):
        t = a["mtype"]
        groups.setdefault(t, []).append(a)
        pp = {L["mk"]: L["p"] for L in a["legs"]}

        def g(k):
            return f"{pp[k] * 100:4.1f}%" if k in pp else "  —  "
        arrow = {"悬殊一致": "→主攻胜负/让球", "相近分歧": "→优先让球·慎赌胜负", "均衡过渡": "→胜负让球并重"}[t]
        print(f'  {a["m"]["no"]} {a["m"]["lg"]:4} Δλ{a["dl"]:.2f} {"方向一致" if a["dir_ok"] else "方向分歧"} '
              f'【{t}】 W{g("W")} H{g("H")} 比分{g("S")} 总进球{g("T")} {arrow}')
    print("  " + "-" * 100)
    for t in ("悬殊一致", "均衡过渡", "相近分歧"):
        if t in groups:
            nos = "、".join(a["m"]["no"] for a in groups[t])
            print(f"  【{t}】{nos}：{TYPE_ADVICE[t]}")


MANUAL_CHECKLIST = [
    "首发名单：双方首发是否已出、此前伤停名单中的核心是否真的缺阵(核心未上=红灯⑭)",
    "结构性战意双确认：保级/争冠/出局【数学状态】+【首发轮换官宣】是否都成立(缺一motiv取1.0)",
    "默契球/积分互利/未来3天留力：是否存在送分、携手出线、关键战轮换等语义格局",
    "突发利空：赛前训练伤退、罢训、换帅、财务/舆情等未反映在当前SP里的消息",
    "天气突变：是否达大雨(λ×0.91)/大雪/大风，与采集时是否一致",
    "赛制判定：是否淘汰赛/两回合/小组末轮(决定G5按1%还是1.5%、淘汰赛引擎是否启用)",
    "锐线可达性人工确认：sharp来源是否真实可溯、kind是live还是close、抓取时间是否在窗口内",
    "开栓决策：胜平负/让球是否在官方开售(选择性开栓)范围内、半全场是否已排除(③禁飞)",
    "资金状态：L连输/W连赢/DD回撤/在途笔数与敞口是否与实际账户一致",
    "临场复核：出票前60分钟用最新SP/锐线重跑一次，CLV变动≥0.10/EV跌≥0.05是否触发撤单/重算",
]


# ==================== v5.8.2 净胜球分布 × 亚盘全档拆解 专项报告（只读analyze挂载的gdiff，不回算）====================
def print_asian_goaldiff_report(A, verbose_dist=True):
    """v5.8.8升级（纯展示，只读analyze已算字段，不触碰概率/选注/结算）：
    ①让球方净胜球逐档人话互斥分布(赢5+/赢4/…/赢1/平/输1/输2+，各档互斥、和=100%)，并显式给出
      让胜=赢≥n+1各档累加、让平=◆恰好赢n、让负=其余累加，回答"-0.5/-1穿盘到底对应赢几球";
    ②模型τ让球三项 vs Pinnacle锐线让球三项并列(各自首选★)，首选不同或让平差≥阈值打⚠让平分歧警示。
    v5.8.2的主视角净胜球分布与邻近亚盘全档保留。ASIAN_REPORT_ENABLED=False可整体关。"""
    if not ASIAN_REPORT_ENABLED:
        return
    line()
    print("净胜球逐档 × 让球两源对照 × 亚盘全档（v5.8.8，最终矩阵只读派生；W全赢/HW赢半/P走盘/HL输半/L全输，cover=W+½HW）")
    print("同源口径：比分=矩阵单格；总进球=沿 i+j=k 斜线求和；净胜球档=沿 i-j=d 反对角线求和——同一张矩阵、各自和=100%")
    line()

    def _fmt_dist(gd):
        return " ".join(f"{d:+d}:{p * 100:.0f}%" for d, p in gd.items()
                        if ASIAN_DIFF_LO <= d <= ASIAN_DIFF_HI and p >= 0.003)

    def _fmt_fav_tiers(fd, n):
        # 让球方视角净胜球【逐档互斥】分布：赢K+合并、中间逐档、平、输1、输L+合并；◆=恰好赢n=让平/走盘档
        if not fd:
            return None
        dmax = max(fd)
        seg = []
        hi = sum(p for d, p in fd.items() if d >= HCAP_TIER_WIN_MERGE)
        if hi >= 0.003:
            seg.append((f"赢{HCAP_TIER_WIN_MERGE}+球", hi))
        for d in range(min(dmax, HCAP_TIER_WIN_MERGE - 1), 0, -1):
            p = fd.get(d, 0.0)
            if p >= 0.003:
                seg.append((f"赢{d}球" + ("◆" if d == n else ""), p))
        p0 = fd.get(0, 0.0)
        if p0 >= 0.003:
            seg.append((("平◆" if n == 0 else "平"), p0))
        p_l1 = fd.get(-1, 0.0)
        if p_l1 >= 0.003:
            seg.append(("输1球", p_l1))
        lo = sum(p for d, p in fd.items() if d <= -HCAP_TIER_LOSE_MERGE)
        if lo >= 0.003:
            seg.append((f"输{HCAP_TIER_LOSE_MERGE}+球", lo))
        if not seg:
            return None
        return "  ".join(f"{lab}{p * 100:.1f}%" for lab, p in seg), sum(p for _, p in seg)

    def _tri(v, pick):
        return "  ".join(("★" if k == pick else " ") + f"{HC_NAME[k]}{v[k] * 100:5.1f}%" for k in range(3))

    for a in sorted(A, key=lambda x: x["m"].get("no", "")):
        g = a.get("gdiff")
        if not g:
            continue
        no, lg = a["m"].get("no"), a["m"].get("lg", "")
        mm = a["m"]
        if g.get("n") is None:
            print(f"  {no} {lg:4}[无让球线] 净胜球(主视角) {_fmt_dist(g['gd_home'])}")
            continue
        fav_cn = "主" if g["fav"] == "home" else "客"
        n = g["n"]; b = g["base_int"]
        print(f"  {no} {lg:4}{fav_cn}让{n} 形态【{g['morph']}】｜让球方赢球{g['p_win'] * 100:5.1f}% "
              f"恰好赢{n}球(走盘/让平){g['p_exact_n'] * 100:5.1f}% "
              f"整数线 穿W(让胜){b['W'] * 100:5.1f}% 走P(让平){b['P'] * 100:5.1f}% 输L(让负){b['L'] * 100:5.1f}%")
        if verbose_dist:
            tt = _fmt_fav_tiers(g["fav_diff"], n)
            if tt:
                tiers_str, tot = tt
                print(f"         让球方逐档(互斥,和{tot * 100:.0f}%) {tiers_str}")
                print(f"         →让胜=赢≥{n + 1}球各档累加{b['W'] * 100:.1f}%；让平=◆恰好赢{n}球{b['P'] * 100:.1f}%；"
                      f"让负=其余各档累加{b['L'] * 100:.1f}%（◆档=亚盘走盘退本）")
            print(f"         净胜球(主视角) {_fmt_dist(g['gd_home'])}")
        # v5.8.8② 模型τ口径 vs Pinnacle锐线口径 并列 + 让平分歧警示（只呈现、不互相覆盖、不改实盘采用源）
        if HCAP_DIVERGE_SHOW:
            mtx = mm.get("_hcap_matrix_raw"); div = mm.get("_hcap_diverge")
            if mtx:
                pick_m = int(max(range(3), key=lambda k: mtx[k]))
                print(f"         模型τ  {_tri(mtx, pick_m)}")
            if div:
                print(f"         锐线   {_tri(div['sharp'], div['pick_s'])}（实盘H腿采用源：{mm.get('_hcap_src')}）")
                if HCAP_DIVERGE_WARN and div["warn"]:
                    print(f"         ⚠让平分歧：模型首选【{HC_NAME[div['pick_m']]}】 vs 锐线首选【{HC_NAME[div['pick_s']]}】，"
                          f"让平概率差{div['draw_gap'] * 100:+.1f}pp（并列呈现不覆盖；继续攒H赛果样本再定该信哪头）")
            elif mtx and str(mm.get("_hcap_src", "")).startswith("matrix"):
                print("         锐线   （无Pinnacle3WayH，实盘回退模型矩阵，无两源对照）")
        cells = []
        for r in g["ladder"]:
            cells.append(f"-{r['line']:g}:W{r['W'] * 100:.0f}/半W{r['HW'] * 100:.0f}/走{r['P'] * 100:.0f}"
                         f"/半L{r['HL'] * 100:.0f}/L{r['L'] * 100:.0f}|穿{r['cover'] * 100:.0f}%")
        print("         亚盘全档 " + "  ".join(cells))


# ======================================================================================
# v5.6 升级块（推荐版 1+2+3+4+5）——本块为纯增量，概率引擎/选注口径一字未改，全部函数自容错。
#   模块2 Pinnacle 开盘→临场线移动历史(零额外请求,多次运行自然积累)
#   模块4 跨市场无风险套利(surebet)确定性扫描
#   模块3 真实相关性的蒙特卡洛当晚/长期盈亏模拟
#   模块1 CLV 投注台账 journal(赛前落账/赛后结算/滚动统计,验证CLV预测力)
#   模块5 空仓决策显式化 + 连黑时间熔断(tilt lock)
# ======================================================================================
import os as _os56
import csv as _csv56
import glob as _glob56
import random as _rnd56
import statistics as _stat56

PB_HIST_DIR = _data_path("pinbook_history")   # v5.8.1统一落DATA_DIR
JOURNAL_DIR = _data_path("journal")           # v5.8.1统一落DATA_DIR(台账CSV+熔断状态跨会话保留)
JOURNAL_CSV = _os56.path.join(JOURNAL_DIR, "clv_journal.csv")
JOURNAL_LOCK = _os56.path.join(JOURNAL_DIR, "lock_state.json")
MC_SAME_LG_RHO = 0.35      # 蒙特卡洛:同联赛腿之间的高斯copula相关(保守体现同联赛同黑;跨联赛=0独立)
TILT_LOSE_STREAK = 5       # 连黑≥5注触发冷静期
TILT_DRAWDOWN = -0.20      # 台账滚动盈亏≤-20%(按已结算投入)触发锁仓
TILT_COOL_DAYS = 2        # 触发后建议冷静天数
_TILT_LOCK56 = False      # v5.6 熔断全局开关：main 出单前依据台账置位，stake_plan 据此强制 f_live=0

# ---------------- 模块2：Pinnacle 线移动历史（不额外发请求，只把每次已抓到的数据存盘对比）----------------
def save_pinbook_history(so, eh, batch=None):
    """collect_pinbook 成功后调用：把当前 1X2/大小球主线/3维让球精简存一份带时间戳历史。"""
    try:
        if not so:
            return None
        _os56.makedirs(PB_HIST_DIR, exist_ok=True)
        b = str(batch or (MATCH_DATE if globals().get("MATCH_DATE") else "auto"))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        evs = []
        for (H, A), v in (so or {}).items():
            evs.append({"h": H, "a": A, "spf": v.get("spf"),
                        "ou_line": (v.get("ou") or {}).get("line") if v.get("ou") else None,
                        # v5.7：补存主盘水位与全档totals，供P0-3多线λt离线回归/线移动核对
                        "ou": v.get("ou"), "ou_multi": v.get("ou_multi"),
                        "eh": {str(k): px for k, px in (eh.get((H, A), {}) or {}).items()}})
        fp = _os56.path.join(PB_HIST_DIR, f"pb_{b}_{ts}.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"ts": ts, "batch": b, "events": evs}, f, ensure_ascii=False)
        return fp
    except Exception:
        return None

def _pb_hist_files(batch=None):
    b = str(batch or (globals().get("MATCH_DATE") or "auto"))
    fs = sorted(_glob56.glob(_os56.path.join(PB_HIST_DIR, f"pb_{b}_*.json")))
    return fs

def _devig3(sp3):
    inv = [1.0 / x for x in sp3]
    s = sum(inv)
    return [x / s for x in inv], s

def line_movement_report(A=None, batch=None, verbose=True):
    """对比当日最早/最晚两份 PinBook 快照，输出三方向赔率与去水概率漂移、steam 方向；<2份则提示多跑积累。"""
    try:
        fs = _pb_hist_files(batch)
        if verbose:
            line(); print("§V5.6-2 Pinnacle 线移动（本运行周期最早快照→最新快照；免费档无真开盘，18点/21点/临场多跑即逼近开盘→临场）"); line()
        if len(fs) < 2:
            if verbose:
                print(f"  当前仅 {len(fs)} 份 PinBook 历史快照（需≥2份才能算移动）。每次运行都会自动存一份，")
                print("  建议 18:00 / 21:00 / 临场各跑一次，即自动形成开盘→临场移动曲线（不额外消耗额度）。")
            return None
        first = json.load(open(fs[0], encoding="utf-8"))
        last = json.load(open(fs[-1], encoding="utf-8"))
        fmap = {(e["h"], e["a"]): e["spf"] for e in first["events"] if e.get("spf")}
        # 当晚场次的英文队名→编号（用 TEAM_ALIAS_CN2EN 对齐 PinBook 英文键）；A为空则退回全量
        # 队名→所属编号；要求一场的主客两队都命中且属同一编号，避免把同队其他对阵带入
        name2no = {}
        if A:
            for a in A:
                m = a["m"]
                for cn in (m.get("home"), m.get("away")):
                    try:
                        en = _cn_en_first(cn)
                        if en: name2no[en] = m["no"]
                    except Exception: pass
        rows = []
        for e in last["events"]:
            if not e.get("spf"): continue
            H, An, sp_now = e["h"], e["a"], e["spf"]
            eh, ea = _en_norm(H), _en_norm(An)
            nh, na = name2no.get(eh), name2no.get(ea)
            no = nh if (A and nh and nh == na) else ("" if A else "")
            if A and not no:   # 聚焦当晚：主客须同时命中同一场，过滤全球/同队其他对阵
                continue
            sp0 = fmap.get((H, An))
            if not sp0:
                continue
            p0, _ = _devig3(sp0); p1, _ = _devig3(sp_now)
            dprob = [(p1[k]-p0[k])*100 for k in range(3)]
            steam = max(range(3), key=lambda k: dprob[k])
            rows.append((no, f"{H} v {An}", sp0, sp_now, dprob, steam))
        if not rows:
            if verbose: print("  早晚快照在当晚场次上无共同记录（需两次运行都已采到这些场），暂无法计算移动。")
            return None
        rows.sort(key=lambda r: -max(abs(x) for x in r[3]))
        if verbose:
            scope = "当晚 %d 场" % len(rows) if A else "全球 %d 场" % len(rows)
            print(f"  对比 {first['ts']} → {last['ts']}，{scope}有移动，按|概率漂移|降序（正=该方向去水概率上升）：")
            for no, nm, sp0, sp1, dp, steam in rows[: (len(rows) if A else 12)]:
                arr = " ".join(f"{DIR[k]}{dp[k]:+4.1f}pp" for k in range(3))
                flag = "  →资金倾向【%s】" % DIR[steam] if abs(dp[steam]) >= 2.0 else ""
                print(f"   {str(no):>3} {nm:30} 赔率{sp0[0]:.2f}/{sp0[1]:.2f}/{sp0[2]:.2f}→{sp1[0]:.2f}/{sp1[1]:.2f}/{sp1[2]:.2f}  {arr}{flag}")
        return rows
    except Exception as e:
        if verbose: print(f"  线移动模块异常(已跳过,不影响主流程):{e}")
        return None

# ---------------- 模块4：跨市场无风险套利 surebet 确定性扫描 ----------------
def surebet_scan(A, verbose=True):
    """竞彩1X2 vs Pinnacle：单场三方向取两边最优赔率，Σ1/best<1 才存在理论无风险套利。
    竞彩单场多数不开单关、且赔率全线下调于锐线——本函数用数据确定性地证明/证伪套利是否存在。"""
    if verbose:
        line(); print("§V5.6-4 跨市场无风险套利扫描（surebet：三方向全覆盖仍盈利才成立；Σ1/最优赔率<1）"); line()
    n_arb = 0; table = []
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        m = a["m"]; no = m["no"]
        cn = m.get("spf"); sh = (m.get("sharp") or {}).get("spf")
        if not cn:
            continue
        try:
            cn = [float(x) for x in cn]
        except Exception:
            continue
        cn_or = sum(1.0/x for x in cn) - 1
        best = list(cn); pb_or = None
        if sh:
            try:
                sh = [float(x) for x in sh]
                pb_or = sum(1.0/x for x in sh) - 1
                best = [max(cn[k], sh[k]) for k in range(3)]
            except Exception:
                pass
        margin = sum(1.0/x for x in best)
        profit = 1 - margin
        is_arb = profit > 0
        n_arb += 1 if is_arb else 0
        table.append((no, cn_or, pb_or, profit, is_arb))
    if verbose:
        for no, cn_or, pb_or, profit, is_arb in table:
            pbs = f"Pinnacle抽水{pb_or*100:4.1f}%" if pb_or is not None else "无Pinnacle"
            tag = "✔理论套利 Σ=%.3f<1 利润%.1f%%" % (margin, profit*100) if is_arb else "无套利 Σ1/最优=%.3f≥1" % margin
            print(f"   {no}  竞彩抽水{cn_or*100:5.1f}%  {pbs:16}  跨平台最优全覆盖→{tag}")
        line()
        if n_arb == 0:
            print(f"  结论：{len(table)}场【全部不存在无风险套利】。竞彩约12.9%抽水+赔率全线下调于Pinnacle，'每次稳赚'的套利路径在结构上不成立；")
            print("        唯一的长期优势来源仍是：正CLV时出手＋大样本＋凯利纪律（见台账与蒙特卡洛）。")
        else:
            print(f"  ⚠发现 {n_arb} 场理论套利；注意竞彩单场多不开单关、必须2串1，单场对冲往往【不可执行】，需人工确认开售方式。")
        line()
    return table

# ---------------- 模块3：真实相关性蒙特卡洛当晚/长期盈亏模拟 ----------------
def _nd_inv_cdf(p):
    return _stat56.NormalDist().inv_cdf(min(max(p, 1e-6), 1-1e-6))

def monte_carlo_slip(slip, A=None, nsim=20000, seed=20260907, verbose=True):
    """以'腿'为基本事件、同联赛腿用高斯copula加相关(MC_SAME_LG_RHO)、跨联赛独立，
    模拟 nsim 个购彩晚的净盈亏分布，并外推长期N晚累计为正概率。slip=print_betting_slip返回值。"""
    if not slip or not slip.get("sub"):
        if verbose:
            line(); print("§V5.6-3 蒙特卡洛：今晚无投注单（空仓），不模拟。空仓即零波动、零期望亏损。"); line()
        return None
    try:
        rng = _rnd56.Random(seed)
        sub, bets = slip["sub"], slip["bets"]
        # 收集腿
        legs = {}; leg_order = []
        def reg(no, L, lg):
            k = (no, L["mk"], L["pick"])
            if k not in legs:
                legs[k] = {"p": float(L["p"]), "lg": lg, "thr": _nd_inv_cdf(float(L["p"]))}
                leg_order.append(k)
            return k
        notes = []
        for (p, sp, c), amt in zip(sub, bets):
            k1 = reg(c["n1"], c["L1"], c.get("lg1"))
            k2 = reg(c["n2"], c["L2"], c.get("lg2"))
            notes.append((k1, k2, float(amt), float(sp)))
        lg_of_idx = {i: legs[k]["lg"] for i, k in enumerate(leg_order)}
        lgs = sorted(set(lg_of_idx.values()))
        lg_zidx = {g: j for j, g in enumerate(lgs)}
        thr = [legs[k]["thr"] for k in leg_order]
        nleg = len(leg_order)
        sqrt_r = MC_SAME_LG_RHO ** 0.5; sqrt_1r = (1-MC_SAME_LG_RHO) ** 0.5
        total_stake = sum(bets)
        night_pnl = []
        for _ in range(nsim):
            Z = [rng.gauss(0, 1) for _ in lgs]
            E = [rng.gauss(0, 1) for _ in range(nleg)]
            hit = [False]*nleg
            for i in range(nleg):
                x = sqrt_r*Z[lg_zidx[lg_of_idx[i]]] + sqrt_1r*E[i]
                hit[i] = (x <= thr[i])
            pnl = 0.0
            for k1, k2, amt, sp in notes:
                i1, i2 = leg_order.index(k1), leg_order.index(k2)
                win = hit[i1] and hit[i2]
                pnl += amt*(sp-1) if win else -amt
            night_pnl.append(pnl)
        # 最长连黑必须在排序前的原始(时间顺序)模拟序列上统计，排序会把负值聚到一起造成虚高
        cur = mx = 0
        for x in night_pnl:
            cur = cur+1 if x < 0 else 0; mx = max(mx, cur)
        night_pnl.sort()
        def q(frac):
            return night_pnl[min(nsim-1, int(frac*nsim))]
        pwin = sum(1 for x in night_pnl if x > 0)/nsim
        pblack = sum(1 for x in night_pnl if x <= -total_stake+1e-9)/nsim
        mean = sum(night_pnl)/nsim
        # 长期：以单晚经验分布重采样，模拟 N 晚累计为正概率
        rng2 = _rnd56.Random(seed+1)
        horizons = {}
        for N in (7, 30, 90, 180):
            ok = 0; trials = 4000
            for _ in range(trials):
                s = 0.0
                for _j in range(N):
                    s += night_pnl[rng2.randrange(nsim)]
                ok += 1 if s > 0 else 0
            horizons[N] = ok/trials
        if verbose:
            line(); print(f"§V5.6-3 蒙特卡洛盈亏模拟（{nsim}晚·高斯copula同联赛相关{MC_SAME_LG_RHO}·固定种子可复现）"); line()
            print(f"  每晚投入 {total_stake:g} 元 | 当晚净盈利概率 {pwin*100:.1f}% | 全黑(一分不中)概率 {pblack*100:.1f}% | 单晚期望 {mean:+.1f} 元(ROI {mean/total_stake*100:+.1f}%)")
            print(f"  单晚盈亏分位：5%差晚 {q(0.05):+.0f}元 / 中位 {q(0.5):+.0f}元 / 95%好晚 {q(0.95):+.0f}元；模拟序列最长连黑 {mx} 晚")
            print("  长期累计为正概率（假设每晚重复同一边际，样本越大越逼近期望）：" +
                  "  ".join(f"{N}晚 {v*100:.0f}%" for N, v in horizons.items()))
            if mean < 0:
                print("  ⚠单晚期望为负→长期累计为正概率随N增大反而趋近0：这正是'不能每次盈利、负EV久赌必亏'的量化证明；只有单晚期望为正(过闸门的注)时,大样本才站在你这边。")
            else:
                print("  单晚期望为正：短期仍可能连黑(方差)，但大样本累计为正概率随N上升——这才是可坚持的正期望系统。")
            line()
        return {"pwin": pwin, "pblack": pblack, "mean": mean, "roi": mean/total_stake,
                "q05": q(0.05), "q50": q(0.5), "q95": q(0.95), "max_lose_streak": mx, "horizons": horizons}
    except Exception as e:
        if verbose: print(f"  蒙特卡洛异常(已跳过):{e}")
        return None

# ---------------- 模块1：CLV 投注台账 ----------------
JOURNAL_COLS = ["batch","ts","sig","no1","mk1","pick1","p1","h1","no2","mk2","pick2","p2","h2",
                "sp_combo","p_combo","clv_legs","ev","conf_min","amt","f_live",
                "result","pnl","settle_ts"]
def _ensure_journal():
    _os56.makedirs(JOURNAL_DIR, exist_ok=True)
    if not _os56.path.exists(JOURNAL_CSV):
        with open(JOURNAL_CSV, "w", newline="", encoding="utf-8-sig") as f:
            _csv56.writer(f).writerow(JOURNAL_COLS)
def _read_journal():
    _ensure_journal(); rows=[]
    with open(JOURNAL_CSV, encoding="utf-8-sig") as f:
        for r in _csv56.DictReader(f): rows.append(r)
    return rows
def _write_journal(rows):
    with open(JOURNAL_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w=_csv56.DictWriter(f, fieldnames=JOURNAL_COLS); w.writeheader()
        for r in rows: w.writerow({k: r.get(k,"") for k in JOURNAL_COLS})
def _conf_min_of(c, A_by_no):
    lv = {"C":0,"B":1,"A":2,"S":3,"S+":4}
    cs=[]
    for no in (c.get("n1"), c.get("n2")):
        m=(A_by_no.get(no) or {}).get("m") if A_by_no.get(no) else None
        if m:
            try: cs.append(lv.get(confidence(m)[0],1))
            except Exception: pass
    return min(cs) if cs else ""
def append_journal_from_slip(A, slip, batch=None, verbose=True):
    """赛前：把投注单每一注落台账（同批次同腿签名去重，重复运行不重复记账）。"""
    if not slip or not slip.get("sub"):
        return 0
    try:
        b=str(batch or globals().get("MATCH_DATE") or "auto")
        A_by_no={a["m"]["no"]:a for a in A}
        rows=_read_journal(); exist={(r["batch"],r["sig"]) for r in rows}
        n=0
        def _hand_of(no):
            aa=A_by_no.get(no); return (aa["m"].get("hand") if aa else "") or ""
        for (p,sp,c),amt in zip(slip["sub"], slip["bets"]):
            sig="|".join(str(x) for x in (c["n1"],c["L1"]["mk"],c["L1"]["pick"],c["n2"],c["L2"]["mk"],c["L2"]["pick"]))
            if (b,sig) in exist: continue
            cl=[c["L1"].get("clv"),c["L2"].get("clv")]
            clv=sum(x for x in cl if x is not None)/len([x for x in cl if x is not None]) if any(x is not None for x in cl) else ""
            try: spd=stake_plan(c); fl=spd.get("f_live",0)
            except Exception: fl=0
            rows.append({"batch":b,"ts":datetime.now().strftime("%Y-%m-%d %H:%M"),"sig":sig,
                "no1":c["n1"],"mk1":c["L1"]["mk"],"pick1":c["L1"]["pick"],"p1":round(c["L1"]["p"],4),"h1":_hand_of(c["n1"]),
                "no2":c["n2"],"mk2":c["L2"]["mk"],"pick2":c["L2"]["pick"],"p2":round(c["L2"]["p"],4),"h2":_hand_of(c["n2"]),
                "sp_combo":round(sp,3),"p_combo":round(p,4),
                "clv_legs":("" if clv=="" else round(clv,4)),"ev":round(c.get("ev") or p*sp-1,4),
                "conf_min":_conf_min_of(c,A_by_no),"amt":amt,"f_live":round(fl,5),
                "result":"","pnl":"","settle_ts":""})
            n+=1
        _write_journal(rows)
        if verbose and n: print(f"  §V5.6-1 台账：赛前新增 {n} 注到 {JOURNAL_CSV}（同批次去重后）。")
        return n
    except Exception as e:
        if verbose: print(f"  台账写入异常(跳过):{e}")
        return 0
def settle_journal(results, batch=None, verbose=True):
    """赛后：results={编号:'主:客'}，对未结算台账注判定两腿命中并记盈亏（按赛前建议amt复盘；真实购票另用actual_tickets）。"""
    try:
        rows=_read_journal(); n=0
        ij=_res_ij
        def _to_hand(x):
            if x in ("", None, "None"): return None
            try: return int(float(x))
            except Exception: return None
        for r in rows:
            if r.get("result"): continue
            if r["no1"] not in results or r["no2"] not in results: continue
            def leg_hit(no,mk,pick,hs):
                i,j=ij(results[no])
                return _leg_hit_by_pick(mk,pick,i,j,_to_hand(hs))[0]  # (命中,实际选项)取命中布尔
            try:
                h1=leg_hit(r["no1"],r["mk1"],r["pick1"],r.get("h1")); h2=leg_hit(r["no2"],r["mk2"],r["pick2"],r.get("h2"))
            except Exception:
                continue
            win=bool(h1 and h2); amt=float(r["amt"] or 0); sp=float(r["sp_combo"] or 0)
            r["result"]="中" if win else "黑"; r["pnl"]=round(amt*(sp-1) if win else -amt,2)
            r["settle_ts"]=datetime.now().strftime("%Y-%m-%d %H:%M"); n+=1
        _write_journal(rows)
        if verbose and n: print(f"  §V5.6-1 台账：赛后结算 {n} 注。")
        return n
    except Exception as e:
        if verbose: print(f"  台账结算异常:{e}")
        return 0
def journal_report(verbose=True):
    """滚动统计：命中率/累计ROI，并按赛前CLV正负分组对比命中率与ROI（验证'正CLV长期盈利'是否在你自己样本上成立）。"""
    try:
        rows=_read_journal(); done=[r for r in rows if r.get("result")]
        if verbose:
            line(); print("§V5.6-1 CLV投注台账（长期优势的唯一客观裁判：≥30注后统计才可信）"); line()
        if not rows:
            if verbose: print("  台账为空：赛前投注单会自动落账，赛后填比分自动结算，积累样本。")
            return None
        def grp(sub):
            if not sub: return None
            stake=sum(float(r["amt"]) for r in sub); pnl=sum(float(r["pnl"]) for r in sub)
            hit=sum(1 for r in sub if r["result"]=="中")
            return {"n":len(sub),"hit":hit,"hr":hit/len(sub),"stake":stake,"pnl":pnl,"roi":(pnl/stake if stake else 0)}
        def _sf(x):
            try: return float(x)
            except Exception: return None
        allg=grp(done)
        pos=grp([r for r in done if (lambda v: v is not None and v>=CLV_MIN)(_sf(r.get("clv_legs")))])
        neg=grp([r for r in done if (lambda v: v is not None and v<CLV_MIN)(_sf(r.get("clv_legs")))])
        if verbose:
            print(f"  累计落账 {len(rows)} 注，已结算 {len(done)} 注。", end="")
            if allg:
                print(f"已结算命中 {allg['hit']}/{allg['n']}={allg['hr']*100:.1f}%，投入{allg['stake']:g}，盈亏{allg['pnl']:+.1f}，ROI {allg['roi']*100:+.1f}%")
            else: print()
            for nm,g in (("赛前CLV≥+3%的注",pos),("赛前CLV<+3%的注",neg)):
                if g: print(f"    {nm}: {g['n']}注 命中{g['hr']*100:.1f}% ROI {g['roi']*100:+.1f}%  ←CLV预测力分组对比")
            if len(done)<30:
                print(f"  样本{len(done)}<30注，命中率/ROI仍受随机波动主导，calibrate建议满30场再据此调参(防过拟合)。")
            line()
        return {"all":allg,"pos_clv":pos,"neg_clv":neg,"total":len(rows)}
    except Exception as e:
        if verbose: print(f"  台账报告异常:{e}")
        return None
def tilt_state(verbose=False):
    """连黑/回撤时间熔断：读已结算台账判定是否锁仓，并实现'冷静期到期自动解除'，避免锁仓期不下注→
    没有红注打断连黑→永久死锁。状态(含首次锁仓时间)写 lock_state.json。"""
    try:
        rows=[r for r in _read_journal() if r.get("result")]
        streak=0
        for r in reversed(rows):
            if r["result"]=="黑": streak+=1
            else: break
        stake=sum(float(r["amt"]) for r in rows); pnl=sum(float(r["pnl"]) for r in rows)
        dd=(pnl/stake) if stake else 0
        reasons=[]
        if streak>=TILT_LOSE_STREAK: reasons.append(f"连黑{streak}注≥{TILT_LOSE_STREAK}")
        if stake and dd<=TILT_DRAWDOWN: reasons.append(f"滚动ROI {dd*100:.0f}%≤{TILT_DRAWDOWN*100:.0f}%")
        raw = bool(reasons)
        now=datetime.now()
        prev={}
        try:
            if _os56.path.exists(JOURNAL_LOCK):
                prev=json.load(open(JOURNAL_LOCK,encoding="utf-8"))
        except Exception:
            prev={}
        first=prev.get("first_lock_ts") or ""
        recovered=False
        if raw:
            if not first:
                first=now.strftime("%Y-%m-%d %H:%M"); lock=True      # 首次触发，开始计冷静期
            else:
                try:
                    days=(now-datetime.strptime(first,"%Y-%m-%d %H:%M")).total_seconds()/86400.0
                except Exception:
                    days=0.0
                if days>=TILT_COOL_DAYS:
                    lock=False; recovered=True; first=""            # 冷静期满→自动解除，给重新观察机会
                else:
                    lock=True
        else:
            lock=False; first=""                                    # 红注打断连黑/回血→解除
        mult=0.0 if lock else 1.0
        state={"lock":lock,"mult":mult,"lose_streak":streak,"rolling_roi":dd,"reasons":reasons,
               "cool_days":(TILT_COOL_DAYS if lock else 0),"first_lock_ts":first,"recovered":recovered,
               "ts":now.strftime("%Y-%m-%d %H:%M")}
        _os56.makedirs(JOURNAL_DIR,exist_ok=True)
        with open(JOURNAL_LOCK,"w",encoding="utf-8") as f: json.dump(state,f,ensure_ascii=False,indent=2)
        if verbose and lock:
            line(); print(f"⛔V5.6-5 时间熔断触发（{'、'.join(reasons)}）：冷静 {TILT_COOL_DAYS} 天内实盘比例强制=0（不追损），冷静期满自动解除。"); line()
        if verbose and recovered:
            line(); print(f"  V5.6-5 冷静期已满 {TILT_COOL_DAYS} 天，熔断自动解除：可恢复，但仅在硬闸门全过时按最小实盘比例出手。"); line()
        return state
    except Exception:
        return {"lock":False,"mult":1.0,"lose_streak":0,"rolling_roi":0,"reasons":[],"cool_days":0,"first_lock_ts":"","recovered":False}

# ---------------- 模块5：今晚决策显式化 ----------------
def decision_briefing(A, slip, lock=None, n_live=None, verbose=True):
    """把'投/不投'做成一等决策：对候选注【逐条真实计算】硬闸门、给结论与'最接近门槛的注差多少'。"""
    if n_live is None:
        n_live = 0
        if slip and slip.get("sub"):
            for _p, _sp, c in slip["sub"]:
                try:
                    if stake_plan(c).get("f_live", 0) > 0: n_live += 1
                except Exception: pass
    if verbose:
        line(); print("§V5.6-5 今晚决策（空仓与下注同等重要——不投=保住12.9%抽水不被收割）"); line()
    if lock and lock.get("lock"):
        if verbose: print(f"  ⛔熔断锁仓中（{'、'.join(lock.get('reasons',[]))}）：今晚决策=【空仓·强制】，所有实盘比例已在出单前归零。"); line()
        return "LOCK"
    A_by_no = {a["m"]["no"]: a for a in (A or [])}
    def _gates(c):
        L1, L2 = c["L1"], c["L2"]
        def _clv_ok(L):
            v = L.get("clv"); vmin = EURO_EDGE_MIN if L.get("vsrc") == "euro" else CLV_MIN
            return (v is not None and v >= vmin)
        cm = _conf_min_of(c, A_by_no)
        ev = c.get("ev")
        return [
            ("双锐线(两腿均Pinnacle/必发)", L1.get("vsrc") == "sharp" and L2.get("vsrc") == "sharp"),
            ("每腿CLV≥门槛(锐线+3%/欧均+5%)", _clv_ok(L1) and _clv_ok(L2)),
            ("组合置信≥S+", cm == 4),
            ("组合EV≥+15%", (ev is not None and ev >= EV_COMBO_MIN)),
            ("ρ上限<0.3", (c.get("rho_hi", 1) < RHO_BLOCK)),
            ("无SP>2.50博冷腿", (L1.get("sp") or 0) <= 2.50 and (L2.get("sp") or 0) <= 2.50),
            ("v5.8.4分层硬闸门(|Δλ|≥1.0且首选≥55%)", sharp_stratum_combo_ok(c, A_by_no)[0]),
        ]
    best = None
    if slip and slip.get("sub"):
        def _score(item):
            g = _gates(item[2]); return (sum(1 for _, ok in g if ok), item[2].get("ev") if item[2].get("ev") is not None else -9)
        best = max(slip["sub"], key=_score)
    if n_live > 0:
        if verbose: print(f"  决策=【实盘 {n_live} 注】（已过双锐线/每腿CLV/置信S+/组合EV/ρ/博冷全部硬闸门，且熔断未触发）。")
        return "LIVE"
    if verbose:
        if best:
            p, sp, c = best; g = _gates(c); ng = sum(1 for _, ok in g if ok); ev = c.get("ev") or p*sp-1
            print(f"  最接近实盘的一注：{fmt_leg(c['n1'],c['L1'])} × {fmt_leg(c['n2'],c['L2'])}，P={p*100:.1f}% EV={ev*100:+.1f}%，硬闸门 {ng}/{len(g)} 过：")
            for lab, ok in g:
                print(f"     {'✓' if ok else '✗'} {lab}")
            gap = max(0, (EV_COMBO_MIN-ev)*100)
            print(f"  决策=【空仓】：该注距组合EV+15%硬门槛还差 {gap:.1f}pp，属观察非机会；其余注通过闸门数更少。")
        else:
            print("  决策=【空仓】（无任何合格候选）。")
        print("  机会成本：空仓省下的不是'少赚'，是规避了负期望——竞彩每晚期望先亏约12.9%，等正CLV才出手是唯一正解。")
        line()
    return "FLAT"
# ======================================================================================


# ======================================================================================
# v5.6 自动化块（用户第3诉求：发一句指令即全自动）——脚本自动拿"机器稳定可拿"的：
#   * 天气(open-meteo 免费无key,按经纬度,UTC对齐开球) 自动回填 review.weather
#   * 缺项研究清单 research_todo_<batch>.json：把"需豆包搜索核实"的语义项(伤停/首发/百家均/战绩)
#     结构化导出(含搜索关键词+回填schema)，豆包据此搜证→回填 ai_research→重跑，形成闭环
#   * AUTO_RUN_SOP：固定指令与豆包内部标准动作
# 说明：伤停/首发/默契球等"开放语义+易变"信息不硬爬脆弱网页，统一走 research_todo→豆包搜索核实，
#       比写死中文网页解析更稳、可交叉验证，符合"查不到填null、绝不编造"的数据铁律。
# ======================================================================================
# 队名(中文)→(城市, lat, lon, 开球当地为UTC对齐用;open-meteo timezone=Etc/UTC)
TEAM_CITY_LL = {
    # 本场9月7-8日
    "卡利亚里": ("Cagliari", 39.22, 9.12), "莱切": ("Lecce", 40.35, 18.17),
    "赫塔费": ("Getafe", 40.31, -3.73), "塞尔塔": ("Vigo", 42.24, -8.72),
    "马尔默": ("Malmo", 55.61, 13.00), "索尔纳": ("Solna", 59.37, 18.00), "AIK索尔纳": ("Solna", 59.37, 18.00),
    "卡尔马": ("Kalmar", 56.66, 16.36), "佐加顿斯": ("Stockholm", 59.31, 18.07),
    "利雅新月": ("Riyadh", 24.72, 46.68), "利雅得新月": ("Riyadh", 24.72, 46.68),
    "新未来SC": ("NEOM", 28.39, 34.76), "NEOM": ("NEOM", 28.39, 34.76),
    "乌迪内斯": ("Udine", 46.07, 13.24), "拉齐奥": ("Roma", 41.90, 12.50),
    "埃斯托里": ("Estoril", 38.71, -9.40), "埃斯托里尔": ("Estoril", 38.71, -9.40), "阿罗卡": ("Arouca", 40.93, -8.41),
    "埃尔切": ("Elche", 38.27, -0.70), "皇家社会": ("SanSebastian", 43.30, -1.98),
    "维多利亚": ("Salvador", -12.97, -38.51), "格雷米奥": ("PortoAlegre", -30.03, -51.23),
    # 常见补充(五大联赛/常用城市)
    "国际米兰": ("Milan", 45.46, 9.19), "AC米兰": ("Milan", 45.46, 9.19), "尤文图斯": ("Turin", 45.07, 7.69),
    "都灵": ("Turin", 45.07, 7.69), "那不勒斯": ("Naples", 40.85, 14.27), "罗马": ("Roma", 41.90, 12.50),
    "佛罗伦萨": ("Florence", 43.77, 11.25), "博洛尼亚": ("Bologna", 44.49, 11.34), "亚特兰大": ("Bergamo", 45.70, 9.67),
    "热那亚": ("Genoa", 44.41, 8.93), "维罗纳": ("Verona", 45.44, 10.99), "帕尔马": ("Parma", 44.80, 10.33),
    "皇马": ("Madrid", 40.42, -3.70), "皇家马德里": ("Madrid", 40.42, -3.70), "马德里竞技": ("Madrid", 40.40, -3.60),
    "巴萨": ("Barcelona", 41.38, 2.17), "巴塞罗那": ("Barcelona", 41.38, 2.17), "塞维利亚": ("Sevilla", 37.39, -5.99),
    "贝蒂斯": ("Sevilla", 37.35, -5.98), "比利亚雷亚尔": ("Villarreal", 39.94, -0.10), "瓦伦西亚": ("Valencia", 39.47, -0.38),
    "毕尔巴鄂": ("Bilbao", 43.26, -2.93), "奥萨苏纳": ("Pamplona", 42.81, -1.65), "巴列卡诺": ("Madrid", 40.39, -3.66),
    "曼城": ("Manchester", 53.48, -2.20), "曼联": ("Manchester", 53.46, -2.29), "利物浦": ("Liverpool", 53.43, -2.96),
    "阿森纳": ("London", 51.55, -0.10), "切尔西": ("London", 51.48, -0.20), "热刺": ("London", 51.60, -0.07),
    "拜仁": ("Munich", 48.14, 11.58), "多特": ("Dortmund", 51.49, 7.45), "巴黎圣日耳曼": ("Paris", 48.85, 2.35),
    "利雅胜利": ("Riyadh", 24.72, 46.68), "吉达联合": ("Jeddah", 21.54, 39.17), "吉达国民": ("Jeddah", 21.50, 39.17),
}
def _wmo_cond(code, prcp):
    try: code=int(code)
    except Exception: code=0
    if (prcp or 0) >= 2.5: return "大雨"
    if code in (71,73,75,77,85,86): return "雪"
    if (51<=code<=67) or (80<=code<=82) or code>=95:
        return "小雨" if (prcp or 0) < 2.5 else "大雨"
    if code==0: return "晴"
    if code in (1,2): return "多云"
    if code==3 or (45<=code<=48): return "阴"
    return "多云"
def auto_weather_one(team, kickoff_utc):
    info = TEAM_CITY_LL.get(str(team).strip())
    if not info: return None
    city, lat, lon = info
    d = kickoff_utc.strftime("%Y-%m-%d")
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%.4f&longitude=%.4f"
           "&hourly=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Etc/UTC&start_date=%s&end_date=%s" % (lat, lon, d, d))
    try:
        djson = json.loads(_http_get(url, timeout=20))
        hr = djson.get("hourly", {})
        times = hr.get("time", []); tgt = kickoff_utc.strftime("%Y-%m-%dT%H:00")
        if tgt not in times: return None
        i = times.index(tgt)
        temp = hr["temperature_2m"][i]; prcp = hr["precipitation"][i] or 0
        code = hr["weather_code"][i]; wind = hr["wind_speed_10m"][i]
        cond = _wmo_cond(code, prcp)
        if cond not in _WEATHER_COEF: cond = "多云"
        return {"cond": cond, "temp": round(float(temp)), "wind": "风速%.0fkm/h" % float(wind),
                "src": "open-meteo %s UTC%s 降水%.1fmm code%s" % (city, tgt[11:16], float(prcp), code)}
    except Exception:
        return None
def auto_collect_weather(A, verbose=True):
    """对每场按主队城市+开球(UTC)自动取天气并回填 review.weather；取不到不编造、列入缺项。"""
    ok=0; miss=[]
    for x in A:
        m = x.get("m", x) if isinstance(x, dict) else x
        try:
            if (m.get("review") or {}).get("weather",{}).get("cond"):  # AI已填则不覆盖
                ok+=1; continue
            kd = kickoff_dt(m)
            if kd is None: miss.append(m["no"]); continue
            kutc = kd - timedelta(hours=8)   # 北京(+08)→UTC
            w = auto_weather_one(m.get("home"), kutc)
            if w:
                m.setdefault("review", {})["weather"]=w; ok+=1
            else:
                miss.append(m["no"])
        except Exception:
            miss.append(m["no"])
    if verbose:
        print(f"  §V5.6自动采集·天气：{ok}/{len(A)} 场已回填(open-meteo)" + (f"；未覆盖城市 {miss}(列入缺项,豆包补)" if miss else ""))
    return miss

def export_research_todo(A, batch=None, verbose=True):
    """导出'需豆包搜索核实'的结构化缺项清单(机器稳定项已由脚本自动拿,这里只列需浏览器渲染/语义判断项)。
    v5.8.1：分 P0/P1 —— P0=stat统计原料与euro_avg百家欧均(缺stat会降级'纯市场λ'、丧失独立统计源；
    缺euro_avg模型只能复读竞彩、会建议空仓)，必须每场补齐；P1=首发/战意/天气等语义项。文件统一落 DATA_DIR。"""
    b=str(batch or globals().get("MATCH_DATE") or "auto")
    STAT_HOW=("stat统计λ原料【P0必补,10个字段一个不能少】:lg_hgf联赛主场场均进球/lg_agf客场场均进球/"
              "lg_hga主场场均失球/lg_aga客场场均失球;h_n主队本赛季【主场】场次、h_gf主场进球、h_ga主场失球;"
              "a_n客队本赛季【客场】场次、a_gf客场进球、a_ga客场失球(主客必须分开,别用总战绩);"
              "取数=500/澳客'战绩/积分'页主客场拆分,能开再对FBref/SofaScore;赛季<5轮或新军无样本可整段null")
    todo=[]
    for a in sorted(A,key=lambda x:x["m"]["no"]):
        m=a["m"]; no=m["no"]; p0={}; p1={}
        if not m.get("stat"): p0["stat"]=STAT_HOW
        if not m.get("euro_avg"): p0["euro_avg"]="百家欧赔均值[主,平,客]最新十进制赔率(500/澳客/足彩网百家平均行,两源交叉)+euro_disp离散度"
        rev=m.get("review") or {}
        if not rev.get("lineup"):
            p1["lineup"]="双方预计首发/伤停名单,量化impact_h/impact_a(核心缺阵-0.2~-0.4)"
        if not rev.get("motivation"):
            p1["motivation"]="排名/保级争冠数学形势与档位(拼命1.4/争取1.2/中游0.7/放假0.5/正常1.0)"
        if not rev.get("weather"):
            p1["weather"]="开球时天气(晴/多云/阴/小雨/大雨)、气温、风(open-meteo已自动补,冲突时以浏览器为准)"
        dims=m.get("dims") or {}
        dim_miss=[k for k in AUX_DIM_KEYS if dims.get(k) in (None,False)]
        need=dict(p0); need.update(p1)
        if need or dim_miss:
            kw=["%s %s 主客场战绩 近10场 进失球"%(m.get("home"),m.get("away")),   # v5.8.1 stat提为第一搜索词
                "%s %s 百家平均欧赔 初盘 即时"%(m.get("home"),m.get("away")),
                "%s %s 伤停 预计首发"%(m.get("home"),m.get("away")),
                "%s %s 积分榜 排名 战意"%(m.get("home"),m.get("away"))]
            todo.append({"no":no,"lg":m.get("lg"),"home":m.get("home"),"away":m.get("away"),
                         "time":m.get("time"),"p0_missing":sorted(p0.keys()),"p1_missing":sorted(p1.keys()),
                         "need":need,"dims_missing":dim_miss,"search_keywords":kw,
                         "fill_schema":"{no,euro_avg:[h,d,a],stat:{lg_hgf,lg_agf,lg_hga,lg_aga,h_n,h_gf,h_ga,a_n,a_gf,a_ga},inj_h,inj_a,motiv_h,motiv_a,review:{lineup,motivation,weather},dims{}}"})
    bkey=re.sub(r'[^0-9A-Za-z_-]',"",b) or "auto"
    fp=_data_path("research_todo_%s.json"%bkey)
    try:
        with open(fp,"w",encoding="utf-8") as f: json.dump(todo,f,ensure_ascii=False,indent=2)
    except Exception: pass
    if verbose:
        line(); print("§V5.8.1 豆包待补研究清单（脚本已自动拿竞彩SP/Pinnacle锐线/天气；【P0】stat/百家欧均必补,缺了降级或空仓）"); line()
        if not todo:
            print(f"  全部 {len(A)} 场数据已齐备，无需豆包额外搜索，直接进入建模。")
        else:
            n_p0=sum(1 for t in todo if t["p0_missing"])
            for t in todo:
                head=("【P0缺:%s】"%",".join(t["p0_missing"])) if t["p0_missing"] else ""
                tail=("P1语义:"+",".join(t["p1_missing"])) if t["p1_missing"] else ""
                dim=(" 辅助维:"+",".join(t["dims_missing"])) if t["dims_missing"] else ""
                print(f"  {t['no']} {t['home']}-{t['away']}: {head}{tail}{dim}")
            print(f"  共 {n_p0} 场缺 P0(stat/euro_avg)。→已导出 {fp}：豆包按 search_keywords 顺序逐项搜索、多源交叉，")
            print("     stat 严格按主/客场拆分填 10 字段，查不到填 null、绝不编造，再按 fill_schema 组 ai_research JSON 回填重跑。")
        line()
    return todo

AUTO_RUN_SOP = """
====================== 豆包全自动运行 SOP（v5.8.1，用户只需发一句固定指令）======================
【固定指令】示例：「按v5.8.1全自动分析今晚竞彩足球，额度500，出终审与台账」
豆包内部标准动作（无需用户逐步指挥）：
  0) 所有跨日积累统一落在脚本旁 jc_data/ 目录(或环境变量 JC_DATA_DIR 指定的固定盘)：calib校准库/
     snapshots赛前快照/journal台账/elo/h2h/pinbook_history。跨会话接续已全自动：新会话只需把上一次的备份zip放进
     脚本旁 jc_backup/(或设环境变量 JC_BACKUP_DIR 指向备份目录)，main一启动就自动【只补缺、不覆盖】还原，无需手动restore；
     赛后结算后又会自动把当晚 jc_data 打包成新zip到 jc_backup/，下载回传即可。也可用 jc_data_backup.py 手动 backup/restore/list。
  1) 运行 auto_pipeline('all', ai_json_text=已有研究或'', bankroll=额度)：脚本自动采竞彩官方SP、
     Pinnacle锐线(1X2+大小球+3维让球)、open-meteo天气，并自动存PinBook线移动历史、落CLV台账；
  2) 读取 jc_data/research_todo_<batch>.json，先清【P0】再清P1：
     · P0-stat：对缺 stat 的场，按主/客场拆分补齐10字段(联赛主客场场均进失球4基准+主队主场样本+客队客场样本)，
       500/澳客战绩页主客分页、FBref/SofaScore交叉；缺stat引擎只能走纯市场λ=复读赔率，必须尽量补上；
     · P0-euro_avg：百家欧赔均值[主,平,客]+离散度(500/澳客/足彩网百家平均行,两源交叉)，缺它模型复读竞彩、会建议空仓；
     · P1：伤停首发(fotmob/官方+中文源对照)/战意数学形势/天气；查不到一律填null、绝不编造；按 fill_schema 组 ai_research JSON；
  2b)若生成 jc_data/team_alias_todo_<batch>.json(中文队名没对上Pinnacle)：按其中队名查标准英文名补进 TEAM_ALIAS_CN2EN
     (或回发给用户代补)后重跑，自动锐线匹配率会逐晚提升；
  3) 携研究JSON再次 auto_pipeline 重跑（三源融合：竞彩0.25+百家均0.55+统计0.20）；
  4) 读取并向用户汇报：体检表/置信度/CLV审计/套利扫描/蒙特卡洛/今晚决策(空仓或实盘)/台账滚动统计；
  5) 次日自动查比分→settle_journal 结算台账→journal_report 看真实ROI与CLV预测力；校准样本满15场进isotonic、
     满60场全信自动校准，满30注给ρ/λ乘子调参建议。
【铁律】不承诺每次盈利；只在双锐线+每腿CLV≥+3%+置信S+ +组合EV≥15%等硬闸门全过才实盘，否则空仓；
        连黑≥5注或滚动ROI≤-20%触发时间熔断强制冷静，绝不追损。
====================================================================================
"""
def show_auto_run_sop(compact=True):
    if compact:
        print("§V5.6 全自动：发「按v5.6全自动分析今晚竞彩」豆包即自动 采集→搜索核实缺项→回填→重跑→终审/台账；次日自动结算。")
    else:
        print(AUTO_RUN_SOP)
# ======================================================================================


def show_manual():
    line()
    print("§D-2 赛前人工语义清单（无法代码化，逐项✓/✗；核心4维任一✗→该场不进实盘）")
    line()
    for i, item in enumerate(MANUAL_CHECKLIST, 1):
        print(f"  □{i:>2} {item}")
    line()
    print("§E v5.5 全自动用法（你只需发编号或『分析全部』，无需其他指令）：豆包按 show_sop() 流程 自动采集竞彩骨架→")
    print("   浏览器补百家欧赔均值/战绩/伤停首发/战意等全量数据→调用 auto_pipeline('all' 或 ['001','003'], ai_json_text=JSON, bankroll=500)，")
    print("   末尾直接给【今晚投注单】：每注串法+建议金额(2元整数倍)+中了可得+中0/1/2注盈亏情景+当晚盈利/全黑概率。")
    print("   数学边界：覆盖分配可做到『中任意1注即回本小赚』，但无法保证每晚盈利；无价值源时程序首选空仓、只给娱乐参考额度。")


def auto_gate_report(plans):
    """§D-1 终选5注自动验证红绿灯：可计算闸门(H1/H2/H3/H5/H6/H7/H9/红灯②⑫/玩法封顶)逐条汇总。"""
    line()
    print("§D-1 终选5注·自动验证红绿灯（全部由引擎按v38.4硬约束计算；⛔=该项不达标）")
    line()
    n_live = 0

    def clv_txt(L):
        return "无锐线" if L.get("clv") is None else f"{L['clv'] * 100:+.1f}%"

    for role, c, sp in plans:
        gates = [
            ("H1ρ<0.3", c["rho_hi"] < RHO_BLOCK),
            ("H2每腿CLV≥+3%", c["L1"].get("clv") is not None and c["L1"]["clv"] >= CLV_MIN
             and c["L2"].get("clv") is not None and c["L2"]["clv"] >= CLV_MIN),
            ("H3置信S+", sp["conf_lo"] == "S+"),
            ("H5组合EV≥15%", c["ev"] is not None and c["ev"] >= EV_COMBO_MIN),
            ("H6/H7单腿EV", leg_ev_ok(c["L1"]) and leg_ev_ok(c["L2"])),
            ("H9双腿锐线", (sp.get("clv1") is not None or c["L1"].get("clv") is not None)
             and (sp.get("clv2") is not None or c["L2"].get("clv") is not None)),
            ("红灯②非博冷", not sp["cold"]),
        ]
        passed = " ".join(f"{'✓' if ok else '⛔'}{name}" for name, ok in gates)
        live = sp["f_live"] > 0
        n_live += 1 if live else 0
        verdict = "✅可实盘" if live else "⛔仅纸面(f_live=0)"
        print(f"  {role.split('·')[0]} [{c['cat']}] P={c['pc']*100:.1f}% "
              f"腿CLV({clv_txt(c['L1'])}/{clv_txt(c['L2'])}) 置信{sp['conf_lo']} → {verdict}")
        print(f"      {passed}")
    print(f"  ── 今晚通过全部实盘闸门、可下注的注数 = {n_live}/5（红灯⑫：实盘2串1单日≤{MAX_PARLAY_LIVE}组；"
          f"其余仅概率参考，禁止为凑必投降门槛·红灯㉚）")



# ===================== §A+ 免费锐线自动采集层（v5.1 新增；下层概率引擎一字未改）=====================
# 目标：运行本文件即【自动、免费、多通道回退】把 竞彩官方SP + 1X2/让球(3维)/大小球锐线 尽量采全，
#       采到的锐线自动去水算 CLV，再无缝交给原引擎出终选5注。任何通道不可达都【跳过并标注、绝不编造】。
# 通道优先级（与 RESEARCH_BRIEF 一致）：Pinnacle(1) → Betfair(2) → OddsPortal(3) → 国内等值(9)。
import urllib.request as _ureq, urllib.parse as _uparse, ssl as _ssl, os as _os
from datetime import datetime as _dt, timezone as _tz, timedelta as _td
import difflib as _difflib
# —— 采集开关 / 免费密钥（推荐用环境变量注入，不写死在文件里；没有 key 也能用官方SP+新浪src9+手动兜底）——
AUTO_COLLECT   = True        # True=运行即自动联网采集；False=回到纯 AI_JSON/内置示例（=v5.0原行为）
MATCH_DATE     = "auto"      # "auto"=北京时间当天；也可写死如 "2026-09-05"
TARGET_NOS     = None        # v5.5 只分析指定编号，如["001","003"]；None或"all"=分析全部场次（用户只发编号即自动填这里）
ODDS_API_KEY   = _os.environ.get("ODDS_API_KEY", "")    # TheOddsAPI：注意其【免费档只含NBA+MLB+h2h+美国书商】,足球/Pinnacle需$29付费档;仅作可选补充
# ★关键免费key：到 RapidAPI 订阅「PinBook Odds」BASIC档($0/月,550次/月,Pinnacle足球无延迟)，把key填这(或环境变量RAPIDAPI_KEY)
#   即可【全自动】拿到 Pinnacle 的 1X2 + 大小球 + 3维让球(3-Way Handicap)，让球无需再手动回填
RAPIDAPI_KEY   = _os.environ.get("RAPIDAPI_KEY", "9d76523d16msha36cce36477c900p12922ajsn874664f9f3e7")  # 已填入 RapidAPI 账号密钥(同一把key通用于该账号已订阅的全部API)；若设置了环境变量 RAPIDAPI_KEY 则以环境变量为准
# v5.7.3 第一层【PinBook 孪生 host 热备池】：Tipsters 家同 schema 的两个 Pinnacle 馈送，字段/端点/让球命名完全一致；
#   顺序=优先顺序，主host网络错误/429/5xx/空数据自动切下一个，各自独立550次/月额度=合计1100次/月。
#   可用环境变量 PINBOOK_HOSTS 逗号分隔覆盖。
PINBOOK_HOSTS  = [h.strip() for h in _os.environ.get(
                     "PINBOOK_HOSTS",
                     "pinbook-odds.p.rapidapi.com,pinnacle-betting-odds.p.rapidapi.com").split(",") if h.strip()]
PINBOOK_HOST   = PINBOOK_HOSTS[0]   # 向后兼容别名(初始主host；运行时以 PB_ACTIVE_HOST 为准)
PB_ACTIVE_HOST = None               # 本轮实际成功使用的host(采集后回填,日志可见)
# v5.7.3 第二层【OddsPapi 奥兹帕皮】：357书商,含 Pinnacle(主盘延迟0.37s)/Betfair交易所/SBOBET/Singbet；
#   免费250次/月。每轮仅 1次赛程+1次批量主盘=2请求。其 externalProviders.pinnacleId 与 PinBook event_id 同源,
#   可做【ID级精确对齐】(不走队名模糊匹配),并对两路Pinnacle报价做一致性互验。
ODDSPAPI_ENABLED = _os.environ.get("ODDSPAPI_ENABLED", "1") not in ("0","false","False","")
ODDSPAPI_HOST    = "odds-api1.p.rapidapi.com"
ODDSPAPI_BOOKS   = ["pinnacle", "betfair-ex"]   # 锐线书商：Pinnacle同源互验 + Betfair交易所第二锐线(src=2)
# v5.7.6 OddsPortal(odds-api1,357书商聚合)百家欧均：额外拉这些主流软盘书商1X2,跨家平均→euro_avg、
#         离散→euro_disp(只做低抽水全球共识主锚+5_dispersion维,绝不进sharp锐线主锚;无效slug服务端自动忽略)
ODDSPAPI_EURO_BOOKS = ["bet365","unibet","williamhill","betway","bwin","marathon","sportingbet","1xbet","ladbrokes","coral"]
ODDSPAPI_EURO_MIN_BOOKS = 4   # 至少N家三项齐全才认作"百家均"(防单家冒充,配合overround 1.03-1.10校验)
ODDSPAPI_SOCCER  = 10                            # OddsPapi 足球 sportId
ODDSPAPI_BATCH   = 25                            # 批量端点一次最多带多少个fixtureId(保守分块)
OP_XDIFF_WARN    = 0.05                          # 两路Pinnacle同向赔率相对差>5%→告警(正常分钟级漂移通常<2%)
OP_XDIFF_DROP    = 0.15                          # >15%→判定某路异常,OddsPapi该场不参与回填(防错套,主源PinBook不受影响)
# v5.7.3 第三层【Bet365 Inplay 软盘参考通道】：bet365是锐利软盘但非锐线,【绝不进sharp主锚】,只做市场共识/偏离度参考
#   和主客方向交叉校验；免费50次/分、月硬上限50万。每场全市场1请求,故只对主批次拉取并设上限保护。
B365_ENABLED     = _os.environ.get("B365_ENABLED", "1") not in ("0","false","False","")
B365_HOST        = "bet365-api-inplay.p.rapidapi.com"
B365_MAX_EVENTS  = 40                            # 单轮最多拉多少场Bet365全市场(请求数上限保护)
B365_WINDOW_H    = 48                            # 只对齐未来48h内的赛前事件
SINA_EURASIA_URL = _os.environ.get("SINA_EURASIA_URL","")  # 当日新浪《竞彩欧亚对照》文章URL → 批量欧均(src=9)
HTTP_TIMEOUT   = 30
# 手动兜底（最重要的让球锐线catch-all）：豆包用联网/浏览器工具读到 JS 站(OddsPortal/Betexplorer EH/
#   dailysports/tipsterarea/必发/澳门/平博)后，把数字按编号粘到下面（引擎照单全收，不自行换算/编造）：
#   {"011":{"src":1,"spf":[主,平,客],"rsp":[让胜,让平,让负],"ou":{"line":2.5,"over":x,"under":y},
#           "kind":"live","time":"20:05","name":"Pinnacle"}}  —— rsp 必须与该场 hand 同一条整数让球线
MANUAL_SHARP = r"""{"023":null}"""
_SHARP_ORDER = {1:0, 2:1, 3:2, 9:3}
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def _http_get(url, referer=None, extra=None, timeout=HTTP_TIMEOUT):
    h = {"User-Agent": _UA, "Accept": "application/json,text/html,*/*", "Accept-Encoding": "gzip, deflate"}
    if referer: h["Referer"] = referer
    if extra: h.update(extra)
    ctx = _ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = _ssl.CERT_NONE
    import gzip as _gzip, zlib as _zlib
    with _ureq.urlopen(_ureq.Request(url, headers=h), timeout=timeout, context=ctx) as r:
        raw = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
        try:
            if "gzip" in enc:
                raw = _gzip.decompress(raw)
            elif "deflate" in enc:
                raw = _zlib.decompress(raw)
            else:
                try: raw = _gzip.decompress(raw)  # 兜底：个别网关不标 Content-Encoding 也返回 gzip
                except Exception: pass
        except Exception: pass
        return raw.decode("utf-8", "ignore")
def _f(x):
    try:
        if x in (None, "", "-", "—"): return None
        return float(x)
    except Exception: return None
def _bj_today():
    return _dt.now(_tz(_td(hours=8))).strftime("%Y-%m-%d")
def _en_norm(s):
    if s is None: return ""
    s = str(s).lower().replace("ñ","n").replace("ü","u").replace("é","e").replace("ø","o").replace("á","a").replace("í","i").replace("ó","o")
    return re.sub(r"[^a-z0-9 ]", " ", s)


# 中→英 队名对照（命中外部英文锐线源用；新日期可在此追加，也可靠模糊匹配兜底）
TEAM_ALIAS_CN2EN = {
 "福冈黄蜂":"Avispa Fukuoka","水户蜀葵":"Mito Hollyhock","山形山神":"Montedio Yamagata","甲府风林":"Ventforet Kofu",
 "济州SK":["Jeju SK","Jeju United"],"蔚山现代":["Ulsan HD","Ulsan Hyundai"],"纽卡斯尔":"Newcastle","伯恩茅斯":"Bournemouth","林肯城":"Lincoln City",
 "南安普敦":"Southampton","佛罗伦萨":"Fiorentina","都灵":"Torino","门兴":"Monchengladbach","埃沃斯堡":"Elversberg",
 "不来梅":"Werder Bremen","莱红牛":"RB Leipzig","帕德博恩":"Paderborn","弗赖堡":"Freiburg","霍芬海姆":"Hoffenheim",
 "多特蒙德":"Dortmund","勒沃库森":"Bayer Leverkusen","柏林联合":"Union Berlin","诺丁汉":"Nottingham Forest",
 "热刺":"Tottenham","曼城":"Manchester City","考文垂":"Coventry","布伦特":"Brentford","桑德兰":"Sunderland",
 "富勒姆":"Fulham","水晶宫":"Crystal Palace","毕尔巴鄂":"Athletic Bilbao","马竞":"Atletico Madrid","朗斯":"Lens",
 "洛里昂":"Lorient","国际米兰":["Internazionale","Inter Milan","Inter","Inter Milano"],"那不勒斯":"Napoli","布兰":"Brann","利勒斯特":"Lillestrom",
 "赫尔城":"Hull City","维拉":"Aston Villa","沙尔克04":"Schalke","拜仁":"Bayern Munich","巴列卡诺":"Rayo Vallecano",
 "桑坦德":"Racing Santander","马里迪莫":"Maritimo","本菲卡":"Benfica","吉达联合":"Al Ittihad","利雅胜利":"Al Nassr",
 "阿贾克斯":"Ajax","埃因霍温":"PSV Eindhoven","罗马":"Roma","亚特兰大":"Atalanta","勒阿弗尔":"Le Havre",
 "布雷斯特":"Brest","比利亚雷":"Villarreal","拉科":"Deportivo La Coruna","布拉干RB":"Bragantino","巴伊亚":"Bahia",
 "卡利亚里":"Cagliari","莱切":"Lecce","赫塔费":"Getafe","塞尔塔":"Celta Vigo","马尔默":"Malmo","索尔纳":"AIK",
 "卡尔马":"Kalmar","佐加顿斯":"Djurgardens","利雅新月":"Al-Hilal","新未来SC":"Neom","乌迪内斯":"Udinese",
 "拉齐奥":"Lazio","埃斯托里":"Estoril","阿罗卡":"Arouca","埃尔切":"Elche","皇家社会":"Real Sociedad",
 "维多利亚":"Vitoria","格雷米奥":"Gremio",
 # ===== v5.7.2 扩充：按 PinBook/Pinnacle 实际英文名补全(2026-09-08 晚23场实测缺37队,另补主流联赛常见队) =====
 # —— 当晚实测补齐 ——
 "首尔FC":["FC Seoul","Seoul"],"雅典AEK":"AEK Athens","LASK林茨":["LASK Linz","LASK"],"布鲁日":["Club Brugge","Club Bruges"],
 "奈梅亨":["NEC Nijmegen","Nijmegen"],"SBV精英":"Excelsior","胡巴卡德":["Al Qadisiyah","Al-Qadsiah","Qadsia"],
 "吉达国民":["Al Ahli","Al-Ahli","Al Ahli Jeddah"],"斯旺西":["Swansea City","Swansea"],"皇马":"Real Madrid",
 "里尔":"Lille","贝蒂斯":"Real Betis","波尔图":["Porto","FC Porto"],"弗鲁米嫩":"Fluminense",
 "普拉滕斯":["Platense","CD Platense"],"江原FC":["Gangwon FC","Gangwon"],"全北现代":["Jeonbuk Motors","Jeonbuk Hyundai"],
 "巴萨":"Barcelona","费耶诺德":"Feyenoord","斯图加特":"Stuttgart","维京":["Viking","Viking FK"],
 "特温特":["FC Twente","Twente"],"特尔斯达":"Telstar","里斯本":["Sporting CP","Sporting Lisbon","Sporting"],
 "加拉塔萨":"Galatasaray","阿森纳":"Arsenal","利物浦":"Liverpool","巴黎圣曼":["Paris Saint Germain","PSG"],
 "布拉迪斯":"Slovan Bratislava","切尔西":"Chelsea","利兹联":"Leeds United","帕梅拉斯":"Palmeiras",
 "基多体大":"LDU Quito","拉普大学":["Estudiantes de la Plata","Estudiantes"],"科林蒂安":"Corinthians",
 # —— 英超/英冠 ——
 "曼联":"Manchester United","埃弗顿":"Everton","西汉姆":"West Ham","狼队":["Wolves","Wolverhampton"],
 "布莱顿":"Brighton","伊普斯维奇":"Ipswich Town","莱切斯特":"Leicester","伯恩利":"Burnley",
 "米德尔斯堡":"Middlesbrough","西布罗姆":["West Brom","West Bromwich"],"斯托克城":"Stoke","普雷斯顿":"Preston",
 "布莱克本":"Blackburn","加的夫":"Cardiff","米尔沃尔":"Millwall","谢周三":"Sheffield Wednesday",
 "谢菲联":"Sheffield United","诺维奇":"Norwich","女王巡游":["QPR","Queens Park Rangers"],"纽卡":"Newcastle United",
 # —— 西甲 ——
 "赫罗纳":"Girona","奥萨苏纳":"Osasuna","塞维利亚":"Sevilla","西班牙人":"Espanyol","马洛卡":"Mallorca",
 "巴伦西亚":"Valencia","阿拉维斯":"Alaves","拉斯帕尔马斯":"Las Palmas","莱万特":"Levente","格拉纳达":"Granada",
 "加的斯":"Cadiz","皇家贝蒂斯":"Real Betis","比利亚雷亚尔":"Villarreal","塞尔塔":"Celta Vigo",
 # —— 意甲 ——
 "尤文":"Juventus","AC米兰":["AC Milan","Milan"],"维罗纳":"Verona","博洛尼亚":"Bologna","热那亚":"Genoa",
 "帕尔马":"Parma","科莫":"Como","蒙扎":"Monza","恩波利":"Empoli","克雷莫纳":"Cremonese","威尼斯":"Venezia",
 "萨索洛":"Sassuolo","弗罗西诺内":"Frosinone","桑普":"Sampdoria","斯佩齐亚":"Spezia","国米":["Internazionale","Inter Milan","Inter Milano"],
 # —— 德甲/德乙 ——
 "法兰克福":"Eintracht Frankfurt","沃尔夫斯堡":"Wolfsburg","美因茨":"Mainz 05","奥格斯堡":"Augsburg",
 "海登海姆":"Heidenheim","圣保利":"St Pauli","波鸿":"Bochum","汉堡":["Hamburger SV","Hamburg"],
 "科隆":["FC Koln","Cologne"],"凯泽斯劳滕":"Kaiserslautern","杜塞尔多夫":"Fortuna Dusseldorf",
 "汉诺威":"Hannover 96","纽伦堡":"Nurnberg","柏林赫塔":"Hertha Berlin",
 # —— 法甲/法乙 ——
 "摩纳哥":"Monaco","马赛":"Marseille","里昂":"Lyon","尼斯":"Nice","南特":"Nantes","雷恩":"Rennes",
 "图卢兹":"Toulouse","欧塞尔":"Auxerre","昂热":"Angers","蒙彼利埃":"Montpellier","斯特拉斯堡":"Strasbourg",
 "梅斯":"Metz","圣埃蒂安":"Saint Etienne","巴黎FC":"Paris FC",
 # —— 荷甲 ——
 "阿尔克马尔":"AZ Alkmaar","乌德勒支":"Utrecht","海伦芬":"Heerenveen","前进之鹰":"Go Ahead Eagles",
 "兹沃勒":"PEC Zwolle","鹿特丹斯巴达":"Sparta Rotterdam","福伦丹":"Volendam","阿尔梅勒":"Almere City",
 "布雷达":"NAC Breda","格罗宁根":"Groningen",
 # —— 葡超 ——
 "布拉加":"Braga","吉马良斯":"Vitoria Guimaraes","法马利康":"Famalicao","圣克拉拉":"Santa Clara",
 "博阿维斯塔":"Boavista","卡萨皮亚":"Casa Pia","摩雷伦斯":"Moreirense","里奥阿维":"Rio Ave",
 # —— 比甲 ——
 "安德莱赫特":"Anderlecht","根特":"Gent","安特卫普":"Royal Antwerp","标准列日":"Standard Liege",
 "圣吉罗斯":"Union Saint Gilloise","梅赫伦":"Mechelen","色格拉布鲁日":"Cercle Brugge","奥哈瓦里":"OH Leuven",
 # —— 苏超 ——
 "凯尔特人":"Celtic","流浪者":"Rangers","阿伯丁":"Aberdeen","哈茨":"Hearts","希伯尼安":"Hibernian",
 "基尔马诺克":"Kilmarnock","邓迪":"Dundee","圣米伦":"St Mirren","马瑟韦尔":"Motherwell","罗斯郡":"Ross County",
 # —— 欧战常客 ——
 "萨尔茨堡":["RB Salzburg","Salzburg"],"格拉茨风暴":"Sturm Graz","布拉格斯巴达":"Sparta Prague",
 "斯拉夫人":"Slavia Prague","哥本哈根":"FC Copenhagen","米迪兰特":"Midtjylland","布隆德比":"Brondby",
 "罗森博格":"Rosenborg","莫尔德":"Molde","博德闪耀":"Bodo/Glimt","费伦茨瓦罗斯":"Ferencvaros",
 "萨格勒布迪纳摩":"Dinamo Zagreb","贝尔格莱德红星":["Red Star Belgrade","Crvena Zvezda"],
 "游击":"Partizan","卢多戈雷茨":"Ludogorets","奥林匹亚科斯":"Olympiacos","帕纳辛奈科斯":"Panathinaikos",
 "塞萨洛尼基":"PAOK","费内巴切":"Fenerbahce","贝西克塔斯":"Besiktas","特拉布宗":"Trabzonspor",
 "皮尔森":"Viktoria Plzen","波兹南莱赫":"Lech Poznan","琴斯托霍瓦":"Rakow",
 "泽尼特":"Zenit","莫陆军":"CSKA Moscow","莫火车头":"Lokomotiv Moscow","莫斯巴达":"Spartak Moscow",
 "克拉斯诺达尔":"Krasnodar","迪纳摩":"Dynamo Moscow",
 # —— 日韩 ——
 "浦项制铁":"Pohang Steelers","水原三星":["Suwon Samsung","Suwon Bluewings"],"仁川联":"Incheon United",
 "大邱FC":"Daegu FC","光州FC":"Gwangju FC","金泉尚武":"Gimcheon Sangmu","大田市民":"Daejeon",
 "横滨水手":"Yokohama F.Marinos","川崎前锋":"Kawasaki Frontale","鹿岛鹿角":"Kashima Antlers",
 "浦和红钻":"Urawa Red Diamonds","神户胜利船":"Vissel Kobe","大阪樱花":"Cerezo Osaka",
 "广岛三箭":"Sanfrecce Hiroshima","东京FC":"FC Tokyo","名古屋鲸八":"Nagoya Grampus",
 "磐田喜悦":"Jubilo Iwata","湘南海洋":"Shonan Bellmare","京都不死鸟":"Kyoto Sanga",
 "町田泽维亚":"Machida Zelvia","新潟天鹅":"Albirex Niigata","大阪钢巴":"Gamba Osaka",
 "札幌冈萨多":"Consadole Sapporo","鸟栖砂岩":"Sagan Tosu","清水心跳":"Shimizu S-Pulse",
 "长崎航海":"V-Varen Nagasaki",
 # —— 沙特 ——
 "利雅青年":"Al Shabab","达曼协作":"Al Ettifaq","布赖代合作":"Al Taawoun","麦加统一":"Al Wehda",
 "达马克":"Damac","费哈":"Al Feiha","赛哈特海湾":"Al Khaleej",
 # —— 美洲 ——
 "弗拉门戈":"Flamengo","圣保罗":"Sao Paulo","桑托斯":"Santos","米内罗竞技":"Atletico Mineiro",
 "克鲁塞罗":"Cruzeiro","博塔弗戈":"Botafogo","巴西国际":"Internacional RS","河床":"River Plate",
 "博卡青年":"Boca Juniors","竞技俱乐部":"Racing Club","独立队":"Independiente","圣洛伦索":"San Lorenzo",
 "罗萨里奥":"Rosario Central","拉努斯":"Lanus","老虎大学":"Tigres UANL","蒙特雷":"Monterrey",
 "墨西哥美洲":"Club America","蓝十字":"Cruz Azul","瓜达拉哈拉":["Guadalajara","Chivas"],
 "国民竞技":"Atletico Nacional","百万富翁":"Millonarios","利马联盟":"Alianza Lima",
 # ===== v5.8.1 2026-09-11 晚12场实测补6队（PinBook馈给逐队核对标准英文名）=====
 "柏太阳神":["Kashiwa Reysol","Kashiwa"],"哈马费萨":["Al-Faisaly","Al Faisaly","Al Faisaly SC"],
 "马斯特里":["Maastricht","MVV Maastricht"],"雷克斯":["Wrexham AFC","Wrexham"],
 "科里蒂巴":["Coritiba","Coritiba FC"],"巴竞技":["Athletico Paranaense","Atletico Paranaense","Athletico-PR"],
 # ===== v5.8.1 2026-09-12 30场实测补3队 =====
 "弗洛西诺":["Frosinone","Frosinone Calcio"],"特罗姆瑟":["Tromso","Tromsø","Tromso IL","Tromsø IL"],
 "福图纳":["Fortuna Sittard","Fortuna"]}

# ===== v5.7.3 补充：按 OddsPapi/Bet365 48h真实赛程逐队核对的别名（两源命名风格不同,一并覆盖；对已有键做合并）=====
_TEAM_ALIAS_V573 = {
 # —— 已有键补 OddsPapi/Bet365 变体 ——
 "曼联":["Manchester United","Man Utd","Man United"],
 "门兴":["Monchengladbach","Borussia M Gladbach","Borussia Monchengladbach","Borussia M.Gladbach"],
 "费哈":["Al Feiha","Al Fayha FC","Al Fayha"],
 "博德闪耀":["Bodo/Glimt","Bodo Glimt"],
 # —— 五大/欧冠欧联遗漏 ——
 "顿涅茨克矿工":["Shakhtar Donetsk","Shakhtar"],"特鲁瓦":"Troyes","马拉加":"Malaga",
 # —— 土超 ——
 "伊斯坦布尔":["Istanbul Basaksehir","Basaksehir FK","Basaksehir"],"加济安泰普":["Gaziantep FK","Gaziantep"],
 "卡斯帕萨":"Kasimpasa","哥兹塔比":"Goztepe","伊尤斯堡":"Eyupspor","乔鲁姆":"Corum FK",
 "埃尔祖鲁姆":"Erzurumspor FK","阿美德":"Amed SK","根克勒比利吉":"Genclerbirligi","里泽斯堡":["Caykur Rizespor","Rizespor"],
 # —— 瑞典超 ——
 "赫根":["BK Hacken","Hacken"],"布鲁马波卡纳":["Brommapojkarna","IF Brommapojkarna"],"哈马比":"Hammarby",
 "IFK哥德堡":["IFK Goteborg","IFK Gothenburg","IFK Goteborg FC"],"天狼星":["Sirius","IK Sirius"],
 "盖斯":"GAIS","哈尔姆斯塔德":"Halmstad","米亚尔比":["Mjallby AIF","Mj llby AIF","Mjallby"],
 "代格福什":"Degerfors","奥尔格里特":"Orgryte IS","韦斯特罗斯":["Vasteras SK","V ster s sk fk","Vasteras"],
 # —— 挪超 ——
 "腓特烈斯塔":"Fredrikstad","汉坎":["HamKam","Ham Kam"],"克里斯蒂安松":["Kristiansund BK","Kristiansund"],
 "斯达":["IK Start","Start"],"桑德菲杰":"Sandefjord","奥勒松":["Aalesund","Aalesunds FK"],
 # —— 丹麦超 ——
 "奥胡斯":["AGF Aarhus","AGF"],"北西兰":["FC Nordsjaelland","Nordsjaelland"],"欧登塞":["Odense BK","Odense"],
 "锡尔克堡":["Silkeborg IF","Silkeborg"],"桑德捷斯基":["Sonderjyske","SonderjyskE"],
 # —— 荷甲 ——
 "海牙":["ADO Den Haag","Den Haag"],"坎布尔":["Cambuur Leeuwarden","Cambuur"],"威廉二世":"Willem II",
 # —— 德乙 ——
 "比勒菲尔德":["Arminia Bielefeld","Bielefeld"],"达姆施塔特":["Darmstadt","SV Darmstadt 98"],
 "德累斯顿迪纳摩":"Dynamo Dresden","菲尔特":["Greuther Furth","Greuther Fuerth","SpVgg Greuther Furth"],
 "荷尔斯泰因基尔":"Holstein Kiel","卡尔斯鲁厄":["Karlsruher SC","Karlsruher"],"奥斯纳布吕克":["VfL Osnabruck","Osnabruck"],
 "科特布斯":["Energie Cottbus","Cottbus"],
 # —— 法乙 ——
 "阿纳西":"Annecy","克莱蒙":["Clermont Foot","Clermont"],"甘冈":"Guingamp","拉瓦勒":"Stade Laval",
 "南锡":"Nancy","巴黎红星":"Red Star FC 93",
 # —— 意乙 ——
 "阿雷佐":"Arezzo","阿韦利诺":"Avellino","卡拉雷塞":"Carrarese","卡坦扎罗":"Catanzaro","尤维斯塔比亚":"Juve Stabia",
 "南蒂罗尔":"Sudtirol","恩特拉":"Virtus Entella",
 # —— 英冠/苏冠 ——
 "伯明翰":["Birmingham","Birmingham City"],"博尔顿":["Bolton Wanderers","Bolton"],
 "查尔顿":["Charlton Athletic","Charlton"],"德比郡":["Derby County","Derby"],"朴茨茅斯":["Portsmouth FC","Portsmouth"],
 "沃特福德":["Watford FC","Watford"],"雷克瑟姆":["Wrexham AFC","Wrexham"],"利文斯顿":"Livingston",
 "拉茨流浪":"Raith Rovers","阿布罗斯":"Arbroath","因弗内斯":"Inverness CT","艾尔联":"Ayr United",
 # —— 西乙 ——
 "阿尔瓦塞特":"Albacete Balompie","科尔多瓦":"Cordoba CF","特内里费":"Tenerife","巴拉多利德":["Real Valladolid","Valladolid"],
 "萨瓦德尔":"Sabadell","休达":"AD Ceuta","安道尔FC":"FC Andorra",
 # —— 韩职 K1/K2 ——
 "富川FC":["Bucheon FC 1995","Bucheon"],"安养FC":"FC Anyang","釜山偶像":["Busan I Park","Busan IPark"],
 "安山绿人":["Ansan Greeners FC","Ansan Greeners"],"清州FC":"Chungbuk Cheongju","忠南牙山":["Chungnam Asan FC","Chungnam Asan"],
 "金海市厅":"Gimhae FC 2008","金浦FC":"Gimpo FC","庆南FC":"Gyeongnam FC","全南天龙":["Jeonnam Dragons","Chunnam Dragons"],
 "城南FC":["Seongnam FC","Seongnam"],
 # —— 日职 J1/J2/联赛杯 ——
 "秋田蓝色闪电":"Blaublitz Akita","今治FC":"FC Imabari","藤枝MYFC":["Fujieda MYFC","Fujieda"],
 "磐城FC":"Iwaki FC","富山胜利":"Kataller Toyama","大宫松鼠":["Omiya Ardija","Omiya"],
 "宫崎特格瓦":"Tegevajaro Miyazaki","栃木SC":["Tochigi SC","Tochigi City"],"德岛漩涡":"Tokushima Vortis",
 "东京绿茵":"Tokyo Verdy","八户于南乡":"Vanraure Hachinohe","仙台七夕":"Vegalta Sendai",
 "长野帕塞罗":["AC Nagano Parceiro","Nagano Parceiro"],"福岛联":"Fukushima United FC",
 "滋贺湖王":"Reilac Shiga FC","赞岐釜玉海":"Kamatamare Sanuki",
 # —— 欧战小联赛常客 ——
 "阿拉特亚美尼亚":"Ararat Armenia","巴尼亚卢卡战士":["Borac Banja Luka","Borac"],"克拉约瓦大学":["CS U Craiova","Universitatea Craiova"],
 "第比利斯伊比利亚":"FC Iberia 1999","亚布洛内茨":"FK Jablonec","考纳斯扎尔吉里斯":["FK Kauno Zalgiris","Kauno Zalgiris"],
 "斯普利特海杜克":"Hajduk Split","贝尔谢巴夏普尔":"Hapoel Beer Sheva","乔治罗尼亚":"Jagiellonia Bialystok",
 "阿拉木图凯拉特":["FC Kairat Almaty","Kairat Almaty","Kairat"],"埃格纳蒂亚":"KF Egnatia","库奥皮奥":"KuPS Kuopio",
 "索菲亚列夫斯基":"Levski Sofia","采列":"NK Celje","OFI克里特":["OFI Crete","OFI"],
 "叶里温凤凰":["FC Pyunik Yerevan","Pyunik"],"林肯红魔":"Lincoln Red Imps FC",
 # —— 沙特 ——
 "费萨里":["Al Faisaly FC","Al Faisaly"],"法特赫":["Al Fateh SC","Al Fateh"],"迪里耶":"Diriyah Club",
 # —— 葡超 ——
 "维塞乌学院":"Academico Viseu",
 # —— 巴甲/巴乙 ——
 "瓦斯科达伽马":["Vasco da Gama","Vasco"],"福塔雷萨":["Fortaleza EC","Fortaleza"],"塞阿拉":["Ceara SC","Ceara"],
 "克里丘马":["Criciuma EC","Criciuma"],"库亚巴":["Cuiaba EC MT","Cuiaba"],"维拉诺瓦竞技":"Vila Nova",
 "新奥里藏特":"Novorizontino","米内罗美洲":["America FC MG","America Mineiro"],"阿瓦伊":["Avai FC SC","Avai"],
 "雷加塔斯":["CR Brasil AL","CRB"],
}
TEAM_ALIAS_CN2EN.update(_TEAM_ALIAS_V573)

# ===== v5.8.1 补充①：按 2026-09-10 竞彩7场实测未命中(斯拉维亚/萨巴赫/阿马多拉/德尔瓦耶)+系统性补欧战/葡超/南美/澳超常客 =====
# 命中瓶颈从来不是 Pinnacle 没开盘、而是中文译名查无此键；补键即直接提升自动锐线匹配率。英文名按 Pinnacle 常用命名给多别名。
_TEAM_ALIAS_V581 = {
 # —— 当晚实测缺失（最高优先）——
 "斯拉维亚":["Slavia Prague","Slavia Praha"], "布拉格斯拉维亚":["Slavia Prague","Slavia Praha"],
 "皇家马德里":"Real Madrid", "巴塞罗那":"Barcelona",   # 常见全称兜底(竞彩多用皇马/巴萨,全称也保证命中)
 "萨巴赫":["Sabah FK","Sabah"],
 "阿马多拉":["Estrela Amadora","Estrela da Amadora"],
 "德尔瓦耶":["Independiente del Valle","Del Valle"], "山谷独立":["Independiente del Valle","Del Valle"],
 # —— 欧冠/欧联/欧协联资格赛常客（中小联赛冠军，竞彩欧战常售、旧典易缺）——
 "卡拉巴赫":["Qarabag FK","Qarabag","Karabakh"], "谢里夫":["Sheriff Tiraspol","FC Sheriff","Sheriff"],
 "赫尔辛基":["HJK Helsinki","HJK"], "卢加诺":"Lugano", "塞尔维特":"Servette", "圣加仑":"St Gallen",
 "里耶卡":"Rijeka", "萨格勒布火车头":"Lokomotiva Zagreb", "布拉迪斯拉发":["Slovan Bratislava","Slovan"],
 "华沙莱吉亚":["Legia Warsaw","Legia"], "布加勒斯特星":["FCSB","Steaua Bucharest"], "克卢日":"CFR Cluj",
 "布拉格斯巴达":"Sparta Prague",
 # —— 葡超补缺 ——
 "吉维森特":"Gil Vicente", "法伦斯":"Farense", "波尔蒂芒人":"Portimonense",
 # —— 解放者杯/南美杯常客（旧典覆盖偏弱）——
 "约森独立":"Independiente Medellin", "秘鲁体育大学":["Universitario","Universitario de Deportes"],
 "巴兰基亚青年":["Atletico Junior","Junior FC","Junior"], "卡利美洲":"America de Cali",
 "塔奇拉":"Deportivo Tachira", "科洛科洛":"Colo Colo", "天主大学":"Universidad Catolica",
 "智利大学":"Universidad de Chile", "亚松森自由":["Libertad","Club Libertad"],
 "亚松森奥林匹亚":["Olimpia","Club Olimpia"], "波特诺山丘":"Cerro Porteno",
 "瓜亚基尔巴塞罗那":["Barcelona SC","Barcelona Guayaquil"], "最强者":"The Strongest",
 "玻利瓦尔":["Bolivar","Club Bolivar"], "佩纳罗尔":"Penarol",
 "民族队":["Nacional","Club Nacional","Nacional Montevideo"],
 # —— 澳超整套（竞彩常年在售、旧典几乎空白）——
 "墨尔本城":"Melbourne City", "西悉尼":"Western Sydney Wanderers", "悉尼FC":"Sydney FC",
 "阿德莱德联":"Adelaide United", "珀斯光荣":"Perth Glory", "惠灵顿凤凰":"Wellington Phoenix",
 "中央海岸":"Central Coast Mariners", "麦克阿瑟":"Macarthur FC", "布里斯班狮吼":"Brisbane Roar",
 "纽卡斯尔喷气机":"Newcastle Jets", "西部联":"Western United", "墨尔本胜利":"Melbourne Victory",
 "奥克兰FC":"Auckland FC",
}
TEAM_ALIAS_CN2EN.update(_TEAM_ALIAS_V581)

# ===== v5.8.7 当日补充：2026-09-14 实测未命中队名（按 PinBook/Pinnacle 实时馈送命名核对，纯增量补键，提升自动锐线匹配率）=====
_TEAM_ALIAS_V587_0914 = {
 "国际图尔":["Inter Turku"],            # 芬超 Inter Turku（Pinnacle 名）
 "瓦萨":["VPS"], "VPS瓦萨":["VPS"],      # 芬超 VPS（瓦萨）
 "桑纳菲":["Sandefjord"], "桑纳菲尤尔":["Sandefjord"],   # 挪超 Sandefjord（博德闪耀对手）
 "棉农":["Pakhtakor Tashkent","Pakhtakor"],              # 亚冠 棉农（塔什干棉农）
 "圣旺红星":["Red Star"],               # 法乙 Red Star FC（巴黎红星/圣旺红星；区别于贝尔格莱德Crvena Zvezda）
}
TEAM_ALIAS_CN2EN.update(_TEAM_ALIAS_V587_0914)


def collect_sporttery(date, main_batch_only=True):
    """通道0(权威/免费/已验证可达)：竞彩官方计算器接口 → 场次 胜平负/让球/比分16格/总进球8档+让球线。
    v5.5.1 关键修复：date='auto'/'upcoming' 时【跨所有业务日期分组、只取未来48h内未开赛】场——
    21点购彩时当天凌晨场已踢完、次日凌晨赛挂在【次日businessDate分组】，旧逻辑只按_bj_today单分组匹配会漏场/误取已开赛场；
    matchStatus接口常滞后(已开赛仍Selling)不可靠，统一用开球时间过滤。指定具体日期则只取该分组(不过滤,尊重指定)。"""
    url = ("https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry?"
           "poolCode=had,hhad,crs,ttg,hafu&channel=c_web")
    d = json.loads(_http_get(url, referer="https://www.sporttery.cn/jc/jsq/zqspf/"))
    groups = d["value"]["matchInfoList"]
    upcoming = date in ("auto", "upcoming")
    if upcoming:
        target_groups = groups
    else:
        grp = next((g for g in groups if g.get("businessDate") == date), None)
        if grp is None:
            raise RuntimeError(f"官方接口无 {date} 分组(可选日期:{[g.get('businessDate') for g in groups]})")
        target_groups = [grp]
    bj_now = _bj_now_naive()   # 北京时间(naive便于比较)
    out = []
    _n_skip_past = 0
    for grp in target_groups:
        bd = grp.get("businessDate")
        for m in grp["subMatchList"]:
            if upcoming:   # 用matchDate(真实开球日)判未开赛,只保留 0<距开球≤48h;剔除已开赛/过远场
                ko = kickoff_dt({"matchDate": m.get("matchDate"), "businessDate": bd, "matchTime": m.get("matchTime")})
                if ko is None:
                    continue
                dh = (ko - bj_now).total_seconds() / 3600.0
                if dh <= 0 or dh > 48:
                    _n_skip_past += 1
                    continue
            had, hh, crs, ttg = m.get("had"), m.get("hhad"), m.get("crs"), m.get("ttg")
            def g(x,k): return None if x is None else x.get(k)
            ssp = {}
            for i in range(4):
                for j in range(4):
                    v = (crs or {}).get(f"s{i:02d}s{j:02d}")
                    if v not in (None, ""): ssp[(i,j)] = float(v)
            pools = {p["poolCode"]: p for p in m.get("poolList", [])}
            def single(code): return bool((pools.get(code) or {}).get("single"))
            out.append({
                "no": m["matchNumStr"][-3:], "lg": m["leagueAbbName"], "time": m.get("matchTime"),
                # matchDate=真实开球自然日(凌晨场比销售businessDate晚一天,早盘/未开赛判定必须用它)；businessDate=销售轮次日
                "matchDate": m.get("matchDate"),
                "businessDate": bd, "matchTime": m.get("matchTime"),
                "lg_full": m.get("leagueAllName"), "home_full": m.get("homeTeamAllName"), "away_full": m.get("awayTeamAllName"),
                "home_rank": (m.get("homeRank") or "").strip("[]"), "away_rank": (m.get("awayRank") or "").strip("[]"),
                "match_id": m.get("matchId"), "sell_status": m.get("matchStatus"),
                "home": m["homeTeamAbbName"], "away": m["awayTeamAbbName"],
                "hand": int(float(hh["goalLine"])) if hh and g(hh,"goalLine") not in (None,"") else None,
                "spf": [_f(g(had,"h")), _f(g(had,"d")), _f(g(had,"a"))] if had else None,
                "rsp": [_f(g(hh,"h")), _f(g(hh,"d")), _f(g(hh,"a"))] if hh else None,
                "ssp": ssp, "tsp": [_f((ttg or {}).get(f"s{k}")) for k in range(8)],
                "open_single": {"w": single("HAD"), "h": single("HHAD"), "score": single("CRS"), "tg": single("TTG")},
                "_sp_time": g(had,"updateTime") or g(hh,"updateTime"), "_src_sp": "竞彩官方接口"})
    if upcoming:
        # main_batch_only=True: 锁定"当前销售批次(竞彩businessDate销售日)"主批次,剔除下一销售日的后批、避免跨批串关;
        # =False: 返回未来48h全部未开赛场(供"指定后批编号"时补骨架)。
        if main_batch_only:
            # v5.7.5修复：竞彩"一批"=同一个businessDate销售日——当天傍晚场(matchDate=今天)与次日凌晨场
            # (matchDate=明天)同属一个销售批次。旧版按matchDate真实开球日锁"最早自然日",傍晚(如17点)运行时
            # 会只保留当天傍晚仅剩的早场、把同批次次日凌晨的主赛全部裁掉(只锁到1场)。
            # 改为：取"最早未开赛场"所属的businessDate,保留该销售批次下全部未开赛场(跨matchDate自然日也保留)。
            _ko_pairs = [(kickoff_dt(z), z) for z in out]
            _ko_pairs = [t for t in _ko_pairs if t[0] is not None]
            if _ko_pairs:
                _main_bd = min(_ko_pairs, key=lambda t: t[0])[1].get("businessDate")
                if _main_bd:
                    out = [z for z in out if z.get("businessDate") == _main_bd]
        out.sort(key=lambda z: (kickoff_dt(z) or _dt.max))   # 临近开赛在前
    return out

def _align_hda(ev, vals):
    """把 {规范化队名:price} 对齐成 [主,平,客]。"""
    hk, ak = _en_norm(ev.get("home_team")), _en_norm(ev.get("away_team"))
    ph = pa = pd = None
    for name, price in vals.items():
        if name in ("draw","tie","x","平"): pd = price
        elif name == hk or (hk and hk in name) or (name and name in hk): ph = price
        elif name == ak or (ak and ak in name) or (name and name in ak): pa = price
    if ph is None or pd is None or pa is None: return None
    return [float(ph), float(pd), float(pa)]

def collect_oddsapi():
    """通道1/2(免费key)：TheOddsAPI 一次拉回 Pinnacle(1)/Betfair(2) 的 1X2(h2h)+大小球(totals)+2维亚盘(spreads留档)。
    返回 {(规范主队,规范客队): {...}}。无 key 直接跳过。"""
    if not ODDS_API_KEY:
        return {}, "跳过TheOddsAPI(可选)：未配 ODDS_API_KEY；注意其免费档仅NBA/MLB，足球Pinnacle需付费档，免费主力请用PinBook"
    url = ("https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey=" + ODDS_API_KEY +
           "&regions=eu,uk&markets=h2h,totals,spreads&oddsFormat=decimal&dateFormat=iso")
    evs = json.loads(_http_get(url))
    order = {"pinnacle":(1,"Pinnacle"),"betfair_ex_uk":(2,"Betfair"),"betfair_ex_eu":(2,"Betfair")}
    out = {}
    for ev in evs:
        H,A = _en_norm(ev["home_team"]), _en_norm(ev["away_team"])
        spfp, oup = {}, {}
        for bm in ev.get("bookmakers", []):
            if bm.get("key") not in order: continue
            src,name = order[bm["key"]]; tm = bm.get("last_update")
            for mk in bm.get("markets", []):
                if mk["key"]=="h2h":
                    tri = _align_hda(ev, {_en_norm(o["name"]):o["price"] for o in mk["outcomes"]})
                    if tri: spfp[src]=(tri,tm,name)
                elif mk["key"]=="totals":
                    bypt={}
                    for o in mk["outcomes"]:
                        pt=o.get("point")
                        if pt is None: continue
                        bypt.setdefault(round(float(pt),2),{})[ "over" if o["name"].lower().startswith("over") else "under"]=float(o["price"])
                    feas=[(abs(pt-2.5),pt,v) for pt,v in bypt.items() if "over" in v and "under" in v]
                    if feas:
                        _,pt,v=min(feas,key=lambda z:z[0]); oup[src]=({"line":pt,"over":v["over"],"under":v["under"]},tm,name)
        def best(dd):
            if not dd: return None
            s=min(dd); val=dd[s]; return (s,)+val
        bs,bo=best(spfp),best(oup)
        out[(H,A)]={"spf":(bs[1] if bs else None),"src":(bs[0] if bs else None),
                    "time":(bs[2] if bs else None),"name":(bs[3] if bs else None),
                    "ou":(bo[1] if bo else None)}
    return out, f"TheOddsAPI: 取到 {len(out)} 场带锐线赛事(Pinnacle优先,Betfair补)"

import tempfile as _tf
_PB_CACHE = {"/kit/v1/markets": _os.path.join(_tf.gettempdir(), "pb_markets.json"),
             "/kit/v1/special-markets": _os.path.join(_tf.gettempdir(), "pb_special.json")}
_PB_HOST_PREF = None    # v5.7.3：本轮首个成功host,后续请求优先它(避免每请求都先撞坏host)
def _pb_host_order():
    hosts = list(PINBOOK_HOSTS)
    if _PB_HOST_PREF in hosts:
        hosts.remove(_PB_HOST_PREF); hosts.insert(0, _PB_HOST_PREF)
    return hosts
def _pb_get(path, params):
    """v5.7.3：孪生host热备。按 PINBOOK_HOSTS 顺序逐个尝试(网络错误/HTTP错误/429/5xx/空壳都切下一个host)，
    全部host失败才回退本地新鲜缓存；成功host记入 PB_ACTIVE_HOST 并在本轮优先复用。"""
    global PB_ACTIVE_HOST, _PB_HOST_PREF
    import time as _time
    qs = _uparse.urlencode(params); last = None
    for host in _pb_host_order():
        url = f"https://{host}{path}?{qs}"
        for _i in range(2):
            try:
                txt = _http_get(url, extra={"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": host}, timeout=30)
                d = json.loads(txt)
                # 空壳/网关报错也算失败,切下一个host(markets必须有events、special必须有specials)
                if path == "/kit/v1/markets" and not d.get("events"):
                    raise RuntimeError(f"{host} markets返回空壳")
                if path == "/kit/v1/special-markets" and "specials" not in d:
                    raise RuntimeError(f"{host} special-markets返回异常")
                PB_ACTIVE_HOST = host; _PB_HOST_PREF = host
                cp = _PB_CACHE.get(path)
                if cp:
                    try:
                        with open(cp, "w", encoding="utf-8") as _cf: _cf.write(txt)
                    except Exception: pass
                return d
            except Exception as e:
                last = e; _time.sleep(1)
    cp = _PB_CACHE.get(path)   # 全部host持续抖动时回退到本地新鲜缓存（赛前赔率，分钟级有效）
    if cp and _os.path.exists(cp):
        with open(cp, encoding="utf-8") as _cf:
            PB_ACTIVE_HOST = (PB_ACTIVE_HOST or "本地缓存"); return json.load(_cf)
    raise last
def _pb_mainline(totals):
    """Pinnacle totals={'2.5':{points,over,under,max}} → 主盘=受注上限max最大者；都无max时退化为最接近2.5。"""
    cands=[]
    for _,v in (totals or {}).items():
        if not isinstance(v,dict): continue
        o,u=v.get("over"),v.get("under")
        if o is None or u is None: continue
        try: pt=float(v.get("points"))
        except Exception: continue
        try: mx=float(v.get("max",-1))
        except Exception: mx=-1
        cands.append((mx,abs(pt-2.5),pt,float(o),float(u)))
    if not cands: return None
    cands.sort(key=lambda z:(-z[0],z[1]) if all(c[0]>=0 for c in cands) else (z[1],))
    _,_,pt,o,u=cands[0]
    return {"line":pt,"over":o,"under":u}
def _pb_ou_multi(totals, lo=OU_MULTI_LO, hi=OU_MULTI_HI):
    """v5.7 P0-3：导出Pinnacle全部有效大小球线[{line,over,under}]（只留[lo,hi]内、双向水位齐全的线），
    供 total_lambda_from_ou_multi 联立拟合总λt；主盘ou仍由_pb_mainline另存，二者互不影响。"""
    out=[]
    for _,v in (totals or {}).items():
        if not isinstance(v,dict): continue
        o,u=v.get("over"),v.get("under")
        if o is None or u is None: continue
        try: pt=float(v.get("points"))
        except Exception: continue
        if lo <= pt <= hi:
            out.append({"line":pt,"over":float(o),"under":float(u)})
    out.sort(key=lambda z:abs(z["line"]-2.5))
    return out or None
# ==================== v5.7.2 RapidAPI 锐线防错配加固（2026-09-08 实测后修复）====================
# 实测发现 PinBook 同一队名对下并存多类事件：①resulting_unit=Corners/Bookings 的角球/牌盘1X2；
# ②UEFA Youth League U19/女足/预备队(U21/Reserve)与成年正赛同日同对阵(2026-09-08晚23场竞彩中4场撞此问题，
# 旧版只按队名取dict最后一条→把U19赔率错套到成年欧冠)。修复：非Regular直接剔；青年/女足/预备队保留为候选并打标，
# 由 _pb_resolve 按【竞彩开赛时间(北京)↔PinBook starts(UTC)】就近消歧，无法确定就弃用(宁缺毋错)。
_PB_JUNIOR_RE = re.compile(r"(youth|u-?\s?(15|16|17|18|19|20|21|23)\b|reserve|women|woman|ladies|girl|primavera|academy)", re.I)
PB_ALLOW_JUNIOR = False       # True=允许青年/女足/预备队候选(竞彩几乎不售这些,默认关)
PB_DISAMBIG_HOURS = 3.0       # 最近候选与竞彩开赛时间差超过该值→判为非同一赛事,弃用锐线
PB_CAND = {}                  # (规范主队,规范客队) -> [候选事件dict...](含league/starts_dt/event_id/junior)
PB_EH_CAND = {}               # (H,A) -> {让球线float: [(px3, event_id, league, starts)]}
def _pb_is_junior(lg):
    return bool(_PB_JUNIOR_RE.search(str(lg or "")))
def _pb_starts_dt(s):
    try:
        return _dt.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S")   # PinBook starts=UTC 无时区
    except Exception:
        return None
def collect_pinbook():
    """通道1(免费key·主力)：RapidAPI「PinBook Odds」= 无延迟 Pinnacle。
    /kit/v1/markets 取 1X2(money_line)+大小球(totals主盘)；/kit/v1/special-markets 取
    bet_type=MULTI_WAY_HEAD_TO_HEAD 且 name 含 '3-Way Handicap' 的【3维让球】三项(让胜/让平/让负)。
    v5.7.2：剔角球/牌盘(非Regular)；同队名多赛事全部留候选(PB_CAND)，so只放"成年优先"默认值，
    最终在assemble里由_pb_resolve按开赛时间消歧。返回 (so, eh, msg) 结构与旧版完全兼容。"""
    if not RAPIDAPI_KEY:
        return {},{}, ("跳过PinBook(Pinnacle)：未配置免费 RAPIDAPI_KEY —— 到 RapidAPI 订阅「PinBook Odds」"
                       "BASIC($0/月,550次/月)即可全自动拿1X2+大小球+3维让球；未配前让球走MANUAL_SHARP兜底")
    so,eh={},{}
    PB_CAND.clear(); PB_EH_CAND.clear()
    n_skip_nonregular=n_skip_junior=0
    try:
        mk=_pb_get("/kit/v1/markets",{"sport_id":1,"event_type":"prematch","is_have_odds":"true"})
        lid2lg={ev.get("league_id"): ev.get("league_name") for ev in mk.get("events",[])}
        for ev in mk.get("events",[]):
            # v5.7.2 fix-1：只收正赛(Regular)；角球盘Corners/牌盘Bookings等衍生结算盘一律剔除
            if (ev.get("resulting_unit") or "Regular") != "Regular":
                n_skip_nonregular+=1; continue
            p0=((ev.get("periods") or {}).get("num_0")) or {}
            ml=p0.get("money_line") or {}
            if all(ml.get(k) is not None for k in ("home","draw","away")):
                H,A=_en_norm(ev.get("home")),_en_norm(ev.get("away"))
                junior=_pb_is_junior(ev.get("league_name"))
                if junior: n_skip_junior+=1
                PB_CAND.setdefault((H,A),[]).append({
                    "spf":[float(ml["home"]),float(ml["draw"]),float(ml["away"])],"src":1,
                    "name":"Pinnacle","time":ev.get("starts"),"ou":_pb_mainline(p0.get("totals")),
                    "ou_multi":_pb_ou_multi(p0.get("totals")),   # v5.7: 全档totals供多线联立λt
                    "league":ev.get("league_name"),"event_id":ev.get("event_id"),
                    "junior":junior,"starts_dt":_pb_starts_dt(ev.get("starts"))})
        # so=向后兼容的默认值：同队名多候选时成年正赛优先、其次开赛更早者
        for k,cands in PB_CAND.items():
            cands.sort(key=lambda c:(c["junior"], c.get("starts_dt") or _dt.max))
            d={kk:vv for kk,vv in cands[0].items() if kk!="starts_dt"}
            so[k]=d
        sp=_pb_get("/kit/v1/special-markets",{"sport_id":1,"event_type":"prematch","is_have_odds":"true"})
        for s in sp.get("specials",[]):
            if s.get("bet_type")!="MULTI_WAY_HEAD_TO_HEAD": continue
            nm=s.get("name","")
            if "3-way handicap" not in nm.lower(): continue
            # v5.7.2 fix-2：让球同步剔青年/女足/预备队(用league_id关联markets的联赛名)
            if _pb_is_junior(lid2lg.get(s.get("league_id"))): continue
            ev=s.get("event") or {}; H,A=_en_norm(ev.get("home")),_en_norm(ev.get("away"))
            mt=re.search(r'([+-]?\d+(?:\.\d+)?)\s*$',nm.strip()); line=float(mt.group(1)) if mt else None
            if line is None: continue
            px=[None,None,None]
            for ln in (s.get("lines") or {}).values():
                lnname=_en_norm(ln.get("name","")); price=_f(ln.get("price"))
                if "draw" in lnname or lnname=="x": px[1]=price
                elif H and (H in lnname or lnname in H): px[0]=price
                elif A and (A in lnname or lnname in A): px[2]=price
            if all(x is not None for x in px) and str(s.get("status","O")).upper()=="O":
                PB_EH_CAND.setdefault((H,A),{}).setdefault(line,[]).append(
                    (px, s.get("event_id"), lid2lg.get(s.get("league_id")), s.get("starts")))
        # eh默认值：每线取首个成年候选(与选定赛事event_id对齐的工作放在assemble)
        for k,ld in PB_EH_CAND.items():
            eh[k]={line:lst[0][0] for line,lst in ld.items()}
    except Exception as e:
        return {},{}, f"PinBook通道异常(已安全跳过,不编造):{e}"
    nline=sum(len(v) for v in eh.values())
    ndup=sum(1 for v in PB_CAND.values() if len(v)>1)
    save_pinbook_history(so, eh)   # v5.6 零额外请求：每次成功采集存一份线移动历史
    extra=[]
    extra.append(f"host={PB_ACTIVE_HOST}" + ("(孪生热备)" if PB_ACTIVE_HOST not in (None,PINBOOK_HOSTS[0],"本地缓存") else ""))
    if n_skip_nonregular: extra.append(f"剔角球/牌盘等非正赛{n_skip_nonregular}个")
    if ndup: extra.append(f"同队名多赛事{ndup}对(按开赛时间消歧)")
    return so,eh,(f"PinBook/Pinnacle(src1): 1X2+大小球 {len(so)} 场、3维让球 {nline} 条线"
                  + (f"（{'、'.join(extra)}）" if extra else "")
                  + ("（让球可自动对齐竞彩hand）" if nline else ""))
def _pb_resolve(r, pbk):
    """v5.7.2：同队名多赛事消歧。按竞彩开球(北京时间)与PinBook starts(UTC)就近选同一场；
    青年/女足候选仅在PB_ALLOW_JUNIOR时可用；时间对不上或两个候选同样近→保守返回None(不套锐线,防错场)。
    返回 (选定候选dict或None, 判定说明)。"""
    cands=PB_CAND.get(pbk)
    if not cands: return None, "无候选"
    ko=kickoff_dt(r)
    def _dh(c):
        sd=c.get("starts_dt")
        if ko is None or sd is None: return 9e9
        return abs(((ko-_td(hours=8))-sd).total_seconds())/3600.0   # 北京→UTC
    scored=sorted(((_dh(c),c) for c in cands), key=lambda z:z[0])
    bd,best=scored[0]
    for d2,c2 in scored[1:]:                       # 最佳若是青年而存在几乎同时的成年候选,取成年
        if best.get("junior") and not c2.get("junior") and d2-bd<=0.35:
            bd,best=d2,c2
    if best.get("junior") and not PB_ALLOW_JUNIOR:
        return None, "仅青年/女足/预备队候选,已弃用"
    if bd>PB_DISAMBIG_HOURS:
        return None, f"最近候选开赛时差{bd:.1f}h>{PB_DISAMBIG_HOURS:g}h,非同一赛事,弃用"
    if len(scored)>1 and abs(scored[1][0]-bd)<=0.25 and scored[1][1] is not best:
        return None, "两个候选开赛时间同样接近,无法消歧,弃用"
    return best, (f"时间差{bd:.1f}h" if bd<9e8 else "无竞彩时间,取成年优先默认")

# ==================== v5.7.3 第二层：OddsPapi（Pinnacle同源互验 + Betfair交易所第二锐线 + 三维让球备份）====================
# 实测语义(2026-09-08,真实接口逐字段核对)：
#  · /fixtures 按 startTimeFrom/To(epoch秒)取赛程；participants.participant1=主队、participant2=客队(与场地一致)；
#    externalProviders.pinnacleId = Pinnacle原生赛事ID,【与 PinBook event_id 完全相同】(同场实测1635267534双向一致)。
#  · /fixtures/odds/main 批量取主盘；odds[书商][行]={marketId,outcomeId,price,...}；市场语义以 /markets 元数据为准：
#    101=全场1X2(outcomes 101主/102平/103客)、totals=大小球(先Over后Under,只取period=fulltime)、
#    spreads-european=三维让球(整数线,outcomes 主/平/客；实测+1线 1.909/4.29/3.45 与PinBook「3-Way Handicap 主+1」
#    三位小数完全一致 → 让球为【主队视角、与竞彩"主让为负"同号】)、spreads=2维亚盘(只留档不合成让球)。
#  · 噪声：SRL模拟联赛/U19-23/Reserve/Women/Youth 约占两成,且存在同对阵双fixtureId → 与PinBook同套时间消歧。
_OP_NOISE_RE = re.compile(r"(youth|u-?\s?(15|16|17|18|19|20|21|23)\b|reserve|women|woman|ladies|girl|primavera|academy|\bsrl\b|simulated|esoccer|cyber)", re.I)
OP_CAND = {}          # (规范主队,规范客队) -> [候选fixture...]
OP_BY_PINID = {}      # Pinnacle原生event_id -> 候选fixture(成年正赛,ID级精确对齐用)
OP_ODDS = {}          # fixtureId -> {"pinnacle":{spf,ou,ou_multi,eh}, "betfair-ex":{...}}
OP_META_CACHE = _os.path.join(_tf.gettempdir(), "op_markets_meta.json")
def _op_get(path, params):
    url = f"https://{ODDSPAPI_HOST}{path}?" + _uparse.urlencode(params)
    return json.loads(_http_get(url, extra={"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": ODDSPAPI_HOST}, timeout=30))
def _op_markets_meta():
    """marketId→市场元数据(静态字典,本地缓存兜底)。返回 {mid:{type,handicap,period,{outcomeId:outcomeName}}}。"""
    raw = None
    try:
        raw = _op_get("/markets", {"sportId": ODDSPAPI_SOCCER})
        try:
            with open(OP_META_CACHE, "w", encoding="utf-8") as f: json.dump(raw, f)
        except Exception: pass
    except Exception:
        if _os.path.exists(OP_META_CACHE):
            try:
                with open(OP_META_CACHE, encoding="utf-8") as f: raw = json.load(f)
            except Exception: raw = None
    meta = {}
    for m in (raw or []):
        meta[m["marketId"]] = {"type": m.get("marketType"), "hcap": m.get("handicap"),
                               "period": m.get("period"),
                               "oc": {o["outcomeId"]: o.get("outcomeName") for o in (m.get("outcomes") or [])}}
    return meta
def _op_is_noise(lg):
    return bool(_OP_NOISE_RE.search(str(lg or "")))
def op_collect_fixtures(now_ts=None, window_h=48):
    """阶段A：拉未来48h足球赛程，建候选注册表(队名键 + Pinnacle原生ID键)。返回(候选对数,消息)。"""
    OP_CAND.clear(); OP_BY_PINID.clear()
    if not RAPIDAPI_KEY or not ODDSPAPI_ENABLED:
        return 0, "跳过OddsPapi：未启用/无key"
    import time as _time
    now_ts = now_ts or int(_time.time())
    try:
        fx = _op_get("/fixtures", {"sportId": ODDSPAPI_SOCCER, "startTimeFrom": now_ts,
                                   "startTimeTo": now_ts + window_h*3600})
    except Exception as e:
        return 0, f"OddsPapi赛程通道异常(已安全跳过):{e}"
    n_noise = 0
    for f in fx:
        if (f.get("status") or {}).get("live"): continue
        t = (f.get("tournament") or {}).get("tournamentName", "")
        p = f.get("participants") or {}
        H, A = _en_norm(p.get("participant1Name")), _en_norm(p.get("participant2Name"))
        if not H or not A: continue
        noise = _op_is_noise(t)
        if noise: n_noise += 1
        cand = {"fixtureId": f.get("fixtureId"), "league": t, "starts_ts": f.get("startTime"),
                "noise": noise, "home": p.get("participant1Name"), "away": p.get("participant2Name"),
                "pinnacleId": ((f.get("externalProviders") or {}).get("pinnacleId"))}
        OP_CAND.setdefault((H, A), []).append(cand)
        pid = cand["pinnacleId"]
        if pid and not noise:    # 成年正赛才进ID精确表(噪声赛事的pinnacleId是其U19对应盘,绝不能对齐成年场)
            OP_BY_PINID.setdefault(pid, cand)
    return len(OP_CAND), f"OddsPapi赛程: {len(OP_CAND)} 对候选(剔噪声{n_noise}个SRL/青年/女足)"
def _op_time_pick(cands, r):
    """与_pb_resolve同口径：按竞彩开赛(北京)与fixture starts(UTC epoch)就近消歧；双候选同近/仅噪声→弃用。"""
    ko = kickoff_dt(r)
    if ko is None:
        adult = [c for c in cands if not c["noise"]]
        return (adult or cands)[0], "无竞彩时间取成年默认"
    target_utc = (ko - _td(hours=8)).replace(tzinfo=_tz.utc).timestamp()   # 北京墙钟→UTC naive→显式UTC epoch(防机器本地时区二次偏移)
    scored = sorted(((abs((c.get("starts_ts") or 0) - target_utc)/3600.0, c) for c in cands), key=lambda z:z[0])  # v5.7.6:只按时间差排序,等距时不比较dict(旧版TypeError)
    bd, best = scored[0]
    for d2, c2 in scored[1:]:
        if best["noise"] and not c2["noise"] and d2-bd <= 0.35: bd, best = d2, c2
    if best["noise"]: return None, "仅噪声候选(SRL/青年/女足),弃用"
    if bd > PB_DISAMBIG_HOURS: return None, f"最近候选开赛时差{bd:.1f}h>{PB_DISAMBIG_HOURS:g}h,弃用"
    if len(scored) > 1 and abs(scored[1][0]-bd) <= 0.25 and scored[1][1] is not best:
        return None, "两个候选同样接近,无法消歧,弃用"
    return best, f"时间差{bd:.1f}h"
def op_resolve(r, pb_event_id, op_map):
    """为一场竞彩选定OddsPapi fixture。优先 Pinnacle原生ID精确对齐(零模糊)；否则走中→英队名+时间消歧。
    op_map: 由 OP_CAND 转成的 {键:候选列表} 供 _match_en 复用(这里直接用全局OP_CAND)。返回(fixture,说明,方式)。"""
    # ① ID级精确：PinBook选定赛事的event_id == OddsPapi的pinnacleId
    if pb_event_id and pb_event_id in OP_BY_PINID:
        return OP_BY_PINID[pb_event_id], "pinnacleId精确对齐", "id"
    # ② 队名模糊匹配(与PinBook同一套双阈值) + 时间消歧
    bk = None
    if not r.get("home") or not r.get("away"): return None,"骨架缺队名,跳过","none"
    ehs, eas = _cn_en_aliases(r["home"]), _cn_en_aliases(r["away"])
    bs, bh, ba = -1.0, 0.0, 0.0
    for k, cands in OP_CAND.items():
        sh = max((_team_match_score(eh, k[0]) for eh in ehs), default=0.0)
        sa = max((_team_match_score(ea, k[1]) for ea in eas), default=0.0)
        if sh+sa > bs: bs, bk, bh, ba = sh+sa, k, sh, sa
    if bk is not None and min(bh, ba) >= 0.6 and bs >= 2.2:
        fx, note = _op_time_pick(OP_CAND[bk], r)
        if fx is None: return None, f"队名命中但{note}", "none"
        return fx, f"队名匹配(分{bh:.2f}/{ba:.2f})+{note}", "name"
    return None, f"无可靠队名匹配(最佳{bh:.2f}/{ba:.2f}/{bs:.2f})", "none"
def _op_parse_book(rows, meta):
    """把某书商在一场的全部报价行 → {spf,ou,ou_multi,eh:{line:三项}}（只取全场；让球主队视角同PinBook）。"""
    by_mid = {}
    for row in (rows or {}).values():
        mid = row.get("marketId"); m = meta.get(mid)
        if not m or m.get("period") not in ("fulltime", None): continue
        by_mid.setdefault(mid, {})[row.get("outcomeId")] = _f(row.get("price"))
    spf = None; tot = {}; eh = {}
    for mid, oc in by_mid.items():
        m = meta[mid]; t = m["type"]; ocnames = m["oc"]
        seq = [(ocnames.get(oid), pv) for oid, pv in oc.items()]
        if t == "1x2" and mid == 101 and len(seq) == 3:   # 仅全场1X2(排除10208上半场)
            d3 = {nm: pv for nm, pv in seq}
            if all(d3.get(k) is not None for k in ("1", "X", "2")): spf = [d3["1"], d3["X"], d3["2"]]
        elif t == "totals":
            try: line = float(m["hcap"])
            except Exception: continue
            d2 = {nm: pv for nm, pv in seq}
            if d2.get("Over") is not None and d2.get("Under") is not None and OU_MULTI_LO <= line <= OU_MULTI_HI:
                tot[line] = {"line": line, "over": d2["Over"], "under": d2["Under"]}
        elif t == "spreads-european":
            try: line = int(round(float(m["hcap"])))
            except Exception: continue
            d3 = {nm: pv for nm, pv in seq}
            if all(d3.get(k) is not None for k in ("1", "X", "2")): eh[line] = [d3["1"], d3["X"], d3["2"]]
    ou = ou_multi = None
    if tot:
        ou_multi = sorted(tot.values(), key=lambda z: abs(z["line"]-2.5))
        ou = ou_multi[0]
    return {"spf": spf, "ou": ou, "ou_multi": ou_multi, "eh": eh or None}
def op_collect_odds(fixture_ids, meta):
    """阶段B：批量拉取指定fixture的主盘(pinnacle+betfair-ex),解析进 OP_ODDS。分块控请求数。"""
    ids = [x for x in dict.fromkeys(fixture_ids) if x and x not in OP_ODDS]
    n_req = 0
    for i in range(0, len(ids), ODDSPAPI_BATCH):
        chunk = ids[i:i+ODDSPAPI_BATCH]
        try:
            arr = _op_get("/fixtures/odds/main", {"fixtureIds": ",".join(chunk),
                                                  "bookmakers": ",".join(dict.fromkeys(ODDSPAPI_BOOKS+ODDSPAPI_EURO_BOOKS))})
            n_req += 1
        except Exception as e:
            return n_req, f"OddsPapi批量赔率异常(跳过本块):{e}"
        for f in arr:
            fid = f.get("fixtureId"); books = f.get("odds") or {}
            OP_ODDS[fid] = {bk: _op_parse_book(rows, meta) for bk, rows in books.items()}
    return n_req, f"OddsPapi批量主盘: {len(ids)} 场/{n_req} 请求(Pinnacle互验+Betfair交易所)"
def _op_xdiff(a3, b3):
    """两路三项赔率最大相对差(任一项缺失返回None)。"""
    if not a3 or not b3 or len(a3) < 3 or len(b3) < 3: return None
    if any(x is None for x in a3[:3]+b3[:3]): return None
    return max(abs(a3[k]-b3[k])/b3[k] for k in range(3))
def _pstdev(xs):
    n=len(xs)
    if n<2: return 0.0
    mu=sum(xs)/n; return (sum((x-mu)**2 for x in xs)/n)**0.5
def op_euro_from_book(op_book):
    """v5.7.6 把OddsPortal多家【软盘】书商1X2聚合成百家欧均：
    返回(euro_avg[主,平,客]算术均赔, euro_disp各家去水概率三项平均标准差, 命中家数, 书商名)。
    只统计三项齐全且赔率落在1.02-40合理区间的软盘书商；锐线(pinnacle/betfair-ex)不混入,避免与sharp同源;
    不足 ODDSPAPI_EURO_MIN_BOOKS 家返回(None,..)——宁可不填也不用单家冒充百家(不编造)。"""
    rows=[]
    for bk in ODDSPAPI_EURO_BOOKS:
        b=(op_book or {}).get(bk)
        if not isinstance(b,dict): continue
        s=b.get("spf")
        if s and len(s)>=3 and all(isinstance(x,(int,float)) and 1.02<x<40 for x in s[:3]):
            rows.append((bk,[float(x) for x in s[:3]]))
    names=[bk for bk,_ in rows]
    if len(rows)<ODDSPAPI_EURO_MIN_BOOKS: return None,0.0,len(rows),names
    avg=[round(sum(s[k] for _,s in rows)/len(rows),3) for k in range(3)]
    probs=[]
    for _,s in rows:
        inv=[1.0/x for x in s]; tot=sum(inv); probs.append([z/tot for z in inv])
    disp=round(sum(_pstdev([p[k] for p in probs]) for k in range(3))/3,4)  # 主/平/客跨家标准差均值
    return avg,disp,len(rows),names

# ==================== v5.7.3 第三层：Bet365 Inplay 软盘参考（只做共识/偏离度+主客交叉校验，绝不进sharp主锚）====================
# 实测语义(2026-09-08)：/bet365/get_prematch_sport_events/soccer 取赛前列表(team1=主/team2=客,startTime=epoch UTC,
#   isCyber=虚拟赛标记,列表跨度长达数月→必须按48h窗口过滤)；单场 /bet365/get_prematch_event_with_markets/{eventId}
#   返回扁平市场行{group,hd,na,designation,coef(=十进制)}：
#   · Full Time Result: na='1'/'Draw'/'2' = 主/平/客；
#   · Handicap Result/Alternative Handicap Result = 三维让球(主队视角,'1'行hd=带符号让球线,'Tie'=让平,'2'=让负,
#     实测主胜1.909热门场 主-1=3.4/让平4.333/客+1=1.8 方向自洽,与PinBook/竞彩同号)；
#   · Goals Over/Under: na=大小球线,designation=Over/Under。
B365_CAND = {}     # (规范主,规范客) -> [候选事件]
B365_ODDS = {}     # eventId -> {spf,eh,ou}
def _b365_get(path):
    url = f"https://{B365_HOST}{path}"
    return json.loads(_http_get(url, extra={"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": B365_HOST}, timeout=30))
def b365_collect_events(now_ts=None, window_h=B365_WINDOW_H):
    """阶段A：赛前事件列表→候选注册表(48h窗口、剔虚拟赛/U系/女足/预备队)。"""
    B365_CAND.clear()
    if not RAPIDAPI_KEY or not B365_ENABLED: return 0, "跳过Bet365软盘通道：未启用/无key"
    import time as _time
    now_ts = now_ts or int(_time.time())
    try:
        evs = _b365_get("/bet365/get_prematch_sport_events/soccer")
    except Exception as e:
        return 0, f"Bet365赛前列表异常(安全跳过):{e}"
    n_skip = 0
    for e in evs:
        try: st = int(e.get("startTime") or 0)
        except Exception: st = 0
        if not (now_ts < st < now_ts + window_h*3600): continue   # 48h窗口(列表跨度长达数月)
        lg = e.get("liga", "")
        if e.get("isCyber") or _op_is_noise(lg): n_skip += 1; continue
        H, A = _en_norm(e.get("team1")), _en_norm(e.get("team2"))
        if not H or not A: continue
        B365_CAND.setdefault((H, A), []).append(
            {"eventId": str(e.get("eventId")), "league": lg, "starts_ts": st, "noise": False,
             "home": e.get("team1"), "away": e.get("team2")})
    return len(B365_CAND), f"Bet365软盘: 48h内{len(B365_CAND)}对候选(剔虚拟/青年{n_skip})"
def _b365_parse(d):
    """单场全市场行 → {spf:[主,平,客],eh:{整数线:[让胜,让平,让负]},ou:{line,over,under}}。"""
    spf = [None, None, None]; eh = {}; ou = None
    # 让球：按|线|聚合 '1'(其hd=主队视角带符号线)/'Tie'/'2'
    ehraw = {}
    for m in d.get("markets", []):
        g, desig, coef = m.get("group"), m.get("designation"), _f(m.get("coef"))
        if coef is None: continue
        if g == "Full Time Result":
            na = m.get("na")
            if na == "1": spf[0] = coef
            elif na == "Draw": spf[1] = coef
            elif na == "2": spf[2] = coef
        elif g in ("Handicap Result", "Alternative Handicap Result") and desig in ("1", "Tie", "2"):
            try: sline = int(round(float(m.get("hd"))))
            except Exception: continue
            mag = abs(sline)
            cell = ehraw.setdefault(mag, {})
            if desig == "1": cell["line"] = sline; cell["h"] = coef
            elif desig == "Tie": cell["d"] = coef
            else: cell["a"] = coef
        elif g == "Goals Over/Under" and desig in ("Over", "Under"):
            try: ln = float(m.get("na"))
            except Exception: continue
            ou = ou or {}; ou.setdefault("lines", {})
            ou["lines"].setdefault(ln, {})["over" if desig == "Over" else "under"] = coef
    for mag, c in ehraw.items():
        if all(c.get(k) is not None for k in ("line", "h", "d", "a")):
            eh[c["line"]] = [c["h"], c["d"], c["a"]]
    if ou and ou.get("lines"):
        feas = [(abs(ln-2.5), ln, v) for ln, v in ou["lines"].items()
                if v.get("over") is not None and v.get("under") is not None]
        if feas:
            _, ln, v = min(feas, key=lambda z: z[0]); ou = {"line": ln, "over": v["over"], "under": v["under"]}
        else: ou = None
    if all(x is None for x in spf): spf = None
    return {"spf": spf, "eh": eh or None, "ou": ou}
def b365_resolve(r):
    """竞彩场→Bet365事件：队名双阈值匹配+开赛时间消歧(无pinnacleId,故比OddsPapi多一层保守)。"""
    bk, bs, bh, ba = None, -1.0, 0.0, 0.0
    ehs, eas = _cn_en_aliases(r["home"]), _cn_en_aliases(r["away"])
    for k in B365_CAND:
        sh = max((_team_match_score(eh, k[0]) for eh in ehs), default=0.0)
        sa = max((_team_match_score(ea, k[1]) for ea in eas), default=0.0)
        if sh+sa > bs: bs, bk, bh, ba = sh+sa, k, sh, sa
    if bk is None or min(bh, ba) < 0.6 or bs < 2.2: return None
    fx, _ = _op_time_pick(B365_CAND[bk], r)
    return fx
def b365_collect_marks(event_ids):
    """阶段B：逐场拉全市场并解析(请求数=场数,受B365_MAX_EVENTS上限保护)。"""
    ids = [x for x in dict.fromkeys(event_ids) if x and x not in B365_ODDS][:B365_MAX_EVENTS]
    n = 0
    import time as _time
    for eid in ids:
        d = None
        for _try in range(2):   # 限流/瞬时抖动重试1次,仍失败则记空(不拖垮整轮)
            try:
                d = _b365_get(f"/bet365/get_prematch_event_with_markets/{eid}"); n += 1; break
            except Exception:
                if _try == 0: _time.sleep(1.2); continue
        B365_ODDS[eid] = _b365_parse(d) if d else {"spf": None, "eh": None, "ou": None}
    return n

def collect_sina_eurasia():
    """通道9(免费/无key)：解析当日新浪《竞彩欧亚对照》文章，取每场前三个十进制赔率=欧洲平均(1X2)，标 src=9。"""
    if not SINA_EURASIA_URL: return {}, "跳过新浪欧均(src9)：未配置 SINA_EURASIA_URL(把当日'竞彩欧亚对照'文章链接填进来即可批量取1X2)"
    try: html=_http_get(SINA_EURASIA_URL)
    except Exception as e: return {}, f"新浪欧亚对照抓取失败(跳过):{e}"
    html=re.sub(r"<[^>]+>"," ",html); out={}
    for mt in re.finditer(r'周[一二三四五六日天]\s*0*(\d{3})', html):
        seg=html[mt.start():mt.start()+400]
        nums=[float(x) for x in re.findall(r'\d+\.\d{1,2}', seg)]
        tri=nums[:3]
        if len(tri)==3 and all(1.01<=x<=60 for x in tri):
            out[mt.group(1)]={"spf":tri,"src":9,"kind":"close","time":"早盘","name":"新浪欧亚对照-欧洲平均"}
    return out, (f"新浪欧均(src9): 解析到 {len(out)} 场" if out else "新浪欧均: 未解析到赔率(检查URL/版式)")

def _parse_manual():
    t=(MANUAL_SHARP or "").strip()
    if not t: return {}
    m=re.search(r'```(?:json)?\s*(.*?)```',t,re.S); raw=m.group(1) if m else t
    br=re.search(r'\{.*\}',raw,re.S)
    if not br: return {}
    d=json.loads(br.group(0)); return {k:v for k,v in d.items() if v}

_MATCH_LOG = []   # v5.3.2 记录中→英队名匹配对照与分数,assemble末尾打印供人工确认(防张冠李戴)
def _cn_en_aliases(cn):
    """v5.7.2：一个中文队名可对应多个Pinnacle英文名(str或list/tuple均可),全部规范化返回。
    v5.8.1：精确键未中时,对词典【中文键】做兜底——双向包含(取最长键,如'斯拉维亚布拉格'→'斯拉维亚')
    或中文串高相似(SequenceMatcher≥0.82)，让译名变体/带城市后缀也能找到英文别名；
    保守阈值+最终仍受 _match_en 主客双≥0.6/总分≥2.2 把关，不会张冠李戴。"""
    if not cn: return []
    v=TEAM_ALIAS_CN2EN.get(cn,"")
    if not v:
        q=str(cn); contain=[k for k in TEAM_ALIAS_CN2EN if len(k)>=2 and (k in q or q in k)]
        if contain:
            v=TEAM_ALIAS_CN2EN[sorted(contain,key=len,reverse=True)[0]]   # 多个包含取最长键=最具体
        else:
            bk,br=None,-1.0
            for k in TEAM_ALIAS_CN2EN:
                r=_difflib.SequenceMatcher(None,q,k).ratio()
                if r>br: br,bk=r,k
            if bk is not None and br>=0.82: v=TEAM_ALIAS_CN2EN[bk]
    if isinstance(v,(list,tuple)): return [_en_norm(x) for x in v if x]
    return [_en_norm(v)] if v else []
def _cn_en_first(cn):
    """v5.7.2：取中文队名对应的首个英文别名(展示/线移动报告等只需一个名字的场景)。"""
    al=_cn_en_aliases(cn)
    return al[0] if al else _en_norm(cn)
def _team_match_score(q, tt):
    if not q: return 0.0
    if q == tt: return 2.0
    if q in tt or tt in q: return 1.0
    return _difflib.SequenceMatcher(None, q, tt).ratio()
# ==================== v5.7.8 SportScore(sportscore1, Tipsters同账号) 赛前结构化补强：在线H2H/伤停首发/积分 ====================
# 同一把RAPIDAPI_KEY;host=sportscore1.p.rapidapi.com。能力:/events/{id}/lineups(含missing_players伤停+is_confirmed官宣)、
# /teams/{h}/h2h-events/{a}(在线交锋,补自积累冷启动)、/seasons/{id}/standings-tables(排名积分,战意量化证据)。
# 原则:只补不覆盖(AI研究>SS在线>本地自积累)、取不到留null不编造、单端点失败只跳过不崩、请求数有上限保护省免费额度。
SS_ENABLED=True
SS_HOST="sportscore1.p.rapidapi.com"
SS_BASE="https://sportscore1.p.rapidapi.com"   # 实测根路径即API根(官方文档示例的/api/v1前缀在本账号404)
SS_SPORT=1
SS_MAX_CALLS=70
SS_LINEUP=True; SS_H2H=True; SS_STAND=True
_SS_CALLS=0; _SS_STAND_CACHE={}; _SS_DIAG={"lu_keys":None,"h2h_keys":None}
def ss_get(path, params=None, timeout=25):
    global _SS_CALLS
    if not RAPIDAPI_KEY or not SS_ENABLED: return None,"disabled"
    if _SS_CALLS>=SS_MAX_CALLS: return None,"call_cap"
    url=f"{SS_BASE}{path}"
    if params: url+="?"+_uparse.urlencode(params)
    _SS_CALLS+=1
    try:
        return json.loads(_http_get(url, extra={"X-RapidAPI-Key":RAPIDAPI_KEY,"X-RapidAPI-Host":SS_HOST}, timeout=timeout)), None
    except Exception as e:
        return None, f"{type(e).__name__}:{getattr(e,'code',None) or str(e)[:60]}"
def _ss_team_name(t):
    if not isinstance(t,dict): return ""
    return _en_norm(t.get("name") or t.get("name_short") or "")
def _ss_event_ts(ev):
    td=ev.get("time_details") or {}
    for k in ("timestamp","start_timestamp","ts"):
        v=td.get(k) or ev.get(k)
        if v:
            try: return float(v)
            except Exception: pass
    for k in ("start_at","start_time","starts_at","date"):
        v=ev.get(k)
        if v:
            try:
                dtv=_dt.fromisoformat(str(v).replace("Z","+00:00"))
                if dtv.tzinfo is None: dtv=dtv.replace(tzinfo=_tz.utc)  # SS的start_at是UTC墙钟字符串,naive必须显式按UTC(旧版按容器本地时区解析会随部署环境漂移)
                return dtv.timestamp()
            except Exception: pass
    return None
def ss_day_events(dates, logs=None, max_pages=6):
    out=[]; first_err=None
    for d in dates:
        for page in range(1,max_pages+1):
            j,err=ss_get(f"/sports/{SS_SPORT}/events/date/{d}", {"page":page})
            if err:
                if page==1 and first_err is None: first_err=(d,err)
                break
            data=(j or {}).get("data")
            if not data: break
            out.extend(data)
            meta=(j or {}).get("meta") or {}
            lp=meta.get("last_page") or meta.get("total_pages")
            try:
                if lp and page>=int(lp): break
            except Exception: break
    if not out and logs and first_err:
        logs.append(f"⚠SportScore当天赛事拉取失败({first_err[0]}:{first_err[1]})—查免费档是否含该端点/订阅是否生效")
    return out
def ss_pick_event(evs, h_en, a_en, ko_ts=None):
    best=None; bs=-1.0; bt=1e18
    for ev in evs:
        sh=_team_match_score(h_en,_ss_team_name(ev.get("home_team")))
        sa=_team_match_score(a_en,_ss_team_name(ev.get("away_team")))
        sc=sh+sa
        if sc<2.2 or min(sh,sa)<0.6: continue
        ts=_ss_event_ts(ev); tgap=(abs(ts-ko_ts)/3600.0 if (ko_ts and ts) else 0.0)
        if sc>bs or (abs(sc-bs)<1e-9 and tgap<bt): best,bs,bt=ev,sc,tgap
    return best
def _ss_num(x):
    if isinstance(x,dict):
        for k in ("ft","regular","current"):
            if x.get(k) is not None: return _ss_num(x[k])
        return None
    try: return int(x)
    except Exception: return None
def ss_h2h_unbeaten(h2h_data, hid, lookback=10, min_n=3):
    games=[]
    for ev in (h2h_data or []):
        if str(ev.get("status"))!="finished": continue
        h=ev.get("home_team") or {}; a=ev.get("away_team") or {}
        hg,ag=_ss_num(ev.get("home_score")),_ss_num(ev.get("away_score"))
        if hg is None or ag is None: continue
        if h.get("id")==hid: gh,ga=hg,ag
        elif a.get("id")==hid: gh,ga=ag,hg
        else: continue
        games.append((gh,ga))
    games=games[-lookback:]
    if len(games)<min_n: return None
    w=sum(1 for gh,ga in games if gh>ga); d=sum(1 for gh,ga in games if gh==ga); l=len(games)-w-d
    return round((w+d)/len(games),3), dict(w=w,d=d,l=l,n=len(games))
def _ss_parse_lineup(data, hid, aid, diag=False):
    out={"home":{},"away":{}}
    items=data if isinstance(data,list) else ([data] if isinstance(data,dict) else [])
    for L in items:
        if not isinstance(L,dict): continue
        tid=(L.get("team_id") or (L.get("team") or {}).get("id"))
        side="home" if tid==hid else ("away" if tid==aid else None)
        miss=[(p.get("name") if isinstance(p,dict) else str(p)) for p in (L.get("missing_players") or [])]
        blk=dict(confirmed=bool(L.get("is_confirmed")), formation=L.get("formation"),
                 missing=[x for x in miss if x], n_start=len(L.get("lineup_players") or []))
        if side: out[side]=blk
        if diag: _SS_DIAG["lu_keys"]=sorted(L.keys())
    return out
def ss_enrich(byno, resolve_map, logs):
    if not SS_ENABLED or not RAPIDAPI_KEY: return
    now=_dt.now(_tz.utc); dates=[(now+_td(days=k)).strftime("%Y-%m-%d") for k in (0,1)]
    evs=ss_day_events(dates, logs)
    n_match=n_lu=n_h2h=n_st=0; previews=[]
    for no,r in sorted(byno.items()):
        try:
            rv=resolve_map.get(no) or {}; pbk=rv.get("pbk")
            if not pbk: continue
            # kickoff_dt是naive北京墙钟,贴UTC+8转epoch即正确UTC秒(与_ss_event_ts的UTC口径一致;旧版多减8h,靠两端错误抵消才未错配)
            ko=kickoff_dt(r); ko_ts=ko.replace(tzinfo=_tz(_td(hours=8))).timestamp() if ko else None
            ev=ss_pick_event(evs,_en_norm(pbk[0]),_en_norm(pbk[1]),ko_ts)
            if not ev: continue
            n_match+=1
            hid=(ev.get("home_team") or {}).get("id"); aid=(ev.get("away_team") or {}).get("id")
            sid=(ev.get("season") or {}).get("id"); eid=ev.get("id")
            rec=dict(eid=eid,hid=hid,aid=aid,sid=sid,ss_name=ev.get("name"),status=ev.get("status"))
            if SS_LINEUP and eid:
                lu,err=ss_get(f"/events/{eid}/lineups")
                if not err and lu is not None:
                    raw=lu.get("data") if isinstance(lu,dict) else lu
                    if raw:
                        rec["lineup"]=_ss_parse_lineup(raw,hid,aid,diag=(_SS_DIAG["lu_keys"] is None)); n_lu+=1
            if SS_H2H and hid and aid:
                j,err=ss_get(f"/teams/{hid}/h2h-events/{aid}", {"page":1})
                if not err and j is not None:
                    raw=j.get("data") if isinstance(j,dict) else j
                    if raw:
                        if _SS_DIAG["h2h_keys"] is None and isinstance(raw[0],dict): _SS_DIAG["h2h_keys"]=sorted(raw[0].keys())
                        u=ss_h2h_unbeaten(raw,hid)   # 只保留计算结果,不挂原始大对象(避免每场冗余存储)
                        if u: rec["h2h"]=u; n_h2h+=1
            if SS_STAND and sid:
                if sid not in _SS_STAND_CACHE:
                    j,err=ss_get(f"/seasons/{sid}/standings-tables"); rows=[]
                    if not err and j is not None:
                        for tb in (j.get("data") or []):
                            for row in (tb.get("standings_rows") or []):
                                t=row.get("team") or {}; f=row.get("fields") or {}
                                rows.append(dict(tid=t.get("id"),pos=row.get("position"),
                                                 pts=f.get("points_total", row.get("points")),
                                                 w=f.get("wins_total"),d=f.get("draws_total"),l=f.get("losses_total"),fields=f))
                    _SS_STAND_CACHE[sid]=rows
                rows=_SS_STAND_CACHE.get(sid) or []
                if rows:
                    fh=next((x for x in rows if x["tid"]==hid),None); fa=next((x for x in rows if x["tid"]==aid),None)
                    if fh or fa: rec["stand"]={"home":fh,"away":fa}; n_st+=1
            pv=[]
            if rec.get("h2h"):
                _,dd=rec["h2h"]; pv.append(f"近{dd['n']}次交锋{dd['w']}胜{dd['d']}平{dd['l']}负(不败率{rec['h2h'][0]:.0%})")
            _lh=(rec.get("lineup") or {}).get("home",{}); _la=(rec.get("lineup") or {}).get("away",{})
            if _lh or _la:
                _cf="官宣" if (_lh.get("confirmed") or _la.get("confirmed")) else "预测"
                pv.append(f"{_cf}阵型主{_lh.get('formation') or '?'}/客{_la.get('formation') or '?'}")
            _sh,_sa=(rec.get("stand") or {}).get("home"),(rec.get("stand") or {}).get("away")
            # 仅当双方都有正积分(赛季已进行)才展示排名;杯赛刚开赛points_total=0时排名无意义,不展示防误导
            if _sh and _sa and _sh.get("pos") and _sa.get("pos") and (_sh.get("pts") or 0)>0 and (_sa.get("pts") or 0)>0:
                pv.append(f"排名主{_sh['pos']}({_sh.get('pts')}分)/客{_sa['pos']}({_sa.get('pts')}分)")
            r["_ss"]=rec
            if pv: previews.append(f"  ·SS {no} {r.get('home')}vs{r.get('away')}: "+"；".join(pv))
        except Exception as _e:
            logs.append(f"⚠SportScore {no}补强异常(跳过该场SS):{type(_e).__name__} {str(_e)[:50]}")
    logs.append(f"SportScore补强: 当天赛事{len(evs)}场、对齐{n_match}场 | 阵容{n_lu} 在线H2H{n_h2h} 积分{n_st} (共调用{_SS_CALLS}次)")
    for _pv in previews: logs.append(_pv)
    if _SS_DIAG["lu_keys"]: logs.append(f"  SS阵容字段:{_SS_DIAG['lu_keys']}")
    if _SS_DIAG["h2h_keys"]: logs.append(f"  SS交锋字段:{_SS_DIAG['h2h_keys']}")
def attach_ss(m):
    if not SS_ENABLED: return
    ss=m.get("_ss")
    if not isinstance(ss,dict): return
    try:
        dims=m.setdefault("dims",{}); info=[]
        if dims.get("6_h2h") in (None,False) and ss.get("h2h"):
            ub,detail=ss["h2h"]; dims["6_h2h"]=ub; m["_h2h_online"]=detail
            info.append(f"近{detail['n']}次交锋主{detail['w']}胜{detail['d']}平{detail['l']}负(不败{ub:.0%})")
        lu=ss.get("lineup")
        if lu:
            m["_ss_lineup"]=lu; h,a=lu.get("home") or {},lu.get("away") or {}
            if h or a:
                cf="官宣" if (h.get("confirmed") or a.get("confirmed")) else "预测"
                miss=len(h.get("missing",[]))+len(a.get("missing",[]))
                info.append(f"阵容[{cf}]主{h.get('formation') or '?'}/客{a.get('formation') or '?'}"+(f",缺阵名单{miss}人" if miss else ""))
        st=ss.get("stand")
        if st:
            m["_ss_stand"]=st; h,a=st.get("home"),st.get("away")
            if h and a and h.get("pos") and a.get("pos") and (h.get("pts") or 0)>0 and (a.get("pts") or 0)>0:
                info.append(f"积分主第{h.get('pos')}({h.get('pts')}分)/客第{a.get('pos')}({a.get('pts')}分)")
        if info: m["ss_info"]="；".join(info)
    except Exception: pass
def _match_en(rec, mapping):
    """中→英对照+模糊匹配。v5.3.2加严：主客两队都要命中(各≥0.6)且总分≥2.2才接受，
    杜绝旧版'只匹配上一队(2.0>1.4)即接受'导致的张冠李戴；匹配明细入_MATCH_LOG供人工核对。
    v5.7.2：中文队名支持多英文别名(取最高分)；只在【成年正赛候选】间选择,青年/女足不参与键匹配。"""
    if not mapping: return None, None
    _h,_a=rec.get("home"),rec.get("away")
    if not _h or not _a: return None,None   # v5.7.6健壮:骨架缺队名无法对齐,安全跳过(旧版rec["home"]直接KeyError崩全场)
    ehs=_cn_en_aliases(_h); eas=_cn_en_aliases(_a)
    bk, bs, bh, ba = None, -1.0, 0.0, 0.0
    for k, v in mapping.items():
        H, A = k[0], k[1]
        sh=max((_team_match_score(eh,H) for eh in ehs), default=0.0)
        sa=max((_team_match_score(ea,A) for ea in eas), default=0.0)
        s = sh + sa
        if s > bs: bs, bk, bh, ba = s, k, sh, sa
    ok = bk is not None and min(bh, ba) >= 0.6 and bs >= 2.2
    _MATCH_LOG.append((rec.get("no"), rec.get("home"), rec.get("away"),
                       (bk if bk else ("", "")), round(bh, 2), round(ba, 2), round(bs, 2), ok))
    if not ok: return None, None
    return bk, mapping[bk]

def _pick(cands, key):
    vals=[(c["src"],c.get(key),c.get("time"),c.get("name")) for c in cands if c.get(key)]
    if not vals: return None,None
    vals.sort(key=lambda z:_SHARP_ORDER.get(z[0],9))
    src,val,tm,nm=vals[0]; return {"val":val,"src":src,"time":tm,"name":nm},None

def clv_audit(ms):
    """逐场打印 1X2/让球 三方向 CLV（锐线去水公平价 vs 竞彩SP），并统计达到+3%的方向，验证价格优势是否存在。"""
    line(); print("§A+ CLV 审计（锐线自动去水→三方向CLV；≥+3%才有价格优势；让球无3维锐线则标缺）"); line()
    wpass=hpass=0; wtot=htot=0; have_rsp=0
    for r in sorted(ms,key=lambda x:x["no"]):
        sh=r.get("sharp"); tag="无锐线"
        wtxt=htxt="—"
        if sh:
            src=sh.get("src",9)
            def _ok3(x): return bool(x) and len(x)>=3 and all(v is not None for v in x[:3])
            if _ok3(sh.get("spf")) and _ok3(r.get("spf")):
                fair=sharp_fair(sh["spf"],src); cs=[]
                for k in range(3):
                    c=clv_one(r["spf"][k],fair[k]) if r["spf"][k] is not None else None; wtot+=1
                    if c is not None:
                        cs.append(f"{c*100:+.1f}%"); wpass+= (1 if c>=CLV_MIN else 0)
                    else: cs.append("—")
                wtxt=f"主{cs[0]}/平{cs[1]}/客{cs[2]}"
            if _ok3(sh.get("rsp")) and _ok3(r.get("rsp")):
                have_rsp+=1; fair=sharp_fair(sh["rsp"],src); cs=[]
                for k in range(3):
                    c=clv_one(r["rsp"][k],fair[k]) if r["rsp"][k] is not None else None; htot+=1
                    if c is not None:
                        cs.append(f"{c*100:+.1f}%"); hpass+=(1 if c>=CLV_MIN else 0)
                    else: cs.append("—")
                htxt=f"让胜{cs[0]}/让平{cs[1]}/让负{cs[2]}"
            else: htxt="缺3维让球锐线"
            tag=f"src{src}/{sh.get('name','')}"
        print(f"  {r['no']} {str(r['home'])[:5]:<5}v{str(r['away'])[:5]:<5} 让{str(r.get('hand')):>3} [{tag}] 1X2CLV:{wtxt}  让球CLV:{htxt}")
    print(f"  ── 1X2 {wpass}/{wtot} 个方向CLV≥+3%；让球 {hpass}/{htot} 达标，已拿到3维让球锐线 {have_rsp}/{len(ms)} 场"
          f"（让球锐线越全，让球腿越可能过H2/H9实盘闸门）")

def eh_watchlist(ms):
    """对仍缺3维让球锐线的场次，输出【免费补抓清单】：豆包照此用联网/浏览器工具读取后把数字填进 MANUAL_SHARP。"""
    miss=[r for r in ms if not (r.get("sharp") and r["sharp"].get("rsp"))]
    if not miss:
        print("§A+ 让球锐线已全部自动获取，无需手动补抓。"); return
    line(); print(f"§A+ 让球(3维)锐线补抓清单：{len(miss)} 场尚缺 sharp.rsp。配了免费 PinBook key 时这里应为空(全自动)；"
                  "未配key才需手动——找【3-Way/European Handicap/让球胜平负】且让球线=该场hand的三项，读到后填 MANUAL_SHARP："); line()
    for r in miss:
        en_h=_cn_en_first(r["home"]); en_a=_cn_en_first(r["away"])
        print(f"  {r['no']} {r['home']}vs{r['away']} (hand={r.get('hand')}): "
              f"OddsPortal/Betexplorer 搜 '{en_h} vs {en_a}' 的 EH/让球胜平负 标签 → "
              f'MANUAL_SHARP["{r["no"]}"]={{"src":1或9,"rsp":[让胜,让平,让负],"kind":"live","time":"HH:MM"}}')

def export_team_alias_todo(batch=None, verbose=True):
    """v5.8.1：把本轮'中文→英文锐线'最终仍未匹配(精确+模糊兜底都查无)的中文队名去重，
    导出 DATA_DIR/team_alias_todo_<batch>.json，形成『未命中→补 TEAM_ALIAS_CN2EN→下次自动命中』闭环。
    返回 [{'cn','nos'}]。已能模糊命中的不计入(无需补)。"""
    miss={}
    for row in _MATCH_LOG:
        try:
            no,h,a,_k,_sh,_sa,_ss,ok=row
        except Exception:
            continue
        if ok: continue
        for cn in (h,a):
            if not cn or _cn_en_aliases(cn): continue   # 模糊兜底已能命中→不必补
            e=miss.setdefault(str(cn),{"cn":str(cn),"nos":[]})
            if str(no) not in e["nos"]: e["nos"].append(str(no))
    for e in miss.values(): e["nos"].sort()
    out=sorted(miss.values(),key=lambda z:z["cn"])
    b=re.sub(r'[^0-9A-Za-z_-]',"",str(batch or globals().get("MATCH_DATE") or "auto")) or "batch"
    fp=_data_path("team_alias_todo_%s.json"%b)
    try:
        with open(fp,"w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    except Exception: fp=None
    if verbose and out:
        line(); print(f"§v5.8.1 队名词典待补：{len(out)} 个中文队名本轮没能对上英文锐线（已导出 {fp}）。")
        print("  把查到的 Pinnacle 标准英文名补进 TEAM_ALIAS_CN2EN（或直接发我代补）后，下次即自动命中、无需手动抄锐线：")
        for x in out:
            print(f"    · {x['cn']}（出现于场次 {'/'.join(x['nos'])}）")
        line()
    return out

def assemble_matches(date, ai_records, want_nos=None):
    """汇总：官方SP为骨架 → 合并AI研究的定性字段(avg/stat/dims/伤停/战意) → 多通道锐线回填 → 输出MATCHES。
    v5.5.1：date='auto'默认锁定'最近开球日'主批次(21点买次日凌晨那批,用matchDate真实开球日判未开赛)；
    若want_nos指定了主批次之外的后批编号,再从未来48h全量池补齐其官方骨架,保证指定编号不被批次裁剪漏掉。"""
    _auto = (date == "auto")
    date = _bj_today() if _auto else date
    logs=[]; _MATCH_LOG.clear()
    try:
        base=collect_sporttery("upcoming" if _auto else date)
        if _auto and want_nos:   # 指定编号可能落在后一批：用全48h池补齐主批次缺失的目标场
            have={r["no"] for r in base}; _want=set(str(x).zfill(3) for x in want_nos)
            extra=[r for r in collect_sporttery("upcoming", main_batch_only=False)
                   if r["no"] in _want and r["no"] not in have]
            if extra: base=base+extra
        logs.append(f"竞彩官方接口: {len(base)} 场未开赛场(主批次"
                    + ("，含指定后批补齐" if (_auto and want_nos) else "") + "；四玩法SP/让球线)")
    except Exception as e:
        base=[]; logs.append(f"⚠竞彩官方接口失败({e})，改用AI_JSON骨架")
    # v5.7.6健壮:剔除官方返回里缺编号/队名的不完整记录(临开赛移除/接口抖动会产生残记录,旧版下游r["home"]硬取崩全场)
    _bad=[r.get("no","?") for r in base if not r.get("no") or not r.get("home") or not r.get("away")]
    if _bad: logs.append(f"⚠剔除缺编号/队名的不完整场次:{_bad}(官方接口临开赛抖动,安全跳过)")
    base=[r for r in base if r.get("no") and r.get("home") and r.get("away")]
    byno={r["no"]:r for r in base}
    QUAL=("lg","time","businessDate","matchTime","home","away","avg","stat","dims","motiv_h","motiv_a","inj_h","inj_a","season_stage",
          "round","promoted","weak_coeff","lh","la","cup","leg","group_state","twoleg","g5","bankroll_tier",
          "L","W","DD","idle_days","spf_open","rsp_open","odds_move","future","ou","res",
          # v5.4 百家欧赔均值[主,平,客](豆包浏览器读500/澳客)与其离散度，作为低抽水全球共识主锚
          "euro_avg","euro_disp",
          "review")  # v5.3.4修复：review随AI回填合并进官方骨架，否则混合联网模式语义核查丢失
    for a in (ai_records or []):
        no=str(a["no"]).zfill(3); r=byno.get(no)
        if r is None:
            if not a.get("home") or not a.get("away"):
                continue   # v5.7.6:纯review/stat补充包在官方骨架缺该场(已开赛被移除/未开售)时不建无队名空壳,防下游r["home"]KeyError
            r=dict(a)
            if isinstance(r.get("ssp"),dict): r["ssp"]={(int(k.split('-')[0]),int(k.split('-')[1])) if isinstance(k,str) else k:v for k,v in r["ssp"].items()}
            byno[no]=r; continue
        if a.get("sharp"): r["_ai_sharp"]=a["sharp"]
        for k in QUAL:
            if k in a and r.get(k) in (None,{},[],""): r[k]=a[k]
    for r in byno.values():
        r.setdefault("season_stage","normal"); r.setdefault("bankroll_tier","std")
        for k,v in (("L",0),("W",0),("DD",0.0),("idle_days",0),("res",None)): r.setdefault(k,v)
    pbso,pbeh,m_pb=collect_pinbook(); logs.append(m_pb)
    # v5.7.3 第二层 OddsPapi 阶段A：赛程候选注册 + 市场元数据(静态)
    op_meta={}
    if ODDSPAPI_ENABLED:
        try:
            _,_mopf=op_collect_fixtures(); logs.append(_mopf); op_meta=_op_markets_meta()
        except Exception as _ex:
            logs.append(f"OddsPapi初始化异常(安全跳过):{_ex}")
    # v5.7.3 第三层 Bet365 软盘阶段A：事件候选注册
    if B365_ENABLED:
        try:
            _,_mbf=b365_collect_events(); logs.append(_mbf)
        except Exception as _ex:
            logs.append(f"Bet365初始化异常(安全跳过):{_ex}")
    try:
        oa,m1=collect_oddsapi()
    except Exception as _ex:
        oa,m1={},f"TheOddsAPI通道异常(已安全跳过):{_ex}"
    logs.append(m1)
    sn,m3=collect_sina_eurasia(); logs.append(m3)
    manual=_parse_manual(); logs.append(f"MANUAL_SHARP手动兜底: {len(manual)} 场" if manual else "MANUAL_SHARP为空")
    # ===== v5.7.3 对齐第一遍：每场先确定 PinBook / OddsPapi / Bet365 / TheOddsAPI 各对应哪一个外部事件 =====
    resolve_map={}; op_ids=[]; b365_ids=[]
    for no,r in sorted(byno.items()):
        pbk,_= _match_en(r,pbso)     # PinBook：先定队名键(H,A)
        pbv,pbnote=(_pb_resolve(r,pbk) if pbk else (None,""))   # 同队名多赛事按开赛时间消歧
        if pbk and pbv is None: logs.append(f"⚠{no} {r.get('home')}vs{r.get('away')} PinBook赛事消歧弃用：{pbnote}")
        opfx,opnote,opmode=None,"","none"
        if ODDSPAPI_ENABLED:
            opfx,opnote,opmode=op_resolve(r,(pbv or {}).get("event_id"),OP_CAND)   # 优先pinnacleId精确对齐
            if opfx: op_ids.append(opfx["fixtureId"])
        bfx=b365_resolve(r) if B365_ENABLED else None
        if bfx: b365_ids.append(bfx["eventId"])
        _,eav=_match_en(r,oa)       # TheOddsAPI（可选,付费档才有足球Pinnacle）
        resolve_map[no]={"pbk":pbk,"pbv":pbv,"opfx":opfx,"opmode":opmode,"opnote":opnote,
                         "bfx":bfx,"eav":eav}
    # v5.7.3 阶段B：OddsPapi 一次批量拉全部目标场(请求数最少)；Bet365 逐场(受上限保护)
    if ODDSPAPI_ENABLED and op_ids:
        try:
            _,_mopo=op_collect_odds(op_ids,op_meta); logs.append(_mopo)
        except Exception as _ex:
            logs.append(f"OddsPapi批量赔率异常(安全跳过):{_ex}")
    if B365_ENABLED and b365_ids:
        try:
            _nb=b365_collect_marks(b365_ids); logs.append(f"Bet365软盘: 拉取{_nb}场全市场(仅共识/偏离参考,不进锐线主锚)")
        except Exception as _ex:
            logs.append(f"Bet365全市场异常(安全跳过):{_ex}")
    # v5.7.8 SportScore结构化补强(在线H2H/伤停首发/积分),resolve_map已含pbk英文键;全程容错不影响主流程
    try:
        ss_enrich(byno, resolve_map, logs)
    except Exception as _ex:
        logs.append(f"SportScore补强整体异常(安全跳过):{_ex}")
    ALIGN_AUDIT=[]   # v5.7.3 逐场三源对齐审计行
    for no,r in sorted(byno.items()):
        m=manual.get(no) or {}
        rv=resolve_map[no]; pbk,pbv=rv["pbk"],rv["pbv"]; opfx=rv["opfx"]; bfx=rv["bfx"]; eav=rv["eav"]
        op_book=OP_ODDS.get(opfx["fixtureId"],{}) if opfx else {}
        op_p=op_book.get("pinnacle"); op_x=op_book.get("betfair-ex")
        # —— 同源互验：PinBook 的 Pinnacle vs OddsPapi 的 Pinnacle（同一上游,分钟级应几乎相等;差异过大弃用OP,防错套）——
        op_p_ok=True; xdiff=None
        if pbv and pbv.get("spf") and op_p and op_p.get("spf"):
            xdiff=_op_xdiff(pbv["spf"],op_p["spf"])
            if xdiff is not None and xdiff>OP_XDIFF_DROP:
                op_p_ok=False
                logs.append(f"⚠{no} {r.get('home')}vs{r.get('away')} 两路Pinnacle 1X2最大相对差{xdiff*100:.1f}%"
                            f">{OP_XDIFF_DROP*100:.0f}%，OddsPapi该场弃用(以PinBook为准,防错套/主客颠倒)")
        cands=[]
        if m.get("spf"): cands.append({"src":m.get("src",9),"spf":m["spf"],"time":m.get("time"),"name":m.get("name","手动")})
        if pbv and pbv.get("spf"): cands.append({"src":1,"spf":pbv["spf"],"time":pbv.get("time"),"name":"Pinnacle","ou":pbv.get("ou"),"ou_multi":pbv.get("ou_multi")})
        # OddsPapi-Pinnacle 与主源同上游(src=1)：主源在时互为校验/备份,主源缺时无缝补位
        if op_p_ok and op_p and op_p.get("spf"):
            cands.append({"src":1,"spf":op_p["spf"],"time":"pre","name":"Pinnacle(OP)","ou":op_p.get("ou"),"ou_multi":op_p.get("ou_multi")})
        if op_x and op_x.get("spf"): cands.append({"src":2,"spf":op_x["spf"],"time":"pre","name":"Betfair交易所","ou":op_x.get("ou")})
        if eav and eav.get("spf"): cands.append({"src":eav["src"],"spf":eav["spf"],"time":eav.get("time"),"name":eav.get("name"),"ou":eav.get("ou")})
        if sn.get(no,{}).get("spf"):
            s=sn[no]; cands.append({"src":9,"spf":s["spf"],"time":s["time"],"name":s["name"]})
        if r.get("_ai_sharp",{}).get("spf"):
            a=r["_ai_sharp"]; cands.append({"src":a.get("src",9),"spf":a["spf"],"time":a.get("time"),"name":"AI研究","ou":a.get("ou")})
        spf,_=_pick(cands,"spf")
        # ou 优先级：手动 > PinBook > OddsPapi-Pinnacle > Betfair交易所 > TheOddsAPI > AI研究
        ou=m.get("ou")
        if ou is None and pbv: ou=pbv.get("ou")
        if ou is None and op_p_ok and op_p: ou=op_p.get("ou")
        if ou is None and op_x: ou=op_x.get("ou")
        if ou is None and eav: ou=eav.get("ou")
        if ou is None: ou=r.get("_ai_sharp",{}).get("ou")
        if ou is not None: r["ou"]=ou   # 修复：锐线/手动大小球回填顶层ou，供market_lambda锚定总λ
        # ou_multi 优先级：PinBook全档 > OddsPapi-Pinnacle全档
        ou_multi = pbv.get("ou_multi") if pbv else None
        if not ou_multi and op_p_ok and op_p: ou_multi=op_p.get("ou_multi")
        if ou_multi: r["ou_multi"]=ou_multi
        # 让球3维链(全部要求与竞彩hand同整数线、主队视角同号；绝不用2维亚盘合成)：
        # 手动 > PinBook-3WayH(同event_id) > OddsPapi-Pinnacle(spreads-european) > OddsPapi-Betfair交易所 > AI
        rsp3=rtime=rname=None
        if m.get("rsp"): rsp3,rtime,rname=m["rsp"],m.get("time"),m.get("name","手动")
        elif pbk is not None and pbv is not None and PB_EH_CAND.get(pbk) and r.get("hand") is not None:
            h=float(r["hand"]); pool=PB_EH_CAND[pbk].get(h)
            # v5.7.2：实测3WayH全部以【主队视角】命名(主让为负),与竞彩hand符号一致；只取 h 这条线,不做-h反线兜底
            tri=None
            if pool:
                eid=pbv.get("event_id"); same=[x for x in pool if x[1]==eid]
                tri=(same or pool)[0][0]   # 优先同event_id；极端缺id时取首个成年候选
            if tri: rsp3,rtime,rname=tri,pbv.get("time"),"Pinnacle-3WayH"
        if rsp3 is None and op_p_ok and op_p and op_p.get("eh") and r.get("hand") is not None:
            tri=op_p["eh"].get(int(round(float(r["hand"]))))
            if tri: rsp3,rtime,rname=tri,"pre","Pinnacle(OP)-EH"
        if rsp3 is None and op_x and op_x.get("eh") and r.get("hand") is not None:
            tri=op_x["eh"].get(int(round(float(r["hand"]))))
            if tri: rsp3,rtime,rname=tri,"pre","BetfairEx-EH"
        if rsp3 is None and r.get("_ai_sharp",{}).get("rsp"):
            a=r["_ai_sharp"]; rsp3,rtime,rname=a["rsp"],a.get("time"),"AI研究"
        if spf:
            nm=spf["name"]; extra=f'/{rname}' if (rname and rname not in str(nm)) else ""
            r["sharp"]={"src":spf["src"],"spf":spf["val"],"rsp":rsp3,"ou":ou,"ou_multi":ou_multi,"kind":"live",
                        "time":spf.get("time") or rtime,"name":f'{nm}{extra}'}
        else:
            r["sharp"]=None
        # ===== v5.7.3 第三层：Bet365 软盘参考(独立字段,不进sharp、不改概率) + 主客方向交叉校验 =====
        soft=B365_ODDS.get(bfx["eventId"]) if bfx else None
        if soft and soft.get("spf"):
            r["soft_b365"]=soft
            if r["sharp"] and r["sharp"].get("spf"):
                sh3=r["sharp"]["spf"]; sf3=soft["spf"]
                if all(x is not None for x in sh3[:3]+sf3[:3]):
                    fav_sh=0 if sh3[0]<=sh3[2] else 2     # 锐线热门方向(只比主/客,平局不参与)
                    fav_sf=0 if sf3[0]<=sf3[2] else 2
                    if fav_sh!=fav_sf:
                        logs.append(f"⚠{no} {r.get('home')}vs{r.get('away')} 主客方向交叉校验不一致："
                                    f"锐线热门={'主' if fav_sh==0 else '客'} vs Bet365热门={'主' if fav_sf==0 else '客'}，请人工核对主客/对齐")
        # ===== v5.7.6 OddsPortal 百家欧均/离散度（只补不覆盖AI手填；软盘共识,不进sharp锐线）=====
        try:
            if not r.get("euro_avg"):
                _ea,_ed,_en,_eks = op_euro_from_book(op_book)
                if _ea:
                    r["euro_avg"]=_ea
                    if not r.get("euro_disp"): r["euro_disp"]=_ed
                    r.setdefault("dims",{})["5_dispersion"]=_ed      # 辅助维:欧赔离散
                    logs.append(f"{no} 百家欧均:OddsPortal {_en}家{_eks} 均赔{_ea} 离散{_ed*100:.1f}%")
        except Exception as _ex:
            logs.append(f"{no} 百家欧均聚合异常(安全跳过):{_ex}")
        # ===== v5.7.3 三源对齐审计记录 =====
        pb_txt=(f"PB✓eid={pbv.get('event_id')}" if pbv else ("PB队名命中但消歧弃用" if pbk else "PB✗"))
        op_txt={"id":"OP✓ID精确","name":"OP✓队名+时间","none":"OP✗"}.get(rv["opmode"],rv["opmode"])
        if rv["opmode"]=="name": op_txt+="("+rv["opnote"]+")"
        bf_txt=("B365✓" if soft else ("B365(无报价)" if bfx else "B365✗"))
        ALIGN_AUDIT.append((no,r.get("home"),r.get("away"),r.get("hand"),pb_txt,op_txt,bf_txt,
                            "让球✓" if rsp3 else "让球缺", (f"同源差{xdiff*100:.1f}%" if xdiff is not None else "")))
        r.pop("_ai_sharp",None)
        _coerce_record(r)
    line(); print("§A+ 免费自动采集层运行日志："); [print("  ·",x) for x in logs]
    if _MATCH_LOG:   # v5.3.2/v5.7.2 中→英队名匹配对照(人工确认有无张冠李戴；✓采用 ×拒绝；采用场也打印英文键供逐场核对)
        acc=[x for x in _MATCH_LOG if x[7]]; rej=[x for x in _MATCH_LOG if not x[7]]
        print(f"  · 中→英队名匹配：采用{len(acc)}场/拒绝{len(rej)}场(主客任一匹配分<0.6或总分<2.2即拒，宁缺毋错)")
        for no,h,a,k,sh,sa,ss,ok in _MATCH_LOG:
            if ok:
                # v5.7.2：任一侧非精确命中(分数<1.0=模糊匹配)打⚠,提示人工重点核对近似队名/同对手不同赛事
                mark=" ⚠模糊匹配请核对" if min(sh,sa)<1.0 else ""
                print(f"      ✓ {no} {h}vs{a} → {k[0]} v {k[1]} (匹配分 主{sh}/客{sa}/总{ss}){mark}")
            elif (h or a):
                print(f"      × {no} {h}vs{a} →候选{k} 分{sh}/{sa}/{ss} 未达阈值,该场不套英文锐线")
    # v5.7.3 三源一一对齐审计表（竞彩场次 ↔ PinBook ↔ OddsPapi ↔ Bet365；让球线是否取到；同源价差）
    line(); print("§A+ v5.7.3 三源对齐审计（逐场可追溯，ID精确=零队名模糊风险）："); line()
    for no,h,a,hand,pb,op,bf,eh,xd in ALIGN_AUDIT:
        print(f"  {no} {str(h)[:6]:<6}v{str(a)[:6]:<6} 让{str(hand):>3} | {pb:<16}| {op:<20}| {bf:<10}| {eh} {xd}")
    ms=[byno[k] for k in sorted(byno)]
    clv_audit(ms); eh_watchlist(ms)
    export_team_alias_todo(batch=date)   # v5.8.1 未匹配中文队名自动导出待补清单(持续扩充词典、抬升自动锐线率)
    return ms

# [内嵌资料·运行时不打印] 免费锐线源完整手册供读码/复制；main实际输出的是 print_free_ladder_brief() 简版
FREE_SOURCE_LADDER = """
【§A+ 免费锐线源阶梯（v5.3.2按2026-09实测可达性更新；豆包联网照此最大化搜索，尤其让球3维）】
〇实测可达性（避免在打不开的源上浪费时间）：
  · 可达且能取到数字：竞彩官方webapi(程序自动)；新浪《竞彩欧亚对照》(每日一文,欧均1X2+亚盘,全场次批量)；
    足彩网zgzcw/澳客okooo/第一彩(百家欧赔均值)；Pinnacle加拿大镜像 www.pinnacle.ca(给美式赔率,需换算十进制)；
    dailysports.net(多家1X2+均值+赔率变动初盘+大小球+AH+xG/进失球统计)、tipsterarea.com、tipsomatic.com(含比分CS赔率)、footystats.org(大小球/BTTS/统计)。
  · 受限/打不开：pinnacle.com直连超时、betfair 403地区限制、500彩票网zx.500.com人机验证、OddsPortal/Betexplorer赔率靠JS动态渲染(首页只有壳,须逐场点EH标签且常取不到)。
1) 1X2胜平负+大小球：优先 Pinnacle(用.ca镜像；美式-138→十进制1+100/138=1.725，+301→1+301/100=4.01)；
   其次 dailysports/tipsterarea/tipsomatic 的均值与多家；国内等值(src9)用新浪欧亚对照的欧洲平均。至少2源交叉。
2) 让球胜平负(3维=让胜/让平/让负,本层重点)：找【3-Way/European Handicap】且让球线与竞彩hand完全一致(主让为负)的【三项】；
   Pinnacle.ca页内有 3-Way Handicap 各整数线(展开取与hand一致那档三项)；OddsPortal/Betexplorer的EH标签为备选。
   【禁止】用2维亚盘上下盘水自行换算3维(口径不同=编造)；取不到填null。
3) 大小球：Over/Under主盘线(最接近2.5)的over/under十进制水位；Pinnacle.ca的Total行、footystats/dailysports可取。
4) 统计λ原料：dailysports/footystats的联赛主客场场均进失球、近5场、xG、排名、H2H，按stat四基准给齐。
5) 程序化免费key(本文件已内置对接)：★RapidAPI「PinBook Odds」BASIC($0/月)一次拿Pinnacle的1X2+大小球+3维让球(配key即全自动)；
   TheOddsAPI仅付费档覆盖足球Pinnacle(可选)；无key时用新浪src9+上述免费网页+MANUAL_SHARP兜底。
6) v5.3.2零配置说明：即便大小球ou取不到，程序也能用竞彩总进球ttg8档SP自动反推总λt，因此1X2(或ttg)务必采全；
   但锐线1X2/3维让球仍需你采，用于CLV与实盘闸门。任何项取不到填null并记来源+时间，禁止插值；出票前60分钟同窗重算CLV。
"""
def print_free_ladder_brief():
    line(); print("§A+ v5.3.4 免费采集+质量校验+λ校正链+豆包AI语义核查(严格双确认)+全局EV主推荐+联合凯利（官方SP/总进球反推λ；PinBook锐线；AI核查首发/战意/默契球/利空/天气并卡实盘；联合配仓锁死≤逐注分数凯利）"); line()


# ===================== v5.2 新增①：采集质量自动校验（只告警、不改数、不编造）=====================
def _fnum(x):
    """字符串数值('1.90')→float；空/非法→None（断网用AI骨架时防止str流入概率引擎崩溃）。"""
    try:
        if x is None or x == "": return None
        return float(x)
    except (TypeError, ValueError):
        return None
def _ssp_key(k):
    """比分SP键统一为(i,j)元组；兼容 '1-2'/'1:2'/(1,2)/[1,2]。"""
    if isinstance(k, tuple): return (int(k[0]), int(k[1]))
    if isinstance(k, list): return (int(k[0]), int(k[1]))
    s = str(k).replace(":", "-").replace("：", "-")
    a, b = re.split(r"[-–]", s)[:2]
    return (int(a), int(b))
def _fix_len(lst, n):
    """列表数值化并定长到n：不足补None、多余截断；非list→None。"""
    if not isinstance(lst, list): return None
    out = [_fnum(x) for x in lst[:n]]
    out += [None] * (n - len(out))
    return out
def _coerce_record(r):
    """把一场记录里所有赔率/盘口字段统一强转为数值、定长、比分键归一（v5.3.2：修缺档崩溃/ssp字符串键；
    v5.3.3：锐线美式赔率(-138/+301)自动换算十进制，豆包从Pinnacle.ca抄回美式线也能直接用）。"""
    for k, n in (("spf", 3), ("rsp", 3), ("spf_open", 3), ("rsp_open", 3), ("tsp", 8), ("euro_avg", 3)):
        if k in r and r[k] is not None:
            r[k] = _fix_len(r[k], n)
    if r.get("euro_disp") is not None:   # v5.4 百家欧赔离散度统一转浮点(兼容'18%'字符串)
        try:
            r["euro_disp"] = float(r["euro_disp"])
        except (TypeError, ValueError):
            try:
                r["euro_disp"] = float(str(r["euro_disp"]).replace("%", "").strip())
            except (TypeError, ValueError):
                r["euro_disp"] = None
    if isinstance(r.get("ssp"), dict):
        r["ssp"] = {_ssp_key(k): _fnum(v) for k, v in r["ssp"].items() if _fnum(v) is not None}
    if isinstance(r.get("ou"), dict):
        for k in ("line", "over", "under"):
            if k in r["ou"]:
                val = _fnum(r["ou"][k])
                r["ou"][k] = amer_to_dec(val) if k in ("over", "under") else val
    sh = r.get("sharp")
    if isinstance(sh, dict):
        for k, n in (("spf", 3), ("rsp", 3)):
            if sh.get(k) is not None:
                sh[k] = _fix_len(sh[k], n)
                # v5.3.3 美式赔率自动换算（Pinnacle加拿大镜像给美式线）；无法换算的保留None
                sh[k] = [amer_to_dec(x) if x is not None else None for x in sh[k]]
        if isinstance(sh.get("ssp"), dict):
            sh["ssp"] = {_ssp_key(k): _fnum(v) for k, v in sh["ssp"].items() if _fnum(v) is not None}
        if isinstance(sh.get("ou"), dict):
            for k in ("line", "over", "under"):
                if k in sh["ou"]:
                    val = _fnum(sh["ou"][k])
                    sh["ou"][k] = amer_to_dec(val) if k in ("over", "under") else val
    return r
def _norm3(sp3):
    if not sp3 or len(sp3) < 3 or any(x is None for x in sp3[:3]): return None
    inv = [1 / x for x in sp3[:3]]; s = sum(inv); return [x / s for x in inv]
def _kl3(p,q):
    return sum(p[k]*log(p[k]/q[k]) for k in range(3) if p[k]>1e-9 and q[k]>1e-9)
def quality_audit(A):
    """四类自动一致性校验：1X2两源偏差 / 泊松反演KL残差 / 让球模型偏差 / 大小球模型偏差 + 八字段完整度。
    阈值：🟡关注、🔴异常；只提示人工回看(伤停/错线/采集错误)，绝不自动改数据。"""
    line(); print("§A+ 采集质量自动校验（多源偏差/KL反演残差/让球·大小球一致性；🟡关注 🔴异常，只告警不改数）"); line()
    ny=nr=0
    for a in sorted(A,key=lambda x:x["m"]["no"]):
        m=a["m"]; flags=[]
        try:  # C1 竞彩去水1X2 vs 锐线去水1X2
            sh=m.get("sharp") or {}
            n1, n2 = _norm3(m.get("spf")), _norm3(sh.get("spf"))
            if n1 and n2:
                d=max(abs(n1[k]-n2[k]) for k in range(3))
                if d>=0.10: flags.append(f"🔴1X2两源差{d*100:.0f}%");nr+=1
                elif d>=0.06: flags.append(f"🟡1X2两源差{d*100:.0f}%");ny+=1
        except Exception: pass
        try:  # C2 市场去水概率 vs 本场泊松模型概率 的KL残差(反演拟合优度)
            qm=_norm3(m.get("spf"))
            if qm:
                kl=_kl3(qm,a["one"])
                if kl>=0.05: flags.append(f"🔴KL残差{kl:.3f}");nr+=1
                elif kl>=0.02: flags.append(f"🟡KL残差{kl:.3f}");ny+=1
        except Exception: pass
        try:  # C3 让球SP去水 vs 模型让球概率
            qr=_norm3(m.get("rsp"))
            if qr and a.get("hcap"):
                d=max(abs(qr[k]-a["hcap"][k]) for k in range(3))
                if d>=0.12: flags.append(f"🔴让球模型差{d*100:.0f}%");nr+=1
                elif d>=0.08: flags.append(f"🟡让球模型差{d*100:.0f}%");ny+=1
        except Exception: pass
        try:  # C4 大小球水位去水 vs 模型总λ在该线的大球概率（若λ正是由该ou锚定，则同源非独立，只标注不判偏差）
            ou=m.get("ou")
            if ou and ou.get("over") is not None and ou.get("under") is not None:
                if "大小球锚" in (a.get("lsrc") or ""):
                    flags.append("◯大小球同源(λ由其锚定,非独立校验)")
                else:
                    q=(1/ou["over"])/((1/ou["over"])+(1/ou["under"]))
                    d=abs(q-p_over_line(a["lt"],float(ou["line"])))
                    if d>=0.10: flags.append(f"🔴大小球差{d*100:.0f}%");nr+=1
                    elif d>=0.06: flags.append(f"🟡大小球差{d*100:.0f}%");ny+=1
        except Exception: pass
        _sh=m.get("sharp") or {}
        # v5.7.1 口径修正：竞彩官方不卖大小球，"大小/λ原料"必须把Pinnacle锐线(ou/ou_multi/spf)计入，
        # 否则有锐线能纯市场反推λ的场仍被误报"缺λ原料/缺大小"(终审日志误报根因)；锐线1X2+大小球即可市场反推λ
        _sharp_ou=_sh.get("ou") or _sh.get("ou_multi")
        have=[("胜",m.get("spf")),("让",m.get("rsp")),("比分",m.get("ssp")),("总进",m.get("tsp")),
              ("锐1X2",_sh.get("spf")),("锐让球",_sh.get("rsp")),
              ("大小",m.get("ou") or _sharp_ou),
              ("λ原料",m.get("stat") or m.get("avg") or (m.get("lh") is not None) or _sharp_ou or _sh.get("spf"))]
        n=sum(1 for _,v in have if v); miss="/".join(k for k,v in have if not v)
        print(f'  {m["no"]} 完整{n}/8 缺[{miss or "无"}]  ' + (" ".join(flags) if flags else "✓一致性正常"))
    print(f"  ── 质量校验汇总：🔴异常{nr}项、🟡关注{ny}项（偏差/残差越大，越要回看是否伤停未更新、让球线对错、或采集错值）")


def lambda_calibration_report(A):
    """v5.3.3 λ校正链透明化：逐场展示 统计λ(联赛标准化+贝叶斯收缩)/竞彩市场锚λt/锐线锚λt/双锚交叉偏差/
    融合权重/战意伤停天气调整前→最终λ/边界异常。回答'每个λ是否经过校正、怎么校正的'。"""
    line(); print("§A+ λ校正链审计（统计λ经联赛标准化+贝叶斯收缩；市场λ经双锚交叉；融合权重随样本自适应；末做边界校正）"); line()
    n_warn = 0
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        m = a["m"]; au = m.get("_lambda_audit") or {}
        seg = [f'{m["no"]} {str(m.get("lg",""))[:4]} 来源={au.get("source","?")}']
        if "cn_lt" in au:
            seg.append(f'竞彩锚λt{au["cn_lt"]:.2f}(主{au.get("cn_h",0):.2f}/客{au.get("cn_a",0):.2f})')
        if "sh_lt" in au:
            seg.append(f'锐线锚λt{au["sh_lt"]:.2f}')
            if "anchor_gap" in au:
                seg.append(f'双锚差{au["anchor_gap"]:.2f}' + ("⚠" if au.get("anchor_warn") else "✓"))
        if "stat_h" in au:
            seg.append(f'统计λ主{au["stat_h"]:.2f}/客{au["stat_a"]:.2f}')
        if au.get("hard_div") is not None:
            seg.append(f'⛔严重背离{au["hard_div"]:.2f}已强制市场')
        if "pre_h" in au:
            seg.append(f'调整前{au["pre_h"]:.2f}/{au["pre_a"]:.2f}')
        seg.append(f'最终λ主{a["lh"]:.2f}/客{a["la"]:.2f}(λt{a["lt"]:.2f})')
        print("  " + " | ".join(seg))
        if au.get("anchor_warn"):
            print(f"      ⚠双锚交叉：{au['anchor_warn']}"); n_warn += 1
        if au.get("ttg_hi"):
            print(f"      ⚠高总λt={au['ttg_hi']}仅由总进球SP反推(聚合档分辨率下降)，建议补大小球ou做双锚交叉"); n_warn += 1
        if m.get("_lambda_warn"):
            print(f"      ⛔边界校正：{m['_lambda_warn']}"); n_warn += 1
        if m.get("_manual_warn"):
            print(f"      ⚠手填一致性：{m['_manual_warn']}"); n_warn += 1
    print(f"  ── λ校正汇总：{len(A)}场全部经过[收缩/双锚交叉/自适应融合/边界]校正链，其中{n_warn}项留痕告警"
          "（统计λ做小样本贝叶斯收缩k=12/升班马20；市场λ以竞彩总进球锚与锐线大小球锚交叉；样本越不足越信市场）。")


# ===================== v5.2 新增②：全局EV最优选注（与角色覆盖模式并列对照）=====================
def final_five_optimal(combos, want=FINAL_MAX_BETS, leg_cap=2):
    """全局Kelly/EV最优，并规避小概率高赔'伪正EV'陷阱：先剔ρ≥0.3；主序列只用非博冷(每腿SP≤2.50)组合,
    层级=可实盘(f_live>0)→过价值硬过滤(按凯利f*优先、再EV)→其余(EV优先)；含SP>2.50博冷腿的组合整体降级为
    '博冷观察'，仅当主序列不足5注时补齐(模型对稀有比分/0球概率不可靠，raw-EV虚高，Kelly会把其仓位压到≈0)。
    每条腿最多复用leg_cap次。返回[(层级,c)]。"""
    # v5.3.6 F3：cand_tr=EV同源可信；cand_fake=跨源伪EV(概率来自spf却配rsp/ssp/tsp、且无独立概率来源)
    cand_tr=[c for c in combos if c["spc"] is not None and c["rho_hi"]<RHO_BLOCK and c.get("ev_trusted",True)]
    cand_fake=[c for c in combos if c["spc"] is not None and c["rho_hi"]<RHO_BLOCK and not c.get("ev_trusted",True)]
    _spcache={}                                            # v5.3.2 缓存stake_plan,20万组合不再重复计算
    def sp(c):
        k=id(c)
        if k not in _spcache: _spcache[k]=stake_plan(c)
        return _spcache[k]
    def pr(c): return c.get("pc_raw", c["pc"])
    def fs(c): return kelly(pr(c),c["spc"])
    def cold(c): return (c["L1"]["sp"] or 0)>2.50 or (c["L2"]["sp"] or 0)>2.50
    def tiers(pool, val_tag):
        live=[c for c in pool if sp(c)["f_live"]>0]; live.sort(key=lambda c:(-sp(c)["f_live"],-fs(c)))
        lid={id(c) for c in live}
        val=[c for c in pool if id(c) not in lid and investable(c)[0]]
        val.sort(key=lambda c:(-fs(c),-(c["ev"] if c["ev"] is not None else -9),-pr(c)))
        vid={id(c) for c in val}
        rest=[c for c in pool if id(c) not in lid|vid]
        rest.sort(key=lambda c:(-(c["ev"] if c["ev"] is not None else -9),-pr(c)))
        return [("★可实盘",c) for c in live]+[(val_tag,c) for c in val]+[("对照·最高EV",c) for c in rest]
    mainc=[c for c in cand_tr if not cold(c)]; longc=[c for c in cand_tr if cold(c)]
    ordered=tiers(mainc,"价值·纸面")+[("博冷观察",c) for _,c in tiers(longc,"博冷观察")]
    # v5.3.6 F3：跨源伪EV注统一压到全序列最后、改标⊗伪EV观察；只有可信注不足5注时才以"观察"名义补齐，绝不冒充价值
    fake=sorted(cand_fake,key=lambda c:(-(c["ev"] if c["ev"] is not None else -9),-pr(c)))
    ordered=ordered+[("⊗伪EV观察",c) for c in fake]
    chosen=[];use={};seen=set()
    for relax in (False,True):                 # 第一轮限腿复用，不够再放开补齐5注
        for tier,c in ordered:
            if len(chosen)>=want: break
            k=ckey(c)
            if k in seen: continue
            if not relax and any(use.get(l,0)>=leg_cap for l in llegs(c)): continue
            seen.add(k);chosen.append((tier,c))
            for l in llegs(c): use[l]=use.get(l,0)+1
        if len(chosen)>=want: break
    return chosen[:want]
def print_optimal_five(A, combos_val):
    line(); print(f"★【主推荐】终选最优{FINAL_MAX_BETS}注·全局EV最优模式（按期望收益/凯利排序+每腿最多用2次；v5.3.2升为主推荐，角色覆盖降为参考）"); line()
    sel=final_five_optimal(combos_val)
    if not sel:
        print("  今日无带SP的合法跨场2串1（可能未采到SP）。");return None
    evs=[];nlive=0;ncold=0;nfake=0;nval=0
    for i,(tier,c) in enumerate(sel,1):
        s=stake_plan(c);evs.append(c["ev"] if c["ev"] is not None else 0);nlive+=(s["f_live"]>0)
        ncold+=(tier=="博冷观察");nfake+=(tier=="⊗伪EV观察");nval+=(tier=="价值·纸面")
        _pr=c.get("pc_raw",c["pc"])*100
        _disc="(同联赛折减显示%.1f%%)"%(c["pc"]*100) if c.get("same_lg") else ""
        print(f"{i}.[{tier}][{c['cat']}] P={_pr:.1f}%{_disc} SP={c['spc']:.2f} EV={(c['ev'] or 0)*100:+.1f}% "
              f"f*={s['f_star']*100:.2f}% 理论{s['f_theory']*100:.3f}%/实盘{s['f_live']*100:.3f}% ρ{c['rho_hi']:.2f}")
        print(f"     {fmt_leg(c['n1'],c['L1'])} × {fmt_leg(c['n2'],c['L2'])}")
    if ncold:
        print(f"  ⚠其中{ncold}注为'博冷观察'(含SP>2.50腿)：稀有比分/0球的raw-EV虚高、模型不可靠，Kelly仓位≈0，仅观察不建议投。")
    if nfake:
        print(f"  ⊗其中{nfake}注为'伪EV观察'：概率仅由胜平负spf反演、却配让球/比分/总进球另一市场SP，且无stat/锐线/手填λ，")
        print("     其+EV是两套抽水错位的假象(F3已拦在价值榜外)，【禁止据此投注】；补stat统计原料或Pinnacle锐线后才可能成为真价值。")
    print(f"  ── 全局EV模式：可实盘(f_live>0) {nlive}/{len(sel)}、同源可信价值注 {nval}/{len(sel)}、伪EV观察 {nfake}/{len(sel)}；"
          + ("有过闸注→仅按其实盘比例投、且单日实盘≤%d组" % MAX_PARLAY_LIVE if nlive
             else ("无任一注过实盘闸门" + ("，且无同源可信正EV注→资金最优动作=【空仓】，下列仅纸面参考、禁止照投" if nval==0
                                        else "，可信价值注仍需双锐线/CLV/S+才放开实盘，暂仅纸面"))))
    print("  · v5.3.2：本模式为【主推荐】(期望收益优先)；上方角色覆盖仅作命中面参考。全部f_live=0时最优动作=空仓。")
    # 主推荐也跑一次组合层联合配仓（其f上界已锁死≤逐注分数凯利，不会放大）
    try:
        opt_plans = [("主推荐", c, stake_plan(c)) for _t, c in sel]
        print_portfolio_kelly(A, opt_plans)
    except Exception:
        pass
    return sel


# ===================== v5.3 新增：组合层凯利联合配仓（计入共用腿同黑/净敞口）=====================
def _final_matrix(a):
    """重建 analyze 使用的最终比分概率矩阵(独立泊松→Dixon-Coles→draw_boost)，保证与各腿显示概率同源。"""
    m=a["m"]; ds=m["spf"][1] if m.get("spf") else None
    M=dixon_coles(base_matrix(a["lh"],a["la"]),a["lh"],a["la"],rho_of_match(a["lh"],a["la"]))  # 与analyze主链同源(v5.8.3建议①④)
    return draw_boost(M,ds)
def _leg_hit(L,hand,i,j):
    """比分(i主,j客)下某条腿是否命中：W看胜负方向/H看让球后方向/S看精确比分/T看总进球。"""
    if L["mk"]=="W":
        return (i>j and L["d"]==0) or (i==j and L["d"]==1) or (i<j and L["d"]==2)
    if L["mk"]=="H":
        s=i+(hand or 0)-j
        return (s>0 and L["d"]==0) or (s==0 and L["d"]==1) or (s<0 and L["d"]==2)
    if L["mk"]=="S":
        a,b=L["pick"].split("-"); return i==int(a) and j==int(b)
    if L["mk"]=="T":
        return i+j==int(L["pick"].replace("球",""))
    return False
def _portfolio_ascent(R,P,ub,groups,cap_total,it=6000,lr=0.05):
    """无scipy兜底：凹目标=组合对数增长，梯度上升后投影到[0,ub]+单场/总仓上限(对数凹→收敛到全局)。"""
    import numpy as np
    x=np.zeros(len(ub)); R=np.array(R);P=np.array(P);ub=np.array(ub,float)
    for _ in range(it):
        w=1+R.dot(x); g=R.T.dot(P/w)
        x=np.minimum(ub,np.maximum(0,x+lr*g))
        for _p in range(25):
            ch=False;s=x.sum()
            if s>cap_total and s>0: x*=cap_total/s;ch=True
            for idxs,cap in groups:
                s=x[idxs].sum()
                if s>cap and s>0: x[idxs]*=cap/s;ch=True
            if not ch: break
    return x
def _project_caps(x,ub,groups,cap_total):
    """把一个配仓向量按 玩法上限/单场上限/日仓 等比压缩到可行域(用于生成'独立配仓的可行对照')。"""
    import numpy as np
    x=np.minimum(np.array(ub,float),np.maximum(0,np.array(x,float)))
    for _ in range(60):
        ch=False;s=x.sum()
        if s>cap_total and s>0: x*=cap_total/s;ch=True
        for idxs,cap in groups:
            s=x[idxs].sum()
            if s>cap and s>0: x[idxs]*=cap/s;ch=True
        if not ch: break
    return x
def portfolio_kelly(A, plans, require_edge=True, deployable_only=False):
    """对终选若干注做组合层联合凯利。
    思路：每场用最终比分矩阵把'本场被选腿'压成命中bitmask分布(精确刻画同场W/H/S/T相关性)；
    跨场独立→枚举联合结果(≤2^腿数)；每注在各联合结果下的净收益 r=SP(中)/-1(丢)；
    最大化期望对数增长 G(f)=Σ p·ln(1+Σ f·r)。v5.3.2关键修复：每注上界=min(玩法硬顶,逐注分数凯利f_theory)，
    联合配仓绝不超过逐注1/8分数凯利(旧版用全凯利+硬顶会把A级注放大数十倍)；共用腿一黑多注同黑由联合分布自动计入。"""
    Ab={a["m"]["no"]:a for a in A}
    items=[]
    for _role,c,sp in plans:
        if c["spc"] is None: continue
        if require_edge and sp["f_star"]<=0: continue
        if deployable_only and sp["f_live"]<=0: continue   # 理论注不得占用可实盘注的单场/日仓预算
        items.append((c,sp,[(c["n1"],c["L1"]),(c["n2"],c["L2"])]))
    if not items: return None
    mlegs={}; legidx={}
    for c,sp,legs in items:
        for no,L in legs:
            mlegs.setdefault(no,[]); k=(no,L["mk"],L["pick"])
            if k not in legidx: legidx[k]=len(mlegs[no]); mlegs[no].append((k,L))
    mdist={}
    for no,lst in mlegs.items():
        a=Ab[no]; M=_final_matrix(a); hand=a["m"].get("hand"); dist={}
        for i in range(len(M)):
            for j in range(len(M[0])):
                mask=0
                for bit,(k,L) in enumerate(lst):
                    if _leg_hit(L,hand,i,j): mask|=(1<<bit)
                dist[mask]=dist.get(mask,0.0)+M[i][j]
        z=sum(dist.values()); mdist[no]={m_:v/z for m_,v in dist.items() if v>1e-12}
    nos=list(mlegs.keys()); outcomes=[]
    def rec(t,cur,p):
        if t==len(nos): outcomes.append((p,cur[:])); return
        for mask,pr in mdist[nos[t]].items():
            cur.append(mask); rec(t+1,cur,p*pr); cur.pop()
    rec(0,[],1.0)
    R=[];P=[]
    for p,cur in outcomes:
        mk={nos[t]:cur[t] for t in range(len(nos))}; row=[]
        for c,sp,legs in items:
            win=all((mk[no]>>legidx[(no,L["mk"],L["pick"])])&1 for no,L in legs)
            row.append(c["spc"] if win else -1.0)
        R.append(row);P.append(p)
    nI=len(items)
    is10w=any(Ab[no]["m"].get("bankroll_tier")=="10w" for no in nos)
    cap_match=0.0135 if is10w else CAP_MATCH
    # v5.3.2 上界=min(玩法硬顶, 逐注分数凯利f_theory)：联合配仓不再把1/8分数凯利放大回全凯利
    ub=[min(CAP_PLAY_EXOTIC if sp["exotic"] else CAP_PLAY_WH, max(sp["f_theory"],0.0)) for _c,sp,_l in items]
    groups=[]
    for no in nos:
        idxs=[k for k,(_c,_sp,legs) in enumerate(items) if any(x[0]==no for x in legs)]
        if len(idxs)>=1: groups.append((idxs,cap_match))
    fj=None;method=""
    try:
        import numpy as np
        from scipy.optimize import minimize
        Ra=np.array(R);Pa=np.array(P);uba=np.array(ub,float)
        def negG(x):
            w=1+Ra.dot(x); return -np.sum(Pa*np.log(w))
        def jac(x):
            w=1+Ra.dot(x); return -Ra.T.dot(Pa/w)
        cons=[{"type":"ineq","fun":(lambda x:DAILY_CAP-x.sum())}]
        for idxs,cap in groups:
            cons.append({"type":"ineq","fun":(lambda x,ix=idxs,cp=cap:cp-x[ix].sum())})
        x0=np.minimum(uba,np.array([sp["f_theory"] for _c,sp,_l in items],float))
        rs=minimize(negG,x0,jac=jac,bounds=[(0,uba[k]) for k in range(nI)],
                    constraints=cons,method="SLSQP",options={"maxiter":400,"ftol":1e-11})
        fj=np.maximum(0,rs.x);method="SLSQP"
    except Exception:
        import numpy as np
        fj=_portfolio_ascent(R,P,ub,groups,DAILY_CAP);method="投影梯度"
    # 独立配仓对照：原始(可能突破单场上限) 与 按上限压缩后的可行对照；联合最优须不劣于可行独立
    indep=[sp["f_theory"] for _c,sp,_l in items]
    indep_f=_project_caps(indep,ub,groups,DAILY_CAP)
    import numpy as np
    Ra=np.array(R);Pa=np.array(P)
    def growth(x):
        x=np.array(x,float);w=1+Ra.dot(x);return float(np.sum(Pa*np.log(w)))
    shared={no:sum(1 for _c,_sp,legs in items if any(x[0]==no for x in legs)) for no in nos}
    shared={no:n for no,n in shared.items() if n>=2}
    return dict(items=items,fj=[float(x) for x in fj],indep=indep,indep_f=[float(x) for x in indep_f],
                groups=groups,ub=ub,cap_match=cap_match,G_joint=growth(fj),
                G_indep=growth(indep),G_indep_f=growth(indep_f),
                method=method,shared=shared,n_out=len(outcomes))
def print_portfolio_kelly(A,plans):
    line(); print("★组合层凯利·联合配仓（比分矩阵枚举联合结果，计入共用腿同黑/净敞口；可实盘与理论分层、互不占预算）"); line()
    try:
        live_plans=[(r,c,sp) for r,c,sp in plans if c["spc"] is not None and sp["f_live"]>0]
        theo_plans=[(r,c,sp) for r,c,sp in plans if c["spc"] is not None and sp["f_star"]>0 and sp["f_live"]<=0]
        def show(tag,res):
            items=res["items"];fj=res["fj"];indep=res["indep"];indep_f=res["indep_f"]
            print(f"  【{tag}】联合结果{res['n_out']}种；求解{res['method']}；单场上限{res['cap_match']*100:.2f}%/日仓{DAILY_CAP*100:.0f}%")
            for k,(c,sp,legs) in enumerate(items):
                adj="，较逐注独立下调(共用腿/单场·日仓)" if indep[k]-fj[k]>1e-6 else ""
                print(f"  · [{c['cat']}] {fmt_leg(c['n1'],c['L1'])} × {fmt_leg(c['n2'],c['L2'])}")
                print(f"      逐注独立{indep[k]*100:.3f}%→可行{indep_f[k]*100:.3f}%→联合{fj[k]*100:.3f}%{adj}")
            if res["shared"]:
                print("  共用腿（一腿错多注同黑，已计入联合分布）："+"、".join(f"{no}被{n}注共用" for no,n in sorted(res["shared"].items())))
            print(f"  ─ Σf：逐注独立{sum(indep)*100:.3f}%/可行压缩{sum(indep_f)*100:.3f}%/联合最优{sum(fj)*100:.3f}%；"
                  f"对数增长G 可行{res['G_indep_f']*100:.4f}%→联合{res['G_joint']*100:.4f}%")
        if live_plans:
            rl=portfolio_kelly(A,live_plans,deployable_only=True)
            if rl: show("可实盘·按此联合f出资",rl)
        else:
            print("  今晚无任一注 f_live>0（未过双锐线/每腿CLV≥+3%/S+实盘闸门）→【可实盘】联合配仓=0。")
        if theo_plans:
            rt=portfolio_kelly(A,theo_plans,require_edge=True)
            if rt: show("理论参考·不占实盘预算(f_live=0,禁止照投)",rt)
        if not live_plans and not theo_plans:
            print("  终选5注凯利边际 f* 均≤0（无正期望）→ 联合最优配仓=0，资金最优动作=空仓，5注仅纸面。")
    except Exception as ex:
        print(f"  ⚠联合配仓计算异常(已安全跳过,不影响其余报告):{ex}")

def _res_ij(res):
    try:
        i, j = str(res).split(":")[:2]; return int(i), int(j)
    except Exception:
        return None
def _leg_settled(L, i, j, hand):
    """单腿是否命中（i,j=赛果,hand=让球线带方向）。"""
    wd = 0 if i > j else (1 if i == j else 2)
    if L["mk"] == "W": return L["d"] == wd
    if L["mk"] == "H":
        if hand is None: return False
        hd = 0 if i + hand - j > 0 else (1 if i + hand - j == 0 else 2)
        return L["d"] == hd
    if L["mk"] == "S": return L["pick"] == f"{i}-{j}"
    if L["mk"] == "T":
        try: return int(L["pick"].replace("球", "")) == (i + j)
        except Exception: return False
    return False
def settle_review(A, final=None, stake=STAKE_UNIT):
    """v5.3.2新增 赛果结算回测：m['res']='主队:客队'时自动核对每场四玩法首选腿、终选2串1的命中与兑现盈亏。
    这是'用结果校正模型'的第一步(先能结算命中率/兑现ROI，后续可据此滚动校准ρ/阈值)；只统计不改模型。"""
    line(); print("★赛果结算回测（给记录填 res='主队进球:客队进球' 即自动结算首选腿命中率与终选注盈亏）"); line()
    hit = {mk: [0, 0] for mk in "WHST"}; nres = 0
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        ij = _res_ij(a["m"].get("res"))
        if ij is None: continue
        nres += 1; i, j = ij; hand = a["m"].get("hand")
        for L in a["legs"]:
            hit[L["mk"]][1] += 1
            hit[L["mk"]][0] += 1 if _leg_settled(L, i, j, hand) else 0
    if nres == 0:
        print("  本批无赛果（赛后给比赛记录补 res='主队:客队' 重跑即自动结算）。"); return
    names = {"W": "胜平负首选", "H": "让球首选", "S": "比分首选", "T": "总进球首选"}
    print(f"  已填赛果 {nres} 场，各玩法【首选腿】命中率：")
    for mk in ("W", "H", "S", "T"):
        h, t = hit[mk]
        if t: print(f"    {names[mk]}：{h}/{t} = {h/t*100:.0f}%")
    if final:
        Amap = {a["m"]["no"]: a for a in A}; win = tot = 0; pnl = 0.0
        for _role, c in final:
            legs = [(c["n1"], c["L1"]), (c["n2"], c["L2"])]
            if not all(Amap.get(no) and _res_ij(Amap[no]["m"].get("res")) for no, _ in legs): continue
            both = True
            for no, L in legs:
                a = Amap[no]; i, j = _res_ij(a["m"]["res"])
                both = both and _leg_settled(L, i, j, a["m"].get("hand"))
            tot += 1; win += 1 if both else 0
            pnl += (c["spc"] * stake - stake) if both else -stake
        if tot:
            print(f"  终选2串1：命中 {win}/{tot} = {win/tot*100:.0f}%；每注{stake:g}元按兑现SP，总盈亏 {pnl:+.1f} 元（ROI {pnl/(tot*stake)*100:+.0f}%）")
    print("  说明：小样本不构成结论；长期须 命中率×平均SP>1 才为正期望，可用本结算滚动校准模型。")


# ===================== v5.5.2 赛前快照锁存 + 赛后只读锁存结算（审计增强；不改概率引擎、不改 settle_review 口径）=====================
def _json_safe(x):
    """递归转 JSON 可序列化（快照内基本都是原生类型，此处做兜底：tuple/set→list、非标量→str）。"""
    if isinstance(x, dict):
        return {str(k): _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    return str(x)


def _snap_leg(L):
    """锁存单腿：只留结算/审计必需字段。mk=玩法,pick=中文选项,d=方向(W/H用),p=赛前概率,sp=赛前即时SP。
    赛后结算只认这里锁存的值，绝不再用赛后数据重算。"""
    return dict(mk=L["mk"], pick=str(L["pick"]),
                d=(None if L.get("d") is None else int(L["d"])),
                p=(round(float(L["p"]), 6) if L.get("p") is not None else None),
                sp=(round(float(L["sp"]), 4) if L.get("sp") is not None else None))


def _snap_note(role, c, amt=None):
    """锁存一注 2串1（程序终选 / v5.5投注单通用）：两腿 + 联合概率 + 总赔 +（投注单）建议金额。"""
    pcombo = c.get("pc_raw")
    if pcombo is None:
        pcombo = c.get("pc")
    d = dict(role=str(role), cat=c.get("cat"),
             n1=str(c["n1"]), L1=_snap_leg(c["L1"]), n2=str(c["n2"]), L2=_snap_leg(c["L2"]),
             spc=(round(float(c["spc"]), 4) if c.get("spc") is not None else None),
             pc=(round(float(pcombo), 6) if pcombo is not None else None))
    if amt is not None:
        d["amt"] = int(amt)
    return d


def _snap_batch_label(batch):
    """批次标签：显式 MATCH_DATE（'auto'除外）优先，否则用快照生成的北京日期；用于赛后按批次找最近快照。"""
    if batch and str(batch).lower() != "auto":
        return str(batch)
    return _bj_now_naive().strftime("%Y-%m-%d")


def _norm_actual_tickets(tickets):
    """把 ACTUAL_TICKETS 规范化为可JSON结构（腿统一成[n,mk,pick]列表，兼容tuple/list）。"""
    out = []
    for t in (tickets or []):
        legs = []
        for x in t.get("legs", []):
            if not x or len(x) < 3:
                continue
            legs.append([str(x[0]), str(x[1]), str(x[2])])
        out.append(dict(name=str(t.get("name", "票")), stake=float(t.get("stake", 0) or 0),
                        payout=(float(t["payout"]) if t.get("payout") is not None else None), legs=legs))
    return out


def save_pre_match_snapshot(A, final, slip=None, batch="auto", actual_tickets=None,
                            outdir=SNAPSHOT_DIR, verbose=True):
    """【赛前】出单后调用：把每场四玩法首选腿+hand+λ+1X2、程序终选注、v5.5投注单(金额)、实际购票台账锁成JSON。
    文件名带批次+北京时间戳、永不覆盖；同时刷新 latest_批次.json 软指针。返回快照路径。"""
    import os
    matches = []
    for a in sorted(A, key=lambda z: str(z["m"].get("no"))):
        m = a["m"]
        ko = kickoff_dt(m)
        matches.append(dict(no=str(m.get("no")), lg=m.get("lg"), home=m.get("home"), away=m.get("away"),
                            matchDate=m.get("matchDate"), businessDate=m.get("businessDate"),
                            time=(ko.strftime("%Y-%m-%d %H:%M") if ko else (m.get("time") or "")),
                            hand=m.get("hand"),
                            lh=round(float(a["lh"]), 4), la=round(float(a["la"]), 4),
                            one=[round(float(x), 6) for x in a["one"]],
                            # v5.7.1 补锁让球三方向/总进球分布/概率源，供赛后自动攒校准样本(旧快照无这些键则读取端降级)
                            hcap=([round(float(x), 6) for x in a["hcap"]] if a.get("hcap") else None),
                            tg=([round(float(x), 6) for x in a["tg"]] if a.get("tg") else None),
                            fuse_mode=(m.get("_v54") or {}).get("fuse_mode"), hcap_src=m.get("_hcap_src"),
                            # v5.7.8 锁存SportScore补强证据(在线交锋/预测阵型/积分摘要+在线H2H明细),供日后复盘升级
                            ss_info=m.get("ss_info"), h2h_online=m.get("_h2h_online"),
                            legs=[_snap_leg(L) for L in a["legs"]]))
    snap_final = [_snap_note(role, c) for role, c in (final or [])]
    snap_slip = None
    if slip and slip.get("sub"):
        snap_slip = [_snap_note("投注单", c, amt=amt)
                     for (_p, _sp, c), amt in zip(slip["sub"], slip.get("bets", []))]
    at = _norm_actual_tickets(ACTUAL_TICKETS if actual_tickets is None else actual_tickets)
    snap = dict(schema="v552_snapshot_v1", created_bj=_bj_now_naive().strftime("%Y-%m-%d %H:%M:%S"),
                batch=_snap_batch_label(batch), bankroll=float(NIGHT_BANKROLL),
                matches=matches, final=snap_final, slip=snap_slip, actual_tickets=at)
    os.makedirs(outdir, exist_ok=True)
    bkey = re.sub(r"[^0-9A-Za-z_-]", "", snap["batch"].replace(":", "").replace(" ", "_")) or "batch"
    ts = _bj_now_naive().strftime("%Y%m%d_%H%M%S")
    fp = os.path.join(outdir, f"snapshot_{bkey}_{ts}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(_json_safe(snap), f, ensure_ascii=False, indent=2)
    try:  # 软指针：赛后留空路径时直接命中
        with open(os.path.join(outdir, f"latest_{bkey}.json"), "w", encoding="utf-8") as f:
            json.dump(_json_safe(snap), f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    if verbose:
        line(); print(f"🔒 v5.5.2 已锁存赛前快照：{fp}")
        print(f"   锁存 {len(matches)} 场首选腿、{len(snap_final)} 注程序终选、"
              f"{len(snap_slip or [])} 注投注单、{len(at)} 张实际购票。")
        print("   赛后填 POST_RESULTS 比分重跑（或调 settle_snapshot_file）即只读本快照对账，"
              "首选不会被赛后赔率/λ漂移重算污染。"); line()
    return fp


def load_snapshot(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _actual_dir(mk, i, j, hand):
    """由终场比分(i主j客)+让球线hand，算某玩法【实际开出选项】的中文，口径与 DIR/HC_NAME/腿pick 完全一致。"""
    if mk == "W":
        return DIR[0 if i > j else (1 if i == j else 2)]
    if mk == "H":
        if hand is None:
            return None
        dh = i + hand - j
        return HC_NAME[0 if dh > 0 else (1 if dh == 0 else 2)]
    if mk == "S":
        return f"{i}-{j}"
    if mk == "T":
        return f"{i+j}球"
    return None


def _leg_hit_by_pick(mk, pick, i, j, hand):
    """按(mk,中文pick)判单腿是否命中（实际购票台账用，不依赖锁存d）。返回(是否中,实际选项)。"""
    act = _actual_dir(mk, i, j, hand)
    return (act is not None and str(pick) == str(act)), act


# ============================ v5.7.1 P1+P2 自动校准闭环 ============================
def parse_results_text(text):
    """P2：把自然语言比分串解析成 {编号:'主:客'}。兼容 '001 1:0'、'1 1-0'、'002　1：1'、分号/逗号/空格/全角分隔；
    正则用前后非数字边界避免把日期2026-09-07误当比分；进球数限制0-12。解析不到返回{}。"""
    if not text:
        return {}
    out = {}
    # 结构=编号 + 空白(或"号"/"场") + 主进球[:：或-]客进球；编号与首个进球间必须有分隔，借此切开编号与比分、避开日期
    pat = re.compile(r'(?<!\d)(\d{1,3})(?:\s*[号场])?\s+(\d{1,2})\s*[:：\-]\s*(\d{1,2})(?!\d)')
    for mt in pat.finditer(str(text)):
        no, i, j = mt.group(1).zfill(3), int(mt.group(2)), int(mt.group(3))
        if 0 <= i <= 12 and 0 <= j <= 12:
            out[no] = f"{i}:{j}"
    return out



# ===== v5.8.1 内置校准种子库（用户累计52条历史样本：批次2026-09-08/09，W=26/H=26，均已过isotonic 15场门槛）=====
# 播种规则：本地样本库缺失则用它起步、已存在则按(batch,no,market)去重补齐；用户赛后真实样本优先、永不被种子覆盖。
# 想完全从零开始：删掉 jc_data/calib_store.json 并清空本段即可。
_SEED_CALIB_JSON = '[{"batch":"2026-09-08","no":"002","market":"W","home":"雅典AEK","away":"LASK林茨","probs":[0.479206,0.268022,0.252771],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"002","market":"H","home":"雅典AEK","away":"LASK林茨","probs":[0.332425,0.26389,0.403685],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"003","market":"W","home":"布鲁日","away":"维拉","probs":[0.366275,0.290647,0.343078],"pick_dir":0,"actual_dir":2,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"003","market":"H","home":"布鲁日","away":"维拉","probs":[0.536402,0.237534,0.226063],"pick_dir":0,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"004","market":"W","home":"奈梅亨","away":"SBV精英","probs":[0.490075,0.266057,0.243868],"pick_dir":0,"actual_dir":1,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"004","market":"H","home":"奈梅亨","away":"SBV精英","probs":[0.351511,0.262413,0.386076],"pick_dir":2,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"005","market":"W","home":"胡巴卡德","away":"吉达国民","probs":[0.420488,0.286539,0.292973],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"005","market":"H","home":"胡巴卡德","away":"吉达国民","probs":[0.277385,0.264186,0.458429],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"006","market":"W","home":"南安普敦","away":"斯旺西","probs":[0.454658,0.283735,0.261607],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"006","market":"H","home":"南安普敦","away":"斯旺西","probs":[0.304634,0.27221,0.423156],"pick_dir":2,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"007","market":"W","home":"桑德兰","away":"赫尔城","probs":[0.473431,0.291988,0.23458],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"007","market":"H","home":"桑德兰","away":"赫尔城","probs":[0.321433,0.284003,0.394564],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"008","market":"W","home":"皇马","away":"国际米兰","probs":[0.50372,0.260484,0.235796],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"008","market":"H","home":"皇马","away":"国际米兰","probs":[0.358203,0.262184,0.379613],"pick_dir":2,"actual_dir":1,"hcap_src":"matrix(锐线方向不明回退)","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"009","market":"W","home":"多特蒙德","away":"比利亚雷","probs":[0.46477,0.271441,0.263789],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"009","market":"H","home":"多特蒙德","away":"比利亚雷","probs":[0.322022,0.261176,0.416802],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"010","market":"W","home":"里尔","away":"贝蒂斯","probs":[0.406967,0.293498,0.299535],"pick_dir":0,"actual_dir":2,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"010","market":"H","home":"里尔","away":"贝蒂斯","probs":[0.265515,0.259384,0.475101],"pick_dir":2,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"011","market":"W","home":"波尔图","away":"曼城","probs":[0.232558,0.269356,0.498086],"pick_dir":2,"actual_dir":2,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"011","market":"H","home":"波尔图","away":"曼城","probs":[0.381807,0.272321,0.345872],"pick_dir":0,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"012","market":"W","home":"弗鲁米嫩","away":"普拉滕斯","probs":[0.483357,0.307509,0.209134],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-08","no":"012","market":"H","home":"弗鲁米嫩","away":"普拉滕斯","probs":[0.300979,0.298277,0.400744],"pick_dir":2,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-09 09:59:13"},{"batch":"2026-09-09","no":"001","market":"W","home":"江原FC","away":"全北现代","probs":[0.319911,0.312884,0.367205],"pick_dir":2,"actual_dir":1,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"001","market":"H","home":"江原FC","away":"全北现代","probs":[0.553385,0.244695,0.20192],"pick_dir":0,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"002","market":"W","home":"拉斯永恒","away":"利雅青年","probs":[0.349157,0.277656,0.373187],"pick_dir":2,"actual_dir":0,"fuse_mode":"v5.6三源","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"002","market":"H","home":"拉斯永恒","away":"利雅青年","probs":[0.552924,0.223903,0.223173],"pick_dir":0,"actual_dir":0,"hcap_src":"matrix","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"003","market":"W","home":"巴萨","away":"费耶诺德","probs":[0.76573,0.135856,0.098415],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"003","market":"H","home":"巴萨","away":"费耶诺德","probs":[0.361382,0.223619,0.414999],"pick_dir":2,"actual_dir":0,"hcap_src":"matrix(锐线方向不明回退)","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"004","market":"W","home":"斯图加特","away":"维京","probs":[0.664405,0.188062,0.147533],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"004","market":"H","home":"斯图加特","away":"维京","probs":[0.362215,0.237465,0.40032],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"005","market":"W","home":"特温特","away":"特尔斯达","probs":[0.653444,0.195219,0.151336],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"005","market":"H","home":"特温特","away":"特尔斯达","probs":[0.357635,0.234884,0.407482],"pick_dir":2,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"006","market":"W","home":"里斯本","away":"加拉塔萨","probs":[0.502724,0.258533,0.238744],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"006","market":"H","home":"里斯本","away":"加拉塔萨","probs":[0.323407,0.251271,0.425322],"pick_dir":2,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"007","market":"W","home":"那不勒斯","away":"阿森纳","probs":[0.198457,0.270593,0.53095],"pick_dir":2,"actual_dir":2,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"007","market":"H","home":"那不勒斯","away":"阿森纳","probs":[0.391523,0.270639,0.337838],"pick_dir":0,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"008","market":"W","home":"利物浦","away":"马竞","probs":[0.503525,0.259472,0.237003],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"008","market":"H","home":"利物浦","away":"马竞","probs":[0.326033,0.251767,0.4222],"pick_dir":2,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"009","market":"W","home":"巴黎圣曼","away":"布拉迪斯","probs":[0.79815,0.113368,0.088481],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"009","market":"H","home":"巴黎圣曼","away":"布拉迪斯","probs":[0.481476,0.228366,0.290157],"pick_dir":0,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"010","market":"W","home":"查尔顿","away":"女王巡游","probs":[0.299595,0.300844,0.399561],"pick_dir":2,"actual_dir":1,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"010","market":"H","home":"查尔顿","away":"女王巡游","probs":[0.516797,0.248037,0.235165],"pick_dir":0,"actual_dir":0,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"011","market":"W","home":"切尔西","away":"利兹联","probs":[0.554124,0.248289,0.197588],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"011","market":"H","home":"切尔西","away":"利兹联","probs":[0.372302,0.25571,0.371987],"pick_dir":0,"actual_dir":0,"hcap_src":"matrix(锐线方向不明回退)","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"012","market":"W","home":"摩雷伦斯","away":"本菲卡","probs":[0.116274,0.17057,0.713156],"pick_dir":2,"actual_dir":2,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"012","market":"H","home":"摩雷伦斯","away":"本菲卡","probs":[0.35016,0.254036,0.395804],"pick_dir":2,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"013","market":"W","home":"帕梅拉斯","away":"基多体大","probs":[0.630348,0.233418,0.136235],"pick_dir":0,"actual_dir":0,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"013","market":"H","home":"帕梅拉斯","away":"基多体大","probs":[0.431366,0.286722,0.281912],"pick_dir":0,"actual_dir":1,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"014","market":"W","home":"拉普大学","away":"科林蒂安","probs":[0.406402,0.344228,0.24937],"pick_dir":0,"actual_dir":1,"fuse_mode":"v5.7锐线主锚","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"014","market":"H","home":"拉普大学","away":"科林蒂安","probs":[0.217184,0.273256,0.50956],"pick_dir":2,"actual_dir":2,"hcap_src":"Pinnacle3WayH","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"015","market":"W","home":"芝加哥","away":"迈国际","probs":[0.381933,0.245183,0.372884],"pick_dir":0,"actual_dir":1,"fuse_mode":"v5.6三源","ts":"2026-09-10 11:00:13"},{"batch":"2026-09-09","no":"015","market":"H","home":"芝加哥","away":"迈国际","probs":[0.245897,0.209925,0.544178],"pick_dir":2,"actual_dir":2,"hcap_src":"matrix","ts":"2026-09-10 11:00:13"}]'
_SEED_CALIB_RECORDS = json.loads(_SEED_CALIB_JSON)
_CALIB_SEED_DONE = False
def _merge_seed_calib(store):
    """把内置种子按(batch,no,market)去重并入store，返回新增条数；不覆盖任何已存在样本。"""
    seen = {(r.get("batch"), str(r.get("no")), r.get("market")) for r in store.get("records", [])}
    add = 0
    for _r in _SEED_CALIB_RECORDS:
        _k = (_r.get("batch"), str(_r.get("no")), _r.get("market"))
        if _k not in seen:
            seen.add(_k); store.setdefault("records", []).append(_r); add += 1
    return add

def calib_load(path=CALIB_STORE):
    """读校准样本库；损坏/不存在返回空结构(绝不因样本库问题让主流程崩)。
    v5.8.1：首次读取时把内置52条种子按(batch,no,market)去重播种/补齐并落盘，之后以本地库为准、每进程只播种一次。"""
    global _CALIB_SEED_DONE
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("records"), list):
            if not _CALIB_SEED_DONE:
                _CALIB_SEED_DONE = True
                if _merge_seed_calib(d) > 0:
                    calib_save(d, path)
            return d
    except Exception:
        pass
    d = {"records": [dict(_r) for _r in _SEED_CALIB_RECORDS]}   # 本地无库：用52条种子起步
    if not _CALIB_SEED_DONE:
        _CALIB_SEED_DONE = True
        try: calib_save(d, path)
        except Exception: pass
    return d


def calib_save(store, path=CALIB_STORE):
    try:
        import os as _os
        if _os.path.dirname(path):
            _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_json_safe(store), f, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def calib_append(recs, path=CALIB_STORE):
    """按 (batch,no,market) 去重追加样本，返回新增条数。"""
    if not recs:
        return 0
    store = calib_load(path)
    seen = {(r.get("batch"), str(r.get("no")), r.get("market")) for r in store["records"]}
    add = 0
    for r in recs:
        k = (r.get("batch"), str(r.get("no")), r.get("market"))
        if k in seen:
            continue
        seen.add(k); store["records"].append(r); add += 1
    if add:
        calib_save(store, path)
    return add


def _pava(pairs, alpha=0.0):
    """加权保序回归(PAVA,非递减)。pairs=[(预测p,0/1)]，返回(排序锚点xs,拟合值ys)映射。
    先按相同预测p分桶聚合经验频率(否则同x点y交替会产生锯齿、插值在相邻点0↔1跳变)，再对唯一x点做加权PAVA。
    v5.7.9：alpha>0时块拟合率用Beta(α,α)先验平滑=(命中和+α)/(样本和+2α)，治小样本0/1硬输出；alpha=0即原硬PAVA。"""
    hit, cnt = {}, {}
    for p, y in pairs:
        p = float(p); hit[p] = hit.get(p, 0.0) + int(y); cnt[p] = cnt.get(p, 0) + 1
    def _rate(h, n):
        return (h + alpha) / (n + 2.0 * alpha)
    blocks = []   # 每块=[命中数和, 样本数和, 锚点p列表]
    for p in sorted(hit):
        blocks.append([hit[p], cnt[p], [p]])
        while len(blocks) >= 2 and _rate(*blocks[-2][:2]) > _rate(*blocks[-1][:2]) + 1e-12:
            b2 = blocks.pop(); b1 = blocks.pop()
            blocks.append([b1[0] + b2[0], b1[1] + b2[1], b1[2] + b2[2]])
    xs = [sum(ps) / len(ps) for _, _, ps in blocks]
    ys = [_rate(h, n) for h, n, _ in blocks]
    return xs, ys


def _iso_interp(xs, ys, p):
    """保序映射的分段线性插值；越界取端点。"""
    if not xs:
        return p
    if p <= xs[0]:
        return ys[0]
    if p >= xs[-1]:
        return ys[-1]
    for t in range(1, len(xs)):
        if p <= xs[t]:
            x0, x1, y0, y1 = xs[t - 1], xs[t], ys[t - 1], ys[t]
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (p - x0) / (x1 - x0)
    return ys[-1]


class ProbCalibrator:
    """一个三分类市场(W=1X2 / H=让球)的概率校准器。v5.7.9 正则化增强版（参数由70条样本双交叉验证确定）：
      · n<CALIB_MIN_ISOTONIC(15)：向1/3温和收缩(强度随样本衰减)，治零样本过自信；
      · 15≤n<CALIB_ISO_FULL_N(60)：正则化保序(isotonic, Beta先验PAVA)与原始概率按权重w渐进混合，
        w=(n-15)/(60-15)线性0→1，小样本轻校准、样本越多越信经验，消除原30场硬切换的跳变；
      · n≥60：全信正则化保序；
      · 任何分支输出都过[CALIB_FLOOR,1-CALIB_FLOOR]地板再归一，杜绝近0/1极端概率(对数损失灾难)。
    关 CALIB_ENABLED 或上层不装载时恒等返回，逐字节回到 v5.7 原始概率。"""
    def __init__(self, records, market, min_n=CALIB_MIN_ISOTONIC, shrink_base=CALIB_SHRINK_BASE,
                 full_n=CALIB_ISO_FULL_N, prior=CALIB_ISO_PRIOR, floor=CALIB_FLOOR):
        self.market = market; self.mode = "identity"; self.n = 0; self.maps = []; self.shrink = 0.0
        self.w = 0.0; self.floor = floor
        rs = [r for r in records if r.get("market") == market and r.get("probs") and r.get("actual_dir") is not None]
        self.n = len(rs)
        if self.n >= min_n:
            self.mode = "isotonic"; self.maps = []
            # 渐进混合权重：[min_n, full_n] 线性 0→1，达到 full_n 后恒为 1
            self.w = max(0.0, min(1.0, (self.n - min_n) / float(full_n - min_n))) if full_n > min_n else 1.0
            self.w = min(self.w, CALIB_W_CAP)   # 2026-09-12 LOO劣化临时封顶(见CALIB_W_CAP注释)
            for k in range(3):
                pairs = [(r["probs"][k], 1 if r["actual_dir"] == k else 0) for r in rs]
                self.maps.append(_pava(pairs, alpha=prior))     # v5.7.9 Beta先验正则化PAVA
        else:
            self.mode = "shrink"
            self.shrink = shrink_base * max(0.0, 1.0 - self.n / float(min_n))

    def _floor_norm(self, out, q):
        """概率地板/封顶后归一，保证三方向和=1且无一为0；异常时回退原始q。"""
        out = [min(1.0 - self.floor, max(self.floor, float(x))) for x in out]
        s = sum(out)
        return [x / s for x in out] if s > 0 else q

    def apply(self, q):
        if q is None:
            return q
        q = [float(x) for x in q[:3]]
        if self.mode == "isotonic":
            iso = [_iso_interp(self.maps[k][0], self.maps[k][1], q[k]) for k in range(3)]
            if self.w >= 1 - 1e-12:
                out = iso
            else:                                   # 渐进混合：小样本在校准经验与原始模型间折中
                out = [(1 - self.w) * q[k] + self.w * iso[k] for k in range(3)]
        elif self.mode == "shrink" and self.shrink > 0:
            w = self.shrink
            out = [(1 - w) * q[k] + w / 3.0 for k in range(3)]
        else:
            return q
        return self._floor_norm(out, q)


_CALIB = {"W": None, "H": None}
_CALIB_STRAT = {"W": {}, "H": {}}   # v5.8.3建议③：实力差分层校准器 {market:{stratum:ProbCalibrator}}
def load_calibrators(path=CALIB_STORE, verbose=False):
    """main赛前/赛后开头调用：从样本库装载W/H校准器到全局。样本不足也装载(走温和收缩)。
    v5.8.3：同时按实力差层(均衡/胶着/悬殊)构建分层校准器；某层样本≥CALIB_STRAT_MIN_N才建桶,否则不建(应用时回退全局)。"""
    recs = calib_load(path).get("records", [])
    # v5.8.6 H独立校准：H校准器只用独立让球源(Pinnacle3WayH)样本训练，剔除matrix回退换皮样本(其概率只是spf重参数化,
    # 会污染让球保序回归)；W校准器口径不变。老样本未存_model_indep，以记录在案的hcap_src白名单为准、可审计。
    _nH_all = sum(1 for r in recs if r.get("market") == "H")
    recs_H = ([r for r in recs if r.get("market") != "H" or r.get("hcap_src") in H_INDEP_SRCS]
              if H_CALIB_INDEP_ONLY else recs)
    _nH_indep = sum(1 for r in recs_H if r.get("market") == "H")
    _CALIB["W"] = ProbCalibrator(recs, "W")
    _CALIB["H"] = ProbCalibrator(recs_H, "H")
    _CALIB_STRAT["W"].clear(); _CALIB_STRAT["H"].clear()
    for mk in "WH":
        _base = recs if mk == "W" else recs_H    # v5.8.6 分层H同样只用独立源样本
        for sname in ("均衡", "胶着", "悬殊"):
            sub = [r for r in _base if r.get("market") == mk and r.get("stratum") == sname]
            if len(sub) >= CALIB_STRAT_MIN_N:   # 小样本不建桶=应用时回退全局,杜绝分层过拟合/双重收缩
                _CALIB_STRAT[mk][sname] = ProbCalibrator(sub, mk, min_n=CALIB_STRAT_MIN_N)
    if H_CALIB_INDEP_ONLY and _nH_all:
        print(f"  · v5.8.6 H独立校准：让球校准仅用独立源样本 {_nH_indep}/{_nH_all}（剔除{_nH_all-_nH_indep}条matrix换皮样本）")
    if verbose:
        for mk in "WH":
            c = _CALIB[mk]
            if c.mode == "isotonic":
                tag = f"正则化保序校准(先验α={CALIB_ISO_PRIOR:g},混合w={c.w:.2f},地板{CALIB_FLOOR:g})"
            else:
                tag = f"温和收缩w={c.shrink:.2f}(样本{c.n}<{CALIB_MIN_ISOTONIC})"
            print(f"  · 概率校准[{mk}]：{c.n}场 → {tag}")
            if CALIB_STRATIFY_ENABLED:
                bt = ", ".join(f"{s}:{_CALIB_STRAT[mk].get(s).n if _CALIB_STRAT[mk].get(s) else 0}场"
                               for s in ("均衡", "胶着", "悬殊"))
                print(f"    分层校准[{mk}]已启用（{bt}；不足{CALIB_STRAT_MIN_N}的层回退全局）")
    return _CALIB


def calib_apply(market, q, lh=None, la=None, stratum=None):
    """analyze最终对外概率处调用；未装载/关开关则恒等返回。
    v5.8.3建议③：CALIB_STRATIFY_ENABLED且能定实力差层时优先该层校准器；该层样本不足/无桶则回退全局(等价旧版)。"""
    if not CALIB_ENABLED:
        return q
    if CALIB_STRATIFY_ENABLED:
        if stratum is None and lh is not None and la is not None:
            stratum = strength_band(abs(float(lh) - float(la)))
        if stratum:
            cs = _CALIB_STRAT.get(market, {}).get(stratum)
            if cs is not None:
                return cs.apply(q)
            # 该实力差层样本不足→落到全局校准器（不做双重收缩）
    c = _CALIB.get(market)
    return c.apply(q) if c else q


def calib_append_from_snapshot(snap, results, path=CALIB_STORE, verbose=True):
    """P2闭环核心：赛后结算时，把赛前锁存的(W/H)三方向预测概率与实际方向自动写入样本库(去重)。
    W用快照one；H优先用快照hcap(v5.7起锁存)，旧快照无hcap则用lh/la/hand重算矩阵让球概率(诚实降级)。"""
    batch = str(snap.get("batch", "auto")); ts = _bj_now_naive().strftime("%Y-%m-%d %H:%M:%S")
    recs = []
    for x in snap.get("matches", []):
        no = str(x.get("no")); res = results.get(no) or results.get(no.lstrip("0") or "0")
        ij = _res_ij(res) if res else None
        if ij is None:
            continue
        i, j = ij; hand = x.get("hand")
        aw = 0 if i > j else (1 if i == j else 2)
        # v5.8.3建议①③：W/H样本统一补攒 λ与实力差分层键(快照matches本就锁存lh/la；老样本缺则=None)
        _lh, _la = x.get("lh"), x.get("la")
        _lt = round(float(_lh) + float(_la), 4) if (_lh is not None and _la is not None) else None
        _dl = round(abs(float(_lh) - float(_la)), 4) if (_lh is not None and _la is not None) else None
        _str = strength_band(_dl) if _dl is not None else None
        if x.get("one"):
            recs.append(dict(batch=batch, no=no, market="W", home=x.get("home"), away=x.get("away"),
                             probs=[float(v) for v in x["one"]], pick_dir=max(range(3), key=lambda k: x["one"][k]),
                             actual_dir=aw, fuse_mode=x.get("fuse_mode"), ts=ts,
                             lh=_lh, la=_la, lt=_lt, dl=_dl, stratum=_str))
        if hand is not None:
            hq = x.get("hcap")
            if not hq and x.get("lh") is not None and x.get("la") is not None:
                try:
                    hq = list(handicap(matrix(float(x["lh"]), float(x["la"])), int(hand)))
                except Exception:
                    hq = None
            if hq:
                s = i + int(hand) - j; ah = 0 if s > 0 else (1 if s == 0 else 2)
                recs.append(dict(batch=batch, no=no, market="H", home=x.get("home"), away=x.get("away"),
                                 probs=[float(v) for v in hq], pick_dir=max(range(3), key=lambda k: hq[k]),
                                 actual_dir=ah, hcap_src=x.get("hcap_src"),
                                 hand=hand, hand_abs=(abs(int(hand)) if hand is not None else None),
                                 lh=x.get("lh"), la=x.get("la"), ts=ts,   # v5.8.2补攒让球档+λ，供日后分让球档τ的赛果LOO回测(老样本缺这几项=None)
                                 lt=_lt, dl=_dl, stratum=_str))  # v5.8.3补总λ/实力差/分层键，供ρ自适应与分层校准回测
    add = calib_append(recs, path)
    if verbose:
        allr = calib_load(path)["records"]
        nW = sum(1 for r in allr if r["market"] == "W"); nH = sum(1 for r in allr if r["market"] == "H")
        line(); print(f"§v5.7.1 校准样本自动攒库：本快照新增 {add} 条；累计 W(1X2) {nW} 场、H(让球) {nH} 场"
                      f"（≥{CALIB_MIN_ISOTONIC}场自动切换isotonic保序校准）。"); line()
    return add


def calib_report(path=CALIB_STORE, verbose=True):
    """样本库概况：分市场样本量、首选命中、多分类Brier、对数损失LogLoss、极端输出率、当前校准方式/混合权重。"""
    recs = calib_load(path)["records"]; out = {}
    for mk, label in (("W", "1X2胜平负"), ("H", "让球胜平负")):
        rs = [r for r in recs if r["market"] == mk]
        if not rs:
            out[mk] = None; continue
        n = len(rs); hit = sum(1 for r in rs if max(range(3), key=lambda k: r["probs"][k]) == r["actual_dir"])
        bri = sum(sum((r["probs"][k] - (1 if k == r["actual_dir"] else 0)) ** 2 for k in range(3)) for r in rs) / n
        ll = sum(-math.log(max(1e-12, r["probs"][r["actual_dir"]])) for r in rs) / n   # v5.7.9 原始概率对数损失
        c = ProbCalibrator(recs, mk)
        # v5.7.9 校准后概率的Brier/LogLoss/极端率（in-sample，供与原始对照；客观泛化见 calib_quality_report 的交叉验证）
        cb = cl = ex = 0.0
        for r in rs:
            q = c.apply(r["probs"]); y = r["actual_dir"]
            cb += sum((q[k] - (1 if k == y else 0)) ** 2 for k in range(3)); cl += -math.log(max(1e-12, q[y]))
            ex += 1 if (min(q) < 0.02 or max(q) > 0.98) else 0
        cb /= n; cl /= n; ex /= n
        out[mk] = dict(n=n, hit=hit / n, brier=bri, logloss=ll, brier_cal=cb, logloss_cal=cl,
                       extreme=ex, mode=c.mode, shrink=c.shrink, w=c.w)
        if verbose:
            if c.mode == "isotonic":
                how = f"正则化保序(w={c.w:.2f})"
            else:
                how = f"温和收缩w={c.shrink:.2f}(攒够{CALIB_MIN_ISOTONIC}场上保序)"
            print(f"  [{label}] 样本{n}场 首选命中{hit}/{n}={hit/n*100:.0f}% "
                  f"原始Brier={bri:.3f}/LogLoss={ll:.3f} → 校准后Brier={cb:.3f}/LogLoss={cl:.3f} "
                  f"极端率={ex*100:.0f}% 校准：{how}")
    return out


def calib_quality_report(path=CALIB_STORE, verbose=True):
    """v5.7.9 新增：校准层客观质量审计（防in-sample自欺）。
    对W/H分别给 ①原始概率 ②现校准器 在【留一法LOO(样本≥该市场数-1训练)】下的 Brier/LogLoss/首选命中/极端率，
    以及校准翻转原始首选方向的次数与净对错。校准只有在交叉验证下不劣于原始、且不制造极端概率时才值得保留。"""
    import math as _math
    recs_all = calib_load(path)["records"]; out = {}
    if verbose:
        line(); print("§v5.7.9 校准质量交叉验证（留一法LOO：每次留1场、其余训练，逐场评估）"); line()
    for mk, label in (("W", "1X2胜平负"), ("H", "让球胜平负")):
        idx = [t for t, r in enumerate(recs_all) if r.get("market") == mk and r.get("probs")
               and r.get("actual_dir") is not None]
        if len(idx) < 5:
            out[mk] = None
            if verbose: print(f"  [{label}] 样本不足({len(idx)}场)，跳过交叉验证。")
            continue
        def _agg(pairs):
            n = len(pairs); b = l_ = h = ex = 0.0
            for q, y in pairs:
                b += sum((q[k] - (1 if k == y else 0)) ** 2 for k in range(3))
                l_ += -_math.log(max(1e-12, q[y])); h += (max(range(3), key=lambda k: q[k]) == y)
                ex += 1 if (min(q) < CALIB_FLOOR + 1e-9 or max(q) > 1 - CALIB_FLOOR - 1e-9) else 0
            return dict(n=n, brier=b / n, logloss=l_ / n, acc=h / n, extreme=ex / n)
        raw_pairs, cal_pairs = [], []; flip = [0, 0, 0]   # [翻转数, 翻后改对, 翻后改错(原本对)]
        for t in idx:
            train = [recs_all[i] for i in idx if i != t]; r = recs_all[t]; y = r["actual_dir"]
            c = ProbCalibrator(train, mk)
            q0 = [float(x) for x in r["probs"]]; q1 = c.apply(q0)
            raw_pairs.append((q0, y)); cal_pairs.append((q1, y))
            d0, d1 = max(range(3), key=lambda k: q0[k]), max(range(3), key=lambda k: q1[k])
            if d0 != d1:
                flip[0] += 1; flip[1] += (1 if d1 == y else 0); flip[2] += (1 if d0 == y else 0)
        a0, a1 = _agg(raw_pairs), _agg(cal_pairs)
        out[mk] = dict(raw=a0, calibrated=a1, flip=flip, n=len(idx))
        if verbose:
            db, dl = a1["brier"] - a0["brier"], a1["logloss"] - a0["logloss"]
            _TOL = 2e-3   # LOO噪声容限：单指标±0.002内视为持平，只有Brier与LogLoss同时劣化超容限才告警
            if db > _TOL and dl > _TOL:
                verdict = "⚠交叉验证双指标劣化,应减弱校准(降w/增先验)"
            elif db < -1e-3 or dl < -1e-3:
                verdict = "✓校准有效(交叉验证改善)"
            else:
                verdict = "≈与原始基本持平(噪声级,维持当前强度)"
            print(f"  [{label}] {len(idx)}场 LOO：原始 Brier {a0['brier']:.3f}/LL {a0['logloss']:.3f}/命中{a0['acc']*100:.0f}%"
                  f" → 校准后 Brier {a1['brier']:.3f}({db:+.3f})/LL {a1['logloss']:.3f}({dl:+.3f})/命中{a1['acc']*100:.0f}%/极端{a1['extreme']*100:.0f}%")
            print(f"      首选方向被校准翻转 {flip[0]} 次：翻后改对 {flip[1]}、把原本对的翻错 {flip[2]}（净{flip[1]-flip[2]:+d}）；{verdict}")
    if verbose: line()
    return out


# ==================== v5.8.2 分让球档 τ 真实赛果 LOO/LOBO 回测（攒够样本后给 HANDICAP_DIAG_TAU_BY 定档）====================
def _hcap3_from_lambda(lh, la, hand, tau, rho=RHO_DC):
    """用赛前λ在指定τ下【重建矩阵源】让球三项[让胜,让平,让负]。τ回测必须用它，不能用样本存的probs——
    那些在有锐线时是Pinnacle市场锚定值，无法反映τ变化。"""
    M = dixon_coles(matrix(float(lh), float(la)), float(lh), float(la), rho)
    M = handicap_diag_boost(M, int(hand), tau)
    return list(handicap(M, int(hand)))


def _tau_score_rows(rows, tau):
    """对一组(lh,la,hand,y)样本在固定τ下返回 brier/logloss/acc/让平偏差(让平预测-实际)。"""
    nb = nl = nh = nd = 0.0
    for lh, la, hand, y in rows:
        h = _hcap3_from_lambda(lh, la, hand, tau)
        nb += sum((h[k] - (1 if k == y else 0)) ** 2 for k in range(3))
        nl += -math.log(max(1e-12, h[y])); nh += (max(range(3), key=lambda k: h[k]) == y)
        nd += h[1] - (1 if y == 1 else 0)
    n = max(1, len(rows))
    return dict(brier=nb / n, logloss=nl / n, acc=nh / n, draw_bias=nd / n, n=len(rows))


# ==================== v5.8.3 建议①ρ自适应 / 建议③分层校准 的真实赛果回测定标 ====================
def _w1x2_from_lambda(lh, la, rho):
    """用赛前λ在指定ρ下重建1X2三项（ρ回测专用；不叠τ，τ属让球层）。"""
    M = dixon_coles(matrix(float(lh), float(la)), float(lh), float(la), rho)
    return list(onextwo(M))


def _rho_score_rows(rows, rho_mode):
    """rows=(lh,la,y)；rho_mode='dc'固定RHO_DC / 'adaptive'自适应 / 数值=指定ρ。返回Brier/LL/命中。"""
    nb = nl = nh = 0.0
    for lh, la, y in rows:
        rho = _rho_adaptive_value(lh, la) if rho_mode == "adaptive" else (RHO_DC if rho_mode == "dc" else rho_mode)
        p = _w1x2_from_lambda(lh, la, rho)
        nb += sum((p[k] - (1 if k == y else 0)) ** 2 for k in range(3))
        nl += -math.log(max(1e-12, p[y])); nh += (max(range(3), key=lambda k: p[k]) == y)
    n = max(1, len(rows))
    return dict(brier=nb / n, logloss=nl / n, acc=nh / n, n=len(rows))


def rho_adaptive_report(path=CALIB_STORE, grid=(-0.16, -0.12, -0.08, -0.04, 0.0), verbose=True):
    """v5.8.3建议①定标：用真实1X2赛果(W样本，v5.8.3起自动补攒lh/la)对比
    现状固定ρ=RHO_DC vs ρ自适应(现系数) vs 网格最优固定ρ 的Brier/LogLoss/命中。
    带λ样本<15不结论(老W样本无λ会被跳过并计数)；只给是否值得开 RHO_ADAPTIVE_ENABLED 的证据，绝不自动改参。"""
    recs = calib_load(path).get("records", [])
    rows = [(float(r["lh"]), float(r["la"]), int(r["actual_dir"])) for r in recs
            if r.get("market") == "W" and r.get("lh") is not None and r.get("la") is not None
            and r.get("actual_dir") is not None]
    n = len(rows); out = dict(n=n)
    if verbose:
        line(); print("§v5.8.3 ρ自适应 真实赛果回测（1X2；样本须v5.8.3起带λ）")
    if n < 15:
        if verbose:
            print(f"  ℹ 带λ的W样本仅{n}场(<15)，不足以评估ρ自适应，继续攒样(无λ老样本已跳过)；维持RHO_ADAPTIVE_ENABLED=False。"); line()
        out["action"] = "样本不足，维持关闭"; return out
    base = _rho_score_rows(rows, "dc"); adapt = _rho_score_rows(rows, "adaptive")
    gres = {g: _rho_score_rows(rows, g) for g in grid}
    best_g = min(grid, key=lambda g: gres[g]["brier"])
    db, dl = adapt["brier"] - base["brier"], adapt["logloss"] - base["logloss"]
    better = db < -0.002 and dl <= 0
    out.update(base=base, adaptive=adapt, grid=gres, best_fixed_rho=best_g,
               d_brier=db, d_logloss=dl, adaptive_better=better)
    if verbose:
        print(f"  样本{n}场 | 现状固定ρ={RHO_DC:+.2f}: Brier{base['brier']:.4f}/LL{base['logloss']:.4f}/命中{base['acc']*100:.0f}%")
        print(f"          ρ自适应(现系数): Brier{adapt['brier']:.4f}({db:+.4f})/LL{adapt['logloss']:.4f}({dl:+.4f})/命中{adapt['acc']*100:.0f}%")
        print(f"  网格最优固定ρ={best_g:+.2f}: Brier{gres[best_g]['brier']:.4f}")
        print("  ✅ 自适应双指标同向改善(>0.002)，可试 RHO_ADAPTIVE_ENABLED=True 并做LOBO复核" if better
              else "  ⏸ 自适应未稳定优于固定ρ(改善<0.002或LL反向)，维持关闭")
        line()
    out["action"] = "可试开启并LOBO复核" if better else "维持关闭"
    return out


def calib_stratified_report(path=CALIB_STORE, market="W", verbose=True):
    """v5.8.3建议③定标：按实力差层(均衡/胶着/悬殊)对比 全局校准 vs 分层校准 的留一(LOO)Brier/LogLoss。
    线上规则一致：某层样本<CALIB_STRAT_MIN_N时该场回退全局。达标层不足2个或总量不足不结论，绝不自动改参。"""
    recs = [r for r in calib_load(path).get("records", [])
            if r.get("market") == market and r.get("probs") and r.get("actual_dir") is not None]
    layers = {s: [r for r in recs if r.get("stratum") == s] for s in ("均衡", "胶着", "悬殊")}
    n = len(recs); counts = {s: len(v) for s, v in layers.items()}
    if verbose:
        line(); print(f"§v5.8.3 [{market}]分层校准LOO回测：总{n}场，层计数 " +
                      " / ".join(f"{s}{counts[s]}" for s in ("均衡", "胶着", "悬殊")))
    ready = [s for s in layers if len(layers[s]) >= CALIB_STRAT_MIN_N]
    if len(ready) < 2:
        if verbose:
            print(f"  ℹ 达到{CALIB_STRAT_MIN_N}场的实力差层不足2个(现达标:{ready or '无'})，分层无统计意义，维持CALIB_STRATIFY_ENABLED=False。"); line()
        return dict(n=n, layers=counts, action="样本不足，维持全局")

    def score(use_strat):
        nb = nl = 0.0
        for k, r in enumerate(recs):
            rest = recs[:k] + recs[k + 1:]; q = r["probs"]; y = int(r["actual_dir"])
            cal = ProbCalibrator(rest, market)
            if use_strat and r.get("stratum") in ready:
                sub = [z for z in rest if z.get("stratum") == r["stratum"]]
                if len(sub) >= CALIB_STRAT_MIN_N:
                    cal = ProbCalibrator(sub, market, min_n=CALIB_STRAT_MIN_N)
            p = cal.apply(q)
            nb += sum((p[t] - (1 if t == y else 0)) ** 2 for t in range(3))
            nl += -math.log(max(1e-12, p[y]))
        return dict(brier=nb / max(1, n), logloss=nl / max(1, n), n=n)

    g, st = score(False), score(True)
    db, dl = st["brier"] - g["brier"], st["logloss"] - g["logloss"]
    better = db < -0.002 and dl <= 0
    if verbose:
        print(f"  LOO 全局: Brier{g['brier']:.4f}/LL{g['logloss']:.4f}")
        print(f"  LOO 分层: Brier{st['brier']:.4f}({db:+.4f})/LL{st['logloss']:.4f}({dl:+.4f})")
        print("  ✅ 分层稳定改善，可试 CALIB_STRATIFY_ENABLED=True" if better else "  ⏸ 分层未稳定优于全局，维持关闭"); line()
    return dict(n=n, layers=counts, global_=g, strat=st, d_brier=db, d_logloss=dl,
                stratified_better=better, action="可试开启" if better else "维持全局")

_TAU_LOG_COLS = ["run_ts", "hand_abs", "n", "draw_freq", "tau_insample", "tau_baseline",
                 "loo_brier", "loo_logloss", "loo_acc", "base_brier", "base_logloss", "base_acc",
                 "rel_brier_pct", "rel_logloss_pct", "lobo", "changed", "suggest_tau", "action"]


def _tau_by_persist(out, run_ts, baseline, grid, min_n, improve, miss_lam, log_csv, latest_json, verbose=False):
    """分档τ回测落两份文件(统一DATA_DIR、IO失败只告警不抛)：滚动台账CSV(每档追加一行,看证据演变)+最新建议JSON(覆盖)。"""
    import csv as _csv_tau
    saved = {"csv": None, "json": None}
    try:   # 最新建议 JSON（覆盖写；无样本也写，留"跑过但暂无证据"痕）
        sug = {int(k): round(float(v), 2) for k, v in out.get("_suggest", {}).items()}
        payload = {"ts": run_ts, "baseline": baseline, "grid": list(grid), "min_n": min_n,
                   "improve": improve, "missing_lambda_skipped": miss_lam,
                   "by_handicap": {str(k): v for k, v in out.items() if isinstance(k, int)},
                   "suggest_for_CONFIG": sug,  # 注：JSON标准会把键存成字符串"1"，要粘进Python请用下方 copy_paste_CONFIG(保留整数键)
                   "copy_paste_CONFIG": "HANDICAP_DIAG_TAU_BY = " + (str(sug) if sug else "{}"),
                   "howto": "把 copy_paste_CONFIG 整行拷到CONFIG替换HANDICAP_DIAG_TAU_BY即可；空{}=全档维持baseline；缺省档自动回退baseline"}
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        saved["json"] = latest_json
    except Exception as e:
        if verbose:
            print(f"  ⚠分档τ最新建议JSON写入失败(不影响回测)：{e}")
    try:   # 滚动台账 CSV（追加；不存在先写 utf-8-sig 表头，Excel直接打开）；无分档样本(空库)不建空台账，只由JSON留痕
        hkeys = sorted(x for x in out if isinstance(x, int))
        if hkeys:
            newfile = not _pp.exists(log_csv)
            with open(log_csv, "a", newline="", encoding="utf-8-sig") as f:
                w = _csv_tau.DictWriter(f, fieldnames=_TAU_LOG_COLS)
                if newfile:
                    w.writeheader()
                for k in hkeys:
                    d = out[k]; loo = d.get("loo") or {}; bse = d.get("loo_baseline") or {}
                    changed = abs(d.get("pick", baseline) - baseline) > 1e-9
                    g = lambda dd, key, nd: (round(dd[key], nd) if dd else "")
                    w.writerow({"run_ts": run_ts, "hand_abs": k, "n": d["n"], "draw_freq": round(d["draw_freq"], 4),
                                "tau_insample": d["tau_insample"], "tau_baseline": baseline,
                                "loo_brier": g(loo, "brier", 5), "loo_logloss": g(loo, "logloss", 5), "loo_acc": g(loo, "acc", 4),
                                "base_brier": g(bse, "brier", 5), "base_logloss": g(bse, "logloss", 5), "base_acc": g(bse, "acc", 4),
                                "rel_brier_pct": round(100 * d.get("rel_brier", 0), 2),
                                "rel_logloss_pct": round(100 * d.get("rel_logloss", 0), 2),
                                "lobo": ("同向" if d.get("lobo_ok") is True else "反向" if d.get("lobo_ok") is False else "单批略"),
                                "changed": int(changed), "suggest_tau": d.get("pick", baseline),
                                "action": ("改档" if changed else ("维持:样本不足" if d["n"] < min_n else "维持:证据不足"))})
            saved["csv"] = log_csv
    except Exception as e:
        if verbose:
            print(f"  ⚠分档τ台账CSV写入失败(不影响回测)：{e}")
    return saved


def tau_by_handicap_report(path=CALIB_STORE, grid=None, baseline=HANDICAP_DIAG_TAU,
                           min_n=TAU_BY_MIN_N, improve=TAU_BY_IMPROVE, verbose=True,
                           save=True, log_csv=TAU_BY_HCAP_LOG_CSV, latest_json=TAU_BY_HCAP_LATEST):
    """分让球档τ的【真实赛果】交叉验证，输出可直接拷给 HANDICAP_DIAG_TAU_BY 的建议字典(out['_suggest'])。
    数据要求：H(让球)校准样本须同时带 lh/la/hand/actual_dir（v5.8.2起赛后自动补攒；种子/v5.8.1前老样本缺λ会被跳过并计数）。
    方法(防in-sample自欺，与calib_quality_report同思路)：每档①全样本τ网格找in-sample最优点；
      ②LOO留一：每次留1场、其余样本选τ、评留出场，汇总自适应τ留出指标并与固定baseline(=2.0)对比；
      ③LOBO留批：按batch整批留出做同向确认。建议规则保守：样本<min_n维持默认；否则LOO的Brier相对改善≥improve
      且LOBO不反向才建议改档，任一不满足都维持2.0——分档τ必须被交叉验证支持，绝不因in-sample好看就改。
    落盘(save=True,统一走DATA_DIR、失败自容错不影响主流程)：①tau_by_handicap_log.csv滚动台账,每次运行每档追加一行
      快照(utf-8-sig,Excel可直接打开,看证据随样本量演变)；②tau_by_handicap_latest.json覆盖写最新全量结果+suggest_for_CONFIG。"""
    grid = grid or TAU_GRID_BY_HCAP
    recs = calib_load(path)["records"]
    by, miss_lam = {}, 0
    for r in recs:
        if r.get("market") != "H" or r.get("actual_dir") is None or r.get("hand") is None:
            continue
        lh, la = r.get("lh"), r.get("la")
        if lh is None or la is None:
            miss_lam += 1; continue
        try:
            by.setdefault(abs(int(r["hand"])), []).append(
                (float(lh), float(la), int(r["hand"]), int(r["actual_dir"]), str(r.get("batch"))))
        except Exception:
            continue
    suggest, out = {}, {}
    run_ts = _bj_now_naive().strftime("%Y-%m-%d %H:%M:%S")
    if verbose:
        line(); print(f"§v5.8.2 分让球档 τ 真实赛果回测（LOO留一+LOBO留批；固定基准τ={baseline:.2f}；网格"
                      f"{grid[0]:.2f}..{grid[-1]:.2f}）"); line()
        if miss_lam:
            print(f"  ℹ {miss_lam}条H老样本缺λ(种子/v5.8.2前)无法重建矩阵、已跳过；v5.8.2起新攒样本自动带λ。")
    if not by:
        if verbose:
            print(f"  暂无可用于τ回测的分档样本(需赛后攒含λ的H记录)，全部维持 HANDICAP_DIAG_TAU={baseline:.2f}。"); line()
        out["_suggest"] = suggest
        if save:
            sv = _tau_by_persist(out, run_ts, baseline, grid, min_n, improve, miss_lam, log_csv, latest_json, verbose)
            if verbose and sv["json"]:
                print(f"  已留痕最新状态：{sv['json']}（台账待有分档样本后写入 {sv['csv'] or log_csv}）")
        return out
    for ncap in sorted(by):
        S = by[ncap]; nr = len(S)
        core = [(a, c, h, y) for a, c, h, y, _ in S]
        ins = [(t, _tau_score_rows(core, t)) for t in grid]
        t_in = min(ins, key=lambda z: z[1]["brier"])[0]
        draw_freq = sum(1 for _, _, _, y, _ in S if y == 1) / nr
        loo = base = None; lobo_ok = None
        if nr >= 2:   # LOO留一（nr=1无法留空训练）
            ad, bd, loo_taus = [], [], []
            for i in range(nr):
                tr = [core[k] for k in range(nr) if k != i]
                tstar = min(grid, key=lambda t: _tau_score_rows(tr, t)["brier"]); loo_taus.append(tstar)
                ad.append(_tau_score_rows([core[i]], tstar)); bd.append(_tau_score_rows([core[i]], baseline))
            avg = lambda lst, key: sum(x[key] for x in lst) / len(lst)
            loo = dict(brier=avg(ad, "brier"), logloss=avg(ad, "logloss"), acc=avg(ad, "acc"))
            base = dict(brier=avg(bd, "brier"), logloss=avg(bd, "logloss"), acc=avg(bd, "acc"))
            batches = sorted(set(x[4] for x in S))
            if len(batches) >= 2:   # LOBO留批同向确认
                lad, lbd = [], []
                for bb in batches:
                    tr = [(a, c, h, y) for a, c, h, y, b0 in S if b0 != bb]
                    te = [(a, c, h, y) for a, c, h, y, b0 in S if b0 == bb]
                    if not tr or not te: continue
                    tstar = min(grid, key=lambda t: _tau_score_rows(tr, t)["brier"])
                    lad.append(_tau_score_rows(te, tstar)); lbd.append(_tau_score_rows(te, baseline))
                if lad:
                    lobo_ok = (sum(x["brier"] for x in lad) / len(lad)) <= (sum(x["brier"] for x in lbd) / len(lbd) + 1e-9)
        rel_b = ((base["brier"] - loo["brier"]) / (base["brier"] + 1e-12)) if loo else 0.0
        rel_l = ((base["logloss"] - loo["logloss"]) / (base["logloss"] + 1e-12)) if loo else 0.0
        cautious = "（样本<30噪声大,建议继续攒后复核）" if nr < 30 else ""
        if nr < min_n:
            pick, verdict = baseline, f"样本{nr}<{min_n}不足，维持默认{baseline:.2f}(继续攒)"
        elif rel_b >= improve and rel_l > 0 and lobo_ok is not False:
            # 双指标门(对齐calib_quality_report)：Brier相对改善达阈值 且 LogLoss同向改善 且 LOBO不反向，才建议改档
            pick, verdict = t_in, (f"LOO双指标改善 Brier{rel_b * 100:.1f}%/LL{rel_l * 100:.1f}%"
                                   + ("且LOBO同向" if lobo_ok else "(单批无LOBO)") + f"→建议τ={t_in:.2f}{cautious}")
        else:
            if lobo_ok is False:
                why = "LOBO反向"
            elif rel_l <= 0:
                why = f"LogLoss未同向改善({rel_l * 100:+.1f}%)"
            else:
                why = f"Brier改善{rel_b * 100:.1f}%未达{improve * 100:.0f}%"
            pick, verdict = baseline, f"{why}→维持{baseline:.2f}"
        if abs(pick - baseline) > 1e-9:
            suggest[ncap] = pick
        out[ncap] = dict(n=nr, draw_freq=draw_freq, tau_insample=t_in, loo=loo, loo_baseline=base,
                         lobo_ok=lobo_ok, rel_brier=rel_b, rel_logloss=rel_l,
                         pick=pick, verdict=verdict, changed=abs(pick - baseline) > 1e-9)
        if verbose:
            if loo:
                print(f"  [让{ncap}球] {nr}场 实际让平{draw_freq * 100:.0f}%｜全样本最优τ={t_in:.2f}｜LOO 自适应 "
                      f"Brier{loo['brier']:.3f}/LL{loo['logloss']:.3f}/命中{loo['acc'] * 100:.0f}% vs 固定{baseline:.2f} "
                      f"Brier{base['brier']:.3f}/LL{base['logloss']:.3f}/命中{base['acc'] * 100:.0f}%"
                      + (f"｜LOBO{'同向✓' if lobo_ok else '反向✗'}" if lobo_ok is not None else "｜LOBO(单批,略)"))
            else:
                print(f"  [让{ncap}球] {nr}场 实际让平{draw_freq * 100:.0f}%｜全样本最优τ={t_in:.2f}（样本<2无法LOO）")
            print(f"        → {verdict}")
    if verbose:
        print("  可直接填 CONFIG：HANDICAP_DIAG_TAU_BY = "
              + (str({int(k): round(float(v), 2) for k, v in suggest.items()}) if suggest else "{}")
              + f"  # 缺省档自动回退{baseline:.2f}")
        line()
    out["_suggest"] = suggest
    if save:
        sv = _tau_by_persist(out, run_ts, baseline, grid, min_n, improve, miss_lam, log_csv, latest_json, verbose)
        if verbose:
            if sv["csv"]:
                print(f"  已落盘：滚动台账 {sv['csv']}（本次每档追加1行）；最新建议 {sv['json'] or '（写入失败）'}")
            line()
    return out


def _plot_tau_convergence(out, baseline, improve, png):
    """读收敛结论出双面板PNG(建议τ轨迹 + LOO改善%轨迹)。Agg后端无显示也能存；图内用英文标签免中文字体乱码。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    hands = sorted(k for k in out if isinstance(k, int))
    if not hands:
        return None
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    cmap = plt.get_cmap("tab10")
    for idx, k in enumerate(hands):
        d = out[k]; c = cmap(idx % 10)
        ax1.plot(d["n_path"], d["tau_path"], "-o", color=c, label=f"handicap {k} [{d['status']}]")
        ax2.plot(d["n_path"], d["rel_path"], "-o", color=c, label=f"handicap {k}")
    ax1.axhline(baseline, ls="--", color="gray", lw=1, label=f"baseline tau={baseline:g}")
    ax1.set_ylabel("suggested tau"); ax1.set_title("Per-handicap suggested tau vs settled-sample size n")
    ax1.grid(alpha=.3); ax1.legend(fontsize=8)
    ax2.axhline(improve * 100, ls="--", color="red", lw=1, label=f"improve gate {improve * 100:g}%")
    ax2.axhline(0, color="k", lw=.6)
    ax2.set_ylabel("LOO Brier improve %"); ax2.set_xlabel("sample size n (settled H matches)")
    ax2.grid(alpha=.3); ax2.legend(fontsize=8)
    plt.tight_layout()
    if png is None:
        png = TAU_BY_HCAP_CONV_PNG
    fig.savefig(png, dpi=130); plt.close(fig)
    return png


def tau_by_convergence_report(csv_path=TAU_BY_HCAP_LOG_CSV, png=None, baseline=HANDICAP_DIAG_TAU,
                              stable_n=TAU_STABLE_MIN_N, window=TAU_STABLE_WINDOW,
                              improve=TAU_BY_IMPROVE, make_figure=True, verbose=True):
    """读 tau_by_handicap_log.csv 滚动台账，看各让球档'建议τ'随样本量n的收敛轨迹，并自动判定哪档已稳定、可定档。
    状态机：不足(n<stable_n) / 抖动未收敛(最近window次建议不一致或临门指标不达标) / 稳定维持(收敛回baseline=无需分档)
    / 可定档(n≥stable_n、最近window次一致收敛到非baseline、且末次改善达阈值且LOBO不反向)。
    返回 {档: {n,n_path,tau_path,rel_path,status,set_tau,verdict,runs}, '_suggest':{可定档...}, '_png':路径}；
    make_figure=True且装了matplotlib则出双面板PNG，缺库/失败自动纯文本降级(结论不受影响)。"""
    import csv as _csv_cv
    if not _pp.exists(csv_path):
        if verbose:
            line(); print(f"ℹ未找到τ台账 {csv_path}（赛后跑过 tau_by_handicap_report 才生成），暂无可视化。"); line()
        return {}
    series = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        for r in _csv_cv.DictReader(f):
            try:
                k = int(r["hand_abs"]); n = int(r["n"]); tau = float(r["suggest_tau"])
                rel = float(r["rel_brier_pct"] or 0.0); changed = (str(r["changed"]) == "1"); lobo = r.get("lobo", "")
            except Exception:
                continue
            series.setdefault(k, []).append((r.get("run_ts", ""), n, tau, rel, changed, lobo))
    out = {}
    if verbose:
        line(); print(f"§v5.8.2 分让球档 τ 收敛轨迹（读滚动台账；定档门槛 n≥{stable_n}、最近{window}次建议一致）"); line()
    for k in sorted(series):
        pts = sorted(series[k], key=lambda z: (z[1], z[0]))
        ns = [p[1] for p in pts]; taus = [p[2] for p in pts]; rels = [p[3] for p in pts]
        n_now = pts[-1][1]; tail = pts[-window:] if len(pts) >= window else pts
        tail_tau = [p[2] for p in tail]; same = len(set(round(t, 3) for t in tail_tau)) == 1; last = pts[-1]
        if n_now < stable_n:
            status, set_tau = "不足", baseline
            verdict = f"样本{n_now}<{stable_n}，继续攒（已回测{len(pts)}次）"
        elif not same:
            status, set_tau = "抖动未收敛", baseline
            verdict = (f"最近{len(tail)}次建议τ在{sorted(set(round(t, 2) for t in tail_tau))}间摆动，未收敛"
                       f"→维持{baseline:.2f}继续观察")
        elif abs(tail_tau[0] - baseline) < 1e-9:
            status, set_tau = "稳定维持", baseline
            verdict = f"n={n_now}≥{stable_n}且最近{len(tail)}次都回到baseline→该档无需分档(τ={baseline:.2f})"
        elif last[4] and last[3] >= improve * 100 and last[5] != "反向":
            status, set_tau = "可定档", tail_tau[0]
            verdict = (f"✓n={n_now}≥{stable_n}、最近{len(tail)}次一致收敛到τ={tail_tau[0]:.2f}、末次LOO改善{last[3]:.1f}%"
                       f"({last[5]})→可写入HANDICAP_DIAG_TAU_BY")
        else:
            status, set_tau = "抖动未收敛", baseline
            verdict = (f"τ看似收敛{tail_tau[0]:.2f}但末次改善{last[3]:.1f}%/changed={int(last[4])}/lobo={last[5]}未全达标"
                       f"→维持{baseline:.2f}")
        out[k] = dict(n=n_now, n_path=ns, tau_path=taus, rel_path=rels, status=status,
                      set_tau=set_tau, verdict=verdict, runs=len(pts))
        if verbose:
            traj = "→".join(f"{t:g}(n={n})" for t, n in zip(taus, ns))
            print(f"  [让{k}球] {n_now}场/{len(pts)}次回测  τ轨迹 {traj}")
            print(f"        →【{status}】{verdict}")
    sug = {k: round(out[k]["set_tau"], 2) for k in out if out[k]["status"] == "可定档"}
    png_path = None
    if make_figure:
        try:
            png_path = _plot_tau_convergence(out, baseline, improve, png)
        except Exception as e:
            if verbose:
                print(f"  （绘图跳过：{e}；文本结论不受影响）")
    if verbose:
        print("  当前可定档：HANDICAP_DIAG_TAU_BY = "
              + (str(sug) if sug else f"{{}}（无档达稳定定档标准，全档维持{baseline:.2f}）"))
        if png_path:
            print(f"  收敛图：{png_path}")
        line()
    out["_suggest"] = sug; out["_png"] = png_path
    return out


def inject_open_sharp(A, batch=None, verbose=False):
    """P1-5：用本批次最早一份PinBook历史快照，给每场注入开盘去水概率(_sharp_open_q/_sharp_open_h)，
    供实盘'收盘线不反向'第二确认。多次运行(18/21/临场)自然形成开盘→临场，零额外请求。"""
    try:
        fs = _pb_hist_files(batch)
        if not fs:
            return 0
        first = json.load(open(fs[0], encoding="utf-8"))
        fmap = {(_en_norm(e["h"]), _en_norm(e["a"])): e for e in first.get("events", [])}
        n = 0
        for a in A or []:
            m = a["m"]; eq = []
            for cn in (m.get("home"), m.get("away")):
                en = _cn_en_first(cn)
                if en: eq.append(en)
            # v5.7.2 fix-4：只接受(主,客)同向键；删除旧版(eq[1],eq[0])反向兜底——
            # 反向键对应另一场(两回合/男女足)且spf仍按对方主客顺序,直接注入会对调主胜/客胜概率方向
            fe = fmap.get((eq[0], eq[1])) if len(eq) == 2 else None
            if not fe or not fe.get("spf"):
                continue
            m["_sharp_open_q"] = _devig3(fe["spf"])[0]
            if m.get("hand") is not None:
                tri = (fe.get("eh") or {}).get(str(float(m["hand"])))
                if tri:
                    m["_sharp_open_h"] = _norm3(sharp_fair(tri, 1))
            n += 1
        return n
    except Exception:
        return 0


def sharp_leg_reversal(m, leg):
    """P1-5：判定某条腿方向是否被Pinnacle线移动'反向'(该方向去水概率较早盘掉≥LINE_REVERSE_PP)。
    leg需含方向d与市场mk('W'/'H')。缺早快照不拦(不误伤)。返回(是否反向,描述)。"""
    try:
        d = leg.get("d"); mk = leg.get("mk", "W")
        if d is None:
            return False, ""
        sh = m.get("sharp") if isinstance(m.get("sharp"), dict) else {}
        if mk == "H":
            qnow = _norm3(sharp_fair(sh["rsp"], sh.get("src", 1))) if sh.get("rsp") else None
            qopen = m.get("_sharp_open_h")
        else:
            qnow = _devig3(sh["spf"])[0] if sh.get("spf") else None
            qopen = m.get("_sharp_open_q")
        if not qnow or not qopen:
            return False, ""
        delta = qnow[d] - qopen[d]
        if delta <= -LINE_REVERSE_PP:
            nm = {"W": "1X2", "H": "让球"}.get(mk, mk)
            return True, f"{nm}方向去水概率较早盘{delta*100:+.1f}pp≤-{LINE_REVERSE_PP*100:.0f}pp(收盘线反向)"
        return False, ""
    except Exception:
        return False, ""


def collect_results_sporttery(date=None, verbose=True):
    """P2预留：自动拉竞彩官方完场比分→{编号:'主:客'}。当前官方结果接口对本环境403(计算器接口正常)，
    取不到就返回{}，由POST_RESULTS/RESULTS_TEXT比分串兜底，绝不编造比分。"""
    if not AUTO_RESULTS_ENABLED:
        return {}
    bd = date or (_bj_now_naive() - _td(days=1)).strftime("%Y-%m-%d")
    url = ("https://webapi.sporttery.cn/gateway/jc/football/getMatchResultV1.qry?"
           f"matchPage=1&matchBeginDate={bd}&matchEndDate={bd}&leagueId=&pageSize=60&pageNo=1&channel=c_web")
    try:
        d = json.loads(_http_get(url, referer="https://www.sporttery.cn/jc/zqkj/"))
        out = {}
        for e in (d.get("value", {}) or {}).get("matchResult", []) or []:
            num = str(e.get("matchNumStr") or e.get("num") or "")[-3:]
            hs = e.get("homeGoalNum") if e.get("homeGoalNum") is not None else e.get("homeScore")
            as_ = e.get("awayGoalNum") if e.get("awayGoalNum") is not None else e.get("awayScore")
            if num and hs is not None and as_ is not None:
                out[num] = f"{hs}:{as_}"
        return out
    except Exception as e:
        if verbose:
            print(f"  · 自动完场比分暂不可达({type(e).__name__})，改用 POST_RESULTS/RESULTS_TEXT 比分串兜底（不影响结算）。")
        return {}


def settle_from_snapshot(snap, results, stake_unit=SETTLE_STAKE_UNIT, verbose=True):
    """★【赛后·只读锁存结算】results={no:'主:客'}（90分钟+补时）。首选/终选/投注单/实际票全部取自赛前快照 snap，
    全程不调 analyze、不重算 λ/首选，故赛后赔率怎么漂移都不影响"当时到底推荐/买了什么"。返回结算事实dict。"""
    M = {str(x["no"]): x for x in snap.get("matches", [])}

    def _get_res(no):
        return results.get(no) or results.get(str(no).zfill(3)) or results.get(str(no).lstrip("0") or "0")

    # —— 1) 每场四玩法【锁存首选】命中（命中判定与 settle_review 同用 _leg_settled，保证口径一致）——
    hit = {mk: [0, 0] for mk in "WHST"}
    rows, calib = {}, []
    for no, x in M.items():
        ij = _res_ij(_get_res(no))
        if ij is None:
            continue
        i, j = ij
        hand = x.get("hand")
        lm = {}
        for L in x.get("legs", []):
            mk = L["mk"]
            hit[mk][1] += 1
            ok = bool(_leg_settled(L, i, j, hand))
            hit[mk][0] += 1 if ok else 0
            lm[mk] = dict(pick=L.get("pick"), p=L.get("p"), sp=L.get("sp"), hit=ok,
                          actual=_actual_dir(mk, i, j, hand))
        wL = next((L for L in x.get("legs", []) if L["mk"] == "W"), None)
        if wL:
            calib.append((no, wL.get("p"), wL.get("pick"), lm.get("W", {}).get("actual"),
                          bool(lm.get("W", {}).get("hit"))))
        rows[no] = dict(i=i, j=j, hand=hand, legs=lm)
        # v5.7.6 赛后滚动自算Elo(键=Pinnacle英文规范名,与赛前查询同源;赛后结算即自动积累,长期成型)
        try:
            if ELO_ENABLED: elo_apply_result(x.get("home"),x.get("away"),i,j,lg=x.get("lg"))
            if H2H_ENABLED: h2h_apply_result(x.get("home"),x.get("away"),i,j,date=x.get("time"),lg=x.get("lg"))
        except Exception: pass
    try:
        if ELO_ENABLED and rows: elo_save()
        if H2H_ENABLED and rows: h2h_save()
    except Exception: pass

    def _note_hit(note):
        """一注2串1是否全中；任一场缺比分返回None(待结算)，否则返回True/False。按锁存中文pick判定。"""
        any_missing = False
        for slot in ("1", "2"):
            no = str(note[f"n{slot}"]); L = note[f"L{slot}"]
            r = rows.get(no)
            if r is None:
                any_missing = True
                continue
            ok, _ = _leg_hit_by_pick(L["mk"], L["pick"], r["i"], r["j"], r["hand"])
            if not ok:
                return False
        return None if any_missing else True

    # —— 2) 程序终选注（锁存）：每注 stake_unit、按锁存总赔 spc 兑现 ——
    fin = []
    for note in snap.get("final", []):
        h = _note_hit(note)
        if h is None:
            continue
        spc = note.get("spc")
        pnl = ((spc * stake_unit - stake_unit) if (h and spc) else (-stake_unit if not h else 0.0))
        fin.append((note, h, pnl))
    # —— 3) v5.5 投注单（锁存真实建议金额）兑现 ——
    slip_out = []
    for note in (snap.get("slip") or []):
        h = _note_hit(note)
        if h is None:
            continue
        amt = float(note.get("amt", 0) or 0); spc = note.get("spc")
        ret = (amt * spc) if (h and spc) else 0.0
        slip_out.append((note, h, amt, ret, ret - amt))
    # —— 4) 实际购票台账（真金白银，命中按票面理论返还 payout）——
    tickets = []
    for t in snap.get("actual_tickets", []):
        detail, both, seen = [], True, True
        for no, mk, pk in t.get("legs", []):
            r = rows.get(str(no))
            if r is None:
                seen = False; both = False; detail.append((no, mk, pk, None, None)); continue
            ok, act = _leg_hit_by_pick(mk, pk, r["i"], r["j"], r["hand"])
            both = both and ok
            detail.append((no, mk, pk, act, ok))
        if not seen:
            continue
        stake = float(t.get("stake", 0) or 0)
        payout = (float(t["payout"]) if (both and t.get("payout") is not None) else 0.0)
        tickets.append((t, both, detail, stake, payout, payout - stake))

    if verbose:
        line(); print(f"★ v5.5.2 赛后【锁存】结算（批次 {snap.get('batch')}，赛前锁存于 {snap.get('created_bj')}；"
                      f"已匹配比分 {len(rows)} 场。首选/注单全部取自赛前快照、未做任何重算）"); line()
        if not rows:
            print("  快照内无场次匹配到比分：检查 POST_RESULTS 的编号是否与快照一致。")
        names = {"W": "胜平负锁存首选", "H": "让球锁存首选", "S": "比分锁存首选", "T": "总进球锁存首选"}
        for no in sorted(rows):
            r = rows[no]; x = M[no]
            _ha, _aa = x.get("home"), x.get("away")
            vs = f"{_ha or ''}vs{_aa or ''}" if (_ha or _aa) else (x.get("lg") or "")
            print(f"  [{no}] {vs} 终场 {r['i']}:{r['j']}（hand={r['hand']}）")
            for mk in "WHST":
                z = r["legs"].get(mk)
                if z:
                    print(f"     {MK_LABEL[mk]}：实际[{z['actual']}] vs 锁存首选[{z['pick']}] -> "
                          f"{'命中' if z['hit'] else '落空'}")
        print("  " + "-" * 66)
        print("  四玩法锁存首选命中：")
        for mk in "WHST":
            hh, tt = hit[mk]
            if tt:
                print(f"     {names[mk]}：{hh}/{tt} = {hh/tt*100:.0f}%")
        if fin:
            w = sum(1 for _, hh, _ in fin if hh); pnl = sum(z for _, _, z in fin)
            line(); print(f"  程序【终选注】锁存结算（每注 {stake_unit:g} 元、按锁存票面SP兑现）："
                          f"命中 {w}/{len(fin)}，总盈亏 {pnl:+.1f} 元")
            for note, hh, z in fin:
                print(f"    [{'中' if hh else '失'}] {note.get('role')} "
                      f"{note['n1']}{note['L1']['mk']}[{note['L1']['pick']}] × "
                      f"{note['n2']}{note['L2']['mk']}[{note['L2']['pick']}]  盈亏 {z:+.1f}")
        if slip_out:
            cost = sum(z[2] for z in slip_out); ret = sum(z[3] for z in slip_out)
            w = sum(1 for z in slip_out if z[1])
            line(); print(f"  v5.5【今晚投注单】锁存结算：{w}/{len(slip_out)} 注中，"
                          f"投入 {cost:.0f} 元 / 返还 {ret:.0f} 元 / 净盈亏 {ret-cost:+.1f} 元")
            for note, hh, amt, rrr, net in slip_out:
                print(f"    [{'中' if hh else '失'}] {amt:.0f}元 "
                      f"{note['n1']}{note['L1']['mk']}[{note['L1']['pick']}]×"
                      f"{note['n2']}{note['L2']['mk']}[{note['L2']['pick']}]  返还{rrr:.0f} 净{net:+.1f}")
        if tickets:
            cost = sum(z[3] for z in tickets); ret = sum(z[4] for z in tickets)
            w = sum(1 for z in tickets if z[1])
            line(); print("  ★【实际购票台账】锁存结算（真金白银；2串1全中按票面理论返还，否则0）：")
            for t, both, detail, stake, payout, net in tickets:
                seg = " × ".join(
                    f"{no}{mk}[{pk}]{'中' if ok else ('失' if ok is False else '待')}"
                    for no, mk, pk, _act, ok in detail)
                print(f"    {t.get('name')} {stake:g}元：{seg} -> {'中奖' if both else '未中'}，"
                      f"返还 {payout:g} 元，净 {net:+.1f}")
            print(f"    合计：投入 {cost:g} 元 / 总返还 {ret:g} 元 / 净盈亏 {ret-cost:+.1f} 元 / 命中 {w}/{len(tickets)}")
        if calib:
            line(); print("  胜平负【锁存首选概率】vs 实际 校准：")
            for no, p, pick, act, ok in calib:
                ps = f"{p*100:.0f}%" if p is not None else "—"
                print(f"    [{no}] 首选[{pick}] 概率{ps} -> 实际[{act}] {'✓' if ok else '✗ 落空'}")
            hw = sum(1 for *_x, ok in calib if ok)
            print(f"    胜平负首选方向命中：{hw}/{len(calib)}")
        line()
    return dict(nres=len(rows), hit=hit, final=fin, slip=slip_out, tickets=tickets,
                calib=calib, rows=rows)


def _find_latest_snapshot(batch=None, outdir=SNAPSHOT_DIR):
    """找本批次最近快照：优先 latest_批次.json；否则取 snapshots 下时间最新的 snapshot_*.json。"""
    import os, glob
    if batch and str(batch).lower() != "auto":
        bkey = re.sub(r"[^0-9A-Za-z_-]", "", str(batch))
        p = os.path.join(outdir, f"latest_{bkey}.json")
        if os.path.exists(p):
            return p
    cands = sorted(glob.glob(os.path.join(outdir, "snapshot_*.json")))
    return cands[-1] if cands else None


def settle_snapshot_file(path=None, results=None, batch="auto", stake_unit=SETTLE_STAKE_UNIT):
    """【赛后对外便捷入口】读赛前快照（路径留空=按批次自动找最近）+ 终场比分 -> 只读锁存结算并打印。"""
    results = POST_RESULTS if results is None else results
    path = path or SNAPSHOT_TO_SETTLE or _find_latest_snapshot(batch)
    if not path:
        print("✗ 未找到赛前快照（snapshots/ 为空且未指定 SNAPSHOT_TO_SETTLE）："
              "请先在赛前运行一次生成快照，再做赛后锁存结算。")
        return None
    snap = load_snapshot(path)
    print(f"（读取赛前快照：{path}）")
    return settle_from_snapshot(snap, results, stake_unit=stake_unit)


# ==================== v5.5 每晚投注单：容错覆盖资金分配 + 盈亏情景（自带金额，照单可买）====================
def _bet_floor(x):
    """竞彩2元/注：向下取整到2的整数倍、最低2元。"""
    return max(BET_UNIT, int(x // BET_UNIT) * BET_UNIT)


def _fill_to_bankroll(bets, bankroll, hi_first=True):
    """v5.5.1 固定每期打满：floor取整后把(bankroll-已分)的偶数零头按概率从高到低逐注+2元，恰好分到=bankroll。
    给任一注加钱只增其命中回报、不会破坏'中任意1注即盈'的覆盖条件，故安全。返回bets。"""
    order = sorted(range(len(bets)), key=lambda i: (-i if hi_first else i))
    guard = 0
    while sum(bets) + BET_UNIT <= bankroll + 1e-9 and guard < 100000:
        idx = order[guard % len(order)] if order else 0
        bets[idx] += BET_UNIT
        guard += 1
    return bets


def cover_staking(items, bankroll=NIGHT_BANKROLL, g=COVER_TARGET, fill_full=True):
    """覆盖模式：从概率最高注起求最大子集，使【命中其中任意1注即净赚≥g】。
    充要条件 每注需投 need_i=bankroll*(1+g)/sp_i 且 Σneed≤bankroll。fill_full=True时零头回填、每期恰好打满。"""
    items = sorted(items, key=lambda z: -z[0])
    for k in range(min(len(items), SLIP_MAX_BETS), 0, -1):
        sub = items[:k]
        need = [bankroll * (1 + g) / (sp + 1e-12) for _, sp, _ in sub]
        if sum(need) <= bankroll - 1e-6:
            rem = bankroll - sum(need)
            raw = [need[i] + (rem * need[i] / sum(need) if sum(need) > 0 else 0) for i in range(k)]
            bets = [_bet_floor(x) for x in raw]
            while sum(bets) > bankroll:                      # 取整超额则从最大注逐档减
                j = max(range(k), key=lambda i: bets[i])
                if bets[j] <= BET_UNIT:
                    break
                bets[j] -= BET_UNIT
            if fill_full:
                _fill_to_bankroll(bets, bankroll)            # 固定打满：零头增厚到恰=bankroll
            return sub, bets
    return [], []


def proportional_staking(items, bankroll=NIGHT_BANKROLL, fill_full=True):
    """兜底：覆盖条件不成立(注多/赔率低)时，按全凯利分数比例分配，金额取整到2元；fill_full时恰好打满。"""
    items = items[:SLIP_MAX_BETS]
    if not items:
        return [], []
    w = [max(1e-9, kelly(p, sp)) for p, sp, _ in items]
    if sum(w) <= 1e-6:                                       # 全负EV凯利=0→退化为按概率分配(纯命中面)
        w = [p for p, _, _ in items]
    s = sum(w)
    raw = [bankroll * x / s for x in w]
    bets = [_bet_floor(x) for x in raw]
    while sum(bets) > bankroll:
        j = max(range(len(bets)), key=lambda i: bets[i])
        if bets[j] <= BET_UNIT:
            break
        bets[j] -= BET_UNIT
    if fill_full:
        _fill_to_bankroll(bets, bankroll)
    return items, bets


def slip_scenario(items, bets):
    """独立近似枚举2^n命中组合：全黑概率/当晚盈利概率/走盘/期望净盈亏/中k注的平均净盈亏。
    注间有共用腿或同联赛时实际相关、全黑概率比独立近似更高(打印时提示)。"""
    n = len(items)
    cost = sum(bets)
    if n == 0:
        return None
    if n > 14:  # 2^n精确枚举上限保护(SLIP_MAX_BETS=5远低于此,仅防参数被改大导致指数爆炸)
        raise ValueError(f"盈亏情景精确枚举最多14注,当前{n}注;请调小SLIP_MAX_BETS")
    pwin = pflat = ploss = enet = 0.0
    byk = {}
    for mask in range(1 << n):
        pr, ret, hits = 1.0, 0.0, 0
        for i, (p, sp, _) in enumerate(items):
            if (mask >> i) & 1:
                pr *= p; ret += bets[i] * sp; hits += 1
            else:
                pr *= (1 - p)
        net = ret - cost
        enet += pr * net
        if net > 1:
            pwin += pr
        elif net < -1:
            ploss += pr
        else:
            pflat += pr
        byk.setdefault(hits, []).append((pr, net))
    pblack = 1.0
    for p, _, _ in items:
        pblack *= (1 - p)
    kdist = {h: (sum(t[0] for t in v), sum(t[0] * t[1] for t in v) / sum(t[0] for t in v)) for h, v in byk.items()}
    return dict(cost=cost, pwin=pwin, pflat=pflat, ploss=ploss, pblack=pblack,
                enet=enet, eroi=enet / cost, kdist=kdist, n=n)


def sharp_stratum_leg_ok(no, L, A_by_no):
    """v5.8.4 锐线分层硬闸门（单腿判定）。返回 (ok, reason)。
    规则：SHARP_GATE_MARKETS 内玩法(默认仅W胜平负)的腿，须 |Δλ|=|lh-la|≥SHARP_GATE_DL_MIN 且
    锁存首选概率 L['p']≥SHARP_GATE_PROB_MIN 才允许进实盘投注单；任一不过只作观察。
    非卡控玩法(H/S/T)、总开关关、缺该场分析或缺λ时一律放行，交给既有CLV/锐线/置信闸门，绝不凭空杀注。"""
    if not SHARP_STRATUM_GATE:
        return True, "闸门关"
    if L.get("mk") not in SHARP_GATE_MARKETS:
        return True, "非卡控玩法"
    a = A_by_no.get(str(no))
    if a is None:
        return True, "缺该场分析不卡"
    try:
        dl = abs(float(a.get("lh")) - float(a.get("la")))
    except Exception:
        return True, "缺λ不卡"
    if dl < SHARP_GATE_DL_MIN - 1e-9:
        return False, f"|Δλ|={dl:.2f}<{SHARP_GATE_DL_MIN:.1f}"
    p = L.get("p")
    if p is None:
        return False, "首选概率缺失"
    if p < SHARP_GATE_PROB_MIN - 1e-9:
        return False, f"首选{p*100:.0f}%<{SHARP_GATE_PROB_MIN*100:.0f}%"
    return True, f"过(|Δλ|{dl:.2f},P{p*100:.0f}%)"


def sharp_stratum_combo_ok(c, A_by_no):
    """v5.8.4 组合层闸门：两腿均过单腿闸门才放行实盘。返回 (ok, [(no,ok,reason),...])。"""
    det = []
    for nn, LL in ((c["n1"], c["L1"]), (c["n2"], c["L2"])):
        ok, rs = sharp_stratum_leg_ok(nn, LL, A_by_no)
        det.append((nn, ok, rs))
    return all(ok for _, ok, _ in det), det


def build_slip_items(sel, min_prob=SLIP_MIN_PROB):
    """从终选[(tier,c)]筛出可买2串1：有SP、联合概率达标、ρ<0.3、同源可信、剔除⊗伪EV观察。"""
    out = []
    for tier, c in sel:
        if "⊗" in str(tier):
            continue
        if c.get("spc") is None or c.get("rho_hi", 0) >= RHO_BLOCK:
            continue
        if not c.get("ev_trusted", True):
            continue
        p = c.get("pc_raw", c["pc"])
        if p < min_prob:
            continue
        out.append((p, c["spc"], c, tier))
    return out


def diversify_slip(items, match_cap=SLIP_MATCH_CAP):
    """容错覆盖要求各注尽量不同时黑：按概率贪心，同一场比赛在整张单最多出现match_cap次；不足2注再放宽补齐。"""
    items = sorted(items, key=lambda z: -z[0])
    cnt, out, seen = {}, [], set()
    for it in items:
        c = it[2]
        if all(cnt.get(n, 0) < match_cap for n in (c["n1"], c["n2"])):
            out.append(it); seen.add(id(c))
            for n in (c["n1"], c["n2"]):
                cnt[n] = cnt.get(n, 0) + 1
    if len(out) < 2:
        for it in items:
            if id(it[2]) not in seen:
                out.append(it); seen.add(id(it[2]))
    return out


def print_betting_slip(A, sel, bankroll=NIGHT_BANKROLL, all_combos=None):
    """v5.5 最终交付：把今晚 bankroll 元【固定打满】自动分到若干2串1，自带每注金额+盈亏情景+诚实风险结论。
    all_combos=全结果组合池(build_combos('all_legs'))：传入后投注单在【全部合格组合】上做容错覆盖优选，
    而不是只在终选5注里挑(第7问'每日最优'：候选池越大、覆盖组合越优)；sel终选注优先排前。"""
    line()
    print(f"★【今晚投注单】固定投入 {bankroll:g} 元/期（21点购凌晨赛·容错覆盖·金额取整到{BET_UNIT}元且每期打满，可照单购买）")
    line()
    raw_items = build_slip_items(sel)                       # 终选注优先
    if all_combos:                                          # v5.5.1 扩大到全结果合格池，去重
        have = {ckey(c) for _, _, c, _ in raw_items}
        for c in all_combos:
            if ckey(c) in have:
                continue
            if c.get("spc") is None or c.get("rho_hi", 0) >= RHO_BLOCK or not c.get("ev_trusted", True):
                continue
            p = c.get("pc_raw", c["pc"])
            if p < SLIP_MIN_PROB:
                continue
            raw_items.append((p, c["spc"], c, "全池")); have.add(ckey(c))
    # —— v5.8.4 锐线分层硬闸门：非筛选W腿(|Δλ|<1.0或首选<55%)的组合不进【实盘投注单】，只留在程序终选/对照里观察 ——
    _A_by_no = {str(a["m"]["no"]): a for a in (A or [])}
    _kept_items, _gate_drop = [], []
    for _it in raw_items:
        _ok, _det = sharp_stratum_combo_ok(_it[2], _A_by_no)
        (_kept_items if _ok else _gate_drop).append((_it, _det))
    if _gate_drop:
        print(f"  ⛔v5.8.4 锐线分层硬闸门（卡{'+'.join(SHARP_GATE_MARKETS)}腿：|Δλ|≥{SHARP_GATE_DL_MIN:.1f} 且 首选≥{SHARP_GATE_PROB_MIN*100:.0f}%）："
              f"{len(_gate_drop)} 注不进实盘、仅作观察——")
        for _it, _det in _gate_drop:
            _c = _it[2]
            _why = "；".join(f"{_nn}腿{_rs}" for _nn, _ook, _rs in _det if not _ook)
            print(f"     × {_c['n1']}{_c['L1']['mk']}[{_c['L1']['pick']}] × {_c['n2']}{_c['L2']['mk']}[{_c['L2']['pick']}]（{_why}）")
    raw_items = [_it for _it, _ in _kept_items]
    _gate_pool = list(raw_items)     # v5.8.7 过v5.8.4闸门(含v5.8.6独立H)但未必过价值门槛的候选池，供兜底档
    _tier_mode = "S价值"
    # —— v5.8.5 TOP2锁定：EV>0 + 两腿CLV>0 硬门槛 → 组合EV降序(并列取两腿首选概率大者) → 只留前TOP2_KEEP注 ——
    if TOP2_LOCK_MODE:
        def _clv_pos(it):
            for L in (it[2]["L1"], it[2]["L2"]):
                v = L.get("clv")
                if v is None or v <= 0:
                    return False
            return True
        _ev_pass = [it for it in raw_items if (it[2].get("ev") if it[2].get("ev") is not None else -9) > TOP2_MIN_EV]
        if TOP2_REQUIRE_CLV_POS:
            _ev_pass = [it for it in _ev_pass if _clv_pos(it)]
        _ev_pass.sort(key=lambda it: (-(it[2].get("ev") or -9),
                                      -max(it[2]["L1"].get("p") or 0, it[2]["L2"].get("p") or 0)))
        _strict = _ev_pass[:TOP2_KEEP]
        if _strict:
            _hidden = len(raw_items) - len(_ev_pass) + max(0, len(_ev_pass) - TOP2_KEEP)
            raw_items = _strict
            print(f"  🎯v5.8.5 TOP{TOP2_KEEP}锁定【价值档】：按[EV>0+两腿CLV>0]过闸、组合EV降序、并列取高命中面排序，"
                  f"只输出前{TOP2_KEEP}注实盘；其余{_hidden}个候选不展示(后台留存校准用)。")
        elif FALLBACK_ENABLED:
            # —— v5.8.7 价值档为空：启动概率优先【稳健兜底档】(允许v5.8.6独立让球H混搭；负EV设出血上限) ——
            _fb = []
            for it in _gate_pool:
                _c = it[2]
                _jp = _c.get("pc_raw", _c.get("pc")) or 0.0
                _evv = _c.get("ev")
                if _evv is None or _evv < FALLBACK_EV_FLOOR:
                    continue                              # 负EV超过出血上限→不碰
                if _jp < FALLBACK_JP_MIN:
                    continue                              # 联合命中率不足
                if min(_c["L1"].get("p") or 0.0, _c["L2"].get("p") or 0.0) < FALLBACK_LEG_PMIN:
                    continue                              # 单腿概率不足
                _fb.append(it)
            _fb.sort(key=lambda it: (-(it[2].get("pc_raw", it[2].get("pc")) or 0.0),
                                     -(it[2].get("ev") or -9)))   # 概率优先：联合命中降序，并列取EV较不负
            raw_items = _fb[:FALLBACK_KEEP]
            _tier_mode = "F兜底"
            if raw_items:
                print("  🟡v5.8.7 今晚无正EV/CLV【价值档】→ 启动【稳健兜底档】(概率优先；W×H混搭时H腿已过v5.8.6独立源校验)：")
                print(f"     门槛=联合命中≥{FALLBACK_JP_MIN:.0%}、单腿首选≥{FALLBACK_LEG_PMIN:.0%}、"
                      f"组合EV≥{FALLBACK_EV_FLOOR:+.0%}(出血上限)；按联合命中降序取前{FALLBACK_KEEP}注。")
                print("     ⚠这是【负EV娱乐档】而非价值实盘：长期期望为负，只走娱乐小仓、命中见好就收、绝不加注追投。")
            else:
                print(f"  v5.8.7 兜底档也无合格注（出血上限{FALLBACK_EV_FLOOR:+.0%} 且 联合命中≥{FALLBACK_JP_MIN:.0%} 区间内为空）。")
        else:
            raw_items = []
    raw_items = diversify_slip(raw_items)
    if not raw_items:
        print("  今晚没有任何同时满足[价值档EV>0+CLV>0 或 兜底档概率/出血门槛 + v5.8.4分层硬闸门/有SP/ρ<0.3/同源可信]的2串1——最诚实的建议是【空仓】，")
        print("  强行下注等于在无优势时下注。若一定要参与，请只用极小微额度娱乐，不要按固定额度硬投。")
        return None
    # 是否存在任何独立统计优势：过实盘闸门 / 正EV / 某腿相对公允价有【正】价值(锐线CLV≥3%或欧赔静态价值≥5%)。
    # 注意：仅有欧赔信源≠有优势(信源只给独立锚,方向价值可能为负)；必须clv达标才算edge，否则降级娱乐档。
    def _leg_edge(L):
        if L.get("vsrc") == "sharp":
            return L.get("clv") is not None and L["clv"] >= CLV_MIN
        if L.get("vsrc") == "euro":
            return L.get("clv") is not None and L["clv"] >= EURO_EDGE_MIN
        return False
    has_edge = any(stake_plan(c)["f_live"] > 0 or (c["ev"] is not None and c["ev"] > 0)
                   or _leg_edge(c["L1"]) or _leg_edge(c["L2"]) for _, _, c, _t in raw_items)
    if _tier_mode == "F兜底":
        has_edge = False   # v5.8.7 兜底档本质负EV：强制按无优势处理→走NO_EDGE_FUN_FRACTION娱乐小仓，不按价值实盘配仓
    eff_bankroll = bankroll if has_edge else round(bankroll * NO_EDGE_FUN_FRACTION / BET_UNIT) * BET_UNIT
    if not has_edge:
        print("  ⛔今晚候选注【没有任何独立价值源】(无百家欧赔均值/锐线、组合EV全为负)：首选动作是【空仓】。")
        print(f"     若仍要参与看球，下面只按 {eff_bankroll:g} 元(={NO_EDGE_FUN_FRACTION*100:g}%额度)给娱乐参考，绝非推荐投入{bankroll:g}元。")
    items3 = [(p, sp, c) for p, sp, c, _t in raw_items]
    sub, bets = cover_staking(items3, eff_bankroll)
    mode = "覆盖(中任意1注即净赚)"
    if len(sub) < 2:                                   # 覆盖凑不齐2注→改比例分配
        sub, bets = proportional_staking(items3, eff_bankroll)
        mode = "比例(按凯利/概率分摊，需中足够注数才盈利)"
    if len(sub) == 0:
        print("  候选注均为负凯利且无法分配，建议空仓。")
        return None
    # 相关性：统计被多注共用的腿(该腿错则多注同黑)与同联赛聚集
    leg_cnt, lgs = {}, []
    for p, sp, c in sub:
        for no, L in ((c["n1"], c["L1"]), (c["n2"], c["L2"])):
            key = (no, L["mk"], L["pick"]); leg_cnt[key] = leg_cnt.get(key, 0) + 1
        lgs.extend([c["lg1"], c["lg2"]])
    same_lg = len(lgs) != len(set(lgs))
    shared = {k: n for k, n in leg_cnt.items() if n >= 2}
    any_live = any(stake_plan(c)["f_live"] > 0 for _, _, c in sub)
    pos_ev = sum(1 for _, _, c in sub if c["ev"] is not None and c["ev"] > 0)
    print(f"  分配模式：{mode}；纳入 {len(sub)} 注；过实盘闸门 {'是' if any_live else '否(均为概率/纸面注)'}；正EV注 {pos_ev}/{len(sub)}")
    print("  " + "-" * 100)
    for i, ((p, sp, c), amt) in enumerate(zip(sub, bets), 1):
        evtxt = f"{c['ev']*100:+.0f}%" if c["ev"] is not None else "—"
        print(f"  第{i}注  {amt:3d}元  | 联合命中{p*100:4.1f}% 总赔{sp:4.2f} 组合EV{evtxt:>6} | 中了得 {amt*sp:5.0f}元")
        print(f"         {fmt_leg(c['n1'], c['L1'])}  ×  {fmt_leg(c['n2'], c['L2'])}")
    sc = slip_scenario(sub, bets)
    total = sum(bets)
    print("  " + "-" * 100)
    fill_note = "每期固定打满" if abs(total - eff_bankroll) < BET_UNIT else f"余 {eff_bankroll-total:g} 元(取整尾差,不足1注)"
    print(f"  合计投入 {total} 元（本次{'投注' if has_edge else '娱乐参考'}额度{eff_bankroll:g}元，{fill_note}"
          + ("" if has_edge else f"；原{bankroll:g}元在无优势时不建议动用") + "）。盈亏情景（注间独立近似）：")
    for h in sorted(sc["kdist"]):
        pr, avgn = sc["kdist"][h]
        print(f"     中{h}注：概率{pr*100:5.1f}%，平均净盈亏 {avgn:+7.1f} 元")
    print(f"  → 全晚【一分不中】概率 {sc['pblack']*100:.1f}%（亏 {total} 元）；当晚净盈利概率 {sc['pwin']*100:.1f}%；"
          f"期望净盈亏 {sc['enet']:+.1f} 元（期望ROI {sc['eroi']*100:+.1f}%）。")
    if shared:
        msg = "、".join(f"{no}{MK_LABEL[mk]}[{pk}]×{n}" for (no, mk, pk), n in sorted(shared.items()))
        print(f"  ⚠共用腿(该腿一旦错、绑定的多注会同黑)：{msg}")
    if same_lg:
        print("  ⚠含同联赛注，结果正相关，实际全黑概率高于上面的独立近似、当晚盈利概率偏乐观。")
    if sc["eroi"] < 0:
        print("  ⚠本单期望净盈亏为负：覆盖买法只是把盈亏分布改成'常小赚、偶全黑'，长期仍是亏——它【不能保证每晚盈利】，")
        print("    约每 {} 个购彩晚就会遇到一次全黑。请把500元视为可承受娱乐预算，绝不因一晚全黑而加倍追投。".format(
            max(2, round(1/max(sc['pblack'],1e-9)))))
    if not any_live:
        print("  ⚠无任一注通过锐线/欧赔价值实盘闸门：在缺少百家欧赔均值euro_avg或锐线时，此单仅为概率热门覆盖，不具备统计优势。")
    print("  纪律：只按上表金额买、不自行加注/改串；命中见好就收；连续回撤按文件风控(DD≥5%×0.8、≥20%停手)。")
    line()
    return dict(mode=mode, bets=bets, sub=sub, scenario=sc)


def calibrate_from_history(matches, verbose=True, min_n=8):
    """v5.3.3 赛果滚动校准：对带 res='主:客' 的已赛场，用最大似然反推两个全局参数——
    ①Dixon-Coles 的 ρ（低比分修正强度）；②总λ系统乘子 LAMBDA_TLT_MULT（校正市场λ整体高/低估）；
    并给1X2首选命中率、多分类Brier、预测概率分桶校准表。只输出建议、不自动覆盖CONFIG(小样本防过拟合)。"""
    rows = []
    for m in matches:
        if not m.get("res"):
            continue
        ij = _res_ij(m["res"])
        if not ij:
            continue
        try:
            a = analyze(dict(m))
        except Exception:
            continue
        i, j = ij
        d = 0 if i > j else (1 if i == j else 2)
        rows.append((a["lh"], a["la"], i, j, d, a["one"]))
    if len(rows) < min_n:
        if verbose:
            print(f"§滚动校准：仅 {len(rows)} 场带赛果（需≥{min_n}），样本不足不校准；多积累已赛场(填res)后再跑。")
        return None
    # ① ρ 网格：实际比分格在不同ρ下的对数似然
    rho_grid = [x / 1000 for x in range(-200, 21, 5)]
    best_rho, best_ll = RHO_DC, -1e18
    for rho in rho_grid:
        ll = sum(log(max(dixon_coles(matrix(lh, la), lh, la, rho)[i][j], 1e-12))
                 for lh, la, i, j, d, one in rows)
        if ll > best_ll:
            best_ll, best_rho = ll, rho
    # ② 总λ乘子网格：实际总进球在不同乘子下的泊松对数似然
    mult_grid = [x / 100 for x in range(85, 116)]
    best_m, best_mll = 1.0, -1e18
    for mu in mult_grid:
        ll = sum(log(max(pois(i + j, (lh + la) * mu), 1e-12))
                 for lh, la, i, j, d, one in rows)
        if ll > best_mll:
            best_mll, best_m = ll, mu
    # ③ 1X2 命中 / Brier / 概率分桶校准
    n = len(rows)
    hit = sum(1 for lh, la, i, j, d, one in rows if max(range(3), key=lambda k: one[k]) == d)
    brier = sum(sum((one[k] - (1 if k == d else 0)) ** 2 for k in range(3))
                for lh, la, i, j, d, one in rows) / n
    bins = {}
    for lh, la, i, j, d, one in rows:
        b = int(max(one) * 10)
        w, t = bins.get(b, (0, 0)); bins[b] = (w + (max(range(3), key=lambda k: one[k]) == d), t + 1)
    if verbose:
        line(); print(f"§A+++ 赛果滚动校准（{n}场已赛样本；最大似然反推参数，只建议、不自动覆盖，防小样本过拟合）"); line()
        print(f"  ① Dixon-Coles ρ：当前{RHO_DC:+.3f} → 样本最优 {best_rho:+.3f}（对数似然{best_ll:.1f}）")
        bias = "高估(应下调)" if best_m < 1 else ("低估(应上调)" if best_m > 1 else "无系统偏差")
        print(f"  ② 总λ乘子：当前{LAMBDA_TLT_MULT:.2f} → 样本最优 {best_m:.2f}（市场总λ{bias}，幅度{(1-best_m)*100:+.1f}%）")
        print(f"  ③ 1X2首选命中 {hit}/{n}={hit/n*100:.0f}%；多分类Brier={brier:.3f}（越低越好，均匀猜测基线0.667）")
        print("  概率校准表（首选预测概率分桶 → 该桶实际命中率，两者越接近越校准）：")
        for b in sorted(bins):
            w, t = bins[b]
            print(f"     预测{b*10}-{b*10+10}%档：实际 {w}/{t} = {w/t*100:3.0f}%")
        if n >= 30:
            print(f"  ★样本已达{n}场(≥30)，可把下列两行替换进 CONFIG 重跑（建议再做一次留出回测确认方向稳定，防过拟合）：")
            print(f"       RHO_DC = {best_rho:+.3f}")
            print(f"       LAMBDA_TLT_MULT = {best_m:.2f}")
        else:
            print(f"  采用建议：现仅{n}场(<30)只观察、不改参数；积累≥30场且方向稳定后可粘贴 "
                  f"RHO_DC = {best_rho:+.3f}、LAMBDA_TLT_MULT = {best_m:.2f} 重跑。")
        line()
    return dict(n=n, rho=best_rho, mult=best_m, hit=hit / n, brier=brier, bins=bins)


def run_from_ai_text(ai_json_text="", sharp_text=None, auto_collect=True, date="auto"):
    """v5.3.4 一键桥接：把豆包联网产出的JSON文本(及SHARP_TEXT紧凑赔率)直接喂入并跑完整流程，免改源码CONFIG。
    用法（交互或外层脚本）：
        import importlib.util
        s=importlib.util.spec_from_file_location('v','足球竞彩一体化_v5.3.4_升级修复版.py')
        v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
        v.run_from_ai_text(open('ai_result.json',encoding='utf-8').read(),
                           sharp_text='016|spf -138 +301 +382|ou 2.75 -109 -103')
    边界说明：本文件是确定性计算引擎，不能自己唤起豆包大模型会话；豆包联网研究在文件外完成，
    本函数把原来'手动粘贴进AI_JSON/SHARP_TEXT再运行'这一步函数化，配合外层编排即可实现半自动闭环。"""
    globals()["AI_JSON"] = ai_json_text or ""
    if sharp_text is not None:
        globals()["SHARP_TEXT"] = sharp_text
    globals()["AUTO_COLLECT"] = auto_collect
    globals()["MATCH_DATE"] = date
    return main()


# v5.5 给执行豆包的标准作业程序：用户只发"分析全部"或若干编号、无其他指令时，严格按此端到端执行
AGENT_SOP = r'''
【用户只发"分析全部/今晚怎么买"或若干场次编号时，豆包的全自动标准作业（无需再向用户追问）】
0) 心态与边界：竞彩返奖率约88.5%，不存在"每晚必盈"。你的职责是把当晚【信息优势最大化】并如实呈现概率，
   绝不能承诺稳赚；最终投注单会算出"当晚盈利概率/全黑概率/期望ROI"，照实转述即可。
1) 取骨架：运行本文件 collect_sporttery("auto"/业务日) 自动拉竞彩官方四玩法SP/让球线/排名/开赛时间(带Referer已可用)；
   若用户给了编号，只保留这些编号(等价于 auto_pipeline(nos=[...]))。
2) 逐场用【浏览器】联网补全(程序直连欧赔站会被反爬，必须浏览器渲染读取；取不到填null、绝不编造)，P0两项每场必清：
   ① euro_avg 百家欧赔"平均赔率"[主,平,客](500彩票网odds.500.com欧赔页/澳客okooo/足彩网zgzcw，取到两个源交叉)、
      euro_disp 百家离散度；② 【P0】stat 严格按主/客场拆分给齐10字段：联赛主场/客场场均进失球4基准(lg_hgf/lg_hga/lg_agf/lg_aga)
      +主队本赛季主场 h_n/h_gf/h_ga +客队本赛季客场 a_n/a_gf/a_ga(500/澳客战绩主客分页、FBref/SofaScore交叉；
      缺stat引擎只能走纯市场λ=复读赔率，样本<5场可null但不许编)；③ spf_open 最初初盘；
   ④ review：预计首发(expected)+伤停影响、战意数学形势、默契球、突发利空、天气(详见RESEARCH_BRIEF)。
   注意用户21点购彩、比赛次日凌晨：读"当前时点"即可，首发用"预计首发"，不要等临场官宣。
   若 jc_data/team_alias_todo_*.json 列出没对上Pinnacle的中文队名，顺手查标准英文名补 TEAM_ALIAS_CN2EN 后重跑。
3) 把上述结果组成JSON数组(键名见RESEARCH_BRIEF)，调用 auto_pipeline(nos, ai_json_text=该JSON, bankroll=500)。
4) 向用户只转述最终【今晚投注单】：每注串法+建议金额+中了可得、合计、以及"中0/1/2注"盈亏情景与
   当晚盈利概率/全黑概率/期望ROI；并复述风险纪律。若程序判定空仓，就如实说"今晚无统计优势，建议空仓/极小娱乐"。
5) 不替用户点击任何购彩/充值；金额仅为按500元额度的数学建议，用户可等比缩放，但不建议超过可承受额度。
6) 【赛后回流·让λ/概率真正越用越准】次日主动用浏览器/检索查昨夜每场最终比分，按 res="主队进球:客队进球" 回填历史记录，
   累积≥8场后 calibrate_from_history 自动用最大似然反推 Dixon-Coles ρ 与总λ系统乘子、输出1X2命中率/Brier/概率校准表；
   ≥30场且方向稳定才建议更新 RHO_DC/LAMBDA_TLT_MULT。没有赛后比分回流，模型只有"赛前内部一致性校验"、无法证明/提升真实命中率。
   同时用 settle_review 自动核对昨晚推荐注的命中与兑现盈亏，做命中率/ROI滚动台账(这是检验"推荐准不准"的唯一客观手段)。
   ★v5.5.2起优先用【锁存结算】：赛前出单已自动把首选/终选/投注单/实际购票锁进 jc_data/snapshots/ 快照(v5.8.1起校准库/
   快照/台账/Elo/H2H统一落脚本旁 jc_data/，或环境变量 JC_DATA_DIR 指定的固定盘；v5.8.1起新会话把备份zip放进 jc_backup/
   即启动自动接续、赛后又自动备份，跨日累积无需手动restore)；
   次日把终场比分填进 POST_RESULTS(或调 auto_pipeline(post_results={编号:'主:客'}))，程序只读取赛前快照对账、绝不用赛后漂移的赔率重算首选，
   并一并结算 ACTUAL_TICKETS 实际购票的返还/净盈亏——保证"当时推荐/买了什么"可审计、跨会话不丢。
'''


def show_sop():
    print(AGENT_SOP)


def auto_pipeline(nos="all", ai_json_text="", sharp_text=None, date="auto", bankroll=None,
                  post_results=None, actual_tickets=None, snapshot_path=None):
    """v5.5 全自动一键入口（用户只发编号或'分析全部'时调用，端到端：自动采集→合并豆包研究→选串→500元投注单）。
    nos: 'all'/None=全部场次，或 ['001','003']；ai_json_text: 豆包浏览器联网研究回填的JSON(强烈建议每场含euro_avg)；
    sharp_text: 可选紧凑锐线文本；date: 业务日'auto'；bankroll: 今晚额度(默认NIGHT_BANKROLL)。末尾即打印【今晚投注单】。
    v5.5.2 新增：post_results={编号:'主:客'}=赛后锁存结算(只读赛前快照、不重算首选)；actual_tickets=实际购票台账；
    snapshot_path=指定要对账的快照(留空按批次自动找最近)。"""
    globals()["TARGET_NOS"] = None if (nos is None or str(nos).lower() == "all") else list(nos)
    globals()["AI_JSON"] = ai_json_text or ""
    if sharp_text is not None:
        globals()["SHARP_TEXT"] = sharp_text
    globals()["AUTO_COLLECT"] = True
    globals()["MATCH_DATE"] = date
    if bankroll:
        globals()["NIGHT_BANKROLL"] = float(bankroll)
    if post_results is not None:
        globals()["POST_RESULTS"] = post_results
    if actual_tickets is not None:
        globals()["ACTUAL_TICKETS"] = actual_tickets
    if snapshot_path is not None:
        globals()["SNAPSHOT_TO_SETTLE"] = snapshot_path
    return main()

def main():
    global MATCHES
    try: auto_restore_on_start()   # v5.8.1 新会话启动先从 jc_backup 最新备份补缺还原(只补缺不覆盖)，使后续calib_load直接读到历史积累
    except Exception as _e: print(f"启动自动接续异常(跳过,不影响运行):{_e}")
    try: load_calibrators(verbose=True)   # v5.7.1 先装载历史校准样本(不足30场走温和收缩)，供本次analyze概率校准
    except Exception as _e: print(f"校准器装载异常(跳过,概率不校准):{_e}")
    ai = parse_ai_json(AI_JSON)
    if AUTO_COLLECT:
        print_free_ladder_brief()
        _want_nos = None if (not TARGET_NOS or str(TARGET_NOS).lower()=="all") else list(TARGET_NOS)
        MATCHES = assemble_matches(MATCH_DATE, ai, want_nos=_want_nos)
        print(f"§A+/§B 自动采集+AI回填合并完成，共 {len(MATCHES)} 场（官方SP为骨架，锐线多通道回填，缺项已置null）")
        if not MATCHES:
            # v5.3.2 B10：联网失败/当日无场不直接退出，回退内置示例并显著标注，保证文件始终可运行
            MATCHES = [dict(m) for m in (ai or SAMPLE_MATCHES)]
            print("⚠官方接口与AI_JSON都未取到场次（断网/非比赛日）：已回退到内置样例数据演示，实战请检查网络/MATCH_DATE或粘贴§A研究JSON。")
    elif ai:
        MATCHES = ai
        print(f"§B 已从联网AI回填JSON解析 {len(MATCHES)} 场（自动覆盖内置示例数据）")
    else:
        print("§B AI_JSON为空→使用文件内置MATCHES（实战时把联网AI输出的JSON粘进AI_JSON即零手填）")
    # v5.3.3 合并 SHARP_TEXT（豆包从Pinnacle等抄回的紧凑赔率文本，美式自动换算；只补不覆盖）
    _n_sharp = merge_sharp_text(MATCHES)
    if _n_sharp:
        print(f"§A+ 已从 SHARP_TEXT 解析并回填 {_n_sharp} 场锐线（美式赔率已自动换算十进制）")
    # v5.5 用户只发场次编号：按 TARGET_NOS 筛选；"分析全部"/None 时不筛
    if TARGET_NOS and str(TARGET_NOS).lower() != "all":
        _want = set(str(x).zfill(3) for x in TARGET_NOS)
        _b = len(MATCHES); MATCHES = [m for m in MATCHES if str(m.get("no", "")).zfill(3) in _want]
        print(f"§ 按你指定的编号 {sorted(_want)} 筛选：{_b}→{len(MATCHES)} 场")
    # v5.6 全自动：analyze前自动补天气(open-meteo回填review.weather；语义缺项稍后导清单交豆包)
    try:
        auto_collect_weather(MATCHES, verbose=True)
    except Exception as _e:
        print(f"  v5.6天气自动采集异常(跳过,不影响主流程):{_e}")
    # v5.3.2 B1：逐场容错——单场缺λ/字段异常只跳过该场并汇总，绝不再因一场坏数据整场崩溃
    A, _bad = [], []
    for m in MATCHES:
        try:
            A.append(analyze(m))
        except Exception as e:
            _bad.append((m.get("no"), str(e)))
    if _bad:
        line(); print(f"⚠以下 {len(_bad)} 场因数据不足/异常已跳过（不影响其余场次；补齐大小球/总进球SP/avg/stat/手填λ之一即可）：")
        for no, e in _bad: print(f"    {no}: {e}")
    if not A:
        print("✗没有任何场次可计算（全部缺λ来源）：请配PinBook key取大小球，或粘贴含avg/stat/ou的§A研究JSON，或手填lh/la。")
        return
    # 手填λ与市场背离告警回显（B6）
    _mw = [a["m"]["no"] for a in A if a["m"].get("_manual_warn")]
    if _mw:
        line(); print("⚠手填λ与市场去水概率显著背离（已仍按手填计算，请人工核对λ或赔率是否录错）：" + "、".join(_mw))
    # —— 输入格式校验（只提示，不中断；致命缺λ在analyze内已抛错）——
    bad = [(m["no"], e) for m in MATCHES for e in validate_one(m)]
    if bad:
        line()
        print("⚠输入格式提示（请按字段模板修正）：")
        for no, e in bad:
            print(f"  {no}: {e}")

    # —— 0. 体检表 ——
    line()
    print("每日选串体检表（λ差/总λt/两向一致/穿盘/首选比分↔总进球峰值；引擎含Dixon-Coles）")
    line()
    for a in sorted(A, key=lambda x: -x["dl"]):
        t1 = "方向一致" if a["dir_ok"] else "方向分歧"
        t2 = "穿盘✓" if a["cover"] is True else ("赢球输盘⚠" if a["cover"] is False else "平局中性")
        si, sj = a["sc"][0][1], a["sc"][0][2]
        # v5.3.6 F4：信息增量igain与独立来源标签，一眼看出本场是"模型独立判断"还是"赔率复读"
        _ig = a.get("igain")
        _itag = "有独立源" if a.get("indep") else ("=市场" if (_ig is None or _ig < IGAIN_FLAT) else "弱增量")
        _igtxt = "—" if _ig is None else f"{_ig * 100:.1f}%"
        # v5.4 早盘/欧赔锚/方向翻转/离散度 透明标签
        _f = a.get("fuse", {}) or {}
        _vt = []
        if _f.get("early"):
            _vt.append(f'早盘{_f.get("hrs")}h')
        if _f.get("has_euro"):
            _vt.append("欧赔锚" + ("·方向翻转⚠" if _f.get("flipped") else ""))
        if (_f.get("disp", 0) or 0) >= EURO_DISP_WARN:
            _vt.append(f'离散{_f["disp"] * 100:.0f}%')
        _v54 = ("  " + " ".join(_vt)) if _vt else ""
        print(f'{a["m"]["no"]} {a["m"]["lg"]:4} λ主{a["lh"]:.2f}/客{a["la"]:.2f} '
              f'|Δλ|{a["dl"]:.2f} λt{a["lt"]:.2f}[{a["lsrc"]}] 1X2{DIR[a["d1"]]}'
              f'{a["one"][a["d1"]] * 100:4.1f}% [{t1}/{t2}] '
              f'首选{si}-{sj}={a["sc_k"]}球/峰{a["tg_peak"]}球 增量{_igtxt}[{_itag}]{_v54} 实赛{a["m"].get("res") or "—"}')

    # v5.3.6 F4：信息增量 + 已赛场首页命中/Brier 汇总
    print()
    information_gain_report(A)
    # —— 0.5 采集完整度/锐线/置信度回显 ——
    print()
    print_input_report(A)
    quality_audit(A)
    lambda_calibration_report(A)   # v5.3.3 λ校正链审计
    ai_review_report(A)            # v5.3.3 豆包AI语义核查（首发/战意/默契球/利空/天气）
    # ===== v5.6 新增：套利扫描 / Pinnacle线移动 / 豆包待补研究清单（均自容错，不改概率引擎）=====
    try: surebet_scan(A)
    except Exception as _e: print(f"v5.6套利扫描异常(跳过):{_e}")
    try: line_movement_report(A)
    except Exception as _e: print(f"v5.6线移动异常(跳过):{_e}")
    try:   # v5.7.1 P1-5：给每场注入最早PinBook快照的开盘去水概率，供实盘"收盘线不反向"第二确认
        _nopen = inject_open_sharp(A, batch=MATCH_DATE)
        if _nopen: print(f"  · v5.7.1 已给 {_nopen} 场注入开盘锐线(收盘线反向≥{LINE_REVERSE_PP*100:.0f}pp将拦实盘)")
    except Exception as _e: print(f"v5.7.1开盘锐线注入异常(跳过):{_e}")
    try: export_research_todo(A, batch=MATCH_DATE)
    except Exception as _e: print(f"v5.6缺项清单异常(跳过):{_e}")
    # v5.6 熔断【前置】：进入选注/出单前先读台账判定锁仓并置全局开关，stake_plan 的 f_live 会据此真正归零
    _lock56 = tilt_state(verbose=True)
    globals()["_TILT_LOCK56"] = bool(_lock56.get("lock"))
    # —— 1. 单场四玩法首选候选表 ——
    print()
    line()
    print("单场四玩法首选候选（胜平负/让球/比分单选[已剔4球+]/总进球单选[只0-4档]；SP待补=该玩法未录SP）")
    line()
    for a in sorted(A, key=lambda x: x["m"]["no"]):
        cells = []
        for L in a["legs"]:
            sp = f"@{L['sp']:.2f}" if L["sp"] is not None else ""
            cells.append(f'{MK_LABEL[L["mk"]]}:{L["pick"]}({L["p"] * 100:.1f}%{sp})')
        print(f'  {a["m"]["no"]} {a["m"]["lg"]:4} ' + " | ".join(cells))
    print()
    print_type_guide(A)
    # v5.8.2 净胜球分布×亚盘全档专项报告（只读展示，自容错，绝不影响后续选串/出单）
    try:
        print()
        print_asian_goaldiff_report(A)
    except Exception as _e:
        print(f"v5.8.2净胜球/亚盘报告异常(跳过,不影响主流程):{_e}")

    combos = build_combos(A)
    by_p = sorted(combos, key=lambda c: -c["pc"])

    # —— 2. 维度一：中奖概率最高 全局Top5 ——
    print()
    line()
    print(f"维度一【中奖概率最高】全局 Top{TOPN}（按 P_combo=p1×p2 降序；EV/ρ/无锐线仅标注，不提前剔除）")
    line()
    for i, c in enumerate(by_p[:TOPN], 1):
        print_combo(c, i)

    # —— 3. 六分类各Top1（F=全局第一）——
    print()
    line()
    print("六分类各 Top1（A胜平负/B让球/C比分/D总进球/E混合/F全场最高；某类无组合如实标注）")
    line()
    seen = set()
    for cat in ["A", "B", "C", "D", "E"]:
        cs = [c for c in by_p if c["cat"] == cat]
        if cs:
            print(f"  {CAT_NAME[cat]}")
            print_combo(cs[0])
        else:
            print(f"  {CAT_NAME[cat]}：⚠️本类今日无合法跨场组合")
        seen.add(cat)
    print(f"  {CAT_NAME['F']}（=维度一全局第1）")
    # v5.7.5修复：可计算场次<2(单场/全缺λ被跳过)时无任何跨场2串1,by_p为空,旧版by_p[0]直接IndexError崩溃
    if by_p:
        print_combo(by_p[0])
    else:
        print("  ⚠当前销售批次可计算场次不足2场（2串1必须跨两场，或剩余场因缺λ/数据不全被跳过）：")
        print("    无任何合法跨场组合，维度二/终选/投注单自动为空，仅保留上方单场概率展示；请改买单关或等下一批次。")

    # —— 4. 维度二：概率×价值最优 Top5（硬过滤后按S=P×EV降序）——
    print()
    line()
    print(f"维度二【概率×价值最优】Top{TOPN}（全结果枚举；硬过滤 组合EV≥0.15+单腿EV达标+ρ上限<0.3 后按 S=P×EV 降序）")
    line()
    combos_val = build_combos(A, "all_legs")  # 全结果池，保证价值最优严格全局（不漏次选高价值结果）
    pool2 = []
    for c in combos_val:
        ok, _ = investable(c)
        if ok:
            pool2.append(c)
    pool2.sort(key=lambda c: -(c.get("pc_raw", c["pc"]) * c["ev"]))

    def dominated(c, pool):  # Pareto：存在另一组合P、EV都不更低且至少一项更高=被支配（v5.3.2用真实概率pc_raw）
        pr = c.get("pc_raw", c["pc"])
        return any(o is not c and o.get("pc_raw", o["pc"]) >= pr and o["ev"] >= c["ev"]
                   and (o.get("pc_raw", o["pc"]) > pr or o["ev"] > c["ev"]) for o in pool)

    if pool2:
        for i, c in enumerate(pool2[:TOPN], 1):
            print_combo(c, i)
            sp = stake_plan(c)
            pf = "被支配" if dominated(c, pool2) else "Pareto非支配"
            exotic = c["L1"]["mk"] in ("S", "T") or c["L2"]["mk"] in ("S", "T")
            cap = "含比分/总进球腿 f≤0.5%" if exotic else "胜负让球 f≤2%(单场硬顶1.5%)"
            print(f"     {pf}；置信{sp['conf_lo']} 理论仓位={sp['f_theory'] * 100:.3f}%/"
                  f"实盘={sp['f_live'] * 100:.3f}%（{cap}；实盘须双锐线+每腿CLV≥+3%+S+）")
        hi_p = max(pool2, key=lambda c: c.get("pc_raw", c["pc"]))
        hi_ev = max(pool2, key=lambda c: c["ev"])
        print(f"     Pareto极端点：最高P解 {hi_p.get('pc_raw', hi_p['pc']) * 100:.1f}% / 最高EV解 EV={hi_ev['ev'] * 100:+.1f}%（供风险偏好选择）")
    else:
        print("  ⚠今日无组合通过维度二硬约束——当前MATCHES未录比分/总进球SP、且胜平负/让球热门EV多为负、")
        print("     本工具又无锐线(CLV无法验证)。按v38.4：这些2串1只作概率参考/纸面跟踪，禁止照投(红灯㉚)。")

    # —— 4.5 终选5注（三榜自动收敛：核心-卫星结构）——
    print()
    line()
    print("参考·角色覆盖5注（固定角色配额做命中面覆盖，非收益最优；★主推荐见后『全局EV最优模式』；附凯利七步占比）")
    line()
    final = final_five(by_p, pool2)
    plans = []
    for role, c in final:
        sp = stake_plan(c)
        plans.append((role, c, sp))
        sp_txt = f"{c['spc']:.2f}" if c["spc"] is not None else "SP待补"
        ev_txt = f"{c['ev'] * 100:+.1f}%" if c["ev"] is not None else "  —  "
        if c["spc"] is None:
            tag = "无SP·纯纸面观察"
        elif c["rho_hi"] >= RHO_BLOCK:
            tag = f"ρ{c['rho_hi']:.2f}禁组(红灯⑱)·禁止实盘"
        elif sp["f_live"] > 0:
            tag = "★实盘闸门全过(双锐线/每腿CLV≥+3%/S+)·可按实盘比例"
        elif sp["f_theory"] <= 0:
            tag = "凯利比例=0·不投钱，仅概率参考/纸面"
        else:
            tag = "仅理论仓位·未过实盘闸门(见推导：缺锐线/CLV/置信度/博冷之一)"
        print(f"{role}  [{c['cat']}] P={c['pc'] * 100:.1f}% SP={sp_txt:>6} EV={ev_txt}")
        print(f"     {fmt_leg(c['n1'], c['L1'])} × {fmt_leg(c['n2'], c['L2'])}")
        print(f"     建议占总资金 → 理论 {sp['f_theory'] * 100:.3f}% ｜当前实盘 {sp['f_live'] * 100:.1f}%  ｜{tag}")
        print(f"       └ 推导：{sp['why']}")
    auto_gate_report(plans)
    # 组合层画像
    ps = [c.get("pc_raw", c["pc"]) for _, c, _ in plans]
    exp_hit = sum(ps)
    at_least = 1.0
    for p in ps:
        at_least *= (1 - p)
    at_least = 1 - at_least
    legcnt = {}
    for _, c in final:
        for lg in llegs(c):
            legcnt[lg] = legcnt.get(lg, 0) + 1
    dup = {leg: n for leg, n in legcnt.items() if n >= 2}
    print("-" * 108)
    print(f"  组合画像：期望命中 {exp_hit:.2f} 注；独立近似下“至少中1注”概率 {at_least * 100:.1f}%"
          f"（这是命中面、不是盈利面；注间有共用腿时为偏乐观近似）")
    # 资金真相：仅对有SP的注，枚举2^n中奖情形，算等额资金下“当晚整体盈利”的真实概率
    funded = [(c.get("pc_raw", c["pc"]), c["spc"]) for _, c in final if c["spc"] is not None]
    if funded:
        nb = len(funded)
        cost = float(nb)  # 等额每注1单位，总成本=注数
        win_p, e_net = 0.0, 0.0
        for mask in range(1 << nb):
            pr, ret = 1.0, 0.0
            for i, (p, sp) in enumerate(funded):
                if (mask >> i) & 1:
                    pr *= p
                    ret += sp
                else:
                    pr *= (1 - p)
            e_net += pr * (ret - cost)
            if ret > cost + 1e-9:
                win_p += pr
        print(f"  资金真相：等额买上述{nb}注有SP者(每注1单位/共{nb:.0f}单位,独立近似)——当晚整体盈利概率仅 "
              f"{win_p * 100:.1f}%，期望净收益率 {e_net / cost * 100:+.1f}%；中1注常回不了本，需多注同中或中高赔。")
    if dup:
        msg = "，".join(f"{leg[0]}{MK_LABEL[leg[1]]}[{leg[2]}]×{n}" for leg, n in sorted(dup.items()))
        print(f"  相关性提示：以下腿被多注共用，该腿错则多注同黑——{msg}")
    else:
        print("  相关性提示：5注无重复腿，分散度良好")
    # v4.5 终选分型契合点评（只点评、不改选注）
    typ = {a["m"]["no"]: a["mtype"] for a in A}
    cover, warn_w, near_h = [], [], []
    for role, c in final:
        short = role.split("·")[0]
        tag = f'{short}({c["n1"]}{c["L1"]["mk"]}×{c["n2"]}{c["L2"]["mk"]})'
        mks = (c["L1"]["mk"], c["L2"]["mk"])
        ts = (typ.get(c["n1"]), typ.get(c["n2"]))
        if "S" in mks or "T" in mks:
            cover.append(tag)
        if any(t == "相近分歧" and mk == "W" for t, mk in zip(ts, mks)):
            warn_w.append(tag)
        if any(t == "相近分歧" and mk == "H" for t, mk in zip(ts, mks)):
            near_h.append(tag)
    seg = []
    if near_h:
        seg.append("相近分歧场用让球H(受让覆盖,契合)" + "、".join(near_h))
    if warn_w:
        seg.append("相近分歧场仍含胜平负W(方向不稳,须锐线CLV/S+确认)" + "、".join(warn_w))
    if cover:
        seg.append("含比分/总进球=高赔小注覆盖(非主力,同玩法ρ高禁组)" + "、".join(cover))
    if seg:
        print("  分型契合：" + "；".join(seg))
    # 仓位汇总（凯利七步后的“占总资金比例”，标准档，与本金绝对额无关）
    sum_th = sum(sp["f_theory"] for _, _, sp in plans)
    sum_live = sum(sp["f_live"] for _, _, sp in plans)
    live_cand = sorted([(role, c, sp) for role, c, sp in plans if sp["f_live"] > 0],
                       key=lambda z: -z[2]["f_live"])[:MAX_PARLAY_LIVE]
    print(f"  仓位汇总：5注理论比例合计 Σf={sum_th * 100:.3f}%、当前【实盘】合计 Σf_live={sum_live * 100:.3f}%"
          f"（日仓上限{DAILY_CAP * 100:.0f}%内；实盘=过双锐线/每腿CLV≥+3%/S+闸门后的比例）；")
    if live_cand:
        names = "、".join(role.split("·")[0] for role, _, _ in live_cand)
        s_live = sum(sp["f_live"] for _, _, sp in live_cand)
        print(f"  红灯⑫单日实盘2串1≤{MAX_PARLAY_LIVE}组：{names} 已过实盘闸门，实盘合计{s_live * 100:.3f}%；")
    else:
        print("  红灯⑫单日实盘2串1≤2组：今晚无任一注通过实盘闸门(缺锐线/CLV不足/置信度<S+/博冷/负EV)，"
              "实盘总额=0、全部纸面；")
    print(f"  占比规则：2串1Σf须≤当日全部投注f的{COMBO_RATIO * 100:.0f}%且单关≥60%——本器只产2串1、无单关，")
    print("           故无锐线/无单关搭配时实盘总额=0；固定本金、不追黑、回撤≥5%按×0.8、≥20%停手。")

    print_portfolio_kelly(A, plans)
    opt_sel = print_optimal_five(A, combos_val)
    # v5.3.2 赛果结算回测（有 res 才输出；优先结算【主推荐】全局EV注，其次角色注）
    settle_review(A, opt_sel if opt_sel else final)
    calibrate_from_history(MATCHES)   # v5.3.3 赛果滚动校准（带res≥8场才输出参数建议）
    # v5.5 最终交付：今晚500元投注单（自带每注金额+盈亏情景，用户可直接照买）
    print()
    betting_slip = print_betting_slip(A, opt_sel if opt_sel else final, NIGHT_BANKROLL, all_combos=combos_val)
    # ===== v5.6：蒙特卡洛盈亏模拟 / CLV台账落账 / 滚动台账 / 时间熔断 / 今晚决策显式化 =====
    try: monte_carlo_slip(betting_slip, A)
    except Exception as _e: print(f"v5.6蒙特卡洛异常(跳过):{_e}")
    try: append_journal_from_slip(A, betting_slip, batch=MATCH_DATE)
    except Exception as _e: print(f"v5.6台账落账异常(跳过):{_e}")
    try: journal_report()
    except Exception as _e: print(f"v5.6台账报告异常(跳过):{_e}")
    # _lock56 已在选注前前置计算（保证 stake_plan 实盘比例受熔断控制），此处直接复用
    try: decision_briefing(A, betting_slip, lock=_lock56)
    except Exception as _e: print(f"v5.6决策简报异常(跳过):{_e}")
    globals()["_TILT_LOCK56"] = False   # 运行结束复位，避免污染同进程后续调用
    # ===== v5.5.2 赛前快照锁存 / 赛后只读锁存结算（不改动上方任何赛前流程与结算口径）=====
    # v5.7.1 P2 三通道比分（优先级）：POST_RESULTS手填dict > RESULTS_TEXT粘贴比分串 > 官方自动接口(当前403则空,不编造)
    _res_all = dict(POST_RESULTS or {})
    for _k, _v in parse_results_text(RESULTS_TEXT).items():
        _res_all.setdefault(_k, _v)
    if AUTO_RESULTS_ENABLED and not _res_all:
        for _k, _v in collect_results_sporttery().items():
            _res_all.setdefault(_k, _v)
    if _res_all:
        globals()["POST_RESULTS"] = _res_all
        try: settle_journal(_res_all, batch=MATCH_DATE)  # v5.6 赛后台账结算
        except Exception as _e: print(f"v5.6台账结算异常(跳过):{_e}")
        # 赛后对账：本次重算仅用于展示；结算只读【赛前快照】，绝不重算首选、绝不覆盖快照
        print()
        line(); print("§v5.5.2/v5.7.1 赛后锁存结算：不重算/不覆盖赛前首选，只读快照对账，并自动攒校准样本。"); line()
        _snap_path = SNAPSHOT_TO_SETTLE or _find_latest_snapshot(MATCH_DATE)
        try:
            settle_snapshot_file(batch=MATCH_DATE, results=_res_all)
        except Exception as _e:
            print(f"⚠赛后锁存结算失败（不影响其余输出）：{_e}")
        # v5.7.1 P2：结算后自动写校准样本库(去重) + 打印滚动校准概况，形成"攒样本→校准→下次出单"闭环
        try:
            if _snap_path:
                _snap4c = load_snapshot(_snap_path)
                calib_append_from_snapshot(_snap4c, _res_all)
                line(); print("§v5.7.1 校准样本库滚动概况（赛后）："); calib_report(); line()
                # v5.8.2 分让球档τ【真实赛果】回测：攒够样本自动给 HANDICAP_DIAG_TAU_BY 建议，样本不足只提示不刷屏
                try:
                    tau_by_handicap_report()
                except Exception as _e2:
                    print(f"⚠v5.8.2 分档τ回测跳过（不影响结算）：{_e2}")
                # v5.8.2 回测后顺手更新"各档τ随样本量收敛轨迹"文本+PNG(台账不足会优雅跳过；开关TAU_CONV_AUTO_AFTER_SETTLE)
                try:
                    if TAU_CONV_AUTO_AFTER_SETTLE:
                        tau_by_convergence_report(make_figure=True)
                except Exception as _e3:
                    print(f"⚠v5.8.2 τ收敛轨迹更新跳过（不影响结算）：{_e3}")
                # v5.8.3 建议①ρ自适应 / 建议③分层校准 真实赛果回测(样本不足只提示、只给证据不自动改参)
                try:
                    rho_adaptive_report()
                except Exception as _e4:
                    print(f"⚠v5.8.3 ρ自适应回测跳过（不影响结算）：{_e4}")
                try:
                    calib_stratified_report(market="W")
                except Exception as _e5:
                    print(f"⚠v5.8.3 分层校准回测跳过（不影响结算）：{_e5}")
        except Exception as _e:
            print(f"⚠v5.7.1 校准样本攒库失败（不影响结算）：{_e}")
        # v5.8.1 赛后所有写入(台账/锁存结算/校准样本)完成后，自动打包 jc_data，省掉手动 backup 指令
        if AUTO_BACKUP_AFTER_SETTLE:
            try:
                line(); auto_backup_data_dir(tag="赛后自动备份"); line()
            except Exception as _e:
                print(f"⚠赛后自动备份失败（不影响结算）：{_e}")
    elif SAVE_SNAPSHOT:
        # 赛前出单：锁存一份永不覆盖的赛前快照，供次日只读对账
        try:
            save_pre_match_snapshot(A, opt_sel if opt_sel else final, betting_slip, batch=MATCH_DATE)
        except Exception as _e:
            print(f"⚠v5.5.2 赛前快照锁存失败（不影响主流程）：{_e}")
    # —— 5. 风控与合规尾注 ——
    print()
    line()
    print("合规与风控（v38.4）：①只跨场串、同场不同玩法禁串(⑤)；②比分剔4球+(⑩)/总进球剔5球+(⑪)，")
    print("  C/D类为单选2串(1注)，三选及以上复式禁止(㉘)，双选复式仅在锐线错价≥5%才用；③ρ上限≥0.3禁组(⑱)，")
    print("  同联赛×0.95仅是概率折减≠ρ；④无锐线仅G8/G9单关可投、禁串关，2串1须每腿CLV≥+3%+置信度S+；")
    print("  ⑤单日实盘2串1≤2组(⑫)、2串1总f≤当日25%、含比分/总进球腿f≤0.5%；半全场③禁飞。本器不替代主口令风控。")
    print("  ★数学事实：高命中≠盈利——维度一热门串EV多为负(水位)，单次/单日无法确保盈利、连黑是常态；")
    print("   长期总体盈利的唯一路径是：只在正EV(维度二)且经锐线CLV验证时下注＋足够样本＋凯利仓位纪律。")
    line()
    print()
    show_manual()
    line()
    try: show_auto_run_sop(compact=True)   # v5.6 全自动固定指令提示
    except Exception: pass
    line()


if __name__ == "__main__":
    main()
