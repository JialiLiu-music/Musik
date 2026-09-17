ssh -p 12524 [root@connect.nmb2.seetacloud.com](mailto:root@connect.nmb2.seetacloud.com)
密码：yRVW7QoAr/hd
/root/autodl-tmp/music-emotion-project

这两个文档（/Users/jialiliu/Desktop/数据集/乐曲结构与动态情感分析.md 和/Users/jialiliu/Desktop/数据集/数据集、人工处理与数据协议.md）是用来介绍我们当前需要完善的论文实验：乐曲结构与动态情感分析。
目前我们已经在 /root/autodl-tmp/music-emotion-project 这个文件夹中放置了很多文件，其中 /root/autodl-tmp/music-emotion-project/data 是存放 DEAM 数据集的目录。接下来需要先确认远程环境、数据布局和可执行工具，再按文档中定义的实验边界推进实现。

然后，对于这个服务器：
如果要访问 GitHub 资源，可以使用 [https://ghfast.top，例如：git](https://ghfast.top，例如：git) clone [https://ghfast.top/https://github.com/stilleshan/dockerfiles](https://ghfast.top/https://github.com/stilleshan/dockerfiles)
如果要访问 Hugging Face，可以使用镜像站：
export HF_ENDPOINT=[https://hf-mirror.com](https://hf-mirror.com)
pip install -U huggingface_hub
huggingface-cli download --resume-download gpt2 --local-dir gpt2

---



## 当前执行记录



### 1. 本地文档确认

已阅读并确认两份约束文档中的核心要求：

- 主数据集是 DEAM，用于逐秒 Valence/Arousal 监督；
- 结构信息来自冻结的 All-In-One 自动输出，不当作人工真值；
- 首轮实验只做 B0 / B1 / B2 / B3 / S1 这五类模型对比；
- 需要把执行命令、问题和处理结果持续记录到 md 文档中。



### 2. 远程服务器初次检查

先尝试了直接 SSH 连接，发现本地环境缺少 `sshpass` 和 `paramiko`，因此改用 `expect` 自动输入密码；第一次非交互 SSH 认证失败，后续用 `expect` 成功进入远程机器。

已确认的远程项目根目录：

- `/root/autodl-tmp/music-emotion-project`

目录现状：

- `data/`
- `experiments/`
- `features/`
- `models/`
- `results/`
- `scripts/`

其中 `scripts/`、`features/`、`results/` 目前都是空目录，说明项目还没有进入完整的实验流水线阶段。

### 3. 数据现状

已确认远程 `data/` 下的关键内容：

- `DEAM_audio/` 下有 205 个 `.mp3` 文件；
- `annotations_raw/annotations averaged per song/dynamic (per second annotations)/` 下存在：
  - `valence.csv`
  - `arousal.csv`
- `annotations_raw/annotations averaged per song/song_level/` 下存在静态标注 CSV；
- `annotations_raw/annotations per each rater/` 下存在逐标注者的动态与静态标注目录。

进一步读取文件头后确认：

- `valence.csv` 与 `arousal.csv` 的列名从 `sample_15000ms` 开始；
- 数据频率是 500ms 一列，和文档中对 DEAM 动态标签的说明一致；
- 当前环境下可用的 Python 是 `/root/miniconda3/bin/python`；
- `torch` 可用，版本为 `2.12.1+cu130`；
- `torch.cuda.is_available()` 为 `True`，且可见 1 张 GPU。



### 4. 发现的问题

- 第一次 SSH 连接失败，原因是当前本地环境没有 `sshpass` / `paramiko`，直接密码自动输入不可用；
- 远程环境一开始通过错误方式调用 `python3`，报出 `python3: command not found`；
- 后续确认远程实际可用解释器是 `python`，路径为 `/root/miniconda3/bin/python`，而不是 `python3`。



### 5. 当前处理结果

已经完成以下判断：

- 远程机器可用，且已经连通到目标项目目录；
- DEAM 音频与动态标签都已经放好；
- 项目目录里还没有正式实现的训练、特征提取、评估脚本；
- 后续可以直接基于 `/root/miniconda3/bin/python` 在这个环境里继续搭建数据处理与实验流程。

---

---



## 6. 追加执行记录（本轮）



### 6.1 远程环境确认

- 远程解释器可用路径：`/root/miniconda3/bin/python`
- `conda` 可用路径：`/root/miniconda3/bin/conda`
- 当前项目没有进入 git 仓库状态，不能按仓库提交流程处理；因此本轮只做文件落盘与执行记录。



### 6.2 新增脚本

已在远程项目 `scripts/` 下放入最小可运行脚本：

- `scripts/prepare_deam.py`

它完成的事情是：

- 扫描 `data/DEAM_audio/*.mp3`；
- 读取 `data/annotations_raw/annotations averaged per song/dynamic (per second annotations)/valence.csv` 与 `arousal.csv`；
- 以标准库生成 `data/manifest.csv`；
- 显式保留未解析的音频时长和采样率字段，不凭空猜测；
- 先把结构字段留空，后续再接 All-In-One 输出。



### 6.3 遇到的问题

1. `valence.csv` 与 `arousal.csv` 的动态标签采样列数不完全一致：
  - `valence_sample_count=1223`
  - `arousal_sample_count=1224`
  - 但它们共享的起始时间一致，都是 `15000ms`
2. 第一次脚本版本直接要求两份表头完全相同，因此在远程运行时抛出：
  - `ValueError: valence/arousal sample grids do not match`
3. 重新设计后，将脚本改成“取共同采样列”策略，避免因一列差异阻断整个预处理流程。



### 6.4 当前结果

最终已成功生成：

- `data/manifest.csv`

远程验证输出如下：

- `audio_count=205`
- `valence_track_count=1802`
- `arousal_track_count=1802`
- `shared_sample_count=1223`
- `first_shared_sample_ms=15000`

`manifest.csv` 头两行已检查，字段顺序正确，首条记录可读。

### 6.6 这一轮新增校验结果

已新增并远程同步：

- `scripts/validate_manifest.py`

它的职责是：

- 检查 `manifest.csv` 是否具备完整字段；
- 检查 `audio_path` 指向的文件是否存在；
- 检查 `label_path` 是否存在；
- 统计空的 `duration_sec` 与 `sample_rate` 行数；
- 输出一组便于后续流水线消费的校验统计。

远程执行结果如下：

- `row_count=205`
- `missing_audio=0`
- `missing_label_dir=0`
- `excluded_rows=0`
- `blank_duration_rows=205`
- `blank_sample_rate_rows=205`
- `data_root_exists=1`

这说明：

- `manifest.csv` 已经能被稳定读取；
- 当前索引的音频与标签路径都有效；
- 但音频元信息还没有补齐，所以 `duration_sec` 和 `sample_rate` 仍保持空值；
- 后续需要单独补一个音频元信息提取步骤，再把这些字段回填进 `manifest`。



### 6.7 当前项目状态

现在远程项目已经至少具备两个可复用入口：

1. `scripts/prepare_deam.py`：生成索引；
2. `scripts/validate_manifest.py`：校验索引。

这意味着数据入口层已经从“手工检查”变成“可重复执行的脚本流程”。

### 6.9 音频元信息回填结果

已新增并远程同步：

- `scripts/fill_audio_metadata.py`

它的职责是：

- 读取已经生成的 `manifest.csv`；
- 使用 `mutagen` 从每个 MP3 中提取时长和采样率；
- 回填 `duration_sec` 与 `sample_rate`；
- 原地覆盖 `manifest.csv`，保持字段顺序不变；
- 继续用 `validate_manifest.py` 检查回填后的结果。

远程执行结果如下：

- `updated_rows=205`
- `already_aligned_rows=0`
- `output_path=data/manifest.csv`
- `row_count=205`
- `missing_audio=0`
- `missing_label_dir=0`
- `excluded_rows=0`
- `blank_duration_rows=0`
- `blank_sample_rate_rows=0`
- `data_root_exists=1`

这说明：

- `manifest.csv` 里的音频元信息已经被补齐；
- 校验脚本确认当前 205 条记录都能被正确读取；
- 数据入口层已经具备“生成索引 → 校验索引 → 回填音频元信息 → 再校验”的完整闭环。



### 6.10 当前阶段结论

现在远程项目已经具备三个脚本入口：

1. `scripts/prepare_deam.py`
2. `scripts/validate_manifest.py`
3. `scripts/fill_audio_metadata.py`

这三个脚本已经覆盖：

- 索引生成；
- 索引校验；
- 音频元信息回填。



### 6.11 动态标签 1Hz 聚合结果

已新增并远程同步：

- `scripts/make_labels_1hz.py`

它的职责是：

- 读取 `valence.csv` 与 `arousal.csv`；
- 只使用两份表里都存在的共享 500ms 栅格；
- 按 `sample_15000ms` + `sample_15500ms` 这种严格相邻的 500ms 对生成 1Hz 结果；
- 输出 `data/labels_1hz/deam_XXXX.csv`；
- 每个输出文件包含 `time_sec,valence,arousal,valid` 四列；
- 同步更新 `manifest.csv` 里的 `label_path`、`label_hz`、`label_start_sec`、`label_end_sec`。

远程执行结果如下：

- `tracks_written=205`
- `rows_written=125255`
- `valid_rows=6150`
- `shared_sample_count=1223`
- `shared_start_ms=15000`
- `shared_end_ms=626000`
- `manifest_path=/root/autodl-tmp/music-emotion-project/data/manifest.csv`
- `labels_root=/root/autodl-tmp/music-emotion-project/data/labels_1hz`

随后再次校验 `manifest.csv`，结果如下：

- `row_count=205`
- `missing_audio=0`
- `missing_label_dir=0`
- `excluded_rows=0`
- `blank_duration_rows=0`
- `blank_sample_rate_rows=0`
- `data_root_exists=1`

这说明：

- 1Hz 派生标签已经稳定落盘；
- `manifest.csv` 已经切换到 1Hz 标签目录；
- 当前数据入口层的索引、音频元信息、动态标签聚合已经连成闭环。



### 7.1 下一阶段计划确认与执行起点

已阅读 `下一阶段工作计划.md`，确认下一阶段不直接跳到训练，而是按下面顺序建立完整数据闭环：

1. 统一 WAV；
2. 固定 train / val / test 曲目划分；
3. 接入 All-In-One 结构分析结果；
4. 提取 MERT 音频特征；
5. 完成音频、标签、结构、特征的时间轴对齐；
6. 再进入基线模型和结构感知模型训练。

本轮先把执行范围收敛到前两个 checkpoint：

- 音频统一转换；
- 固定曲目划分与资产校验。



### 7.2 本地新增脚本

已在本地新增三个脚本，准备同步到远程项目 `scripts/`：

1. `convert_audio_wav.py`
  - 读取 `data/manifest.csv`；
  - 保留原始 MP3 路径到 `raw_audio_path`；
  - 将 `audio_path` 切换到模型用 WAV；
  - 默认输出到 `data/audio_wav/deam_XXXX.wav`；
  - 默认统一为 mono / 16000 Hz / PCM WAV。
2. `split_manifest.py`
  - 读取 `manifest.csv`；
  - 以 `track_id` 为单位做确定性划分；
  - 默认比例为 train 70%、val 15%、test 15%；
  - 默认 seed 为 `deam-structure-emotion-v1`；
  - 目标是避免同一首曲目跨集合泄漏。
3. `validate_assets.py`
  - 检查 `manifest.csv` 中的 WAV 音频是否存在；
  - 检查 `raw_audio_path` 是否还能回到原始 MP3；
  - 检查 `labels_1hz/deam_XXXX.csv` 是否存在；
  - 统计 train / val / test 行数；
  - 统计标签总行数和有效标签行数。

这三个脚本构成下一层数据入口：

```text
manifest.csv
  -> convert_audio_wav.py
  -> split_manifest.py
  -> validate_assets.py
  -> 可训练样本入口
```



### 7.3 当前阻塞

本轮尝试通过 `expect + ssh/scp` 继续访问远程服务器时，连接在认证前被远端直接关闭，典型输出为：

- `Connection closed by 198.18.2.238 port 12524`
- `scp: Connection closed`

因此目前状态是：

- 本地脚本已经准备完成；
- 本地脚本已经准备完成；
- 远程同步和执行曾被 SSH 连接中断阻塞；
- All-In-One 可用性尚未完成远程确认。

连接恢复后，执行顺序为：

```text
scp convert_audio_wav.py / split_manifest.py / validate_assets.py
  -> python scripts/convert_audio_wav.py
  -> python scripts/split_manifest.py
  -> python scripts/validate_assets.py
  -> 检查 All-In-One 是否已安装或是否需要安装
```



### 7.4 远程恢复后的执行结果

远程连接恢复后，已成功同步以下脚本到项目 `scripts/`：

- `convert_audio_wav.py`
- `split_manifest.py`
- `validate_assets.py`

随后执行固定曲目划分：

```text
/root/miniconda3/bin/python scripts/split_manifest.py \
  --manifest /root/autodl-tmp/music-emotion-project/data/manifest.csv
```

执行结果：

- `row_count=205`
- `updated_rows=205`
- `train_rows=144`
- `val_rows=31`
- `test_rows=30`
- `seed=deam-structure-emotion-v1`

划分以 `track_id` 为唯一单位，未把同一首歌曲拆到不同集合中。

执行 WAV 转换初次发现远程环境没有 `ffmpeg`，随后使用远程 Conda 安装成功：

- `ffmpeg version 9.0.1`
- 安装路径：`/root/miniconda3/bin/ffmpeg`

使用绝对路径重新执行 WAV 转换后，资产校验通过：

- `row_count=205`
- `wav_audio_rows=205`
- `missing_audio=0`
- `missing_raw_audio=0`
- `missing_label_file=0`
- `invalid_split_rows=0`
- `train_rows=144`
- `val_rows=31`
- `test_rows=30`
- `total_label_rows=125255`
- `valid_label_rows=6150`

这说明：

- 205 首音频均已生成模型用 WAV 路径；
- 原始 MP3 路径通过 `raw_audio_path` 保留；
- 205 首音频、1Hz 标签和固定数据划分已经在 `manifest.csv` 中闭合；
- 没有缺失音频、标签或非法划分记录。



### 7.5 All-In-One 当前状态

远程项目内尚未发现 All-In-One 结构分析产物，Python 环境中的 `allinone` 模块也不存在：

- `allinone=False`

因此下一步不是直接写结构索引，而是先安装或同步 All-In-One 工具及其模型权重，然后对 205 首 WAV 生成冻结结构输出。结构输出应独立保存，并在生成后回填：

- `structure_path`
- `structure_version`
- `structure_start_sec`
- `structure_end_sec`



### 7.6 最终校验

再次运行原有 `validate_manifest.py`，结果为：

- `row_count=205`
- `missing_audio=0`
- `missing_label_dir=0`
- `excluded_rows=0`
- `blank_duration_rows=0`
- `blank_sample_rate_rows=0`
- `data_root_exists=1`
- `wav_files=205`

当前可确认的阶段成果：

### 8.1 All-In-One 官方入口确认

已确认官方仓库和使用协议：

- 仓库：`mir-aidj/all-in-one`
- Python 包：`allin1==1.1.0`
- CLI：`allin1 <audio.wav> -o <output_dir>`
- 默认模型：`harmonix-all`
- 输入建议：统一使用 WAV，避免 MP3 解码造成 20–40ms 时间偏移
- JSON 输出核心字段：`path`、`bpm`、`beats`、`downbeats`、`beat_positions`、`segments`
- `segments` 记录 `start`、`end` 和功能标签，例如 `intro`、`verse`、`chorus`、`bridge`

本项目只把 All-In-One 输出作为冻结的自动结构输入，不把它称为人工结构真值。后续结构索引至少保存：

- `track_id`
- `structure_path`
- `structure_version`
- `structure_start_sec`
- `structure_end_sec`
- `structure_segment_count`



### 8.2 远程环境准备结果

远程环境检查结果：

- GPU：`NVIDIA GeForce RTX 3080 Ti, 12288 MiB`
- 可用磁盘：约 `50G`
- Git：`2.34.1`
- 已创建独立 Conda 环境：`/root/miniconda3/envs/aio`
- Python：`3.10.21`

文档建议组合为 Python 3.10、PyTorch 2.5.0、NATTEN 0.17.5 和 `allin1==1.1.0`。首次创建环境时，Conda 的 `libmamba` solver 配置失效，改用 `--solver classic` 后环境创建成功。

随后尝试安装 PyTorch wheel，但下载源在超时后中止：

- `aio` 环境目前只有 `pip/setuptools/wheel`；
- `torch` 尚未安装；
- `allin1` 尚未安装；
- 远程项目仍没有结构输出。

因此当前准确状态是：

```text
官方结构输出格式：已确认
GPU 与磁盘条件：已确认
独立 aio 环境：已创建
PyTorch / NATTEN / allin1：待解决下载源后安装
单曲目结构验证：尚未执行
205 首批量结构分析：尚未执行
```

下一步应优先解决 PyTorch/NATTEN 的兼容 wheel 获取，再运行一首 WAV 的 `allin1` 验证；验证 JSON 字段和时间范围后，才批量生成结构文件并回填 `manifest.csv`。

```text
```text
MP3 原始资产
  -> 16000 Hz / mono / PCM WAV
  -> 固定 train / val / test 曲目划分
  -> 1Hz VA 标签
  -> manifest.csv 统一引用
```

### 2026-09-10：All-In-One 环境准备状态更新（未完成）

- 功能名称：独立 `aio` 环境的 PyTorch/CUDA 依赖准备；
- 当前状态：未完成，不能进入 All-In-One 推理验证；
- 已确认：`torch==2.5.0+cu121` 已安装，`nvidia-cuda-runtime-cu12==12.1.105` 已安装；
- 安装方式：切换到 `https://pypi.tuna.tsinghua.edu.cn/simple`，单一后台安装任务继续获取 CUDA 依赖；
- 最近安装进度：`cuDNN` 已下载约 617 MB，随后开始下载 `nvidia-cublas-cu12`；
- 当前阻塞：远程 SSH 连接连续被节点主动关闭，尚未重新获得安装日志和最终验证结果；
- 未确认项：CUDA 依赖完整性、`torch.cuda.is_available()`、GPU 型号、`NATTEN`、`allin1` 和单曲目 JSON 输出；
- 数据与原始 MP3/WAV/标签文件未修改。

在重新获得远程连接并确认以下结果前，不将环境准备标记为完成：

```text
import torch
  -> torch.__version__
  -> torch.version.cuda
  -> torch.cuda.is_available()
  -> torch.cuda.get_device_name(0)
```

### 2026-09-10：CUDA 依赖安装后续检查（仍未完成）

- 功能名称：独立 `aio` 环境的 CUDA 依赖补齐与 Torch 验证；
- 当前状态：未完成，不能进入 All-In-One 推理验证；
- 本轮操作：继续使用清华 PyPI 镜像安装剩余 CUDA 依赖，并尝试验证 `torch` 与 `natten`；
- 观测结果：安装任务结束后，远程 SSH 在认证后不再返回命令输出；`torch` 版本、CUDA 可用性、GPU 型号和 `natten` 版本均未取得可复验证据；
- 当前阻塞：远程节点在密码认证后命令挂起，连最小 `echo REMOTE_OK` 检查也在超时；
- 未确认项：CUDA 依赖完整性、`torch.cuda.is_available()`、GPU 型号、`NATTEN`、`allin1` 和单曲目 JSON 输出；
- 数据与原始 MP3/WAV/标签文件未修改；
- 处理原则：不把此次环境准备标记为完成，不启动 All-In-One 安装或结构批处理。

### 2026-09-10：远程节点恢复重试与环境验证（仍未完成）

- 功能名称：远程 `aio` 环境可达性和 Torch/NATTEN 验证；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：重试 SSH 最小命令，并在连接恢复后执行 `pip show`、Torch 导入和 NATTEN 导入验证；
- 观测结果：最小 `printf REMOTE_OK` 曾成功返回，但随后带 Python 环境检查的连接再次在密码认证后超时；
- 当前阻塞：远程节点的 SSH 会话稳定性不足，无法获得完整、可复现的依赖版本和 GPU 验证输出；
- 未确认项：CUDA 依赖完整性、`torch.cuda.is_available()`、GPU 型号、`natten` 版本、`allin1` 和单曲目 JSON 输出；
- 数据与原始 MP3/WAV/标签文件未修改；
- 处理原则：不启动 All-In-One 安装、单曲目推理或结构批处理，直到环境验证命令稳定返回。

### 2026-09-10：远程环境再次验证失败（仍未完成）

- 功能名称：远程节点恢复后的 `aio` 环境复核；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：使用连接超时、重试次数和 keepalive 参数，执行最小连通性、Python 版本和 `pip show` 检查；
- 观测结果：SSH 到达密码认证阶段，但在认证后 20 秒内未返回 `REMOTE_OK`、Python 版本或依赖信息；
- 当前阻塞：远程节点仍无法稳定执行命令，现有连接不足以证明 CUDA、Torch 或 NATTEN 状态；
- 未确认项：`torch.cuda.is_available()`、GPU 型号、`natten` 版本、`allin1` 和单曲目 JSON 输出；
- 数据与原始 MP3/WAV/标签文件未修改；
- 处理原则：不启动 All-In-One 安装、单曲目推理或结构批处理。

### 2026-09-10：远程节点低频连通性复查（仍未完成）

- 功能名称：远程 All-In-One 环境恢复检查；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：等待并重新执行带连接超时控制的最小 SSH 命令 `printf 'REMOTE_OK'`；
- 观测结果：节点可进入密码认证阶段，但认证后仍未在规定时间内返回最小输出；
- 当前阻塞：远程执行通道不稳定，无法安全读取或修改 `aio` 环境；
- 未确认项：Torch/CUDA/NATTEN 完整验证、All-In-One 安装、单曲目推理和结构批处理；
- 数据与原始 MP3/WAV/标签文件未修改；
- 处理原则：继续保持结构分析任务未启动，避免在不稳定节点上产生不可复现产物。

### 2026-09-10：All-In-One 本地结构处理链路准备（部分完成）

- 功能名称：All-In-One 批处理、独立结构索引和结构资产校验组件；
- 当前状态：本地脚本已完成并通过 Python 语法检查，远程结构执行仍未开始；
- 新增文件：`run_allin1_batch.py`、`index_allin1_structure.py`、`validate_allin1_structure.py`；
- 数据流设计：`manifest.csv` 提供曲目和 WAV 路径；批处理器为每首曲目生成独立 JSON；索引器只读取 JSON 并生成独立 CSV；校验器检查 JSON、segments 字段、边界单调性和索引完整性；
- 输出约束：结构 JSON 保存为 `structure_allin1/<track_id>.json`，批处理日志保存为 `batch_log.jsonl`，不覆盖原始 MP3、WAV、标签或现有 manifest 字段；
- 可复现参数：批处理器支持固定 CLI、输出目录和 `--limit`，索引器显式记录 `structure_version` 和 UTC 分析时间；
- 本地验证：三个脚本均通过 `python -m py_compile`，已检查新增脚本诊断；
- 远程状态：SSH 节点仍在密码认证后超时，新增脚本尚未同步或执行；
- 当前阻塞：必须先恢复稳定远程执行通道，再同步脚本、验证 `aio` 环境并运行单曲目；
- `task-26` 和 `task-27` 仍不能标记完成。

### 2026-09-10：本地结构链路端到端验证（部分完成）

- 功能名称：结构 JSON 生成结果的索引与完整性校验；
- 当前状态：本地验证完成，远程 205 首结构分析仍未开始；
- 验证方法：使用临时合成 manifest 和两段有序 segment 的 JSON，执行索引生成后再执行结构校验；
- 验证结果：`index_rows=1`、`indexed_json=1`、`missing_json=0`、`invalid_json=0`、`invalid_segments=0`、`blank_bounds=0`；
- 功能名称：All-In-One 批处理器的成功、断点和失败分支；
- 验证方法：使用临时模拟 CLI 和一个缺失音频行，执行批处理器；
- 验证结果：成功行 `written=1`、缺失音频行 `failed=1`、日志行数为 `2`，证明失败不会被静默吞掉；
- 本地脚本均已通过语法检查，真实 All-In-One CLI 尚未运行；
- 远程状态：SSH 节点仍无法稳定执行命令，不能同步脚本或生成真实结构；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- `task-25`、`task-26`、`task-27` 仍按远程可验证结果推进。

### 2026-09-10：结构索引覆盖与 manifest 回填链路准备（部分完成）

- 功能名称：结构索引覆盖检查和 manifest 安全回填；
- 当前状态：本地组件完成，真实 205 首数据回填尚未执行；
- 新增文件：`validate_structure_coverage.py`、`update_manifest_structure.py`；
- 覆盖规则：结构索引必须与 manifest 的 `track_id` 集合完全一致，拒绝重复曲目、缺失曲目和额外曲目；
- 回填规则：仅覆盖结构字段，保留原 manifest 的音频、标签和 split 字段，并输出到新文件，不直接覆盖原始 `manifest.csv`；
- 本地验证结果：`manifest_tracks=2`、`index_tracks=2`、`missing_index_tracks=0`、`extra_index_tracks=0`、`updated_rows=2`、`complete_rows=2`；
- 远程同步结果：`update_manifest_structure.py` 和 `validate_structure_coverage.py` 已通过 SCP 传入远程 `scripts/` 目录；
- 远程状态：SCP 文件传输可用，但 SSH 认证后的命令执行仍不稳定，尚未运行真实结构分析；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- `task-25`、`task-26`、`task-27` 仍不能标记完成。

### 2026-09-10：远程窗口再次关闭后的执行记录（未完成）

- 功能名称：远程脚本同步与 All-In-One 执行窗口复查；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：同时重试 SSH 最小命令和 SCP 远程脚本读取，未启动新的安装或批处理任务；
- 观测结果：SSH 在密码认证后超时，SCP 同样在密码认证后超时；本轮没有产生新的远程执行结果；
- 已保留成果：本地五个结构脚本、索引覆盖规则和安全 manifest 回填链路均已完成语法检查与临时数据验证；
- 当前阻塞：远程节点没有稳定执行窗口，因此无法取得 Torch/CUDA/NATTEN 验证、All-In-One 单曲目 JSON 或 205 首批处理结果；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- 下一次恢复窗口的固定顺序：先验证最小 SSH 命令，再验证 `aio`，然后执行单曲目，最后才启动批处理。

### 2026-09-10：远程执行通道再次复查（仍未完成）

- 功能名称：远程 All-In-One 执行窗口复查；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：按固定顺序执行最小 SSH 命令，并尝试读取远程已同步的结构脚本；
- 观测结果：SSH 和 SCP 均在密码认证后超时，没有返回远程命令输出或文件内容；
- 当前阻塞：远程节点无法提供稳定执行窗口，不能证明 `aio` 环境或已同步脚本的实际状态；
- 保持不变：本地结构脚本和索引/回填链路已完成验证，原始 MP3/WAV/标签/manifest 未修改；
- 下一步入口：远程恢复后优先执行单一短命令验证，再运行带硬超时的 Torch 检查，避免再次启动长时间无输出任务。

### 2026-09-10：音频—标签—结构时间轴对齐入口（部分完成）

- 功能名称：逐秒样本表生成器；
- 当前状态：本地实现和临时数据验证完成，真实数据尚未执行；
- 新增文件：`build_aligned_samples.py`；
- 数据流：读取 `manifest.csv`、1Hz 标签文件和独立结构索引，把每个标签时间点映射到对应自动结构段，输出统一样本表；
- 输出字段：`track_id`、`split`、`time_sec`、`audio_path`、`label_path`、`valence`、`arousal`、`valid`、`segment_index`、`segment_label`；
- 对齐规则：结构段使用半开区间 `[start, end)`，时间点不落入任何结构段时保留空段归属；结构段起止必须递增且不能重叠；manifest 与结构索引的曲目集合必须完全一致；
- 本地验证结果：临时数据写入 `rows_written=4`、`valid_rows=3`、`structure_aligned_rows=4`，输出行数为 `4`；
- 远程同步结果：`build_aligned_samples.py` 已通过 SCP 传入远程 `scripts/` 目录；
- 当前阻塞：真实结构 JSON 尚未生成，暂不能构建正式对齐样本表；
- 数据与原始 MP3/WAV/标签/manifest 未修改。

### 2026-09-10：对齐样本表质量校验（部分完成）

- 功能名称：对齐样本表质量检查器；
- 当前状态：本地实现、临时数据验证和远程同步完成，正式数据尚未执行；
- 新增文件：`validate_aligned_samples.py`；
- 校验内容：必需字段、曲目数量、split 合法性、每曲目时间单调性、有效标签是否包含 valence/arousal、结构段归属是否为空；
- 本地验证结果：`rows=3`、`tracks=2`、`valid_rows=2`、`invalid_rows=0`、`blank_segment_rows=0`、`invalid_split_rows=0`、`non_monotonic_rows=0`、`split_count=2`；
- 远程同步结果：`validate_aligned_samples.py` 已通过 SCP 传入远程 `scripts/` 目录；
- 远程状态：SSH 认证后仍超时，无法执行正式样本表生成和校验；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- `task-25`、`task-26`、`task-27` 仍按真实远程产物推进。

### 2026-09-10：远程只读探测再次失败（未完成）

- 功能名称：All-In-One 远程环境恢复探测；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：执行远程残留进程查询，并以短超时重试最小 SSH 命令和 `aio` Python 版本检查；未启动安装、单曲目推理或批处理；
- 观测结果：连接在密码认证后被服务端关闭，未返回进程列表、`REMOTE_OK` 或 Python 版本；
- 结论：当前没有新的可验证环境证据，不能将 Torch/CUDA/`natten` 或 All-In-One 标记为已验证；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- 下一步入口：远程连接恢复后，仍按“残留进程查询 → Torch/CUDA → `natten` → 单曲目推理”的顺序执行。

### 2026-09-10：远程短连接三次复查（未完成）

- 功能名称：All-In-One 远程执行通道复查；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：等待后连续执行三次独立 SSH 短命令探测，命令均设置连接和会话硬超时；未启动安装、环境修改、单曲目推理或批处理；
- 观测结果：三次均以退出码 `255` 结束，均收到 `Connection closed by 198.18.2.0 port 12524`，没有返回远程命令输出；
- 结论：远程执行通道仍不可用，Torch/CUDA/`natten` 和 All-In-One 单曲目验证没有新增证据；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- 下一步入口：远程节点恢复后从残留进程查询开始，不重复安装已有依赖。

### 2026-09-10：SSH 已开启后的远程执行复查（未完成）

- 功能名称：All-In-One 远程环境恢复与最小命令验证；
- 当前状态：未完成，`task-25` 继续进行中；
- 本轮操作：在用户重新开启 SSH 后，尝试执行远程残留进程查询、`aio` Python 版本检查和独立最小 SSH 命令；未启动安装、环境修改、单曲目推理或批处理；
- 观测结果：远程连接未返回 `REMOTE_OK`、进程列表或 Python 版本；复查过程在认证后无输出并超时，无法证明远程 shell 已恢复；
- 结论：不能据此推进 Torch/CUDA/`natten` 验证，也不能启动 All-In-One；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- 下一步入口：取得稳定远程命令输出后，按“残留进程查询 → Torch/CUDA → `natten` → 单曲目推理”的顺序继续。

### 2026-09-10：Torch CUDA 环境恢复验证（部分完成）

- 功能名称：All-In-One GPU 基础运行环境；
- 当前状态：部分完成，Torch/CUDA 已验证，`natten` 和单曲目推理仍未完成；
- 修复内容：按 `torch 2.5.0+cu121` 的依赖要求补齐并统一 CUDA 12.1 组件，纠正此前错误安装的 CUPTI 12.9 版本；
- 验证命令：`/root/miniconda3/envs/aio/bin/python -c 'import torch; ...'`，外层设置 60 秒硬超时；
- 验证结果：`torch=2.5.0+cu121`、`cuda_build=12.1`、`cuda_available=True`、`device=NVIDIA GeForce RTX 3080 Ti`；
- 已知警告：环境缺少 `numpy`，Torch 导入产生 `Failed to initialize NumPy` 警告；该警告不影响本次 CUDA 可用性验证，但在 All-In-One 安装前必须补齐运行依赖；
- `natten` 当前仍未安装，尚未执行真实 All-In-One 单曲目推理；
- 数据与原始 MP3/WAV/标签/manifest 未修改；
- `task-25` 继续进行中，不能标记完成。

### 2026-09-10：All-In-One 依赖安装与单曲目验证（未完成）

- 功能名称：官方 All-In-One 运行依赖准备；
- 当前状态：部分完成，环境导入可用，但真实推理未完成；
- 远程仓库：`/root/autodl-tmp/all-in-one`，commit=`18e78903c0365147a2c5d4e5e57ebf88cb7d800e`；
- 已验证：`numpy=2.2.6`、`natten=0.17.5`、All-In-One CLI 可导入；官方要求的 `madmom` 已从 `https://github.com/CPJKU/madmom` 安装并验证导入；
- 兼容处理：All-In-One 当前 commit 使用旧 NATTEN 符号，而 NATTEN 0.17.5 提供 `na1d_qk`/`na1d_av`/`na2d_qk`/`na2d_av`；保留原 `dinat.py` 为 `dinat.py.orig`，新增最小 `natten_legacy_compat.py`，仅将旧调用参数映射到新 API；
- 单曲目输入：`data/audio_wav/deam_0076.wav`；设备参数：`--device cuda`；
- 运行结果：Demucs 阶段产生 1 组产物，All-In-One 后续阶段运行至 900 秒硬超时；`data/structure_allin1_smoke/` 中 `STRUCT_FILES=0`，未生成 JSON；
- 结论：不能声称单曲目推理完成，也不能启动 205 首批处理；当前需要继续定位 All-In-One 后续阶段的阻塞点；
- 原始 MP3/WAV、标签和 `manifest.csv` 未修改；仅远程 `aio` 环境及独立 smoke 目录发生变化；
- `task-25` 继续进行中，`task-26`、`task-27` 保持待开始。

### 2026-09-10：All-In-One 单曲目真实推理验证完成

- 功能名称：All-In-One 单曲目结构分析与运行环境验证；
- 当前状态：已完成并通过真实产物校验；
- 阻塞处理：首次重试因远程无法访问 `huggingface.co` 而停留在 Demucs 配置下载；验证 `https://hf-mirror.com/adefossez/HTDemucs/resolve/main/htdemucs.yaml` 返回 HTTP 200 后，使用 `HF_ENDPOINT=https://hf-mirror.com` 重新执行；
- 输入：`data/audio_wav/deam_0076.wav`；模型：`harmonix-fold0`；设备：`cuda`；多进程：关闭；保留 Demucs 和频谱中间产物；
- 真实输出：`data/structure_allin1_singleprocess_smoke/deam_0076.json`，文件大小 1132 bytes；
- 输出结构：顶层字段为 `beat_positions`、`beats`、`bpm`、`downbeats`、`path`、`segments`；`bpm=95`；`segments=4`；边界范围 `0.0–45.04` 秒；segment 字段为 `start`、`end`、`label`；
- 质量校验：JSON 可解析，segment 顺序合法、起止时间无逆序或重叠；分析总耗时 `24.896` 秒；
- 环境证据：`torch=2.5.0+cu121`、`cuda_build=12.1`、`cuda_available=True`、设备为 `NVIDIA GeForce RTX 3080 Ti`；`natten=0.17.5`；All-In-One commit=`18e78903c0365147a2c5d4e5e57ebf88cb7d800e`；
- 结论：已满足启动 205 首批处理的前置条件；All-In-One 输出仍定义为冻结的自动结构分析结果，不作为人工结构真值；
- 未修改原始 MP3/WAV、标签和原始 `manifest.csv`；新增远程 smoke 脚本、日志及独立 smoke 输出目录；
- `task-25` 标记完成，下一步进入 `task-26` 批量结构输出与独立索引。

### 2026-09-11：205首冻结结构批处理启动

- 功能名称：All-In-One 205首批量结构输出；
- 当前状态：进行中，尚未完成，不能标记完成；
- 执行方式：远程使用 `/root/miniconda3/envs/aio/bin/python scripts/run_allin1_batch.py`，输入 `data/manifest.csv`，输出 `data/structure_allin1/`，每曲目独立 JSON，启用断点跳过；
- 运行环境：`HF_ENDPOINT=https://hf-mirror.com`，All-In-One CLI 为 `/root/miniconda3/envs/aio/bin/allin1`，默认模型 `harmonix-all`；
- 启动结果：批处理进程已在远程后台运行；manifest 共 205 首曲目（文件 206 行含表头）；
- 当前进度：已生成 7 个顶层结构 JSON，当前正在分析 `deam_0083.wav`；未观测到批处理进程异常；
- 数据保护：未覆盖原始音频、标签和 `data/manifest.csv`；中间输出集中在独立的 `data/structure_allin1/.runs/`；
- 下一步：等待 205 首批处理结束，检查 `batch_log.jsonl` 的 written/failed 计数，再生成独立结构索引并执行完整性校验。

### 2026-09-11：205首结构批处理进行中 checkpoint

- 功能名称：All-In-One 批量冻结结构生成；
- 当前状态：进行中，未标记完成；
- 当前观测：远程批处理主进程仍存活，已生成 131 个顶层 JSON，当前正在处理 `deam_0217.wav`；
- 运行约束：继续使用 `HF_ENDPOINT=https://hf-mirror.com`，不重复启动并发任务；
- 数据保护：原始音频、标签和 `data/manifest.csv` 未修改；
- 未完成项：尚未取得完整 205 首 written/failed 统计，暂不生成正式结构索引或回填 manifest。

### 2026-09-11：205首冻结结构输出与独立索引完成

- 功能名称：All-In-One 批量冻结结构输出与结构索引；
- 当前状态：已完成并通过真实远程产物校验；
- 批处理结果：205 首曲目全部 `written`，`skipped=0`，`failed=0`；生成顶层结构 JSON 共 205 个；批处理结束后无残留 All-In-One 进程；
- 结构索引：生成 `data/structure_index.csv`，索引行数 205；记录 `track_id`、音频路径、结构路径、结构版本、分析时间、BPM、结构边界和 segment 数量；
- JSON 校验：`indexed_json=205`、`missing_json=0`、`invalid_json=0`、`invalid_segments=0`、`blank_bounds=0`；
- 覆盖校验：manifest 曲目 205、索引曲目 205、缺失 0、额外 0；
- 运行环境：`HF_ENDPOINT=https://hf-mirror.com`；All-In-One commit=`18e78903c0365147a2c5d4e5e57ebf88cb7d800e`；模型版本记录为 `harmonix-all`；
- 处理说明：首次使用相对 `--structure-dir` 生成索引时触发路径相对化错误，改用绝对路径重新执行成功；原始结构 JSON 未修改；
- `task-26` 标记完成，进入结构回填和对齐样本校验。

### 2026-09-11：结构回填与真实对齐样本表完成

- 功能名称：结构字段安全回填和音频—结构—1Hz VA 对齐样本表；
- 当前状态：已完成并通过真实远程校验；
- 安全回填：生成 `data/manifest_with_structure.csv`，manifest 行数 205、更新行数 205、结构字段完整行数 205；原始 `data/manifest.csv` 未覆盖；
- 对齐样本：生成 `data/aligned_samples.csv`，写入 125255 行，覆盖 205 首曲目；有效 VA 行 6150，全部映射到结构 segment；
- 对齐校验：`tracks=205`、`valid_rows=6150`、`invalid_rows=0`、`invalid_split_rows=0`、`non_monotonic_rows=0`；split 数量为 3；
- 标签路径修复：manifest 的 `label_path` 表示标签目录而非单个 CSV，构建器已按 `track_id.csv` 解析目录路径；兼容单文件标签路径；已同步远程并重新生成样本表；
- 无效 VA 时间点中有 119105 行未落入结构段，属于标签时间范围超出自动结构边界的无效行；所有有效 VA 行均已完成结构归属；
- 输出文件：`data/structure_index.csv`、`data/manifest_with_structure.csv`、`data/aligned_samples.csv`；
- `task-27` 标记完成；原始音频、标签和原始 `data/manifest.csv` 未修改。

### 2026-09-12：冻结 MERT 提取器与特征质量校验器实现（待远程验证）

- 功能名称：MERT-v1-95M 冻结特征提取与 1 Hz 时间轴契约；
- 当前状态：实现完成，远程单曲目验证尚未完成，不能标记 `task-29` 或 `task-30` 完成；
- 新增文件：`extract_mert.py`、`validate_mert_features.py`；
- 固定数据流：读取 manifest 中的 WAV → 重采样到 24 kHz → 使用 `m-a-p/MERT-v1-95M` 推理 → 平均最后四层隐藏表示 → 按 1 秒半开区间 `[i, i+1)` 聚合 → 输出中心时间戳 `i+0.5`；
- 固定推理参数：窗口 10 秒、窗口 hop 5 秒、`bin_sec=1.0`；窗口尾部采用零填充，最后一个窗口补齐到音频尾部；模型 `eval()`、关闭梯度并使用 `torch.inference_mode()`；
- 输出产物：每曲目一个 `track_id.npz`，保存 `features[T,768]` 与 `time_sec[T]`；另存同名 JSON，记录模型、采样率、窗口、hop、层聚合规则、形状、时长、设备和耗时；
- 校验内容：manifest 曲目集合与 `.npz` 完全一致、无缺失或额外文件、特征维度为 768、时间戳与特征行数一致、数值有限、时间戳严格为 1 Hz 中心点、JSON 元数据与产物一致；
- 保护约束：默认不覆盖已有特征，只有显式传入 `--overwrite` 才重算；原始音频、标签、结构结果和原始 `manifest.csv` 不修改；
- 当前阻塞：远程 SSH 返回 `Permission denied (publickey,password)`；尝试现有 `autodl` 别名后服务端主动关闭连接，尚未取得 PID `78412`、模型缓存、磁盘空间或 MERT 单曲目前向的实时证据；
- 下一步：恢复远程认证后先检查 PID `78412` 和磁盘，再以单曲目执行提取器和校验器，验证实际输出形状与耗时后才扩展至 205 首。

### 2026-09-12：远程 MERT 只读恢复探测仍受认证阻塞

- 功能名称：远程 MERT 验证任务恢复检查；
- 当前状态：未完成，`task-28` 继续进行中；
- 本轮操作：只读尝试当前记录的端口 `12524` 和本地 SSH 配置中的 `autodl` 别名；未启动新的下载、安装、推理或批处理；
- 观测结果：端口 `12524` 返回 `Permission denied (publickey,password)`；别名端口 `16371` 被服务端主动关闭；没有获得 `REMOTE_OK`、PID `78412`、日志、模型缓存、GPU 或磁盘证据；
- 本地状态：`extract_mert.py` 和 `validate_mert_features.py` 已通过 `python3 -m py_compile`；远程特征产物尚未生成；
- 数据与原始音频、标签、结构结果和 manifest 未修改。

### 2026-09-12：MERT 提取核心契约本地模拟验证

- 功能名称：冻结 MERT 时间轴聚合和产物校验的本地模拟验证；
- 当前状态：本地模拟验证通过，真实远程模型验证尚未完成，`task-30` 不能标记完成；
- 验证方式：使用 12 秒、24 kHz 临时 WAV 和模拟 13 层、768 维模型输出，不读取正式数据、不下载模型；
- 验证结果：输出形状 `[12,768]`，时间戳为 `0.5, 1.5, ..., 11.5`，最后四层均值规则正确；生成的 `.npz` 与 JSON 通过 `validate_mert_features.py`；结果为 `manifest_tracks=1`、`feature_files=1`、`missing=0`、`extra=0`、`invalid=0`、`total_frames=12`；
- 修复内容：单曲目提取入口现在自行创建输出目录，避免直接调用时因目录不存在失败；
- 依赖边界：将 `transformers` 导入下沉至 CLI 启动入口，使时间轴核心逻辑可在无模型下载环境中独立测试；远程环境仍会在实际加载模型时检查 `transformers`；
- 数据与正式音频、标签、结构结果、manifest 未修改；
- 未完成项：仍需恢复远程认证，检查 PID `78412`、磁盘和缓存，完成真实单曲目 MERT 前向后才执行 205 首提取。

### 2026-09-12：MERT 与有效 VA 标签的时间轴对齐校验器

- 功能名称：MERT 特征—1Hz VA 时间戳对齐校验；
- 当前状态：本地模拟验证通过，正式 205 首特征尚未生成，`task-30` 不能标记完成；
- 新增文件：`validate_mert_alignment.py`；
- 校验规则：仅对 `aligned_samples.csv` 中 `valid=1` 的行分组检查；每首曲目必须存在对应 `.npz`，特征与时间数组长度一致，时间戳有限，且每个有效标签时间点必须在 MERT 时间轴中以绝对误差不超过 `1e-6` 秒匹配；
- 本地结果：临时数据中 2 条有效样本全部匹配，`missing_feature_files=0`、`invalid_feature_files=0`、`missing_timestamps=0`、`matched_rows=2`；
- 数据保护：只读检查特征和对齐样本，不修改正式数据、manifest 或结构结果；
- 下一步：远程恢复后按“单曲提取 → 特征维度校验 → 标签时间轴对齐校验 → 205 首批量提取”的顺序执行。

### 2026-09-12：MERT 工具链 CLI 与语法复查

- 功能名称：MERT 提取、特征校验和时间轴校验工具入口复查；
- 当前状态：本地复查通过，远程模型和 205 首正式产物尚未验证；
- 验证结果：`extract_mert.py`、`validate_mert_features.py`、`validate_mert_alignment.py` 均通过 `python3 -m py_compile`，三个 `--help` 入口均正常返回；
- 依赖边界：本地环境为 Python 3.14、Torch 2.13.0，未安装 `transformers`，因此未执行真实模型前向；远程执行必须使用已锁定的 `aio` 环境及 `transformers==4.38.2`、`accelerate==0.28.0`；
- 状态约束：没有把本地模拟结果冒充 MERT 实测结果；`task-28`、`task-29` 保持进行中，`task-30` 保持待开始；
- 数据与正式音频、标签、结构结果、manifest 未修改。

### 2026-09-12：远程 MERT 单曲目真实前向与对齐验证完成

- 功能名称：MERT-v1-95M 单曲冻结特征提取、维度校验和 VA 时间轴对齐；
- 当前状态：单曲目验证完成，已满足启动全量提取条件；`task-28` 可标记完成，`task-29` 继续进行中，`task-30` 等待全量校验；
- 远程环境：Python `3.10.21`、Torch `2.5.0+cu121`、CUDA 可用、GPU `NVIDIA GeForce RTX 3080 Ti`、NumPy `2.2.6`、`transformers==4.38.2`、`accelerate==0.28.0`；
- 模型状态：`m-a-p/MERT-v1-95M` 已从缓存加载，缓存目录约 361 MB；根分区剩余约 18 GB；
- 输入：`data/audio_wav/deam_0076.wav`，实际重采样后时长 `45.034875` 秒；输出目录为独立的 `data/features_mert95m_smoke/`；
- 真实输出：`deam_0076.npz` 的 `features_shape=(45,768)`，时间戳为 `0.5–44.5` 秒，全部特征值有限；JSON 元数据记录 `sample_rate_hz=24000`、窗口 `10.0s`、hop `5.0s`、`bin_sec=1.0`、最后四层平均、设备 `cuda`，单曲提取耗时 `0.733s`；
- 特征校验：`manifest_tracks=1`、`feature_files=1`、`missing=0`、`extra=0`、`invalid=0`、`total_frames=45`；
- 对齐校验：该曲目对齐样本共 611 行，其中有效 VA 行 30；`missing_feature_files=0`、`invalid_feature_files=0`、`missing_timestamps=0`、`matched_rows=30`；
- 进程约束：此前 PID `78412` 已不存在，本轮没有重复启动旧任务；当前单曲任务已结束；
- 数据保护：原始音频、标签、结构结果和原始 `manifest.csv` 未修改；全量提取将写入独立特征目录。

### 2026-09-12：MERT 205 首全量提取与最终时间轴校验完成

- 功能名称：冻结 MERT-v1-95M 全量特征产物、环境锁定和 VA 对齐校验；
- 当前状态：已完成并通过远程真实产物校验；`task-28`、`task-29`、`task-30` 均可标记完成；
- 全量命令：在远程 `/root/autodl-tmp/music-emotion-project` 使用 `/root/miniconda3/envs/aio/bin/python scripts/extract_mert.py`，输入 `data/manifest.csv`，输出 `data/features_mert95m/`，设置 `HF_ENDPOINT=https://hf-mirror.com`、`--device cuda`；
- 批处理结果：`written=205`、`skipped=0`、`failed=0`；最终无残留提取进程；
- 特征完整性校验：`manifest_tracks=205`、`feature_files=205`、`missing=0`、`extra=0`、`invalid=0`、`total_frames=9225`；205 首全部为 `[45,768]`，所有特征数值有限；
- 时间轴对齐校验：`valid_sample_rows=6150`、`checked_tracks=205`、`missing_feature_files=0`、`invalid_feature_files=0`、`missing_timestamps=0`、`matched_rows=6150`；有效 VA 标签与 MERT 时间戳 100% 匹配；
- 边界修复：首次全量校验发现 2 条 `44.5s` 标签因 `floor(duration_sec)` 被遗漏；定位为 `deam_0146`（44.9565s）和 `deam_0272`（44.643083s）。修正为保留所有中心时间戳不超过音频时长的末端部分秒区间，并用字段完整的临时 manifest 正确重算两曲目；修复后总帧数由 9223 变为 9225，对齐由 6148/6150 变为 6150/6150；
- 环境锁定：远程生成 `env-locks/aio-mert-pip-freeze.txt`（84 行）和 `env-locks/aio-mert-core-versions.txt`；核心版本为 Torch `2.5.0+cu121`、CUDA build `12.1`、CUDA 可用、Transformers `4.38.2`、Accelerate `0.28.0`、NumPy `2.2.6`、SoundFile `0.14.0`；
- 资源状态：最终根分区仍约 18 GB 可用，GPU 任务结束后释放；
- 数据保护：特征写入独立目录 `data/features_mert95m/`；原始音频、标签、结构结果和原始 `data/manifest.csv` 未修改。

### 2026-09-12：B0/B1/B2/B3/S1 训练工具链与最小烟测完成

- 功能名称：冻结 MERT 特征上的 B0/B1/B2/B3/S1 动态 VA 训练、评估和产物保存；
- 当前状态：已完成并通过远程真实烟测；`task-31`、`task-32`、`task-33` 均可标记完成；
- 数据契约：读取 `data/features_mert95m/*.npz` 与 `data/aligned_samples.csv`，仅使用 `valid=1` 行；按 `track_id` 固定划分为 train/val/test，训练按曲目计算损失并在曲目集合上评估；结构模型通过 `segment_index` 使用自动结构边界；
- 模型入口：统一 CLI 已覆盖 B0 训练集均值、B1 局部模型、B2 平坦双向 GRU、B3 等长分段模型和 S1 自动结构层级模型；B3 等长分段数复用自动结构段数量；
- 修复内容：修正 manifest 遍历时将单曲目字典误当作有效样本列表的问题；修正 `Path` 配置无法 JSON 序列化的问题；smoke 子集无 test 曲目时按契约跳过 test 评估；
- 本地验证：`python3 -m py_compile train.py` 通过，`ReadLints` 未发现 `train.py` 诊断；修复后的 `train.py` 已同步至远程 `scripts/train.py`；
- 远程烟测命令：使用 `/root/miniconda3/envs/aio/bin/python scripts/train.py`，固定 manifest、aligned samples 和 `data/features_mert95m`，`--max-tracks 10 --max-epochs 2 --patience 2 --device cuda`；
- 烟测结果：B0、B1、B2、B3、S1 五项均成功；B2/S1 各完成 2 epoch，B1/B3 各完成 2 epoch，B0 指标已保存；五项训练 loss 均为有限值；
- 产物校验：`runs/smoke-b0/metrics.json` 存在；`runs/smoke-b1`、`runs/smoke-b2`、`runs/smoke-b3`、`runs/smoke-s1` 均包含 `best.pt`、`metrics.json`、`val_predictions.json`；B2/S1 均覆盖 smoke 子集的 2 首验证曲目、每首 30 帧；
- checkpoint 校验：用远程 `aio` 环境重新加载 B2/S1 的 `best.pt`，对保存的验证曲目重新预测并与 `val_predictions.json` 逐元素比较，`RELOAD_OK b2`、`RELOAD_OK s1` 均通过；固定全量曲目划分加载结果为 train 144、val 31、test 30；
- 指标示例：B2 smoke 验证 `ccc_mean=0.5039658695`、`mae_mean=0.1887100786`、`rmse_mean=0.2167740986`；S1 smoke 验证 `ccc_mean=0.2137373164`、`mae_mean=0.2647178844`、`rmse_mean=0.2975161672`。这些仅为 10 首 smoke 子集、2 epoch 的工具链证据，不作为正式实验结论；
- 失败与重试：首次烟测分别暴露样本分组遍历错误和配置序列化错误，修复后重新执行；最终五项命令均返回成功，远程无残留训练进程；
- 数据保护：训练仅写入独立 `runs/smoke-*` 目录，未修改原始音频、标签、结构结果、特征和原始 `data/manifest.csv`；
- 未完成项：尚未启动 205 首正式训练、3 个以上随机种子、测试集最终评估、模型比较、消融和误差分析。

### 2026-09-12：正式训练入口冻结与首个种子验证集训练启动

- 功能名称：正式训练测试集隔离和首个种子五模型训练；
- 当前状态：进行中，尚未完成，不能标记正式实验完成；
- 修改内容：`train.py` 新增显式 `--evaluate-test` 开关，默认只评估验证集；测试集评估仅在模型设计冻结后显式启用；
- 本地验证：`python3 -m py_compile train.py` 通过，`ReadLints` 未发现诊断；修复后的脚本已同步远程；
- 执行计划：使用固定 seed `20260903`、全量 train/val/test 曲目划分、最多 100 epoch、patience 12、AdamW 初始学习率 `1e-3`、weight decay `1e-4`、梯度裁剪 `1.0`；输出分别写入 `runs/formal-${model}-seed20260903-valonly/`；
- 当前运行：B0 已完成并写出验证集均值指标；B1 正在训练，B2/B3/S1 尚未开始；此次正式训练默认不评估 test；
- 误操作处理：曾误启动一个带 `--evaluate-test` 的批次，完成 B0 后在 B1 训练期间停止；其目录不作为正式结果使用；
- 数据保护：训练和日志只写入独立 `runs/` 目录，未修改音频、标签、结构结果、MERT 特征或原始 `data/manifest.csv`；
- 未完成项：需要等待五模型验证集训练结束，校验 checkpoint、逐曲验证预测和指标，再决定是否扩展到更多种子。

### 2026-09-12：首个种子正式验证集训练完成并通过校验

- 功能名称：B0/B1/B2/B3/S1 首个正式种子验证集训练；
- 当前状态：已完成并通过远程真实产物校验；多种子训练仍进行中，不能标记正式实验整体完成；
- 执行参数：seed `20260903`，全量曲目划分 train=144、val=31、test=30，最多 100 epoch，patience 12，AdamW，学习率 `1e-3`，weight decay `1e-4`，梯度裁剪 `1.0`，未启用 `--evaluate-test`；
- 输出目录：`runs/formal-b0-seed20260903-valonly/` 至 `runs/formal-s1-seed20260903-valonly/`；原先误启动的带测试评估目录不作为正式结果；
- 训练结果：B0 指标已保存；B1 最佳 epoch=24，B2=19，B3=35，S1=8；四个可训练模型均生成 `best.pt`、`metrics.json`、`val_predictions.json`；
- 验证指标：B0 `ccc_mean≈0`；B1 `0.4859588742`；B2 `0.7317613959`；B3 `0.6959877908`；S1 `0.5929899663`；所有 MAE、RMSE、CCC 和训练历史值均为有限数；
- 产物校验：31 首验证曲目均有预测，每首 30 帧；重新加载 B1/B2/B3/S1 checkpoint 后逐元素复现保存预测，全部通过；固定 split 再次确认 train=144、val=31、test=30；
- 决策：B2 验证 CCC 明显高于 B0，满足文档规定的扩展条件；启动 seed `20260904`、`20260905` 的 B1/B2/B3/S1 验证集训练；
- 数据保护：只写入独立 `runs/` 目录，未修改音频、标签、结构结果、MERT 特征和原始 `data/manifest.csv`。

### 2026-09-12：多种子正式训练推进中

- 功能名称：B1/B2/B3/S1 多随机种子验证集训练；
- 当前状态：进行中，尚未完成，不能标记正式实验整体完成；
- 已完成：seed `20260904` 的 B1、B2、B3、S1 均完成最多 100 epoch 训练与 patience 12 早停，分别保存在 `runs/formal-${model}-seed20260904-valonly/`；
- 当前执行：seed `20260905` 的 B1 已完成，B2 已通过 `nohup` 后台启动；B3、S1 尚未启动；
- 测试隔离：所有多种子任务均未启用 `--evaluate-test`，当前只生成训练/验证结果；测试集保持冻结，不参与模型选择；
- 运行约束：远程长连接曾在串行任务中途截断，未发现模型错误；后续改为单模型独立后台任务并轮询 `metrics.json`，避免会话生命周期影响训练；
- 数据保护：所有产物写入独立 `runs/formal-*-seed*-valonly/` 目录，原始音频、标签、结构、特征和 `data/manifest.csv` 未修改；
- 未完成项：完成 seed `20260905` 的 B2/B3/S1 后，仍需校验多种子指标与 checkpoint，随后才可冻结设计并显式评估 test。

### 2026-09-12：B0 正式基线产物契约补齐

- 功能名称：B0 训练集均值基线的可复现产物和统一验证输出；
- 当前状态：已完成并通过远程真实校验；对应 `task-35` 的 B0 受影响目录已补齐；
- 修改内容：`train.py` 的 B0 分支新增 `val_predictions.json`、`baseline.json`、完整 `metrics.json` 配置快照和 `test_metrics=null`；B0 不生成神经网络 `best.pt`，而以训练集均值作为明确的非参数基线产物；
- 运行命令：远程使用 `aio` 环境、全量 manifest/aligned samples/MERT 特征、`--model b0 --seed 20260903 --device cuda` 重建 `runs/formal-b0-seed20260903-valonly/`；
- 校验结果：31 首验证曲目全部存在，每首 30 帧；保存预测逐元素等于 `train_mean`；CCC、MAE、RMSE 和配置值均可读取且有限；`evaluate_test=false`，未评估测试集；
- 本地验证：`python3 -m py_compile train.py` 通过，`ReadLints` 未发现 `train.py` 诊断；脚本已同步到远程 `scripts/train.py`；
- 数据保护：仅更新独立 B0 正式运行目录和训练脚本，未修改原始音频、标签、结构、MERT 特征或原始 `data/manifest.csv`。

### 2026-09-12：修复评估口径后的 13 个正式验证集产物完成

- 功能名称：B0/B1/B2/B3/S1 曲目级验证评估、多种子正式训练产物和重载复现校验；
- 当前状态：验证集正式训练及产物核验已完成；`task-35`、`task-36`、`task-37` 可标记完成；测试集仍未评估，正式模型报告、消融和误差分析尚未开始；
- 产物范围：B0 1 个目录，B1/B2/B3/S1 各 3 个目录，共 13 个 `runs/formal-*-seed*-valonly/`；B1/B2/B3/S1 均包含 `best.pt`、`metrics.json`、`val_predictions.json`，B0 包含 `baseline.json`、`metrics.json`、`val_predictions.json`；
- 统一校验：无训练进程残留；所有指标和训练历史为有限值；31 首验证曲目集合、`track_id`、时间戳、真实 VA 和每曲 30 帧全部一致；12 个神经模型 checkpoint 均可重新加载，预测与保存结果逐元素一致；B0 保存均值预测并逐元素复现；
- 测试隔离：13 个目录的 `config.evaluate_test=false` 且 `test_metrics=null`，固定划分仍为 train=144、val=31、test=30；本轮没有使用测试集选择模型或报告测试结论；
- 当前曲目级验证 CCC：B0 `0.000000`（单种子）；B1 三种子为 `0.053606/0.051713/0.056435`，均值 `0.053918`、样本标准差 `0.002377`；B2 为 `0.117223/0.146038/0.108503`，均值 `0.123921`、样本标准差 `0.019643`；B3 为 `0.095420/0.119872/0.116268`，均值 `0.110520`、样本标准差 `0.013201`；S1 为 `0.091099/0.071938/0.081843`，均值 `0.081627`、样本标准差 `0.009582`；三种子结果均按每曲计算指标后再取曲目均值；
- 当前审计信息：远程源码 `scripts/train.py` SHA-256 为 `37055e898dc3f6c1f89e4dac37269ef33d0b3eeb475130353dff41a117356985`；`aligned_samples.csv` SHA-256 为 `c1d874858cc3f5279c9f65bb3e6fe9ec241d54a24a1582f5f28ac36d5b6cb082`；原始 `manifest.csv` SHA-256 为 `589354e21984ed25e8079258df70bfdb1c1017ae31c0ef65c6f9bbe9be9c71f8`；环境为 Python `3.10.21`、Torch `2.5.0+cu121`、CUDA `12.1`、NumPy `2.2.6`、Transformers `4.38.2`、Accelerate `0.28.0`、GPU `NVIDIA GeForce RTX 3080 Ti`；
- 日志说明：各目录的 `metrics.json` 已保存逐 epoch `history`、最佳 epoch、配置和指标；`train.log` 文件存在但当前为空，未形成独立的原始 stdout 日志，因此该项按“指标历史可审计、原始训练日志缺失”记录，不将空日志冒充完整日志；
- 结果废弃说明：此前按“全体验证帧拼接”口径产生的正式数值，以及早期不完整 B0 目录，均不作为实验结果；当前只认可本条所述的曲目级聚合和修复后产物；
- 下一步边界：只有在验证集协议和模型设计正式冻结后，才可显式启用 `--evaluate-test`；在此之前不得报告测试集结论；
- 数据保护：训练结果写入独立 `runs/` 目录；原始音频、标签、结构结果、MERT 特征和原始 `data/manifest.csv` 未修改。

### 2026-09-12：设计冻结后的正式测试集只读评估

- 功能名称：冻结验证集选择结果后的测试集最终评估；
- 当前状态：已完成并通过远程真实产物校验；`task-38`、`task-39`、`task-40` 可标记完成；
- 设计冻结：沿用已完成验证集阶段的固定 train/val/test 曲目划分（144/31/30）、MERT-v1-95M 冻结特征、B0/B1/B2/B3/S1 模型定义、AdamW 参数、早停规则和曲目级指标聚合；未使用测试集重新选择模型、超参数或结构；
- 实现修改：`train.py` 新增 `--evaluate-only` 入口，只读取既有 `metrics.json`、`baseline.json` 或 `best.pt`，在测试集上生成独立的 `test_metrics.json` 和 `test_predictions.json`，不覆盖验证指标、验证预测或 checkpoint；本地 `python3 -m py_compile train.py` 和 `ReadLints` 均通过，修复后的脚本已同步远程；
- 执行范围：B0 使用 `runs/formal-b0-seed20260903-valonly/`；B1/B2/B3/S1 使用 3 个种子对应的 12 个正式目录，共完成 13 个测试评估产物；测试集仅在设计冻结后被读取；
- 测试完整性：30 首测试曲目全部覆盖，每首 30 帧；`track_id`、时间戳、真实 VA 和预测数组与冻结对齐样本一致；所有测试指标有限；13 个目录均记录 `evaluate_only=true`；无残留评估进程；
- 测试集曲目级 CCC：B0 `-0.000000`（单种子）；B1 三种子为 `0.023539/0.029581/0.027315`，均值 `0.026812`、样本标准差 `0.003052`；B2 为 `0.036208/0.018956/0.027378`，均值 `0.027514`、样本标准差 `0.008627`；B3 为 `0.006114/0.016483/-0.009869`，均值 `0.004243`、样本标准差 `0.013275`；S1 为 `0.005886/0.033166/0.042199`，均值 `0.027084`、样本标准差 `0.018906`；
- 结果解释：在当前固定设计和 3 个种子下，S1 测试 CCC 均值仅略高于 B2，且跨种子波动更大；B3 未显示测试集收益。因此本轮不能支持“自动音乐乐段具有稳定增量价值”的论文主张，只能将其作为未获支持的实验观察，并结合验证集结果共同报告；
- 结果边界：测试集结果用于最终一次性报告，不反向修改模型、超参数、数据划分或验证集结果；尚未执行 bootstrap、配对置换检验、边界距离分层和失败歌曲误差分析；
- 数据保护：测试评估只新增各正式运行目录中的 `test_metrics.json` 与 `test_predictions.json`，未修改原始音频、标签、结构结果、MERT 特征、原始 `data/manifest.csv` 或已有验证产物。

### 2026-09-12：测试集曲目级统计、配对差异和结构边界分层分析

- 功能名称：正式测试结果的曲目级 bootstrap、S1 配对比较和自动边界距离误差分析；
- 当前状态：已完成并通过远程真实产物校验；`task-41`、`task-42`、`task-43`、`task-44` 可标记完成；
- 新增文件：本地及远程 `scripts/analyze_results.py`；独立报告 `reports/formal-test-analysis.json`；
- 固定口径：统计单位为曲目，不将所有秒级帧拼接成单一总体指标；测试集共 30 首曲目；bootstrap 10000 次，随机种子 `20260912`；S1 与 B2、B3 的比较使用同一测试曲目上的配对差和 10000 次符号置换；
- 复现校验：同一命令重复生成临时报告，与正式报告字节级一致；报告内数值全部有限；边界分析使用自动 All-In-One 内部 segment 起点（不含 0 秒）到测试时间点的最近距离，分组为 `0-1s`、`1-3s`、`3-5s`、`>5s`；自动结构仅作为模型输入和分层参考，不作为人工结构真值；
- 曲目级测试 CCC 均值及 95% bootstrap 区间：B0 `0.000000`；B1 `0.026812`；B2 `0.027514`；B3 `0.004243`；S1 `0.027084`；完整区间和各指标保存在 `reports/formal-test-analysis.json`；
- 配对结果：S1−B2 的 `ccc_mean` 平均差 `-0.000430`，95% bootstrap 区间约为 `[-0.034089, 0.035440]`，双侧置换 `p=0.981702`；S1−B3 平均差 `0.022841`，95% bootstrap 区间约为 `[-0.007216, 0.062015]`，双侧置换 `p=0.226977`；当前数据不支持 S1 相对于 B2 或 B3 的显著稳定优势；
- 边界误差结果：B2 各距离组 MAE 为 `0-1s: 0.199068`、`1-3s: 0.195473`、`3-5s: 0.195808`、`>5s: 0.193221`；B3 为 `0.212922`、`0.213863`、`0.215808`、`0.215870`；S1 为 `0.208977`、`0.206996`、`0.207408`、`0.208963`；每组均覆盖 30 首曲目，具体 RMSE、时间点数和结构化 JSON 见报告；
- 结果解释：在当前实验规模、固定划分和 3 个随机种子下，S1 没有相对 B2 的可辨识增益，S1 相对 B3 的正差异也未达到统计显著；边界附近与段内误差差异较小，不能据此声称模型对结构边界具有特殊鲁棒性或敏感性；
- 实现限制：当前 bootstrap 是对曲目级指标做 percentile 区间；跨种子结果先按曲目对种子取均值再进行曲目级统计；边界分层把同一曲目的多个种子误差汇入曲目均值，不执行边界分组显著性检验；尚未实施 Holm 校正、完整配对置换矩阵、失败歌曲人工复核和可视化曲线；
- 数据保护：分析仅读取冻结测试预测和 All-In-One JSON，报告写入独立 `reports/`，未修改训练产物、原始音频、标签、结构结果、MERT 特征或原始 `data/manifest.csv`。

### 2026-09-12：论文级统计补充与失败曲目审计

- 功能名称：Holm 多重比较校正、失败曲目清单、排除原因清单和统计报告复现审计；
- 当前状态：已完成并通过远程真实产物校验；`task-45`、`task-46`、`task-47`、`task-48` 可标记完成；
- 修改内容：扩展 `scripts/analyze_results.py`，新增 Holm step-down 校正，校正族定义为 `S1 versus B2/B3 × valence_ccc/arousal_ccc`；新增对测试预测非有限值的失败曲目扫描，以及对 `manifest.csv` 中 `quality_status=excluded` 或存在 `exclude_reason` 的排除曲目扫描；
- 审计结果：测试集 30 首曲目全部有完整预测，`failures=[]`；当前 manifest 没有排除曲目，`exclusions=[]`；每个边界距离组均覆盖 30 首曲目，报告中的数值均有限；
- Holm 结果：`b3:arousal_ccc` 校正后 `p=0.165583`；`b2:valence_ccc`、`b2:arousal_ccc`、`b3:valence_ccc` 校正后均为 `1.000000`；没有主要比较在 Holm 校正后达到显著；
- 可复现性：使用相同输入、bootstrap=10000、permutation=10000、随机种子 `20260912` 重跑，临时报告与 `reports/formal-test-analysis.json` 字节级一致；
- 结果限制：该校正只针对预先定义的四项主要 CCC 比较；边界分层仍是描述性分析，没有进行分组显著性检验；没有新增人工结构审计或失败歌曲人工复核，因为当前机器校验未发现失败或排除项；
- 数据保护：仅更新独立统计脚本和 `reports/formal-test-analysis.json`，未修改训练 checkpoint、测试预测、原始音频、标签、结构结果、MERT 特征或原始 `data/manifest.csv`。

### 2026-09-12：论文模型比较表和逐曲误差清单

- 功能名称：验证集/测试集统一模型比较报告、跨种子指标汇总和逐曲误差排序；
- 当前状态：已完成并通过远程真实产物校验；`task-49`、`task-50`、`task-51`、`task-52` 可标记完成；
- 新增文件：本地及远程 `scripts/build_paper_report.py`；独立报告 `reports/paper-results.json` 和 `reports/paper-results.csv`；
- 固定数据流：仅读取冻结的 `val_predictions.json` 与 `test_predictions.json`，不重新训练、不读取测试标签参与模型选择、不改写已有指标文件；B0 使用单种子，B1/B2/B3/S1 使用 `20260903/20260904/20260905` 三个种子；
- 报告内容：验证集 31 首、测试集 30 首的 B0/B1/B2/B3/S1 指标均值与跨种子标准差；以 S1 平均 `mae_mean` 降序生成验证集和测试集逐曲误差清单，并同时列出 B2/B3 误差及差值；
- 汇总结果：验证集 `ccc_mean` 为 B0 `0.000000`、B1 `0.053918`、B2 `0.123921`、B3 `0.110520`、S1 `0.081627`；测试集为 B0 `-0.000000`、B1 `0.026812`、B2 `0.027514`、B3 `0.004243`、S1 `0.027084`；完整 Valence/Arousal CCC、MAE、RMSE 和标准差保存在 JSON/CSV；
- 误差审计：测试集 S1 平均 MAE 最高的曲目包括 `deam_0262`（`0.470508`）、`deam_0115`（`0.388266`）、`deam_0468`（`0.384141`）、`deam_0253`（`0.362046`）和 `deam_0098`（`0.347666`）；这些是误差定位候选，不直接解释为结构失败原因；
- 校验结果：报告 JSON 数值全部有限；模型、划分、种子数量和曲目数量符合协议；CSV 共有 10 行；验证误差清单 31 首、测试误差清单 30 首；相同输入重复运行后报告字节级一致；
- 论文边界：当前结果可以支持“B2 在验证集上是最强基线，测试集上 B2 与 S1 基本持平”的描述；不能支持自动乐段层级模型具有稳定增量收益；逐曲误差清单只能用于后续定性检查，不能在测试集上反向筛选曲目或修改模型；


### 2026-09-12：论文方法、结果与限制材料草稿

- 功能名称：基于冻结实验产物的论文方法、实验结果、结论和限制整理；
- 当前状态：已完成并通过本地内容一致性校验；`task-53`、`task-54`、`task-55` 可标记完成；
- 新增文件：独立材料 `reports/paper-materials.md`；
- 方法边界：明确 DEAM 仅提供动态 Valence/Arousal 监督，冻结 MERT-v1-95M 提供秒级音频表示，冻结 All-In-One 仅提供自动乐段边界和段落归属；自动结构不作为人工结构真值；
- 数据与时间轴：整理 205 首音频、6150 条有效 VA 行、固定 train/validation/test=`144/31/30`、MERT 总计 9225 帧、每首 `[45,768]`、1 Hz 中心时间戳和 100% 有效 VA 时间匹配；
- 模型对照：记录 B0 训练集均值、B1 局部模型、B2 平坦双向 GRU、B3 等长分段层级模型和 S1 自动乐段层级模型的职责关系；明确 S1 只有同时稳定优于 B2 与 B3 才能支持自动结构增益主张；
- 结果表：整理验证集和测试集曲目级 `ccc_mean`，并记录跨种子均值和样本标准差；验证集 B2=`0.123921 (0.019643)`、S1=`0.081627 (0.009582)`；测试集 B2=`0.027514 (0.008627)`、S1=`0.027084 (0.018906)`；
- 统计结论：记录测试集 S1−B2 平均差 `-0.000430`、95% bootstrap 区间约 `[-0.034089, 0.035440]`、置换 `p=0.981702`；S1−B3 平均差 `0.022841`、区间约 `[-0.007216, 0.062015]`、置换 `p=0.226977`；Holm 校正后的四项主要 CCC 比较均未显著；
- 论文结论边界：材料只支持“B2 在验证集上最强，测试集 B2 与 S1 基本持平”的表述；明确当前实验没有获得自动乐段层级上下文带来稳定增量收益的证据，不将未显著结果表述为结构增益；
- 限制记录：包含自动结构未经完整人工真值评估、测试集仅 30 首、边界分析为描述性分析、仅覆盖当前冻结 MERT/All-In-One/轻量模型、未进行 PMEmo 外部验证和 SALAMI/人工结构审计等限制；
- 校验结果：材料关键数据、协议边界和限制措辞均通过本地检查；材料仅引用既有冻结报告，未启动训练、未重新评估测试集、未修改冻结模型或预测产物；
- 数据保护：只新增 `reports/paper-materials.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告或原始 `data/manifest.csv`。

### 2026-09-12：论文结果表格稿

- 功能名称：论文可直接引用的数据规模、模型关系、曲目级指标、分轴指标引用位、配对统计和边界分层表格；
- 当前状态：已完成并通过本地内容校验及 Markdown 诊断；`task-56`、`task-57`、`task-58` 可标记完成；
- 新增文件：独立材料 `reports/paper-tables.md`；
- 表格内容：新增数据与实验规模表、模型输入关系表、验证集/测试集 `ccc_mean` 汇总表、测试集 S1−B2/S1−B3 配对比较表、自动边界距离描述性分析表以及论文结论口径表；
- 数值范围：表格使用已记录的 205 首曲目、144/31/30 划分、6150 条有效监督、9225 个 MERT 特征帧、B2/S1 验证与测试 CCC、bootstrap 区间、置换 p 值和 Holm 校正结果；
- 分轴指标约束：由于冻结 `paper-results.json` 当前仅在远程报告目录，未将未经当前工作区读取校验的 Valence/Arousal 分轴数字写入表格；表 4 保留远程 JSON 引用位，并明确最终排版必须读取 `summary[split][model][metric].mean`，不得从 `ccc_mean` 反推分轴值；
- 论文边界：表格明确区分“当前实验支持的表述”和“不可支持的表述”，不得把 All-In-One 自动边界当成人工结构真值，也不得把未显著结果表述为自动结构增益；
- 校验结果：关键指标、统计值、协议字段和限制口径检查通过；`ReadLints` 未发现 `reports/paper-tables.md` 诊断；未启动训练或测试重评估；
- 数据保护：只新增 `reports/paper-tables.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告或原始 `data/manifest.csv`。

### 2026-09-12：论文正文结构化初稿

- 功能名称：将已冻结的数据协议、模型设计、实验结果、讨论、限制和结论整理为论文正文结构；
- 当前状态：已完成并通过本地内容一致性检查及 Markdown 诊断；`task-59`、`task-60`、`task-61` 可标记完成；
- 新增文件：独立材料 `reports/paper-draft.md`；
- 章节范围：包含摘要、引言、数据与任务定义、模型方法、实验设置、结果、讨论、局限性和结论，共 8 个正文部分；
- 固定内容：正文复用 205 首曲目、6150 条有效监督、144/31/30 曲目划分、9225 个 MERT 特征帧、B0/B1/B2/B3/S1 模型关系和曲目级评估协议；
- 结果内容：正文使用已记录的 B2/S1 验证与测试 `ccc_mean`、S1−B2/S1−B3 配对差异、bootstrap 区间、置换 p 值、Holm 校正及边界分层结果；分轴指标保留从冻结 JSON 直接引用的约束，不做反推；
- 结论边界：明确 B2 在验证集最强、测试集 B2 与 S1 基本持平，当前没有获得自动乐段层级上下文带来稳定增量收益的证据；没有将未显著结果表述为结构增益，也没有将 All-In-One 自动结构当作人工真值；
- 讨论约束：可能原因仅作为后续研究假设，不写成当前实验已验证的因果解释；限制中保留测试曲目规模、自动结构真值缺失、描述性边界分析、模型和表示范围以及缺少外部验证等内容；
- 校验结果：正文章节、关键冻结数值和边界措辞检查通过；`ReadLints` 未发现 `reports/paper-draft.md` 诊断；未启动训练、未重新评估测试集、未修改冻结模型或预测产物；
- 数据保护：只新增 `reports/paper-draft.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、其他论文材料或原始 `data/manifest.csv`。

### 2026-09-12：论文图表规格与投稿前核对清单

- 功能名称：论文图表目录、图注约束、数据来源规则和投稿前一致性核对清单；
- 当前状态：已完成并通过本地内容校验及 Markdown 诊断；`task-62`、`task-63`、`task-64` 可标记完成；
- 新增文件：独立材料 `reports/paper-figures-checklist.md`；
- 图表规划：定义数据流图、五模型结构对照图、验证/测试模型比较图、逐曲配对差异图、自动边界距离误差图和可选高误差曲目定性图；
- 图表约束：统一使用曲目级统计单位；多种子绘制均值和样本标准差；测试集只消费冻结预测和统计报告；图注必须说明 All-In-One 是自动结构来源而非人工结构真值；
- 结果引用：记录已核实的验证/测试 `ccc_mean` 汇总、S1−B2/S1−B3 配对结果和边界分层结果；未新增实验指标，不根据 `ccc_mean` 反推 Valence/Arousal 分轴值；
- 投稿检查：覆盖数据时间轴、MERT 参数、模型控制关系、测试集隔离、曲目级指标、bootstrap/置换/Holm 统计、限制表述和文件复现信息；
- 当前阻塞：本地工作区没有远程冻结的 `paper-results.json` 和 `formal-test-analysis.json` 副本，分轴图、逐曲配对图和最终分轴表必须在远程报告只读可访问后再填入，并保留来源和哈希；
- 论文边界：清单禁止将自动边界写成人工段落标注，禁止把未显著结果写成结构增益，禁止使用测试集误差清单反向筛选模型或曲目；
- 校验结果：清单关键章节、冻结数值、阻塞说明和禁止性约束检查通过；`ReadLints` 未发现 `reports/paper-figures-checklist.md` 诊断；未启动训练、未重新评估测试集、未修改冻结产物；
- 数据保护：只新增 `reports/paper-figures-checklist.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、其他论文材料或原始 `data/manifest.csv`。

### 2026-09-12：冻结报告驱动的论文图表生成脚本

- 功能名称：从冻结机器可读报告生成模型比较图和自动边界误差图；
- 当前状态：脚本实现完成并通过语法、CLI、静态诊断和缺失输入安全停止校验；真实图表尚未生成，原因是本地没有远程冻结 JSON；`task-65`、`task-66`、`task-67` 可标记完成；
- 新增文件：`render_paper_figures.py`；
- 输入契约：只读取 `paper-results.json` 的 `summary[split][model][ccc_mean]` 和 `formal-test-analysis.json` 的 `boundary_error[model][stratum][mae][track_mean]`；校验模型集合、验证/测试曲目数、曲目级统计单位和自动结构非真值标记；
- 输出设计：生成 `figure-model-comparison.png`、`figure-boundary-error.png` 和 `figures-metadata.json`；输出目录由调用方指定，默认不会覆盖冻结报告、预测或训练产物；
- 图表口径：模型比较图绘制验证/测试 `ccc_mean` 及多种子样本标准差；边界图绘制 B2/S1 的四个自动边界距离组 MAE；均不新增统计检验或模型选择逻辑；
- 安全约束：冻结 JSON 缺失、协议字段不匹配或边界字段缺失时直接报错，不生成占位图；逐曲配对图暂不实现，因为当前统计报告未保存逐曲配对差值；
- 校验结果：`python3 -m py_compile render_paper_figures.py`、`--help` 均通过；缺少冻结报告时输出 `frozen report not found` 并停止，未生成图表；`ReadLints` 未发现脚本诊断；
- 当前限制：由于远程冻结报告尚未同步到本地，本轮没有伪造或手工生成 PNG；待远程报告只读可访问后，使用固定输入运行并记录来源哈希、输出文件和复跑结果；
- 数据保护：只新增 `render_paper_figures.py`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告或原始 `data/manifest.csv`。

### 2026-09-12：论文图表脚本临时协议端到端验证

- 功能名称：使用最小冻结报告协议样例验证论文图表生成链路；
- 当前状态：已完成并通过真实绘图、PNG 可读取、元数据和清理校验；`task-68`、`task-69`、`task-70` 可标记完成；
- 验证范围：在 `/tmp` 创建不代表正式实验结果的最小 `paper-results.json` 和 `formal-test-analysis.json`，仅覆盖脚本所需字段；未读取或修改正式远程报告；
- 执行结果：脚本成功输出 `figure-model-comparison.png`、`figure-boundary-error.png` 和 `figures-metadata.json`；两张 PNG 文件均为非空且可读取，元数据确认统计单位为 `track`、自动结构不是真值、测试结果为只读消费；
- 安全结果：删除全部临时 JSON、PNG 和元数据文件；缺少冻结报告时脚本仍会输出 `frozen report not found` 并停止，不生成占位图；
- 论文边界：本次只验证软件链路，不把临时样例数值或临时图像作为实验产物，不改变任何正式模型、统计结果或论文结论；
- 校验结果：端到端绘图返回 `PAPER_FIGURES_OK`，输出完整性返回 `PAPER_FIGURES_RENDER_OK`，清理完成；
- 数据保护：未修改正式音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、论文材料或原始 `data/manifest.csv`。

### 2026-09-12：论文图注、表注与正文引用规范

- 功能名称：为论文图表和正文建立统一的图注、表注、交叉引用及禁止性表述替换规范；
- 当前状态：已完成并通过关键措辞检查及 Markdown 诊断；`task-71`、`task-72`、`task-73` 可标记完成；
- 新增文件：独立材料 `reports/paper-captions-and-citations.md`；
- 图注内容：覆盖数据流图、五模型结构图、验证/测试模型比较图、逐曲配对差异图、自动边界距离误差图和高误差曲目定性图；
- 表注内容：覆盖数据规模、模型定义、曲目级 CCC、分轴指标来源、配对统计、边界分层和结论口径；
- 引用关系：规定方法部分引用表 1、图 2；结果部分引用图 3–5 和表 3、表 5–6；所有引用均要求说明曲目级统计、测试集隔离和自动结构边界性质；
- 结论约束：明确禁止“人工段落标签”“真实乐段边界”“结构显著提升”等表述，统一替换为自动结构、描述性差异和当前固定协议下的保守结论；
- 排版流程：规定最终排版前直接从冻结 JSON 填充分轴指标、只读生成真实图表、保存输入哈希、复跑关键数字并写入独立 `reports/`；
- 校验结果：图注、表注、交叉引用和禁止性替换规则检查通过；`ReadLints` 未发现 `reports/paper-captions-and-citations.md` 诊断；未新增实验数值、未启动训练、未重新评估测试集；
- 数据保护：只新增 `reports/paper-captions-and-citations.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、其他论文材料或原始 `data/manifest.csv`。

### 2026-09-12：论文材料最终一致性审计

- 功能名称：论文正文、结果表格、图表清单和图注引用规范的一致性自动审计；
- 当前状态：已完成并通过正式本地审计；`task-74`、`task-75`、`task-76` 可标记完成；
- 新增文件：`audit_paper_materials.py` 和独立审计报告 `reports/paper-materials-audit.json`；
- 审计范围：检查五份本地论文材料是否存在，检查 205 首、144/31/30、6150、9225、曲目级统计、冻结模块、自动结构非人工真值、测试集隔离等关键约束；
- 审计结果：`status=ok`；关键文本缺失 `0`；冻结数值缺失 `0`；正文段落缺失、结果表缺失和图注章节缺失均为 `0`；正文危险结论数量 `0`；
- 安全设计：仅对正文 `paper-draft.md` 检查危险结论，图注规范中的“禁止表述”示例不会被误判；远程机器可读报告本地副本状态如实记录为 `false`，不影响本地材料审计通过；
- 校验结果：`python3 -m py_compile audit_paper_materials.py`、`--help` 和正式审计均通过；输出 `PAPER_MATERIALS_AUDIT status=ok`；审计产物完整性检查通过；`ReadLints` 未发现脚本或审计报告诊断；
- 数据保护：只新增审计脚本和 `reports/paper-materials-audit.json`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、论文材料或原始 `data/manifest.csv`。

### 2026-09-12：论文材料包索引与交付说明

- 功能名称：集中索引论文正文、表格、图注、图表清单、审计报告和生成脚本，并说明最终排版顺序及禁止事项；
- 当前状态：已完成并通过正式审计复跑、索引内容校验和 Markdown 诊断；`task-77`、`task-78`、`task-79` 可标记完成；
- 新增文件：独立材料 `reports/paper-package-index.md`；
- 材料包范围：列出 `paper-draft.md`、`paper-materials.md`、`paper-tables.md`、`paper-captions-and-citations.md`、`paper-figures-checklist.md`、`paper-materials-audit.json`、`audit_paper_materials.py` 和 `render_paper_figures.py` 的用途与状态；
- 冻结来源：明确最终排版只能使用远程 `paper-results.json`、`paper-results.csv`、`formal-test-analysis.json` 及正式运行目录中的冻结预测和元数据；
- 交付顺序：定义只读获取报告并保存哈希、填充分轴表、生成真实图表、检查来源和元数据、复跑材料审计的固定流程；
- 结论摘要：集中记录验证集 B2 最强、测试集 B2 与 S1 基本持平、S1−B2/S1−B3 未显著以及当前不能主张稳定结构增益；
- 禁止事项：明确不得把 All-In-One 自动结构写成人工真值，不得把验证集优势写成测试集泛化优势，不得从 `ccc_mean` 反推分轴指标，不得使用测试集误差清单反向调参；
- 校验结果：正式审计再次输出 `PAPER_MATERIALS_AUDIT status=ok`；关键文本、冻结数值、章节/表格/图注覆盖和正文危险结论均为 0；索引内容校验通过；
- 当前阻塞：远程机器可读报告尚未同步为本地副本，分轴表和正式 PNG 图表仍需在只读访问恢复后完成；该状态已在索引和审计报告中如实记录；
- 数据保护：只新增 `reports/paper-package-index.md`，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、其他论文材料或原始 `data/manifest.csv`。

### 2026-09-13：远程冻结报告只读访问复核

- 功能名称：尝试只读访问远程 `paper-results.json` 和 `formal-test-analysis.json`，为最终分轴表和正式图表生成解除阻塞；
- 当前状态：远程访问未完成，`task-80` 已完成；`task-81` 因认证阻塞取消；`task-82` 记录完成；
- 探测范围：仅检查 `/root/autodl-tmp/music-emotion-project/reports/paper-results.json`、`reports/formal-test-analysis.json` 是否存在并读取 SHA-256；未执行远程写操作，未修改远程项目；
- 访问结果：普通非交互 SSH 和本地认证辅助方式均返回 `Permission denied (publickey,password)`；无法在当前会话中安全读取远程报告；
- 处理决策：不将旧摘要、临时样例或人工抄录数值冒充远程正式报告；不生成正式 PNG，不填充分轴指标表；已完成的 `render_paper_figures.py`、论文材料包和本地审计保持有效；
- 当前可用产物：正文、表格、图注、图表清单、材料包索引、`audit_paper_materials.py`、`paper-materials-audit.json` 均保留；本地材料审计此前为 `status=ok`；
- 后续恢复条件：认证恢复后，只读同步两个远程 JSON 和 CSV，保存来源 SHA-256，填充表 4，运行 `render_paper_figures.py`，检查输出元数据并重新运行材料审计；不得借此修改冻结模型、预测、测试结论或数据划分；
- 数据保护：本次仅追加访问状态记录，未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、论文材料或原始 `data/manifest.csv`。

### 2026-09-13：论文材料一键收口脚本

- 功能名称：从冻结 JSON 自动填充分轴表、复用正式图表渲染、计算来源 SHA-256 并生成交付元数据；
- 当前状态：脚本实现完成，临时最小协议端到端验证通过；正式收口未执行，原因仍是远程冻结 JSON 认证阻塞；`task-84`、`task-85` 可标记完成；
- 新增文件：`finalize_paper_package.py`；原始 `reports/paper-tables.md` 未修改；
- 输入契约：要求 `paper-results.json`、`formal-test-analysis.json` 和表格模板；严格校验曲目级统计单位、`val/test=31/30`、五模型集合、六个分轴指标、`ccc_mean` 及图表所需标准差字段；严格校验自动结构非人工真值、30 首测试曲目和四个边界距离组；
- 输出契约：调用 `render_paper_figures.py` 生成模型比较图和自动边界误差图，输出填充后的 `paper-tables-filled.md`、两张 PNG、`source-sha256.json` 和 `delivery-metadata.json`；输出目录必须为新建或空目录，不覆盖原始材料；
- 安全行为：任一输入缺失、JSON 无效、协议不匹配、表格行顺序不匹配或数值非有限时，在创建输出目录前直接失败；不使用正文、旧摘要、临时数字或人工抄录结果补值；
- 校验结果：`python3 -m py_compile finalize_paper_package.py`、`--help`、缺失输入安全停止均通过；临时样例链路返回 `PAPER_PACKAGE_FINALIZED` 和 `PAPER_PACKAGE_SAMPLE_OK`，确认表格占位符被替换、PNG 非空、哈希和元数据可解析；`ReadLints` 未发现脚本诊断；
- 清理结果：临时 JSON、PNG、填充表格、哈希、元数据及输出目录均已删除；临时样例不作为正式实验产物；
- 正式状态：由于远程 `paper-results.json` 和 `formal-test-analysis.json` 仍无法认证访问，正式分轴表、正式 PNG 和正式来源哈希没有生成，不能标记正式图表完成；
- 数据保护：未启动训练、未重新评估测试集、未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、原始 `data/manifest.csv` 或既有论文材料。

### 2026-09-13：论文材料包索引补充收口脚本

- 功能名称：将 `finalize_paper_package.py` 纳入论文材料包索引，补齐脚本用途、验证状态和正式运行阻塞说明；
- 当前状态：已完成并通过文件内容检查；正式收口仍等待远程冻结报告认证恢复；
- 修改内容：仅修改 `reports/paper-package-index.md` 的生成工具清单，未修改冻结报告、表格模板、正文或图表产物；
- 记录内容：明确收口脚本负责协议校验、分轴表填充、图表生成、来源哈希和交付元数据，并注明正式运行尚未执行；
- 校验结果：索引中已出现 `finalize_paper_package.py`，脚本此前已通过语法、CLI、缺失输入停止和临时协议端到端验证；
- 数据保护：未启动训练、未重新评估测试集、未修改原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、原始 `data/manifest.csv` 或其他论文材料。

### 2026-09-13：远程冻结报告访问再次复核

- 功能名称：再次只读检查远程 `paper-results.json` 和 `formal-test-analysis.json` 是否可访问；
- 当前状态：认证阻塞仍未解除，未执行同步、哈希读取或正式收口；
- 执行范围：仅使用 BatchMode SSH 检查两个报告的可读性并在成功时读取 SHA-256；未执行远程写操作；
- 访问结果：仍返回 `Permission denied (publickey,password)`；两个冻结报告继续不可安全读取；
- 处理决策：不生成正式分轴表、PNG 或来源哈希，不使用旧摘要、临时样例或人工抄录数值替代；
- 数据保护：未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、论文材料或原始 `data/manifest.csv`。

### 2026-09-13：本地论文交付前置条件复核

- 功能名称：复核本地收口脚本、图表脚本、材料审计和正式报告副本状态；
- 当前状态：本地前置检查通过，正式收口仍被远程认证阻塞；
- 校验结果：`finalize_paper_package.py`、`render_paper_figures.py` 和 `audit_paper_materials.py` 均通过 `py_compile`；材料审计输出 `PAPER_MATERIALS_AUDIT status=ok`，缺失文本、冻结数值、章节/表格和危险结论均为 `0`；
- 来源状态：本地未发现 `reports/paper-results.json`、`reports/formal-test-analysis.json` 或 `reports/paper-tables-filled.md`，未把本地材料误当作正式冻结报告或正式交付物；
- 处理决策：未生成正式图表、分轴表或哈希清单；等待远程只读认证恢复后，直接运行既定收口脚本；
- 数据保护：未启动训练、未重新评估测试集、未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、论文材料或原始 `data/manifest.csv`。

### 2026-09-13：收口脚本元数据与来源哈希增强

- 功能名称：补齐一键收口脚本的图表元数据输出和渲染脚本来源哈希；
- 当前状态：已完成并通过临时协议端到端复验；正式收口仍被远程冻结报告认证阻塞；
- 修改内容：更新 `finalize_paper_package.py`，在正式输出目录中新增 `figures-metadata.json`，并将 `render_paper_figures.py` 纳入 `source-sha256.json`；
- 输出契约：正式目录现在包含 `paper-tables-filled.md`、`figure-model-comparison.png`、`figure-boundary-error.png`、`figures-metadata.json`、`source-sha256.json` 和 `delivery-metadata.json`；
- 校验结果：`python3 -m py_compile finalize_paper_package.py` 通过；临时样例返回 `PAPER_PACKAGE_FINALIZED` 和 `PAPER_PACKAGE_METADATA_OK`，确认元数据存在、自动结构非真值标记为真、渲染脚本哈希已记录、交付元数据包含 `figures-metadata.json`；
- 清理结果：临时 JSON、PNG、填充表格、图表元数据、哈希、交付元数据及输出目录均已删除；
- 正式状态：未生成正式图表、分轴表或哈希清单；等待远程只读认证恢复后再运行正式收口；
- 数据保护：未启动训练、未重新评估测试集、未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、统计报告、原始 `data/manifest.csv` 或既有论文材料。

### 2026-09-13：正式论文材料一键收口完成

- 功能名称：只读同步远程冻结报告并生成正式论文交付目录；
- 当前状态：已完成并通过正式产物验证；`task-86`、`task-87`、`task-88` 可标记完成；
- 输入目录：`reports/frozen-inputs-20260913-120829`，包含远程只读复制的 `paper-results.json` 和 `formal-test-analysis.json`；
- 输出目录：`reports/final-paper-package-20260913-121100`，为当前推荐正式交付目录；早期调试输出目录 `final-paper-package-20260913-120829` 和 `final-paper-package-20260913-121000` 已删除，避免误用；
- 来源哈希：远程与本地一致，`paper-results.json` 为 `7408a199cf28933effbfe5ec14bfe4fb6d8d3d75702d8ace9b9635e9d68c4192`，`formal-test-analysis.json` 为 `869bc9322b9e544e4bbe53542c77737ae79a3fa1bf04e62d5269bf3aceec95db`；
- 正式输出：`paper-tables-filled.md`、`figure-model-comparison.png`、`figure-boundary-error.png`、`figures-metadata.json`、`source-sha256.json` 和 `delivery-metadata.json`；
- 表格结果：表 4 已由冻结 `paper-results.json` 直接填充分轴指标；例如验证集 B2 为 Valence CCC `0.098579`、Arousal CCC `0.149264`，测试集 S1 为 Valence CCC `0.026166`、Arousal CCC `0.028001`；
- 图表结果：两张正式 PNG 均通过 PNG 头校验，图表元数据记录曲目级统计、自动结构非人工真值和测试集只读；
- 校验结果：`FINAL_PACKAGE_V3_OK` 通过；`audit_paper_materials.py --reports-dir reports` 输出 `PAPER_MATERIALS_AUDIT status=ok`，缺失文本、冻结数值、章节/表格和危险结论均为 `0`；
- 脚本修正：`finalize_paper_package.py` 已修正填充表 4 后的状态说明和表 5 前空行，避免正式填充表格出现过时阻塞说明或 Markdown 粘连；
- 数据保护：仅新增冻结报告本地副本目录和正式交付目录，并更新收口脚本及记录；未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、原始 `data/manifest.csv` 或原始 `reports/paper-tables.md`。

### 2026-09-13：论文材料索引与审计状态同步

- 功能名称：将材料索引和自动审计状态同步到正式交付完成后的事实状态；
- 当前状态：已完成并通过增强审计；`task-89`、`task-90`、`task-91` 可标记完成；
- 修改内容：更新 `reports/paper-package-index.md`，移除“冻结报告尚未同步”“正式运行待认证恢复”等过时阻塞说明，改为指向 `reports/frozen-inputs-20260913-120829` 和 `reports/final-paper-package-20260913-121100`；
- 审计增强：更新 `audit_paper_materials.py`，新增冻结输入目录、报告 SHA-256、正式交付目录、PNG 头、填充表格占位符和输出文件完整性检查；
- 审计报告：更新 `reports/paper-materials-audit.json`，其中 `remote_machine_readable_reports_local_copy=true`，`frozen_inputs.status=ok`，`final_package.status=ok`；
- 校验结果：`python3 -m py_compile audit_paper_materials.py` 通过；`audit_paper_materials.py --reports-dir reports --output reports/paper-materials-audit.json` 输出 `PAPER_MATERIALS_AUDIT status=ok`、`FROZEN_INPUTS_STATUS=ok`、`FINAL_PACKAGE_STATUS=ok`，缺失文本、冻结数值、章节/表格和危险结论均为 `0`；
- 数据保护：未启动训练、未重新评估测试集、未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、原始 `data/manifest.csv` 或原始 `reports/paper-tables.md`。

### 2026-09-13：图表清单与图注交付状态同步

- 功能名称：将图表清单和图注规范同步到正式图表与填充表格已生成后的状态；
- 当前状态：已完成并通过增强审计；`task-92`、`task-93`、`task-94` 可标记完成；
- 修改内容：更新 `reports/paper-figures-checklist.md`，将图 3 数据源改为 `reports/frozen-inputs-20260913-120829/paper-results.json`，将图 3 和图 5 正式图表指向 `reports/final-paper-package-20260913-121100`，并把“当前阻塞项”改为“当前正式交付状态”；
- 修改内容：更新 `reports/paper-captions-and-citations.md`，将表 4 注释和最终排版操作顺序改为使用正式交付目录中的填充表格、正式 PNG、来源哈希、图表元数据和交付元数据；
- 保留限制：图 4 逐曲配对差异图仍未生成；如后续需要，必须新增只读导出逻辑并继续记录来源哈希，不得用测试集逐曲差异反向筛选曲目或改变结论；
- 校验结果：过时阻塞表述复查通过；`audit_paper_materials.py --reports-dir reports --output reports/paper-materials-audit.json` 输出 `PAPER_MATERIALS_AUDIT status=ok`、`FROZEN_INPUTS_STATUS=ok`、`FINAL_PACKAGE_STATUS=ok`，缺失文本、冻结数值、章节/表格和危险结论均为 `0`；
- 数据保护：未启动训练、未重新评估测试集、未修改远程项目、原始音频、标签、结构 JSON、MERT 特征、训练 checkpoint、冻结预测、既有统计报告、原始 `data/manifest.csv` 或原始 `reports/paper-tables.md`。

### 2026-09-17：本任务工作汇总与状态纠正

以下仅记录本次对话实际执行和核查的工作，不替代上文其他任务已完成的正式交付记录。

#### 已完成

1. 使用更新后的 SSH 端口连接远程实验机，确认项目位于 `/root/autodl-tmp/music-emotion-project`；读取训练入口 `scripts/train.py --help` 和已有运行目录，确认存在 B1/B2/B3/S1 的三种子实验记录。本任务未启动新的训练。
2. 下载正式统计报告至 `/Users/jialiliu/Documents/app/experiments/formal-test-analysis.json`，并读取其统计协议、模型汇总、配对检验和边界距离分层结果。报告包含 30 首测试曲目，B1/B2/B3/S1 各 3 个种子，bootstrap 和置换检验各 10,000 次。本任务尚未核对该副本与上文冻结输入的来源哈希。
3. 创建并多次更新 `/Users/jialiliu/Documents/app/实验步骤.md`，加入用户的段落层级研究目标、模型和损失概要，以及正式测试诊断。但该文档仍是待修订草案，尚未完整落实全部消融与 Go/No-Go 协议。
4. 创建 `/Users/jialiliu/Documents/app/experiments/plot_results.py`。用户在本机运行后生成三张 PNG；文件存在不代表已通过科研数据正确性验收，限制见下文。

#### 从正式报告读取的结果

| 模型 | 测试集平均 CCC（VA 两轴平均） | 曲目级 95% bootstrap CI |
|---|---:|---|
| B1 | 0.026812 | [0.001786, 0.052787] |
| B2 | 0.027514 | [-0.015891, 0.070016] |
| B3 | 0.004243 | [-0.043442, 0.041157] |
| S1 | 0.027084 | [0.001413, 0.054784] |

- S1−B2 平均 CCC 差为 −0.000430，配对置换 p=0.981702；S1−B3 为 0.022841，p=0.226977。这两个平均指标的 p 值不是 Holm 校正值。
- 主要检验族为 S1 对 B2/B3 × Valence/Arousal CCC，共四项。S1 对 B3 的 Arousal CCC 未校正 p=0.041396，Holm 校正后 p=0.165583；其余三项校正 p=1.0，均未达到 0.05。
- 边界距离分层中，B2 的 MAE 约为 0.193–0.199，S1 约为 0.207–0.209。描述性结果未显示 S1 在边界附近优于 B2；不能据此推断边界误差原因或统计显著性。
- 当前证据不足以支持 S1 优于 B2/B3；不显著不等于证明模型等效。正式论述应保留两轴结果、配对差值区间与测试曲目数量限制。

#### 必须纠正的产物问题及此前汇报

- `experiments/results.csv` 曾由远程汇总文件转换，随后被测试集摘要覆盖，当前不包含验证集和分轴完整信息。其 `pearson` 列误用 CCC 数值，属于数据处理错误，不是实测 Pearson，禁止引用。
- `dynamic_trajectory_diagnostic.png` 来自脚本内的正弦合成数据，不是真实标签或 B2 预测，禁止作为实验结果或模型动态能力证据。
- `test_metric_profile.png` 包含上述错误 Pearson 数据，必须重做；`model_ccc_comparison.png` 未经过完整来源核验。三张旧图均应暂缓用于论文。
- 三张 PNG 的修改时间仍为 2026-09-16 12:37；后续自动运行未证明更新成功。此前“图表已重新生成”的汇报不准确。
- 新增边界图尝试运行失败（退出码 134），未生成边界 MAE/RMSE PNG。报错发生于 Matplotlib 初始化附近，但未完成根因诊断，不能认定只由字体缓存权限导致。
- `实验步骤.md` 仍残留偏离主线的多尺度增强建议、被试级统计、以两个模型 CI 不重叠判断差异等内容，需改为曲目级配对差值推断，并完整替换为用户确认的段落层级协议。
- 本任务未读到原始“下一阶段工作计划.md”，未完成在线文献检索或 DOI 核验，也未完整实现七项消融；此前关于这些事项已完成的表述应撤回。

#### 尚待完成（按优先级）

1. 优先核验并复用上文已有正式交付目录和冻结报告，避免重复生成冲突版本；校验报告来源哈希。
2. 修复绘图脚本：删除缺失数据时伪造指标的回退逻辑；不再以 CCC 代替 Pearson；只从可追溯的真实数据生成图表，分轴呈现 CCC/MAE/RMSE，并注明 CI 或种子标准差的含义。
3. 重写实验步骤，使 B1/B2/B3/S1、A1–A7、曲目级统计及 Go/No-Go 条件前后一致；完成相关文献检索和创新边界核验。
4. 只读检查现有预测、训练配置和参数量，再确定哪些消融确实缺失。新实验首先在训练/验证集推进；测试集已经查看，应明确后续分析的探索性，不能继续据测试结果调参并宣称独立确认。
5. 如需真实逐秒轨迹和配对差异图，读取已有冻结预测并记录来源，不用合成曲线替代；完成图表视觉检查及本地保存。
6. 确认论文代码仓库地址和分支，整理代码、正式图表、协议与来源记录后提交上传。本任务尚未进行 Git 提交或 GitHub 推送，工作目录 `/Users/jialiliu/Documents/app` 本身不是 Git 仓库。

本次汇总不包含 SSH 密码，不宣称完成新的训练、消融、正式图表验收或 GitHub 发布。
