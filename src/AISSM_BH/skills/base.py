"""
Base skill class for AISSM_BH
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from AISSM_BH.utils.shell import run_shell_command


class BaseSkill(ABC):
    """Base class for simulation skills"""
    
    def __init__(self, workspace: str = "./md_workspace", gmx_bin: str = "gmx"):
        """
        Initialize the base skill.

        Parameters
        ----------
        workspace : str, optional
            Workspace directory. Default is "./md_workspace".
        gmx_bin : str, optional
            GROMACS binary. Default is "gmx".
        """
        from AISSM_BH.core.enums import SimulationPhase
        
        self.workspace = os.path.abspath(workspace)
        self.stage = SimulationPhase.SETUP
        
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        
        os.chdir(self.workspace)
        self.gmx_bin = gmx_bin
        
        logging.info(f"Skill initialized with workspace: {self.workspace}")

    
    def check_gromacs_installation(self) -> Dict[str, Any]:
        """
        Check if GROMACS is installed and available.

        Returns
        -------
        dict
            Result with keys: ``success``, ``installed``, ``version`` or ``error``.
        """
        result = self.run_shell_command(f"{self.gmx_bin} --version", capture_output=True)
        
        if result["success"]:
            version_info = result["stdout"].strip()
            return {
                "success": True,
                "installed": True,
                "version": version_info
            }
        else:
            return {
                "success": False,
                "installed": False,
                "error": "GROMACS is not installed or not in PATH"
            }
    
    def run_shell_command(self, command: str, capture_output: bool = True,
                         suppress_output: bool = False) -> Dict[str, Any]:
        """
        Run a shell command.

        Parameters
        ----------
        command : str
            Shell command to run.
        capture_output : bool, optional
            Whether to capture stdout/stderr. Default is True.
        suppress_output : bool, optional
            Whether to suppress terminal output. Default is False.

        Returns
        -------
        dict
            Result with keys: ``success``, ``return_code``, ``stdout``, ``stderr``.
        """
        return run_shell_command(command, capture_output, suppress_output)
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the protocol.

        Returns
        -------
        dict
            State with keys: ``success``, ``workspace_path``, ``current_stage``.
        """
        pass
    
    @abstractmethod
    def check_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for the protocol are met.

        Returns
        -------
        dict
            Result with keys: ``success``, ``installed``, ``version`` or ``error``.
        """
        pass
    
    def create_mdp_file(self, mdp_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an MDP parameter file for GROMACS.

        This method delegates to the centralized factory function in
        ``AISSM_BH.config.mdp_templates``.

        Parameters
        ----------
        mdp_type : str
            Type of MDP file.
        params : dict, optional
            Override parameters.

        Returns
        -------
        dict
            Result dictionary.
        """
        from AISSM_BH.config.mdp_templates import create_mdp_file as _create_mdp
        return _create_mdp(mdp_type, params)
    
    def set_simulation_stage(self, stage: str) -> Dict[str, Any]:
        """
        Set the current simulation stage.

        Parameters
        ----------
        stage : str
            Name of the stage to set.

        Returns
        -------
        dict
            Result with keys: ``success``, ``stage``, ``previous_stage`` or ``error``.
        """
        from AISSM_BH.core.enums import SimulationPhase
        
        try:
            self.stage = SimulationPhase[stage]
            return {
                "success": True,
                "stage": self.stage.name,
                "previous_stage": self.stage.name
            }
        except KeyError:
            return {
                "success": False,
                "error": f"Unknown stage: {stage}. Available stages: {[s.name for s in SimulationPhase]}"
            }

    @abstractmethod
    def is_applicable(self, user_input: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this skill applies to the user input and context.

        Parameters
        ----------
        user_input : str
            The user's input text.
        context : dict
            Context with phase, has_ligand, workspace.

        Returns
        -------
        bool
            True if this skill applies, False otherwise.
        """
        pass

    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Return the list of tool schemas provided by this skill.

        Returns
        -------
        list of dict
            Tool definitions. Subclasses must override.
        """
        return []