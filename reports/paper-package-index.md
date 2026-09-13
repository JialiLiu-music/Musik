# 论文材料包索引与交付说明

> 当前状态：本地论文材料包已整理并通过一致性审计。远程冻结机器可读报告已只读同步到 `reports/frozen-inputs-20260913-120829`；正式分轴表、模型比较图、边界误差图、来源哈希和交付元数据已生成到 `reports/final-paper-package-20260913-121100`。

## 一、核心论文文档

| 文件 | 用途 | 是否可直接作为正文基础 |
|---|---|---|
| `reports/paper-draft.md` | 摘要、引言、数据、模型、实验、结果、讨论、限制和结论 | 是，可结合正式图表和填充表格排版 |
| `reports/paper-materials.md` | 方法、协议、结果和限制的完整材料汇总 | 是，用于核对事实和数值来源 |
| `reports/paper-tables.md` | 数据规模、模型关系、CCC 汇总、配对统计和边界分层表 | 是，原始模板保留；正式填充版见交付目录 |
| `reports/paper-captions-and-citations.md` | 图注、表注、正文交叉引用和禁止性表述替换 | 是，用于最终排版 |
| `reports/paper-figures-checklist.md` | 图表规格、数据来源、投稿前核对清单 | 是，用于排版和复现验收 |

## 二、审计与生成工具

| 文件 | 用途 | 当前验证状态 |
|---|---|---|
| `audit_paper_materials.py` | 审计论文材料章节、关键数值和结论边界 | `PAPER_MATERIALS_AUDIT status=ok` |
| `render_paper_figures.py` | 从冻结 JSON 只读生成模型比较图和边界误差图 | 语法、CLI、临时协议端到端绘图通过 |
| `finalize_paper_package.py` | 校验冻结报告、填充分轴表、生成图表、保存来源哈希和交付元数据 | 正式收口通过；推荐目录 `reports/final-paper-package-20260913-121100` |
| `reports/paper-materials-audit.json` | 最近一次论文材料机器审计结果 | `status=ok` |

## 三、冻结结果来源

最终排版使用以下冻结结果，不得从正文手工推导新的数值：

- 本地只读副本 `reports/frozen-inputs-20260913-120829/paper-results.json`：模型汇总、跨种子均值/标准差和逐曲误差清单；
- 本地只读副本 `reports/frozen-inputs-20260913-120829/formal-test-analysis.json`：bootstrap、配对置换、Holm 校正、边界距离分层和失败/排除审计；
- 正式交付目录 `reports/final-paper-package-20260913-121100`：填充表格、正式 PNG、图表元数据、来源哈希和交付元数据；
- 远程项目仍为冻结源头；本地副本 SHA-256 已记录在正式交付目录的 `source-sha256.json`。

## 四、当前已确认的论文结论

- 验证集上 B2 的曲目级 `ccc_mean=0.123921`，为五个模型中最高；
- 测试集 B2=`0.027514`，S1=`0.027084`，两者基本持平；
- S1−B2 的测试集平均差为 `-0.000430`，置换 `p=0.981702`；
- S1−B3 的测试集平均差为 `0.022841`，置换 `p=0.226977`；
- Holm 校正后的预定义主要比较均未显著；
- 当前实验没有获得自动乐段层级上下文带来稳定增量收益的证据。

## 五、最终排版操作顺序

1. 使用 `reports/final-paper-package-20260913-121100/paper-tables-filled.md` 作为表格排版来源；
2. 使用 `reports/final-paper-package-20260913-121100/figure-model-comparison.png` 和 `figure-boundary-error.png` 作为正式图表来源；
3. 使用 `source-sha256.json` 和 `delivery-metadata.json` 核对冻结报告、表格模板、渲染脚本和输出列表；
4. 检查正文、表格、图注和摘要是否保留测试集隔离、曲目级统计和自动结构非人工真值边界；
5. 运行 `audit_paper_materials.py --reports-dir reports`，确认材料、冻结输入和正式交付目录均为 `ok`；
6. 不使用测试集结果反向修改模型、超参数、数据划分或已封存结论。

## 六、禁止事项

- 不把 All-In-One 自动结构写成人工结构真值；
- 不把验证集最优直接写成测试集泛化最优；
- 不把未显著结果写成自动结构增益；
- 不根据 `ccc_mean` 反推 Valence/Arousal 分轴指标；
- 不使用测试集逐曲误差清单筛选曲目或调参；
- 不修改原始 `data/manifest.csv`、音频、标签、结构、MERT 特征、checkpoint 和冻结预测。