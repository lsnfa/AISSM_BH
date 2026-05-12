"""
MCP (Model Context Protocol) server for AISSM_BH.

Dynamically exposes tools based on the current skill's schema, eliminating
duplicated manual wrappers.
"""

from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional

from AISSM_BH.core.baihong_mdagent import BHMDAgent

mcp = FastMCP("aissm-bh")
agent = None

# ---------------------------------------------------------------------------
# Manual tools that cannot be auto-registered
# ---------------------------------------------------------------------------

@mcp.tool()
async def init_aissm_bh(workspace: str, gmx_bin: str = "gmx") -> Dict[str, Any]:
    """
    Initialize the AISSM_BH MCP server.

    Parameters
    ----------
    workspace : str
        Path to the simulation workspace directory.
    gmx_bin : str, optional
        GROMACS binary name or path. Default is "gmx".

    Returns
    -------
    dict
        Status message.
    """
    global agent
    agent = BHMDAgent(workspace=workspace, api_key="dummy", gmx_bin=gmx_bin)
    _register_skill_tools()
    return {"success": True, "message": f"Initialized with workspace: {workspace}"}


@mcp.tool()
async def switch_agent_skill(skill: str) -> Dict[str, Any]:
    """
    Switch to another skill.

    Parameters
    ----------
    skill : str
        Skill identifier: "ligand", "mmpbsa", or "analysis".

    Returns
    -------
    dict
        Result of the switch operation.
    """
    global agent
    if agent is None:
        return {"success": False, "error": "agent not initialized"}

    if skill not in ("ligand", "mmpbsa", "analysis"):
        return {"success": False, "error": "skill not supported"}

    if skill == "mmpbsa":
        agent.switch_to_mmpbsa_skill()
    elif skill == "ligand":
        agent.switch_to_protein_ligand_skill()
    elif skill == "analysis":
        agent.switch_to_analysis_skill()

    _register_skill_tools()
    return {"success": True, "message": f"switched to {skill} skill"}


# ---------------------------------------------------------------------------
# Dynamic tool registration
# ---------------------------------------------------------------------------

_METHOD_ALIASES = {
    "get_workspace_info": "get_state",
}


def _register_skill_tools() -> None:
    """Register all tools declared in the current skill's schema."""
    if agent is None:
        return

    for tool_def in agent.current_skill.get_tool_schema():
        name = tool_def["function"]["name"]
        desc = tool_def["function"].get("description", "")
        method_name = _METHOD_ALIASES.get(name, name)

        captured_name = name
        captured_method = method_name

        async def tool_func(**kwargs) -> Dict[str, Any]:
            """Auto-generated tool wrapper."""
            nonlocal captured_name, captured_method
            if agent is None:
                return {"success": False, "error": "agent not initialized"}

            func = getattr(agent.current_skill, captured_method, None)
            if func is None:
                return {"success": False, "error": f"Unknown function: {captured_name}"}

            return func(**kwargs)

        tool_func.__name__ = name
        tool_func.__doc__ = desc
        mcp.tool()(tool_func)