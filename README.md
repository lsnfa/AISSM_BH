# AISSM_BH
**人工智能驱动的分子动力学模拟助手**

**AISSM_BH—将GROMACS模拟从手动流程提升至智能自动化。

告别重复的命令行操作和漫长的错误调试。  
由BHAI团队（百宏集团）开发的AI驱动分子动力学助手，现已提供专业、稳定且完全自动化的模拟体验。

---

##项目简介

**AISSM_BH**是由BHAi团队（百宏集团）开发的基于人工智能的分子动力学模拟助手。它以GROMACS引擎为基础，支持用户通过自然语言指令完成蛋白质及蛋白-配体复合物的整个模拟流程。工作流程包括拓扑生成、溶剂化处理、能量最小化、NVT/NPT平衡、生产分子动力学模拟、轨迹分析（RMSD、RMSF、回转半径、氢键、二级结构），以及MM-PBSA/GBSA结合自由能计算。

该工具支持两种运行模式：**Copilot（咨询模式）和Agent（自主模式）。它兼容包括OpenAI、DeepSeek和Gemini在内的主流大型语言模型，并提供MCP（模型上下文协议）服务器接口，可与Claude Desktop和Cursor等人工智能开发环境无缝集成。

**：专业、可重复且高效——确保每次模拟都能获得可靠的结果。

---

## Key Features

**：自动检测用户意图，并在蛋白质模拟、蛋白质-配体复合物准备、轨迹分析和MM-PBSA计算等专业技能之间动态切换。
**：只需一次提示，即可完成从输入PDB文件到生成全面分析报告的完整流程。
**：兼容OpenAI、DeepSeek、Gemini以及任何与OpenAI兼容的API端点。
：通过清晰的优先级层次结构管理多个项目中的参数（命令行 > 环境变量 > YAML文件 > 默认值）。
**：工具模式与当前技能自动同步，实现与现代AI编码助手的深度集成。

---

##安装

```bash
# 创建一个隔离的虚拟环境（推荐）
python -m venv AISSM_BH_env
source AISSM_BH_env/bin/activate

# 通过pip安装
pip install git+https://github.com/lsnfa/AISSM_BH.git


# 可选：用于蛋白质-配体复合物模拟
conda install -c conda-forge acpype

# 可选：用于MM-PBSA/GBSA结合自由能计算
conda install -c conda-forge gmx_mmpbsa
```

---

##快速入门

###1. 准备工作区和输入结构

```bash
mkdir md_workspace && cd md_workspace
wget https://files.rcsb.org/download/1PGA.pdb
grep -v HOH 1PGA.pdb > 1pga_protein.pdb
cd ..
```

### 2. Run with DeepSeek (Recommended)

```bash
aissm_bh --workspace md_workspace/ \
  --prompt "setup simulation system for 1pga_protein.pdb in the workspace" \
  --api-key $DEEPSEEK_API_KEY \
  --model deepseek-chat \
  --url https://api.deepseek.com/chat/completions
```

### 3. Run with OpenAI

```bash
aissm_bh --workspace md_workspace/ \
  --prompt "setup simulation system for 1pga_protein.pdb in the workspace" \
  --api-key $OPENAI_API_KEY \
  --model gpt-4o \
  --url https://api.openai.com/v1/chat/completions
```

### 4. Run with Gemini

```bash
aissm_bh --workspace md_workspace/ \
  --prompt "setup simulation system for 1pga_protein.pdb in the workspace" \
  --api-key $GEMINI_API_KEY \
  --model gemini-2.0-flash \
  --url https://generativelanguage.googleapis.com/v1beta/chat/completions
```

### 5. Agent Mode (Fully Autonomous Execution)

```bash
aissm_bh --workspace md_workspace/ \
  --prompt "run 1 ns production md for 1pga_protein.pdb and analyze rmsd, rmsf, gyration" \
  --mode agent
```

### 6. Using YAML Configuration (Recommended for Reproducibility)

Create `my_config.yaml`:

```yaml
workspace: ./md_workspace
model: deepseek-chat
mode: agent
log_level: INFO
api_key: sk-your-key-here
```

Execute:

```bash
aissm_bh --config my_config.yaml --prompt "run 10 ns production MD and generate analysis report"
```

**Priority Order**: Command-line arguments > Environment variables > YAML configuration > Code defaults

---

## Command-Line Arguments

| Argument       | Type   | Default                                      | Description |
|----------------|--------|----------------------------------------------|-------------|
| `--api-key`    | str    | —                                            | API key (can also use `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` environment variable) |
| `--url`        | str    | `https://api.openai.com/v1/chat/completions` | LLM service endpoint |
| `--model`      | str    | `gpt-4o`                                     | Model name |
| `--workspace`  | str    | `./md_workspace`                             | Working directory |
| `--prompt`     | str    | —                                            | Initial prompt |
| `--mode`       | str    | `copilot`                                    | Operation mode: `copilot` or `agent` |
| `--log-level`  | str    | `INFO`                                       | Logging level |
| `--log-file`   | str    | `md_agent.log`                               | Log file path |
| `--no-color`   | flag   | `False`                                      | Disable colored terminal output |
| `--config`     | str    | —                                            | Path to YAML configuration file |

---

## Supported Skills

| Skill              | Responsibility |
|--------------------|----------------|
| **Protein**        | Standard protein MD workflow: topology generation → solvation → ion addition → energy minimization → NVT/NPT equilibration → production run |
| **Protein-Ligand** | Protein-ligand complex preparation: ligand extraction, parameterization (OpenBabel + ACPYPE), complex merging |
| **Analysis**       | Trajectory processing, RMSD/RMSF/Rg/hydrogen bond/secondary structure/energy analysis, and comprehensive reporting |
| **MM-PBSA**        | MM-PBSA/GBSA binding free energy calculation and result parsing |

**Routing Priority**: MM-PBSA > Protein-Ligand > Analysis > Protein (default fallback)

---

## MCP Service

AISSM_BH provides an MCP (Model Context Protocol) server interface, allowing other AI applications to directly invoke its toolset. After initialization via `init_aissm_bh`, all skill-specific tools are automatically registered. Users can also manually switch skills using `switch_agent_skill`. Tool schemas are dynamically synchronized with each skill’s `get_tool_schema()` method, eliminating manual maintenance.

---

## Contributing

We welcome contributions via Issues and Pull Requests:

1. **Fork** the repository
2. Create a feature branch (`git checkout -b feature/xxx`)
3. Install in development mode (`pip install -e .`)
4. Verify functionality before submission
5. Push your branch and open a Pull Request

---

## License

This project is derived from GROMACS Copilot and is dual-licensed:

- **GPL v3** (Open-source license)
- **Commercial License** (Required for closed-source or commercial applications — please contact BHAI Team for authorization)

For full details, see [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md).

---

## Disclaimer

AISSM_BH is provided "as is" without any express or implied warranties. Users assume full responsibility for any risks associated with its use. The authors disclaim all liability for consequences arising from the use, misuse, or misinterpretation of this software. Simulation results should be independently validated prior to publication or practical application.

This software is intended solely for research and educational purposes. Users are responsible for ensuring compliance with applicable laws, regulations, and ethical standards in their jurisdiction.

---

## Contact

**BHAI Team** | baihongai@163.com

---

*Current Version: V1.0.0*
