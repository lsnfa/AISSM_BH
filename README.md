# AISSM_BH
**AI-Powered Molecular Dynamics Simulation Assistant**

**AISSM_BH** — Elevating GROMACS simulations from manual workflows to intelligent automation.

Bid farewell to repetitive command-line operations and prolonged error debugging.  
The AI-driven molecular dynamics assistant developed by BHAI Team (Baihong Group) now delivers professional, stable, and fully automated simulation experiences. 🧬🤖

---

## Project Introduction

**AISSM_BH** is an AI-powered molecular dynamics simulation assistant developed by BHAI Team (Baihong Group). Built upon the GROMACS engine, it enables users to complete the entire simulation workflow for proteins and protein-ligand complexes through natural language instructions. The workflow includes topology generation, solvation, energy minimization, NVT/NPT equilibration, production molecular dynamics runs, trajectory analysis (RMSD, RMSF, radius of gyration, hydrogen bonding, secondary structure), and MM-PBSA/GBSA binding free energy calculations.

The tool supports two operational modes: **Copilot (advisory mode)** and **Agent (autonomous mode)**. It is compatible with major large language models including OpenAI, DeepSeek, and Gemini, and provides an MCP (Model Context Protocol) server interface for seamless integration with AI development environments such as Claude Desktop and Cursor.

**Core Strengths**: Professional, reproducible, and efficient — ensuring reliable results for every simulation.

---

## Key Features

- **Intelligent Skill Routing**: Automatically detects user intent and dynamically switches between specialized skills for protein simulation, protein-ligand complex preparation, trajectory analysis, and MM-PBSA calculations.
- **End-to-End Automation**: Completes the full pipeline from input PDB file to comprehensive analysis report with a single prompt.
- **Multi-Model Support**: Compatible with OpenAI, DeepSeek, Gemini, and any OpenAI-compatible API endpoints.
- **YAML Configuration**: Manage parameters across multiple projects with clear priority hierarchy (command-line > environment variables > YAML file > defaults).
- **Dynamic MCP Tool Registration**: Tool schemas automatically synchronize with the active skill, enabling deep integration with modern AI coding assistants.

---

## Installation

```bash
# Create an isolated virtual environment (recommended)
python -m venv AISSM_BH_env
source AISSM_BH_env/bin/activate

# Install via pip
pip install git+https://github.com/lsnfa/AISSM_BH.git

# Development installation (editable mode)
git clone https://github.com/lsnfa/AISSM_BH.git
cd AISSM_BH
pip install -e .

# Optional: For protein-ligand complex simulations
conda install -c conda-forge acpype

# Optional: For MM-PBSA/GBSA binding free energy calculations
conda install -c conda-forge gmx_mmpbsa
```

---

## Quick Start

### 1. Prepare Workspace and Input Structure

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