> From: https://chatgpt.com/c/69ba8739-9c5c-83ab-a792-1c4a3416290c

# you asked

帮我配置一个做LBE下结构材料腐蚀的 多Agent配置

---

# chatgpt response

我先按“可落地的技术方案”来给您设计，不只讲概念。先核对一下目前常用的多 Agent / 工具接入方式，再直接给您一套适合 **LBE（铅铋共晶）下结构材料腐蚀研究** 的分层配置。

我已经核对了底层形态：**MCP 更适合接工具/数据源**，**Agents SDK 更适合做多 Agent 的 handoff 和流程编排**。MCP 的官方规范里把 **tools / resources** 作为标准接入面，OpenAI Agents SDK 则明确支持 **specialized agents、handoffs、traces** 这类多 Agent 运行方式。([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com))

可以。下面我直接给您一套 **面向 LBE（铅铋共晶）下结构材料腐蚀研究** 的 **多 Agent 配置方案**，默认按：

- **编排层**：OpenAI Agents SDK  
- **工具层**：MCP servers  
- **运行风格**：**中心调度 + 专家 Agent + 审核回路**

来设计。

这样配的原因很直接：MCP 适合把外部工具、数据库、文件资源([模型上下文协议](https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com))gents SDK 侧重 **specialized agents、handoffs、traces**。source=chatgpt.com))结构

## 推荐拓扑

```text
User
  ↓
[Coordinator / PM Agent]
  ├── [Literature Agent]       文献检索 / DOI / 摘要 / 证据卡片
  ├── [Data Agent]             实验台账 / 样品信息 / 暴露条件 / 氧浓度
  ├── [Microstructure Agent]   SEM/EDS/XRD/截面厚度/元素分布解释
  ├── [Mechanism Agent]        氧化层形成 / 溶解 / 选择性脱合金 / 流动腐蚀机理
  ├── [Kinetics Agent]         抛物线/线性动力学 / Arrhenius / 拟合 / 不确定度
  ├── [Experiment Agent]       后续实验设计 / 对照组 / 参数窗口
  └── [Reviewer Agent]         证据审查 / 引用核对 / 结论降级 / 风险提示
  ↓
Final Answer / Report / Slide / Markdown
```

## 为什么这样分

这不是“多几个机器人”而已，而是把您的研究任务拆成 **证据、图像、机理、模型、实验设计、审稿** 六类不同认知负荷。

对 LBE 腐蚀题目，最常见的失败点有三个：

1. **文献结论和样品现象混着讲**  
2. **显微图像解释跳步**  
3. **动力学拟合和机理结论直接绑定，没有审查层**

所以我建议您一定保留一个 **Reviewer Agent**，专门做“降温处理”：
- 哪些是证据支持的
- 哪些只是推断
- 哪些需要补实验

---

# 2. 每个 Agent 的职责配置

## A. Coordinator / PM Agent
**作用**：唯一对用户讲话，分派任务，汇总结果，控制 handoff。

### 输入
- 用户问题
- 当前项目上下文
- 各 Agent 返回的结构化结果

### 输出
- 最终回答
- 研究笔记
- 后续任务清单

### 规则
- 不直接做细节机理判断
- 必须先收集证据，再给结论
- 遇到冲突，优先交给 Reviewer Agent

---

## B. Literature Agent
**作用**：找论文、抽 DOI、提炼实验条件和主要结论。

### 重点抽取字段
```json
{
  "paper_title": "",
  "doi": "",
  "material": "",
  "temperature_c": null,
  "oxygen_condition": "",
  "flow_condition": "",
  "exposure_time_h": null,
  "main_observation": "",
  "oxide_structure": "",
  "claimed_mechanism": "",
  "limitations": ""
}
```

### 专门负责的问题
- 316L / 316Ti / T91 / 15-15Ti 在 LBE 中的差异
- 氧浓度窗口对保护氧化层稳定性的影响
- 流动条件、旋转盘、静态暴露对腐蚀模式的影响
- Ti、Si、Cr、Ni 等元素作用

### 不做的事
- 不直接下最终机理论断
- 不直接解释您自己的显微图片

---

## C. Data Agent
**作用**：把您自己的实验条件整理成机器能读的“样品事实表”。

### 维护的字段
```json
{
  "sample_id": "",
  "alloy": "316L / 316Ti / T91 / 15-15Ti",
  "composition_wt": {},
  "surface_state": "polished / shot peened / cold worked",
  "environment": "LBE",
  "temperature_c": 500,
  "oxygen_wt_percent": "1e-6",
  "velocity_m_s": null,
  "time_h": 1000,
  "specimen_geometry": "",
  "post_characterization": ["SEM", "EDS", "XRD", "EPMA"],
  "measured_oxide_thickness_um": [],
  "notes": ""
}
```

### 作用
- 把“实验条件缺失”暴露出来
- 给后续动力学拟合、文献对比提供统一输入

---

## D. Microstructure Agent
**作用**：专门解释显微图、EDS 线扫、面扫、层厚统计。

### 擅长任务
- 氧化层分层判断
- 内氧化 / 外氧化
- 元素富集区、贫化区判读
- 裂纹、剥落、孔隙、渗透通道识别
- 多张图之间的一致性检查

### 输出格式
```json
{
  "figure_id": "",
  "observations": [
    "表层连续氧化层",
    "内层存在Fe-Cr尖晶石候选区",
    "局部可见孔隙/剥落"
  ],
  "possible_interpretations": [],
  "confidence": "high/medium/low",
  "needs_more_data": ["higher magnification", "line scan", "phase identification"]
}
```

### 注意
它只能给“显微层面的解释”，不能单独宣布“机理已经证明”。

---

## E. Mechanism Agent
**作用**：从多源证据中推理腐蚀机理。

### 机理标签建议
```text
- protective oxidation
- non-protective oxidation
- dissolution corrosion
- selective leaching / dealloying
- liquid metal penetration assisted degradation
- flow-accelerated corrosion
- breakaway oxidation
- internal oxidation
```

### 产出
- 主机理
- 次机理
- 触发条件
- 证据链
- 反证点

### 输出模板
```json
{
  "primary_mechanism": "",
  "secondary_mechanisms": [],
  "supporting_evidence": [],
  "counter_evidence": [],
  "required_validation": []
}
```

---

## F. Kinetics Agent
**作用**：只做动力学，不碰形貌主观判断。

### 擅长
- 厚度—时间拟合
- 抛物线动力学 `x^2 = kt`
- 线性动力学 `x = kt`
- 分段动力学
- Arrhenius 拟合
- 误差传播

### 输入
- 时间
- 氧化层厚度
- 温度
- 样品分组

### 输出
```json
{
  "model_candidates": ["parabolic", "linear", "bilinear"],
  "best_fit": "",
  "parameters": {
    "k": null,
    "r2": null
  },
  "fit_quality_comment": "",
  "warning": ""
}
```

### 强制规则
- 拟合不好时必须说“不支持”
- 不允许因为 R² 还行就强行绑定机理

---

## G. Experiment Agent
**作用**：根据当前争议点，给出下一轮实验设计。

### 典型建议内容
- 氧浓度梯度组
- 不同流速组
- 316L vs 316Ti 对照
- shot peening / cold work 对照
- 不同时间点截断实验
- 需要补的表征：XRD、TEM、GDOES、EPMA、EBSD

---

## H. Reviewer Agent
**作用**：这是最关键的“防胡说”层。

### 审核项
- 每条结论是否有证据来源
- 文献结论是否外推过度
- 您自己的样品现象是否被过度解释
- 图像解释与动力学结果是否矛盾
- 是否缺关键条件：氧浓度、流速、样品表面状态、暴露时间

### 输出
```json
{
  "approved_claims": [],
  "downgraded_claims": [],
  "unsupported_claims": [],
  "missing_critical_data": [],
  "final_reliability": "high/medium/low"
}
```

---

# 3. MCP Server 应该怎么拆

MCP 的核心是把外部能力作为标准化 **tools** 和 **resources** 暴露给 Agent。工具可调用，资源可作为上下文读取。/modelcontextprotocol.io/specification/draft/server/tools?utm_source=chatgpt.com))“大而全”的 server。

## 3.1 `mcp-literature`
**用途**：论文、DOI、摘要、关键词、BibTeX

### tools
- `search_papers(query, year_from, year_to, material, env)`
- `get_paper_metadata(doi)`
- `extract_experiment_conditions(text_or_pdf)`
- `build_evidence_cards(paper_ids)`

### resources
- `/papers/cache/...`
- `/bib/library.json`
- `/evidence_cards/*.json`

---

## 3.2 `mcp-labdata`
**用途**：实验台账、样品元数据、暴露条件

### tools
- `list_samples(project_id)`
- `get_sample_record(sample_id)`
- `query_exposure_conditions(filters)`
- `save_analysis_note(sample_id, note)`

### resources
- `/samples/master_table.csv`
- `/experiments/*.json`
- `/logs/*.md`

---

## 3.3 `mcp-micrograph`
**用途**：图像测量和表征结果解析

### tools
- `measure_oxide_thickness(image_path, method, n_lines)`
- `extract_line_profile(image_path, start, end)`
- `segment_layers(image_path, mode)`
- `summarize_eds_map(image_bundle_id)`

### resources
- `/images/raw/...`
- `/images/processed/...`
- `/measurements/*.csv`

---

## 3.4 `mcp-kinetics`
**用途**：动力学拟合和统计

### tools
- `fit_parabolic(time, thickness)`
- `fit_linear(time, thickness)`
- `fit_arrhenius(temperature, k_values)`
- `compare_models(dataset_id)`

### resources
- `/fits/*.json`
- `/plots/*.png`

---

## 3.5 `mcp-mechanism`
**用途**：机理规则库 + 专家规则

### tools
- `infer_mechanism(observation_bundle)`
- `match_mechanism_patterns(features)`
- `generate_counter_hypotheses(bundle)`

### resources
- `/rules/lbe_corrosion_rules.yaml`
- `/knowledge/oxide_patterns.json`

---

## 3.6 `mcp-export`
**用途**：导出结果

### tools
- `export_markdown(report_bundle)`
- `export_ppt_outline(report_bundle)`
- `export_bibtex(doi_list)`

---

# 4. 我建议您直接采用的 handoff 规则

OpenAI 的 Agents SDK 文档和示例都把 **handoff** 当成多 Agent 协作的核心机制：一个 Agent 可以把任务转交给更合适的专门 Agent。nai.com/api/docs/guides/agents-sdk/?utm_source=chatgpt.com))ator
  → Literature Agent
  → Data Agent
  → Microstructure Agent
  → Mechanism Agent
  → Kinetics Agent
  → Reviewer Agent
  → Coordinator
```

## 有图片时
```text
Coordinator
  → Data Agent
  → Microstructure Agent
  → Literature Agent
  → Mechanism Agent
  → Reviewer Agent
  → Coordinator
```

## 有实验设计需求时
```text
Coordinator
  → Literature Agent
  → Data Agent
  → Reviewer Agent
  → Experiment Agent
  → Coordinator
```

---

# 5. 一套能直接放进项目里的配置文件

下面给您一个 **YAML 版配置**。  
这不是官方固定格式，而是**工程上非常好维护**的一种组织方式。

```yaml
project:
  name: lbe-corrosion-multi-agent
  domain: "LBE corrosion of structural materials"
  default_language: zh-CN
  output_style: "research-grade"

runtime:
  orchestrator: openai_agents_sdk
  model: gpt-5
  reasoning_effort: medium
  tracing: true

mcp_servers:
  - name: literature
    transport: stdio
    command: python
    args: ["servers/literature_server.py"]
  - name: labdata
    transport: stdio
    command: python
    args: ["servers/labdata_server.py"]
  - name: micrograph
    transport: stdio
    command: python
    args: ["servers/micrograph_server.py"]
  - name: kinetics
    transport: stdio
    command: python
    args: ["servers/kinetics_server.py"]
  - name: mechanism
    transport: stdio
    command: python
    args: ["servers/mechanism_server.py"]
  - name: export
    transport: stdio
    command: python
    args: ["servers/export_server.py"]

agents:
  - id: coordinator
    role: orchestrator
    handoffs_to:
      - literature_agent
      - data_agent
      - microstructure_agent
      - mechanism_agent
      - kinetics_agent
      - experiment_agent
      - reviewer_agent
    tools_from:
      - export

  - id: literature_agent
    role: evidence_retrieval
    handoffs_to: [coordinator, reviewer_agent]
    tools_from:
      - literature

  - id: data_agent
    role: experiment_context_builder
    handoffs_to: [coordinator, reviewer_agent]
    tools_from:
      - labdata

  - id: microstructure_agent
    role: image_interpreter
    handoffs_to: [coordinator, reviewer_agent, mechanism_agent]
    tools_from:
      - micrograph

  - id: mechanism_agent
    role: corrosion_mechanism_reasoner
    handoffs_to: [coordinator, reviewer_agent]
    tools_from:
      - mechanism
      - literature

  - id: kinetics_agent
    role: oxidation_kinetics_modeler
    handoffs_to: [coordinator, reviewer_agent]
    tools_from:
      - kinetics

  - id: experiment_agent
    role: next_experiment_designer
    handoffs_to: [coordinator]
    tools_from:
      - literature
      - labdata

  - id: reviewer_agent
    role: claim_auditor
    handoffs_to: [coordinator]
    tools_from:
      - literature
      - labdata
      - kinetics
      - mechanism

policies:
  require_citations: true
  separate_observation_from_inference: true
  reject_unsupported_claims: true
  ask_for_missing_critical_metadata: false
  degrade_confidence_when_data_missing: true
```

---

# 6. 每个 Agent 的 system prompt 模板

## 6.1 Coordinator

```text
You are the coordinator for an LBE corrosion research assistant.

Your job:
1. Understand the user task.
2. Delegate to specialist agents.
3. Merge outputs into a rigorous final answer.
4. Never overstate confidence.
5. Keep observations, literature evidence, mechanisms, and modeling clearly separated.

Rules:
- Do not invent experimental conditions.
- If oxygen concentration, temperature, flow condition, time, or alloy state is missing, explicitly mark uncertainty.
- Final answer must include:
  a) known facts
  b) inferred interpretation
  c) missing evidence
  d) next best action
```

---

## 6.2 Literature Agent

```text
You are the literature agent for LBE corrosion of structural materials.

You only do:
- paper retrieval
- metadata extraction
- experiment condition extraction
- evidence card construction

You must return structured evidence.
Do not give final mechanistic conclusions unless directly stated by the source.
Always separate:
- source claim
- source limitation
- your note
```

---

## 6.3 Microstructure Agent

```text
You are the microstructure interpretation agent.

You analyze SEM/EDS/XRD/cross-section evidence.
You must distinguish:
- direct visual observations
- likely interpretation
- uncertain interpretation

Never claim a phase unless supported by direct phase evidence or explicitly marked as tentative.
```

---

## 6.4 Mechanism Agent

```text
You are the corrosion mechanism reasoning agent for LBE-exposed structural alloys.

You integrate:
- literature evidence
- experiment context
- microstructure observations
- kinetics outputs

Output must contain:
1. primary mechanism
2. secondary mechanism
3. evidence supporting each
4. counter-evidence
5. required validation experiments

Never convert a plausible hypothesis into a proven conclusion.
```

---

## 6.5 Reviewer Agent

```text
You are the reviewer agent.

Your task is to challenge and downgrade unsupported claims.

Check:
- missing conditions
- overextended literature comparisons
- image over-interpretation
- poor kinetic fit used as mechanistic proof
- citation gaps

Return:
- approved claims
- downgraded claims
- unsupported claims
- missing critical data
- final reliability level
```

---

# 7. 推荐的项目目录

```text
lbe-corrosion-multi-agent/
├─ app/
│  ├─ main.py
│  ├─ agent_registry.py
│  ├─ prompts/
│  │  ├─ coordinator.txt
│  │  ├─ literature_agent.txt
│  │  ├─ data_agent.txt
│  │  ├─ microstructure_agent.txt
│  │  ├─ mechanism_agent.txt
│  │  ├─ kinetics_agent.txt
│  │  ├─ experiment_agent.txt
│  │  └─ reviewer_agent.txt
│  └─ schemas/
│     ├─ evidence_card.py
│     ├─ observation_bundle.py
│     ├─ kinetics_result.py
│     └─ review_report.py
├─ servers/
│  ├─ literature_server.py
│  ├─ labdata_server.py
│  ├─ micrograph_server.py
│  ├─ kinetics_server.py
│  ├─ mechanism_server.py
│  └─ export_server.py
├─ data/
│  ├─ samples/
│  ├─ papers/
│  ├─ images/
│  ├─ fits/
│  └─ reports/
├─ config/
│  └─ agents.yaml
└─ README.md
```

---

# 8. 一段最小可用的编排伪代码

下面是 **工程骨架**。  
具体 import 名称您需要按当前安装的 Agents SDK 版本微调，因为 SDK 会迭代；但整体组织方式是对的。OpenAI 官方文档明确支持用 Agents SDK 做多 Agent 编排和 handoff。nai.com/api/docs/guides/agents-sdk/?utm_source=chatgpt.com))from pathlib import Path
import yaml

# 按当前 SDK 版本微调
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

BASE = Path(__file__).resolve().parents[1]

def load_text(p: str) -> str:
    return (BASE / p).read_text(encoding="utf-8")

def build_servers():
    return {
        "literature": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/literature_server.py")]
        ),
        "labdata": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/labdata_server.py")]
        ),
        "micrograph": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/micrograph_server.py")]
        ),
        "kinetics": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/kinetics_server.py")]
        ),
        "mechanism": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/mechanism_server.py")]
        ),
        "export": MCPServerStdio(
            command="python",
            args=[str(BASE / "servers/export_server.py")]
        ),
    }

def build_agents(servers):
    literature_agent = Agent(
        name="Literature Agent",
        instructions=load_text("app/prompts/literature_agent.txt"),
        mcp_servers=[servers["literature"]],
    )

    data_agent = Agent(
        name="Data Agent",
        instructions=load_text("app/prompts/data_agent.txt"),
        mcp_servers=[servers["labdata"]],
    )

    microstructure_agent = Agent(
        name="Microstructure Agent",
        instructions=load_text("app/prompts/microstructure_agent.txt"),
        mcp_servers=[servers["micrograph"]],
    )

    mechanism_agent = Agent(
        name="Mechanism Agent",
        instructions=load_text("app/prompts/mechanism_agent.txt"),
        mcp_servers=[servers["mechanism"], servers["literature"]],
    )

    kinetics_agent = Agent(
        name="Kinetics Agent",
        instructions=load_text("app/prompts/kinetics_agent.txt"),
        mcp_servers=[servers["kinetics"]],
    )

    experiment_agent = Agent(
        name="Experiment Agent",
        instructions=load_text("app/prompts/experiment_agent.txt"),
        mcp_servers=[servers["literature"], servers["labdata"]],
    )

    reviewer_agent = Agent(
        name="Reviewer Agent",
        instructions=load_text("app/prompts/reviewer_agent.txt"),
        mcp_servers=[
            servers["literature"],
            servers["labdata"],
            servers["kinetics"],
            servers["mechanism"],
        ],
    )

    coordinator = Agent(
        name="Coordinator",
        instructions=load_text("app/prompts/coordinator.txt"),
        mcp_servers=[servers["export"]],
        handoffs=[
            literature_agent,
            data_agent,
            microstructure_agent,
            mechanism_agent,
            kinetics_agent,
            experiment_agent,
            reviewer_agent,
        ],
    )

    return coordinator

def main():
    servers = build_servers()
    coordinator = build_agents(servers)

    user_task = """
    分析316Ti在500°C、饱和氧浓度LBE中暴露1000h后的氧化行为，
    结合截面SEM/EDS和文献，判断主导机制，并给出下一步实验建议。
    """

    result = Runner.run_sync(coordinator, user_task)
    print(result.final_output)

if __name__ == "__main__":
    main()
```

---

# 9. 对 LBE 腐蚀场景，最重要的 5 条约束

这部分不是框架文档，而是我给您的**领域规则**，很重要。

## 规则 1：观察、解释、结论必须三段分开
例如：

- **观察**：外层约 8–12 μm，局部剥落  
- **解释**：可能存在非致密氧化层或热应力导致附着力不足  
- **结论**：暂不支持“必然 breakaway oxidation”，需补 XRD/更多时间点

---

## 规则 2：动力学拟合不能单独证明机理
`x² = kt` 拟合得不错，只能说“与抛物线控制相容”，不能直接说“机理已证明为扩散控制”。

---

## 规则 3：文献比较必须对齐 4 个条件
- 温度
- 氧浓度
- 流动/静态
- 表面状态/材料状态

这 4 个不对齐，Literature Agent 和 Reviewer Agent 都应该降置信度。

---

## 规则 4：显微相判断必须降级措辞
没有相鉴定时不要写：
- “确定为 Fe₃O₄”
- “确定为尖晶石”

应写：
- “疑似 Fe-rich outer oxide”
- “可能为 Fe-Cr spinel-like inner layer”

---

## 规则 5：必须允许“无法判断”
这点非常关键。  
一个好的科研多 Agent，不是更会说，而是更会 **停下来**。

---

# 10. 我给您的默认落地版本

如果您现在就要开始做，我建议直接用这个版本：

## 轻量版（最实用）
- 1 个 Coordinator
- 1 个 Literature Agent
- 1 个 Microstructure Agent
- 1 个 Mechanism Agent
- 1 个 Reviewer Agent
- 3 个 MCP server：
  - `mcp-literature`
  - `mcp-micrograph`
  - `mcp-export`

适合：先做**论文解读 + 图像解释 + 机理推理**

---

## 标准版（最适合科研）
- 7 个 Agent
- 6 个 MCP server
- 启用 Reviewer 审核闭环
- 保存 evidence cards / observation bundles / fit results

适合：**持续写论文、做实验、积累知识库**

---

## 增强版（适合课题组）
再加两个：

- `Code Agent`：专门写 ImageJ / Python 分析脚本
- `Planning Agent`：把实验计划按周输出

---

# 11. 我建议您下一步直接做什么

您这类题目，最合适的第一步不是先写 UI，而是先把这 3 个对象定下来：

```text
1. evidence_card
2. observation_bundle
3. review_report
```

只要这三个结构化对象定好了，多 Agent 很快就能跑起来。

---

如果您愿意，我下一条可以直接继续给您补一套**完整可运行版本**，包括：

- `agents.yaml`
- 7 个 Agent 的完整 prompt 文件
- 6 个 MCP server 的 Python 骨架
- `evidence_card.py / review_report.py` 的 Pydantic 数据结构
- 一个专门适配 **316L / 316Ti / T91 / 15-15Ti 在 LBE 中腐蚀研究** 的规则库 `lbe_corrosion_rules.yaml`

---

# you asked

分析研究趋势

---

# chatgpt response

我先读取您上传的表格，确认字段结构，再基于里面的数据做研究趋势分析。随后我会给您一版可直接用于汇报的结论。

我已经把主文献库做了去重统计，时间范围是 **2004–2026**，总量约 **518 篇**。初步看，趋势非常明显：**2022 年后显著加速，2024–2026 是集中爆发期**，而且研究重点正在从“基体钢本体腐蚀”转向“涂层、复杂环境、耦合效应和机制精细化”。

可以。下面我按您上传的 **LBESCI.xlsx** 做一个**研究趋势分析**。  
我先说明口径：

## 数据口径
- 我把主文献库主要按这 3 个 sheet 合并后去重分析：  
  **`corrosci.jonm` + `OTHER` + `26.3.2`**
- 去重方式：**优先 DOI，其次标题**
- 得到主样本约 **518 篇**，时间跨度 **2004–2026**
- 另外把专题 sheet 作为辅助判断：  
  - **`流动`**：53 篇  
  - **`辐照`**：18 篇  
  - **`LBE宏观性能影响`**：105 篇

> 说明：专题 sheet 和主库之间存在交叉，**不能简单相加**。  
> 下面的“主题数量”有些是基于标题关键词做的粗分类，**可重复归类**，更适合看方向，不适合当绝对精确值。

---

# 一句话结论

**LBE 下结构材料腐蚀研究已经从“基体材料在静态/单因素环境下的腐蚀与脆化”阶段，明显转向“流动-氧浓度-辐照-应力/磨损耦合环境下的机制解析，以及涂层/新型合金的工程化防护”阶段。**

---

# 1. 发文趋势：2022 年后明显加速，2024–2026 是爆发期

## 年度数量变化（主库去重后）
- **2022**：40 篇
- **2023**：51 篇
- **2024**：71 篇
- **2025**：100 篇
- **2026**：45 篇（但这是未完全年份，不能直接和全年比）

## 分阶段看更清楚
| 阶段 | 年均文献量 |
|---|---:|
| 2004–2014 | **约 10.7 篇/年** |
| 2015–2021 | **约 13.3 篇/年** |
| 2022–2025 | **约 65.5 篇/年** |
| 2023–2025 | **约 74.0 篇/年** |

## 这说明什么
这不是简单“稳步增长”，而是**近几年研究热度陡增**。  
通常这意味着三个事同时发生了：

1. **领域工程需求增强**  
   LBE 作为 ADS、先进核能冷却剂相关材料问题，实用导向更强。

2. **研究问题变复杂了**  
   早期主要讨论“会不会腐蚀、会不会脆化”，现在更多在问：
   - 为什么形成多层氧化膜
   - 氧浓度窗口怎么控制
   - 流动条件下保护膜为什么失效
   - 辐照后膜层和界面怎么演化

3. **评价对象从裸材扩展到防护体系**
   包括 FeCrAl、氧化物涂层、高熵合金、非晶合金、MAX 相等。

---

# 2. 期刊分布：核心阵地非常集中，但重心在外扩

## 主库中最核心的两个期刊
- **JOURNAL OF NUCLEAR MATERIALS**：**154 篇**
- **CORROSION SCIENCE**：**86 篇**

这两个期刊基本就是该方向的“双核心”：
- **JNM** 更偏 **核材料服役场景、材料行为、工程背景**
- **Corrosion Science** 更偏 **腐蚀机制、氧化层、界面演化、机理解释**

## 2023–2026 最近阶段
近年高频期刊包括：
- **CORROSION SCIENCE**：55 篇
- **JOURNAL OF NUCLEAR MATERIALS**：43 篇
- **JMR&T**
- **SURFACE & COATINGS TECHNOLOGY**
- **ANNALS OF NUCLEAR ENERGY**
- **ENGINEERING FRACTURE MECHANICS**

## 趋势判断
这说明研究正在从“核材料专属问题”进一步扩展到：
- **表面工程**
- **断裂/力学失效**
- **材料设计**
- **服役环境耦合**

也就是：**从单纯腐蚀问题，转成“腐蚀 + 力学 + 表界面工程”的综合问题。**

---

# 3. 研究主题的演化路径

---

## 第一阶段：2004–2014  
### 关键词：**T91、液态金属脆化、流动 LBE、基础腐蚀行为**

这一阶段的主线非常清楚：  
先把最基本的问题搞明白——**材料接触 LBE 后会发生什么失效。**

代表特点：
- 重点材料以 **T91、马氏体钢、不锈钢** 为主
- 重点问题是：
  - **液态金属脆化（LME）**
  - **流动和氧浓度对腐蚀的影响**
  - **机械性能下降**
  - **基础氧化行为**

您表里的典型早期文献就很能说明问题：
- **Effect of contact conditions on embrittlement of T91 steel by lead-bismuth**（2004）
- **Corrosion behaviour of stainless steels in flowing LBE at low and high oxygen concentration**（2004）
- **Effects of temperature and strain rate on the mechanical properties of T91 material tested in liquid lead bismuth eutectic**（2006）
- **Liquid metal embrittlement of T91 martensitic steel evidenced by small punch test**（2007）

### 这一阶段的本质
> 先确认“危险性”和“基本失效模式”。

---

## 第二阶段：2015–2021  
### 关键词：**氧化动力学、保护膜稳定性、流动条件、不同钢种对比**

这阶段研究开始从“现象确认”转向“**机理细化**”。

重点变化：
- 开始更系统地看：
  - **氧浓度窗口**
  - **流动工况**
  - **氧化膜分层**
  - **扩散控制/溶解控制**
- 材料对比更明确：
  - **T91**
  - **316 系**
  - **15-15Ti**
  - F/M steels

这一阶段相当于建立了后来很多工作的基础逻辑：
- 为什么有时形成保护膜，有时失效
- 为什么流动环境更严苛
- 为什么成分微调会影响膜层质量

### 这一阶段的本质
> 从“会腐蚀”走向“**怎么腐蚀、什么条件下加速腐蚀**”。

---

## 第三阶段：2022–至今  
### 关键词：**涂层、新材料、辐照耦合、复杂工况、机制精细化**

这是您表格中最明显的主趋势。

---

### 3.1 涂层研究明显成为热点

基于标题粗分类，**涂层/包覆类**文献数量变化很明显：

- **2020–2022**：12 篇
- **2023–2025**：55 篇
- **2026**：9 篇（未完全年）

这是非常典型的“热点转向”。

代表方向包括：
- **FeCrAl / FeCrAlY**
- **FeAl / Al2O3**
- **Cr/ZrO2**
- **高熵合金涂层**
- **非晶涂层**

您表里的代表文献有：
- **Screening of the FeCrAl LBE corrosion-resistant coatings: The effect of Cr and Al contents**（2023）
- **Enhancing LBE corrosion resistance through inhibition diffusion approach for AlTixCrFe HEA coating**（2024）
- **Research progress on LBE corrosion-resistant coatings: A review**（2024）
- **Insights into LBE corrosion behavior of the FeCrAlTi and FeCrAlNb coatings**（2026）

### 趋势判断
未来不是简单比“哪种基体钢更耐蚀”，而是比：
- **谁能形成更稳定的阻挡层**
- **谁在流动/低氧/辐照下不失效**
- **谁更有工程可实施性**

也就是研究焦点已经从 **bulk alloy selection**，转向 **surface/interface engineering**。

---

### 3.2 辐照相关研究在重新升温

专题 sheet“辐照”只有 18 篇，不算多，但时间分布很有意思：
- 2011–2012：少量起步
- 2015–2019：不连续
- **2021 后明显恢复**
- **2024–2025 增长明显**

代表文献：
- **Structure of surface oxides on martensitic steel under simultaneous ion irradiation and molten LBE corrosion**（2022）
- **Study on LBE corrosion failure of FeAl/Al2O3 coatings after ion irradiation**（2024）
- **Effect of Au ion irradiation on microstructure, mechanical, and LBE corrosion properties of Cr/ZrO2 coatings**（2024）
- **Corrosion behavior of irradiated FeCrAlY coatings in oxygen-deficient and flowing LBE**（2025）

### 趋势判断
这说明领域开始从“常规腐蚀环境”走向更真实的服役环境：
- **辐照 + 腐蚀**
- **辐照 + 流动 + 低氧**
- **辐照后膜层稳定性**

这类问题更接近核能实际服役场景，后续大概率继续升温。

---

### 3.3 流动 LBE 仍是主线，但研究方式在变

“流动”专题 sheet 有 **53 篇**，时间跨度很长，说明它一直是核心问题之一。  
但最近几年它的研究重点不再只是“流动会不会更严重”，而是：

- 流场如何改变氧化膜形成和剥落
- 流动下多层氧化膜如何演化
- 静态/流动之间机制差异
- 流动与低氧、辐照、合金元素设计的耦合

代表文献：
- **Corrosion behaviour of stainless steels in flowing LBE at low and high oxygen concentration**（2004）
- **Oxidation behavior of T91 steel in flowing oxygen-containing lead-bismuth eutectic at 500 °C**（2016）
- **Corrosion kinetics and mechanisms of 15-15Ti steel in flowing liquid LBE at 500°C**（2024）
- **Revealing corrosion mechanism of Si-doping 9 wt.% Cr F/M steels in oxygen-saturated static and flowing LBE at 550 °C**（2025）
- **Toward Understanding the Formation and Microstructure of Complex Multilayered Oxide Scales in Flowing LBE**（2025）

### 趋势判断
流动研究没有降温，只是从“现象对比”升级成“**复杂多层氧化膜和局部失效机制研究**”。

---

### 3.4 力学/脆化研究从“是否脆化”转向“阈值与服役后性能”

按标题粗分类，**液态金属脆化/力学**相关是一个长期主线，主库里有大约 **94 篇**。

它的变化不是数量暴涨，而是问题变细：
- 早期：是否发生 LME、疲劳性能是否下降
- 近年：  
  - 预暴露时间的影响  
  - 裂纹起始阈值  
  - 韧性/延展性变化  
  - 腐蚀后宏观性能响应  

例如您表里的：
- **Enhanced toughness and ductility of T91 steel after exposure to liquid LBE saturated by oxygen at 350–500 °C**（2024）
- **Liquid metal embrittlement of T91 steel in liquid LBE: The role of long-term pre-exposure and threshold stress of crack initiation**（2025）

### 趋势判断
现在大家不满足于“测腐蚀层厚度”，更关心：
> **腐蚀后材料还能不能服役、什么时候开始危险失效。**

---

### 3.5 新材料路线开始增多，但还没取代传统钢种

近年比较活跃的新路线：
- **高熵合金**
- **非晶合金**
- **MAX 相**
- 含 **Al、Si、Ta、Ti、Nb** 等元素优化的材料/涂层

例如：
- **AlTixCrFe HEA coating**（2024）
- **Mo-based amorphous alloys**（2026）
- **gelcasted MAX phases in contaminated LBE**（2024）
- **Ta segregation on HEA corrosion resistance**（2026）

### 但现阶段并没有取代传统主角
主库标题中高频材料仍然是：
- **T91**
- **316/316L/316Ti/316H**
- **F/M steels**
- **奥氏体不锈钢**
- **FeCrAl 系**

这说明目前领域仍然是“两条线并行”：
1. **传统结构材料服役机理**
2. **新型防护材料/表面工程**

---

# 4. 材料对象趋势：谁是主角

## 从标题统计看，主角仍然非常明确
- **T91**：约 **92 篇**
- **316 系（316/316L/316Ti/316H）**：约 **56 篇**
- **FeCrAl/FeCrAlY/FeAl**：约 **29 篇**
- **马氏体/FM 钢相关**：约 **124 篇**
- **奥氏体不锈钢相关**：约 **100 篇**

## 最近几年（2023–2026）
- **T91**：35 篇
- **316 系**：32 篇
- **FeCrAl/FeCrAlY/FeAl**：23 篇

### 这说明什么
- **T91 和 316 系**仍然是“标准参照材料”
- **FeCrAl 系**增长很快，说明其在防护层/表面工程方向很受重视
- **15-15Ti**总量不算大，但在**流动 LBE**方向有持续存在感，属于“有特定应用价值的小众重点材料”

---

# 5. 这个领域现在最强的 4 个热点

我把趋势压缩成最重要的 4 条：

## 热点 1：涂层化
研究重点已经明显从“选更好的钢”变成“给现有材料做更可靠的表面防护”。

## 热点 2：耦合环境化
单一静态腐蚀不够了，越来越多工作在做：
- 流动
- 低氧/高氧
- 辐照
- 应力
- 摩擦/磨损  
这些因素的组合。

## 热点 3：机制精细化
不再只看总腐蚀厚度，而更重视：
- 多层氧化膜结构
- 扩散阻挡
- 界面完整性
- 剥落/裂纹/局部失效

## 热点 4：性能导向
腐蚀研究和力学性能、裂纹阈值、韧性损失开始更紧密结合。  
这意味着后续高质量论文更容易往“**腐蚀—组织—性能**”链条走。

---

# 6. 我对未来 2–3 年研究方向的判断

如果只根据您这个文献库判断，未来最值得关注的是：

## 方向 A：**流动 + 低氧 + 辐照** 的耦合腐蚀
这是最接近真实服役条件的方向，也是现在还没有完全做透的方向。

## 方向 B：**涂层失效机制**
不是简单比较“谁更耐蚀”，而是研究：
- 为什么前期有效、后期失效
- 界面扩散如何演化
- 辐照后涂层为什么开裂/脱层/失稳

## 方向 C：**多层氧化膜的形成与演变**
特别是流动 LBE 下的复杂膜层结构，是当前非常前沿的切入点。

## 方向 D：**腐蚀后宏观性能评价**
把腐蚀层、组织变化、裂纹起始、阈值应力、疲劳/断裂统一起来，更容易形成完整论文链条。

---

# 7. 如果您是要做论文选题，我给您的判断

## 最有潜力的切入方式
### 方案 1：传统材料 + 复杂环境
例如：
- **316Ti / 15-15Ti / T91 在流动 LBE 中的氧化动力学与膜层演化**
- 再加一个变量：氧浓度、预处理、表面状态、辐照前后

优点：
- 容易和已有文献对接
- 机制线清楚
- 论文更稳

### 方案 2：涂层/新材料 + 失效机理
例如：
- **FeCrAl、Al2O3、Cr/ZrO2、HEA 涂层在 LBE 中的失效机制**
- 看扩散、开裂、剥落、辐照后稳定性

优点：
- 新
- 容易进入热点
- 但实验难度更高

### 方案 3：腐蚀—力学耦合
例如：
- **长时预暴露后阈值应力、裂纹起始、脆化行为**
- 比单纯测腐蚀厚度更有“服役意义”

优点：
- 工程价值高
- 论文差异化明显

---

# 8. 最终结论

## 您这个文献库反映出来的主趋势可以概括成一句话：

**LBE 结构材料腐蚀研究的主轴，正在从“基体材料的基础腐蚀与脆化评估”，升级为“复杂服役环境下界面保护机制与失效机制的系统研究”，其中涂层化、耦合化、机制精细化和性能导向化，是当前最明显的四个方向。**

如果您要，我下一步可以继续直接帮您做两种版本中的一种：

1. **把这份趋势分析整理成论文开题/综述可直接使用的正式段落**  
2. **把这些趋势进一步提炼成“LBE 腐蚀研究路线图 + 选题建议”**

---

# you asked

给我饱和氧流动腐蚀相关的优质文章

---

# chatgpt response

我先从您上传的文献表里筛出 **“饱和氧 + 流动腐蚀”** 相关条目，再按相关性和代表性给您做一份优质文章清单。

下面这组，适合您做 **LBE 中“饱和氧/高氧控制 + 流动腐蚀”** 的文献主线。  
我按 **“先读必读基础 → 再读最新机制/工程化”** 排。严格命中 **flowing + oxygen-saturated / oxygen-containing** 的放前面；316/奥氏体扩展文献放后面。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311504005458?utm_source=chatgpt.com))
## 一、最值得先读的 8 篇

1. **Aiello et al., 2004, *Journal of Nuclear Materials***  
   **Corrosion behaviour of stainless steels in flowing LBE at low and high oxygen concentration**  
   DOI: **10.1016/j.jnucmat.2004.07.011**  
   这是经典起点。核心价值不是“饱和氧”本身，而是把 **低氧下的溶解腐蚀** 和 **高氧下的保护性氧化** 这条主线讲清楚了，做流动 LBE 腐蚀几乎都绕不过去。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311504005458?utm_source=chatgpt.com))
2. **Schroer et al., 2012, *Journal of Nuclear Materials***  
   **Corrosion kinetics of Steel T91 in flowing oxygen-containing lead-bismuth eutectic at 450 °C**  
   DOI: **10.1016/j.jnucmat.2011.11.014**  
   这篇非常硬。它给了 **450 °C、2 m/s、平均 1.1×10⁻⁶ mass% O、最长 8000 h** 的长时动力学数据，并明确提到 T91 形成 **双层腐蚀产物层（magnetite + Fe-Cr spinel）**，很适合拿来当动力学和膜层结构的基准文献。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311511009664?utm_source=chatgpt.com))
3. **Schroer et al., 2014, *Nuclear Engineering and Design***  
   **Performance of 9% Cr steels in flowing lead-bismuth eutectic at 450 and 550°C, and 10⁻⁶ mass% dissolved oxygen**  
   DOI: **10.1016/j.nucengdes.2014.01.023**  
   这篇偏工程环路条件，价值在于 **CORRIDA loop、450/550 °C、2 m/s、10⁻⁶ 级氧浓度、最长 8000/20000 h**。如果您要写“工程适用性”“长期服役窗口”，这篇很重要。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0029549314001356?utm_source=chatgpt.com))
4. **Tian et al., 2016, *Materials and Corrosion***  
   **Oxidation behavior of T91 steel in flowing oxygen-containing lead-bismuth eutectic at 500 °C**  
   DOI: **10.1002/maco.201609075**  
   这篇相当于把 T91 的流动高氧腐蚀从 450 °C 往 **500 °C** 推了一步，适合和 2012 那篇配合着读，看温度升高后氧化行为与膜层演化怎么变。([Wiley Online Library](https://onlinelibrary.wiley.com/doi/10.1002/maco.201609075?utm_source=chatgpt.com))
5. **Tian et al., 2024, *Journal of Nuclear Materials***  
   **Corrosion kinetics and mechanisms of 15–15Ti steel in flowing liquid lead-bismuth eutectic at 500°C**  
   DOI: **10.1016/j.jnucmat.2024.155344**  
   这篇很值得读。它研究的是 **500 °C、1 m/s、1–3×10⁻⁶ wt% O** 的 15-15Ti，在“高氧保护区”里讨论了 **氧化动力学、合金元素溶解、氧化层剥落** 的耦合问题，已经比传统 T91 工作更接近您后面要做的机理深化。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S002231152400446X?utm_source=chatgpt.com))
6. **Sun et al., 2023, *Journal of Nuclear Materials***  
   **Correlation between impact angle and corrosion-erosion damage behavior of ferritic/martensitic steel exposed to flowing oxygen-saturated lead-bismuth eutectic**  
   DOI: **10.1016/j.jnucmat.2023.154745**  
   如果您关注“**流动冲刷 + 腐蚀**”而不是单纯静态氧化，这篇必须看。摘要直接给出 **~3 m/s、500 °C、oxygen-saturated LBE**，重点是 **冲击角度** 如何改变膜层损伤、屈曲和剥落。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311523005123?utm_source=chatgpt.com))
7. **Zheng et al., 2023, *Materials Today Communications***  
   **Effects of laser surface remelting on damage resistance of oxide scales on T91 exposed to flowing oxygen-saturated lead-bismuth eutectic**  
   DOI: **10.1016/j.mtcomm.2023.107223**  
   这篇偏表面工程，但很实用。条件同样是 **~3 m/s、500 °C、oxygen-saturated LBE**，看的是 **激光表面重熔** 能不能提高 T91 氧化层在流动环境下的抗损伤能力。做“预处理/表面改性”方向时，这篇非常合适。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S2352492823019141?utm_source=chatgpt.com))
8. **Zhao et al., 2025, *Journal of Nuclear Materials***  
   **Revealing corrosion mechanism of Si-doping 9 wt. % Cr F/M steels in oxygen-saturated static and flowing LBE at 550 °C**  
   DOI: **10.1016/j.jnucmat.2025.156011**  
   这是近年的机制型文章。重点不是“有没有腐蚀”，而是 **Si 掺杂如何改变 F/M steel 在饱和氧静态/流动 LBE 中的氧化行为和微观机理**。如果您后面做元素设计或机理综述，这篇优先级很高。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311525004052?utm_source=chatgpt.com))
## 二、机制深化时再补的 2 篇

9. **Zhao et al., 2025, *High Temperature Corrosion of Materials***  
   **Toward Understanding the Formation and Microstructure of Complex Multilayered Oxide Scales in Flowing Lead-Bismuth Eutectic (LBE)**  
   DOI: **10.1007/s11085-025-10356-0**  
   这篇适合做“膜层结构”深化阅读。摘要信息显示，它讨论的是 **T91 在 500 °C、90° 冲击、流动氧饱和 LBE** 下形成的 **复杂多层氧化膜**，并强调这与静态 LBE 常见的双层氧化膜不同。([Springer Link](https://link.springer.com/content/pdf/10.1007/s11085-025-10356-0.pdf?utm_source=chatgpt.com))
10. **Schroer et al., 2010, *Journal of Nuclear Materials***  
    **Oxidation behaviour of P122 and a 9Cr–2W ODS steel at 550 °C in oxygen-containing flowing lead-bismuth eutectic**  
    DOI: **10.1016/j.jnucmat.2009.10.019**  
    这篇适合做 9Cr 体系横向比较。它给出的重点是 **550 °C、oxygen-containing flowing LBE** 下形成 **spinel 型致密层 + 内氧化区**，并且尝试用动力学规律来预测更长时间的金属减薄。([科学直通车](https://www.sciencedirect.com/science/article/pii/S0022311509008277?utm_source=chatgpt.com))
## 三、如果您偏奥氏体 / 316 系，再补这 2 篇

11. **Tsisar et al., 2014, *Journal of Nuclear Materials***  
    **Corrosion behavior of austenitic steels 1.4970, 316L and 1.4571 in flowing LBE at 450 and 550 °C with 10⁻⁷ mass% dissolved oxygen**  
    DOI: **10.1016/j.jnucmat.2014.08.024**  
    这篇不是“严格饱和氧”，而是 **oxygen-controlled**，但它对 **316L 与其他奥氏体钢** 在流动 LBE 中的对比非常有价值；摘要直接给出 **2 m/s、10⁻⁷ mass% O、450/550 °C、最长 8766/2011 h**。做 316 系综述时建议必补。([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311514005522?utm_source=chatgpt.com))
12. **Tian, 2020, *Oxidation of Metals***  
    **Growth and Exfoliation Behavior of the Oxide Scale on 316L and T91 in Flowing Liquid Lead-Bismuth Eutectic at 480 °C**  
    DOI: **10.1007/s11085-019-09953-7**  
    这篇适合看 **316L vs T91** 的氧化层生长和剥落差异。公开摘要信息给出了 **0.3 m/s、480 °C、最长 3000 h**，并指出 316L 主要是较薄的 **Fe-Cr spinel**，而 T91 是 **magnetite + Fe-Cr spinel + internal oxidation zone**。([DeepDyve](https://www.deepdyve.com/browse/journals/0030-770X/2020/v93/i1-2?rows=10&start=0&utm_source=chatgpt.com))
## 四、阅读顺序建议

如果您现在是为了 **快速搭建“饱和氧流动腐蚀”知识框架**，建议这样读：

**先读**  
- Aiello 2004  
- Schroer 2012  
- Schroer 2014  

**再读**  
- Tian 2016  
- Tian 2024（15-15Ti）  
- Sun 2023（冲击角/冲蚀-腐蚀）  

**最后读机制深化**  
- Zhao 2025（Si 掺杂）  
- Zhao 2025（复杂多层氧化膜）([科学直通车](https://www.sciencedirect.com/science/article/abs/pii/S0022311504005458?utm_source=chatgpt.com))
如果您下一步要做 **316Ti / 15-15Ti / T91** 其中某一个材料，我建议直接按材料给您再筛一版“最该精读的 5 篇”。

---

# you asked

给我找高校研究LBE流动腐蚀的博士论文

---

# chatgpt response

我先按“高校 + 博士论文/博士学位论文 + LBE/lead-bismuth eutectic + flowing corrosion”这个口径筛一轮，优先找**可定位到学校、作者、年份、题目**的正式学位论文。

我再从您上传的文献表里补查一遍“thesis / dissertation / 博士学位论文”线索，避免漏掉表里已经整理过的高校来源。

可以。  
我按 **“高校正式博士学位论文 / 明确与 LBE（铅铋共晶）/ 流动腐蚀 或强相关服役环境有关”** 的口径筛了一轮。结论是：

## 先说结论

**严格直接命中“LBE 流动腐蚀”这一主题的博士论文，并不算多。**  
公开能较高置信确认的，最值得您先抓的是下面这几篇；其余不少博士论文更偏 **氧控 LBE、静态 LBE、应力腐蚀、焊缝/涂层、或实验回路平台**，也很有用，但不属于最纯粹的“流动腐蚀博士论文”。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm))
# 一、直接命中“LBE 流动腐蚀”的博士论文

## 1) 李聪｜中国科学技术大学｜2021
**题目**：**结构钢在流动铅铋合金中多种腐蚀失效模式的交互作用机制**  
这篇是我这轮里**最直接、最贴题**的一篇。公开信息显示，这项博士工作围绕**流动铅铋**腐蚀平台展开，并且改进了动态腐蚀装置，使研究不再局限于 0° 冲击角，还引入了接近 90° 的流动冲刷条件；材料对象包括 **T91** 和 **304N**。另有高校教师主页可交叉确认，李聪于 **2021 年在中科大获博士学位**，研究方向就是**流动液态铅铋中的金属材料腐蚀机理**。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm))
## 2) 近藤正聡（Masatoshi Kondo）｜东京工业大学｜2006
**题目**：**流動鉛ビスマス条件下の鋼材及びセラミックスの組織変化と液体内化学制御に関する研究**  
东京工业大学相关页面明确写到，他于 **2006 年获得东京工业大学博士学位**，博士论文题目就是这篇。题目本身已经直接点明 **“流动铅铋条件下”**，对象覆盖**钢材与陶瓷**，并涉及**液体内化学控制**。如果您要追日本在**流动 LBE 回路、氧控制、材料组织变化**这条线，这篇很关键。([kondo.zc.iir.titech.ac.jp](https://kondo.zc.iir.titech.ac.jp/introduction.html))
## 3) Christopher Petersson｜KTH Royal Institute of Technology｜2024
**题目**：**Alumina-forming stainless steels in liquid lead and lead-bismuth eutectic**  
这篇不是“只做 LBE 流动腐蚀”，但它是**明确的博士论文**，而且摘要写得很清楚：工作包括 **erosion-corrosion rig（冲蚀-腐蚀装置）** 条件下的研究，环境覆盖**液态铅和 LBE**。如果您关心 **流动/冲刷 + 腐蚀 + 新型铝化不锈钢**，这篇非常值得进主文献。([kth.diva-portal.org](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf))
# 二、相关度很高，但不完全等同于“流动腐蚀”的博士论文

## 4) 田书建｜中国科学技术大学｜2016
**题目**：**T91和15-15Ti钢在500 ℃液态铅铋合金氧控条件下腐蚀行为与机理研究**  
这是明确标注为**博士学位论文**的中科大学位论文。它更偏 **氧控 LBE 腐蚀行为与机理**，从题名本身看**不直接强调流动**，但对 **T91 / 15-15Ti / 氧浓度窗口 / 氧化机理** 这条主线非常重要。做“流动腐蚀”综述时，它通常属于必须补的基础博士论文。([hplpb.com.cn](https://www.hplpb.com.cn/cn/article/doi/10.11884/HPLPB202335.220398))
## 5) 刘静｜中国科学技术大学｜2015
**题目**：**T91和316L钢在液态Pb-Bi共晶合金中应力腐蚀行为研究**  
这篇可确认是**博士学位论文**，方向更偏 **应力腐蚀 / 液态金属脆化相关行为**，不是严格的“流动腐蚀”，但如果您研究的是 **流动腐蚀—力学失效耦合**，这篇很值得一起读。([中国科学院投资研究中心](https://www.inest.cas.cn/new/rcdw/dwgk/fyjy/202201/t20220125_317484.html))
## 6) 常海龙｜中国科学院大学｜2018
**题目**：**控氧液态铅铋合金实验装置研究**  
这是**博士学位论文**，重心不是材料腐蚀机理本体，而是**控氧液态铅铋实验装置/平台**。对做 **流动 LBE 腐蚀回路、氧控系统、实验条件稳定性** 的人很有参考价值，属于“平台型博士论文”。([mater-rep.com](https://www.mater-rep.com/CN/10.11896/cldb.21090168))
## 7) Oksana Klok｜Vrije Universiteit Brussel (VUB)｜2018
**题目**：**Liquid Metal Corrosion Effects in MYRRHA Candidate 316L Austenitic Stainless Steel**  
VUB 的 MYRRHA 博士项目页面明确列出这是一项 **PhD project**。但页面也明确说明，其腐蚀实验是**静态 LBE**，所以它不属于流动腐蚀博士论文，不过对 **316L 在 LBE 中的腐蚀行为** 很有代表性。([myrrha.be](https://www.myrrha.be/science-output/phd-dissertations/liquid-metal-corrosion-effects-myrrha-candidate-316l-austenitic-stainless-steel))
## 8) Amke Lescur｜根特大学（UGent）｜2023
**题目**：**The Influence of Liquid Lead-Bismuth Environment on Mechanical Properties and Corrosion Resistance of Austenitic Stainless Steel Welds**  
UGent 研究门户把它明确标成 **Doctoral thesis**。方向偏 **奥氏体不锈钢焊缝在 LBE 中的力学与耐蚀性**，与“流动腐蚀”并不完全同义，但对**焊缝/接头区服役可靠性**很有价值。([researchportal.sckcen.be](https://researchportal.sckcen.be/en/publications/the-influence-of-liquid-lead-bismuth-environment-on-mechanical-pr/))
## 9) 陈钢｜江苏大学｜2019
**题目**：**CLAM钢母材和焊缝在550℃液态铅铋合金中的腐蚀机制研究**  
可通过答辩公告和学位授予名单交叉确认这是**博士学位论文**。它更偏 **CLAM 钢及焊缝在 LBE 中的腐蚀机制**，不是明确的流动腐蚀题名，但做**结构材料 / 焊缝 / 高温 LBE**方向时值得纳入。([yjsy.ujs.edu.cn](https://yjsy.ujs.edu.cn/info/1364/7466.htm))
# 三、如果您只想保留“最贴题”的清单

如果只保留和 **“高校 + 博士论文 + LBE 流动腐蚀”** 最贴近的，我建议您优先锁定这 4 篇：

1. **李聪，中科大，2021**  
   《结构钢在流动铅铋合金中多种腐蚀失效模式的交互作用机制》 ([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm))
2. **近藤正聡，东京工业大学，2006**  
   《流動鉛ビスマス条件下の鋼材及びセラミックスの組織変化と液体内化学制御に関する研究》 ([kondo.zc.iir.titech.ac.jp](https://kondo.zc.iir.titech.ac.jp/introduction.html))
3. **Christopher Petersson，KTH，2024**  
   *Alumina-forming stainless steels in liquid lead and lead-bismuth eutectic*  
   （包含 erosion-corrosion 装置下的 LBE 研究） ([kth.diva-portal.org](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf))
4. **田书建，中科大，2016**  
   《T91和15-15Ti钢在500 ℃液态铅铋合金氧控条件下腐蚀行为与机理研究》  
   （虽非明确“流动”，但对流动高氧腐蚀研究非常接近、非常重要） ([hplpb.com.cn](https://www.hplpb.com.cn/cn/article/doi/10.11884/HPLPB202335.220398))
# 四、我对现状的判断

从这轮结果看，**真正公开且可明确定位的“LBE 流动腐蚀博士论文”数量比期刊论文少得多**。高校博士研究更常见的分布是：

- **流动 / 冲蚀-腐蚀 / 回路平台**
- **氧控 LBE 腐蚀**
- **静态 LBE 腐蚀**
- **LME / 应力腐蚀 / 力学性能**
- **焊缝 / 涂层 / 新型合金**

也就是说，您后面做综述时，往往要把“**严格流动腐蚀博士论文**”和“**强相关博士论文**”分成两层来用。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm))
下一步如果您要，我可以继续给您整理一版 **“这些博士论文对应的下载入口线索 + 各自研究对象（T91 / 316L / 15-15Ti / 焊缝 / 涂层）+ 哪几篇最适合您当前课题”**。

---

# you asked

这些博士论文对应的下载入口线索 + 各自研究对象（T91 / 316L / 15-15Ti / 焊缝 / 涂层）+ 哪几篇最适合您当前课题”

---

# chatgpt response

我在补每篇博士论文的**实际获取线索**，重点核对两类信息：  
1）能否直接下载全文；2）如果不能，至少能否定位到 **学位库入口 / 学校仓储 / PDF 页面**。随后我会顺手按 **T91 / 316L / 15-15Ti / 焊缝 / 涂层** 给您归类。

我已经把“能直接下 PDF”和“只能定位到学位库/仓储条目”的情况分开了。  
结论先给您：**真正适合您当前“饱和氧/氧控 + 流动腐蚀”主线的，优先看 4 篇：李聪、田书建、Christopher Petersson、Amke Lescur。**

可以。  
我按您前面连续在问的方向，把“当前课题”默认理解为：

> **LBE 中结构材料在饱和氧 / 氧控条件下的流动腐蚀**，并重点关心 **T91、316 系、15-15Ti、焊缝、表面防护/涂层**。

下面我把 **下载入口线索 + 研究对象归类 + 对您当前课题的适配度** 直接合并给您。

---

# 一、最适合您当前课题的 4 篇

## 1) 李聪｜中科大｜2021  
**题目**：**结构钢在流动铅铋合金中多种腐蚀失效模式的交互作用机制**  
**研究对象**：**流动 LBE 下的结构钢失效模式**，非常贴近“流动腐蚀主线”；作者公开简介也明确写了其博士与后续研究方向是**流动液态铅铋中的金属材料腐蚀机理**。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com))
**为什么适合您当前课题**：  
这篇是您现在这条线里最该优先找的博士论文，因为它不是泛泛讲 LBE，而是直接落在 **“流动铅铋 + 多种腐蚀/失效模式耦合”** 上。您如果后面要写“氧化层剥落、冲刷、局部失效、流动加速腐蚀”这类内容，它最对口。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com))
**下载入口线索**：  
目前公开检索里，我能稳定定位到的是 **CNKI 博士学位论文条目**；最直接的找法是去 **CNKI 中国博士学位论文全文数据库** 用**完整题名**检索。若您学校或单位开通了 CNKI 学位库，通常可直接下载；我这轮没有稳定抓到公开 PDF。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com))
---

## 2) 田书建｜中科大｜2016  
**题目**：**T91和15-15Ti钢在500 ℃液态铅铋合金氧控条件下腐蚀行为与机理研究**  
**研究对象**：**T91 + 15-15Ti**，条件是 **500 ℃ + 氧控 LBE**。这篇在后续综述中被明确作为博士论文引用，Google Scholar 公开学术档案也列出了该学位论文。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com))
**为什么适合您当前课题**：  
如果您现在重点是 **“氧控/饱和氧附近的腐蚀行为、氧化层、动力学、T91 与奥氏体钢对比”**，这篇比很多国外综述还更贴近您的研究输入。虽然题名没有直接写“流动”，但它和您要做的 **高氧/氧控腐蚀机制主线** 非常接近，尤其适合补 **15-15Ti**。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com))
**下载入口线索**：  
目前我稳定确认到的是 **论文被正式综述引用** 和 **Google Scholar 条目**；实际下载大概率还是走 **CNKI 学位库** 或中科大馆藏检索。公开网页里我这轮没有抓到稳定的开放 PDF。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com))
---

## 3) Amke Lescur｜根特大学｜2023  
**题目**：**The Influence of Liquid Lead-Bismuth Environment on Mechanical Properties and Corrosion Resistance of Austenitic Stainless Steel Welds**  
**研究对象**：**奥氏体不锈钢焊缝**；摘要明确写到做了 **静态和动态流动铅铋** 的长期暴露腐蚀分析，并比较了焊缝与母材在不同条件下的表现。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T))
**为什么适合您当前课题**：  
如果您关心 **“流动 LBE 下焊缝/接头是否比母材更脆弱”**，这篇非常有用。它不是单纯材料本体腐蚀，而是把 **焊缝微观组织、机械性能、静态/动态流动铅铋腐蚀** 放在一起看，适合您后面做“腐蚀—组织—性能”链条。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T))
**下载入口线索**：  
最稳的是 **UGent Academic Bibliography / Handle 条目**，能确认题名、作者、页数、ISBN、答辩日期；但页面同时写了 **“No license (in copyright)”**，所以这更像**正式馆藏入口**，不一定开放全文。若您要全文，优先从 **UGent handle 页面**、校图馆跨馆，或联系作者/导师线。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T))
---

## 4) Christopher Petersson｜KTH｜2024  
**题目**：**Alumina-forming stainless steels in liquid lead and lead-bismuth eutectic**  
**研究对象**：**铝化不锈钢 / alumina-forming steels**；摘要明确写到使用 **SSRT rig** 和 **Erosion-Corrosion rig (ECO)**，研究环境包括 **liquid lead 与 LBE**。([KTH Diva Portal](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf))
**为什么适合您当前课题**：  
这篇不是传统的 **T91/316L/15-15Ti 本体腐蚀**，而是更偏 **防护材料 / 先进钢种 / 冲蚀-腐蚀 rig**。如果您后续准备往 **表面防护、Al2O3 保护层、材料升级路线** 扩展，它是非常好的博士论文入口。([KTH Diva Portal](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf))
**下载入口线索**：  
这是您这批里**最好拿全文**的一篇。KTH 的 **DiVA** 页面明确标出 **Open Access in DiVA**，并给出 **FULLTEXT02.pdf**、文件大小和 permanent link；公开 PDF 可直接读。([KTH Diva Portal](https://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A1914011))
---

# 二、按研究对象给您归类

## 1. **T91 / 15-15Ti**
### 首选：田书建（中科大，2016）  
这是最直接的一篇：题名就把 **T91** 和 **15-15Ti** 写出来了，而且是 **500 ℃ + 氧控 LBE**。对您做材料比较、氧化层、机制梳理最有用。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com))
### 次选：李聪（中科大，2021）  
更偏 **流动铅铋 + 失效模式耦合**。如果您现在重点是 **流动腐蚀 / 冲刷 / 局部失效**，它比田书建那篇更靠近“流动主线”。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com))
---

## 2. **316L / 奥氏体钢**
### 首选：Oksana Klok（VUB，2018）  
**题目**：**Liquid Metal Corrosion Effects in MYRRHA Candidate 316L Austenitic Stainless Steel**  
MYRRHA 官方博士页面明确写了作者、学校、导师；页面摘要还写明它的核心是 **316L 在 LBE 中的液态金属腐蚀**，重点放在 **dissolution corrosion、氧浓度、塑性变形、组织不均匀性、表面状态**，并明确说明**所有腐蚀实验都在 static LBE** 中完成。([Myrrha](https://www.myrrha.be/science-output/phd-dissertations/liquid-metal-corrosion-effects-myrrha-candidate-316l-austenitic-stainless-steel))
**下载线索**：  
公开检索里有两条比较实用：  
一条是 **MYRRHA/SCK CEN 的博士页面**；另一条是 **ResearchGate 条目**，搜索结果直接显示 “**Thesis PDF Available**”。另外还有一条来自 **SCK CEN portal PDF** 的搜索结果，但我这边打开时工具返回异常，所以把它作为辅助线索，不当成已核实的稳定入口。([Myrrha](https://www.myrrha.be/science-output/phd-dissertations/liquid-metal-corrosion-effects-myrrha-candidate-316l-austenitic-stainless-steel))
### 次选：刘静（中科大，2015）  
**题目**：**T91和316L钢在液态Pb-Bi共晶合金中应力腐蚀行为研究**  
这是 **T91 + 316L**，但更偏 **应力腐蚀 / 脆化**，不是严格的流动腐蚀主线。做“316L 服役后性能”时值得补。([中国知网](https://www.cnki.com.cn/Article/CJFDTotal-JSGC202104021.htm?utm_source=chatgpt.com))
---

## 3. **焊缝 / 接头**
### 首选：Amke Lescur（UGent，2023）  
适合看 **奥氏体不锈钢焊缝在静态与动态流动铅铋中的表现差异**。如果您要做“焊缝是不是薄弱环节”，这篇优先级很高。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T))
### 次选：陈钢（江苏大学，2019）  
**题目**：**CLAM钢母材和焊缝在550℃液态铅铋合金中的腐蚀机制研究**  
江苏大学答辩海报和博士学位获得者公示都能确认这是一篇正式博士论文。虽然题名没有直接写“流动”，但同课题组公开论文明确做了 **CLAM TIG 焊缝在 550 ℃、1.70 / 2.31 / 2.98 m/s 流动 LBE 中 1500 h** 的研究，所以这篇博士论文对 **焊缝 + 流动铅铋** 很可能非常贴近。([yjsy.ujs.edu.cn](https://yjsy.ujs.edu.cn/info/1364/7466.htm?utm_source=chatgpt.com))
**下载线索**：  
我目前稳定拿到的是 **答辩海报 + 学位授予公示**；公开全文入口这轮没稳定抓到。实际最可能还是 **CNKI/Wanfang 按完整题名检索**。([yjsy.ujs.edu.cn](https://yjsy.ujs.edu.cn/info/1364/7466.htm?utm_source=chatgpt.com))
---

## 4. **涂层 / 防护材料 / 新型钢**
### 首选：Christopher Petersson（KTH，2024）  
它不是传统意义的“涂层博士论文”，但路线非常接近：**alumina-forming steels、LME、erosion-corrosion rig**，适合您从“基体钢腐蚀”往“保护性表面/先进钢种”升级。最重要的是它 **公开全文最好拿**。([KTH Diva Portal](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf))
---

## 5. **氧控平台 / 流动化学控制**
### 常海龙（国科大，2018）  
**题目**：**控氧液态铅铋合金实验装置研究**  
这篇更偏 **实验平台、氧控装置、回路能力**，不是直接讲某一种钢的腐蚀机理，但如果您后面自己要搭实验逻辑、写“试验装置与氧控方法”，价值很高。后续综述中明确将其作为 **Ph.D. Thesis, UCAS, 2018** 引用。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.21090168?utm_source=chatgpt.com))
### 近藤正聡（东京工大，2006）  
**题目**：**流動鉛ビスマス条件下の鋼材及びセラミックスの組織変化と液体内化学制御に関する研究**  
T2R2 学校仓储明确标出这是 **Ph.D. thesis**，并列出了 **题名、作者、东工大、授予日期、Thesis (Ph.D.)**；页面还显示了一个 **File 图标**。我能确认它是正式的学校仓储记录，但这轮没有进一步验证到开放 PDF 是否可直接下。([t2r2.star.titech.ac.jp](https://t2r2.star.titech.ac.jp/cgi-bin/publicationinfo.cgi?lv=en&q_publication_content_number=CTT100602686))
---

# 三、如果只从“对您现在课题最有用”排序

按您现在这条 **“饱和氧/氧控 + 流动腐蚀 + 结构材料”** 主线，我建议顺序是：

## 第一梯队
1. **李聪 2021** —— 最贴近 **流动 LBE 失效模式**。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com)) 
2. **田书建 2016** —— 最贴近 **T91 / 15-15Ti + 氧控 500 ℃**。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com)) 
3. **Amke Lescur 2023** —— 如果您关心 **焊缝/动态流动铅铋**，这篇非常值。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T)) 

## 第二梯队
4. **Christopher Petersson 2024** —— 适合您把课题往 **防护材料/冲蚀-腐蚀** 扩展，而且全文最好拿。([KTH Diva Portal](https://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A1914011)) 
5. **Oksana Klok 2018** —— 适合补 **316L**，但它是 **static LBE**，不属于最纯的“流动腐蚀”线。([Myrrha](https://www.myrrha.be/science-output/phd-dissertations/liquid-metal-corrosion-effects-myrrha-candidate-316l-austenitic-stainless-steel)) 
6. **常海龙 2018 / 近藤 2006** —— 更偏 **氧控平台 / 化学控制 / 回路体系**，做装置和方法学时很有用。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.21090168?utm_source=chatgpt.com)) 

---

# 四、我再给您一个最省时间的拿文策略

## 先拿能直接读全文的
- **Christopher Petersson 2024**：KTH DiVA 公开全文最稳。([KTH Diva Portal](https://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A1914011)) 
- **Oksana Klok 2018**：先试 **ResearchGate**；搜索结果显示 thesis PDF 可用。([ResearchGate](https://www.researchgate.net/publication/340298812_Liquid_Metal_Corrosion_Effects_in_MYRRHA_Candidate_316L_Austenitic_Stainless_Steel?utm_source=chatgpt.com)) 

## 再拿需要机构权限的
- **李聪 2021**：CNKI 学位库 exact title。([中国知网](https://cdmd.cnki.com.cn/Article/CDMD-10358-1021072920.htm?utm_source=chatgpt.com)) 
- **田书建 2016**：CNKI / 中科大馆藏 exact title。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com)) 
- **刘静 2015**：CNKI / 中科大馆藏 exact title。([中国知网](https://www.cnki.com.cn/Article/CJFDTotal-JSGC202104021.htm?utm_source=chatgpt.com)) 

## 焊缝方向单独补
- **Amke Lescur 2023**：先走 UGent handle；如果没全文，再走馆际互借或联系作者。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T)) 
- **陈钢 2019**：先按完整题名去 CNKI/Wanfang；公开网页目前只稳定到答辩与授予信息。([yjsy.ujs.edu.cn](https://yjsy.ujs.edu.cn/info/1364/7466.htm?utm_source=chatgpt.com)) 

---

# 五、我替您下判断

如果您现在要做的是：

- **T91 / 15-15Ti 的氧控与流动腐蚀**：先看 **田书建 + 李聪**。([Mater Rep](https://www.mater-rep.com/CN/10.11896/cldb.19070056?utm_source=chatgpt.com)) 
- **316 系尤其 316L 机制**：先看 **Oksana Klok**，再补 **刘静**。([Myrrha](https://www.myrrha.be/science-output/phd-dissertations/liquid-metal-corrosion-effects-myrrha-candidate-316l-austenitic-stainless-steel)) 
- **焊缝/接头在流动 LBE 中的表现**：先看 **Amke Lescur**，再补 **陈钢**。([根特大学学术文献库](https://biblio.ugent.be/publication/01H3VF2RCKYX1JWJEXRXBGPN3T)) 
- **往涂层/先进防护材料走**：先看 **Christopher Petersson**。([KTH Diva Portal](https://kth.diva-portal.org/smash/get/diva2%3A1914011/FULLTEXT02.pdf)) 

如果您要，我下一条我可以直接继续给您做一份：

**“这几篇博士论文的章节级精读路线图（先读哪几章、各自能提炼出什么结论、和您当前课题怎么对接）”**。