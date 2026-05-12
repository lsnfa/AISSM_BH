"""
MM-PBSA/GBSA binding free energy calculation skill for GROMACS Copilot
"""

import os
import logging
from typing import Dict, Any, Optional, List

from AISSM_BH.skills.base import BaseSkill
from AISSM_BH.utils.shell import check_command_exists, run_shell_command


class MMPBSASkill(BaseSkill):
    """Skill for MM-PBSA/GBSA binding free energy calculations"""
    
    def __init__(self, workspace: str = "./md_workspace", gmx_bin: str = "gmx"):
        """
        Initialize the MM-PBSA protocol.

        Parameters
        ----------
        workspace : str
            Directory to use as the working directory. Default is ./md_workspace.
        gmx_bin : str
            Path to GROMACS binary. Default is gmx.
        """
        super().__init__(workspace)
        
        # Initialize MM-PBSA specific attributes
        self.trajectory_file = None
        self.topology_file = None
        self.index_file = None
        self.protein_group = None
        self.ligand_group = None
        self.complex_group = None
        self.mmpbsa_dir = os.path.join(workspace, "mmpbsa")
        self.gmx_bin = gmx_bin
        
        # Create MM-PBSA directory if it doesn't exist
        if not os.path.exists(self.mmpbsa_dir):
            os.makedirs(self.mmpbsa_dir)
        
        logging.info(f"MM-PBSA skill initialized with workspace: {self.workspace}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the protocol.

        Returns
        -------
        dict
            Dictionary with protocol state information.
        """
        try:
            mmpbsa_files = []
            if os.path.exists(self.mmpbsa_dir):
                mmpbsa_files = os.listdir(self.mmpbsa_dir)
            
            return {
                "success": True,
                "workspace_path": self.workspace,
                "mmpbsa_directory": self.mmpbsa_dir,
                "trajectory_file": self.trajectory_file,
                "topology_file": self.topology_file,
                "index_file": self.index_file,
                "protein_group": self.protein_group,
                "ligand_group": self.ligand_group,
                "complex_group": self.complex_group,
                "mmpbsa_files": mmpbsa_files
            }
        except Exception as e:
            logging.error(f"Error getting MM-PBSA state: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workspace_path": self.workspace
            }
    
    def check_mmpbsa_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for MM-PBSA analysis are met.

        Returns
        -------
        dict
            Dictionary with prerequisite check information.
        """
        # Check GROMACS installation
        gromacs_result = run_shell_command(f"{self.gmx_bin} --version", capture_output=True)
        gromacs_installed = gromacs_result["success"]
        
        # Check gmx_MMPBSA installation
        gmx_mmpbsa_installed = check_command_exists("gmx_MMPBSA")
        
        # Check for required files
        required_files = ["md.tpr", "md.xtc"]
        missing_files = [file for file in required_files if not os.path.exists(os.path.join(self.workspace, file))]
        
        if missing_files:
            return {
                "success": False,
                "installed": {
                    "gromacs": gromacs_installed,
                    "gmx_mmpbsa": gmx_mmpbsa_installed
                },
                "missing_files": missing_files,
                "error": f"Missing required files: {', '.join(missing_files)}"
            }
        
        # Set file paths if all required files exist
        self.trajectory_file = "md.xtc"
        self.topology_file = "md.tpr"
        
        return {
            "success": True,
            "installed": {
                "gromacs": gromacs_installed,
                "gmx_mmpbsa": gmx_mmpbsa_installed
            }
        }
    
    def create_mmpbsa_index_file(self, protein_selection: str = "Protein",
                         ligand_selection: str = "LIG") -> Dict[str, Any]:
        """
        Create index file for MM-PBSA analysis.

        Parameters
        ----------
        protein_selection : str
            Selection for protein group. Default is Protein.
        ligand_selection : str
            Selection for ligand group. Default is LIG.

        Returns
        -------
        dict
            Dictionary with result information.
        """
        if not os.path.exists(os.path.join(self.workspace, "md.tpr")):
            return {
                "success": False,
                "error": "Topology file not found"
            }
        
        # Create index file with protein and ligand groups
        cmd = f"""echo -e "name {protein_selection}\\nname {ligand_selection}\\n\\nq" | gmx make_ndx -f md.tpr -o mmpbsa/mmpbsa.ndx"""
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to create index file: {result['stderr']}"
            }
        
        # Get group numbers from the index file
        groups_cmd = "grep '\\[' mmpbsa/mmpbsa.ndx | grep -n '\\[' | awk '{print $1, $2, $3}'"
        groups_result = self.run_shell_command(groups_cmd)
        
        if not groups_result["success"]:
            return {
                "success": False,
                "error": f"Failed to extract group numbers: {groups_result['stderr']}"
            }
        
        # Parse the group numbers from output
        try:
            lines = groups_result["stdout"].strip().split('\n')
            group_dict = {}
            
            for line in lines:
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        group_num = int(parts[0]) - 1  # Adjust for 0-based indexing
                        group_name = parts[1].strip()
                        group_dict[group_name] = group_num
            
            # Find protein and ligand groups
            # protein_group = None
            # ligand_group = None
            # complex_group = None
            
            # for group_name, group_num in group_dict.items():
            #     if protein_selection in group_name:
            #         protein_group = group_num
            #     if ligand_selection in group_name:
            #         ligand_group = group_num
            #     if f"{protein_selection} | {ligand_selection}" in group_name:
            #         complex_group = group_num
            
            # if protein_group is None or ligand_group is None or complex_group is None:
            #     return {
            #         "success": False,
            #         "error": f"Could not identify protein, ligand, or complex groups in index file"
            #     }
            
            # self.index_file = "mmpbsa/mmpbsa.ndx"
            # self.protein_group = protein_group
            # self.ligand_group = ligand_group
            # self.complex_group = complex_group
            group_dict["success"] = True
            return group_dict
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing group numbers: {str(e)}"
            }
    
    def create_mmpbsa_input(self, method: str = "pb",
                           startframe: int = 1,
                           endframe: int = 1000,
                           interval: int = 10,
                           ionic_strength: float = 0.15,
                           with_entropy: bool = False) -> Dict[str, Any]:
        """
        Create input file for MM-PBSA/GBSA calculation.

        Parameters
        ----------
        method : str
            Method to use (pb or gb). Default is pb.
        startframe : int
            First frame to analyze. Default is 1.
        endframe : int
            Last frame to analyze. Default is 1000.
        interval : int
            Interval between frames. Default is 10.
        ionic_strength : float
            Ionic strength for PB calculation. Default is 0.15.
        with_entropy : bool
            Whether to include entropy calculation. Default is False.

        Returns
        -------
        dict
            Dictionary with result information.
        """
        try:
            mmpbsa_input = "&general\n"
            mmpbsa_input += f"  sys_name = Protein_Ligand\n"
            mmpbsa_input += f"  startframe = {startframe}\n"
            mmpbsa_input += f"  endframe = {endframe}\n"
            mmpbsa_input += f"  interval = {interval}\n"
            
            if with_entropy:
                mmpbsa_input += "  entropy = 1\n"
                mmpbsa_input += "  entropy_seg = 25\n"  # Number of frames for entropy calculation
            
            mmpbsa_input += "/\n\n"
            
            if method.lower() == "pb":
                mmpbsa_input += "&pb\n"
                mmpbsa_input += f"  istrng = {ionic_strength}\n"
                mmpbsa_input += "  fillratio = 4.0\n"
                mmpbsa_input += "  inp = 2\n"
                mmpbsa_input += "  radiopt = 0\n"
                mmpbsa_input += "/\n"
            elif method.lower() == "gb":
                mmpbsa_input += "&gb\n"
                mmpbsa_input += f"  saltcon = {ionic_strength}\n"
                mmpbsa_input += "  igb = 5\n"  # GB model (5 = OBC2)
                mmpbsa_input += "/\n"
            
            input_file_path = os.path.join(self.mmpbsa_dir, "mmpbsa.in")
            with open(input_file_path, "w") as f:
                f.write(mmpbsa_input)
            
            return {
                "success": True,
                "input_file": input_file_path,
                "method": method,
                "startframe": startframe,
                "endframe": endframe,
                "interval": interval,
                "with_entropy": with_entropy
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating MM-PBSA input file: {str(e)}"
            }
    
    def run_mmpbsa_calculation(self,
                               ligand_mol_file: str,
                               index_file: str,
                               topology_file: str,
                               protein_group: str,
                               ligand_group: str,
                               trajectory_file: str,
                               overwrite: bool = True,
                               verbose: bool = True) -> Dict[str, Any]:
        """
        Run MM-PBSA/GBSA calculation.

        Parameters
        ----------
        ligand_mol_file : str
            The Antechamber output mol2 file of ligand parametrization.
        index_file : str
            GROMACS index file containing protein and ligand groups.
        topology_file : str
            GROMACS topology file (tpr) for the system.
        protein_group : str
            Name or index of the protein group in the index file.
        ligand_group : str
            Name or index of the ligand group in the index file.
        trajectory_file : str
            GROMACS trajectory file (xtc) for analysis.
        overwrite : bool, optional
            Whether to overwrite existing output files. Default is True.
        verbose : bool, optional
            Whether to print verbose output. Default is True.

        Returns
        -------
        dict
            Dictionary with result information.
        """
        if not index_file or not os.path.exists(os.path.join(self.workspace, index_file)):
            return {
                "success": False,
                "error": "Index file not found"
            }
        
        input_file = os.path.join(self.mmpbsa_dir, "mmpbsa.in")
        if not os.path.exists(input_file):
            return {
                "success": False,
                "error": "MM-PBSA input file not found. Run create_mmpbsa_input() first."
            }
        
        # Run gmx_MMPBSA
        overwrite_flag = "-O" if overwrite else ""
        # verbose_flag = "--verbose" if verbose else ""
        
        cmd = f"cd {self.workspace} && gmx_MMPBSA {overwrite_flag} -i {input_file} -cs {topology_file} -ci {index_file} -cg {protein_group} {ligand_group} -ct {trajectory_file} -lm {ligand_mol_file} -o {self.mmpbsa_dir}/FINAL_RESULTS_MMPBSA.dat -nogui"
        
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"MM-PBSA calculation failed: {result['stderr']}"
            }
        
        # Check if output file exists
        final_results = os.path.join(self.mmpbsa_dir, "FINAL_RESULTS_MMPBSA.dat")
        if not os.path.exists(final_results):
            return {
                "success": False,
                "error": "MM-PBSA calculation did not produce expected output file"
            }
        
        return {
            "success": True,
            "results_file": final_results,
            "output_dir": self.mmpbsa_dir
        }
    
    def check_prerequisites(self):
        pass
    
    def parse_mmpbsa_results(self) -> Dict[str, Any]:
        """
        Parse MM-PBSA/GBSA results.

        Returns
        -------
        dict
            Dictionary with parsed results.
        """
        final_results = os.path.join(self.mmpbsa_dir, "results_FINAL_RESULTS_MMPBSA.dat")
        if not os.path.exists(final_results):
            return {
                "success": False,
                "error": "MM-PBSA results file not found"
            }
        
        try:
            # Read results file
            with open(final_results, "r") as f:
                lines = f.readlines()
            
            # Parse results
            results = {}
            data_block = False
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or line.startswith("***") or line.startswith("==="):
                    continue
                
                # Start data block
                if line.startswith("DELTA TOTAL"):
                    data_block = True
                    continue
                
                if data_block and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value_parts = parts[1].strip().split()
                        
                        if len(value_parts) >= 3:
                            mean = float(value_parts[0])
                            std = float(value_parts[1])
                            std_err = float(value_parts[2])
                            
                            results[key] = {
                                "mean": mean,
                                "std": std,
                                "std_err": std_err
                            }
            
            # Extract binding energy components
            binding_energy = results.get("DELTA TOTAL", {}).get("mean", 0)
            van_der_waals = results.get("VDWAALS", {}).get("mean", 0)
            electrostatic = results.get("EEL", {}).get("mean", 0)
            polar_solvation = results.get("EGB/EPB", {}).get("mean", 0)
            non_polar_solvation = results.get("ESURF", {}).get("mean", 0)
            
            return {
                "success": True,
                "binding_energy": binding_energy,
                "components": {
                    "van_der_waals": van_der_waals,
                    "electrostatic": electrostatic,
                    "polar_solvation": polar_solvation,
                    "non_polar_solvation": non_polar_solvation
                },
                "detailed_results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing MM-PBSA results: {str(e)}"
            }

    def is_applicable(self, user_input: str, context: Dict[str, Any]) -> bool:
        """
        Check if this skill is applicable for the given input.

        Parameters
        ----------
        user_input : str
            User input string to check.
        context : dict
            Context dictionary with additional information.

        Returns
        -------
        bool
            True if this skill is applicable, False otherwise.
        """
        keywords = ["mmpbsa", "mmgbsa", "binding free energy", "binding affinity", "delta g"]
        if any(kw in user_input.lower() for kw in keywords):
            return True
        if context.get("phase") == "COMPLETED" and context.get("has_ligand"):
            return True
        return False

    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get the tool schema for this skill.

        Returns
        -------
        list
            List of tool definitions for this skill.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_mmpbsa_prerequisites",
                    "description": "Check if prerequisites for MM-PBSA analysis are met",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_mmpbsa_index_file",
                    "description": "Create index file for MM-PBSA analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "protein_selection": {
                                "type": "string",
                                "description": "Selection for protein group"
                            },
                            "ligand_selection": {
                                "type": "string",
                                "description": "Selection for ligand group"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_mmpbsa_input",
                    "description": "Create input file for MM-PBSA/GBSA calculation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "description": "Method to use (pb or gb)",
                                "enum": ["pb", "gb"]
                            },
                            "startframe": {
                                "type": "integer",
                                "description": "First frame to analyze"
                            },
                            "endframe": {
                                "type": "integer",
                                "description": "Last frame to analyze"
                            },
                            "interval": {
                                "type": "integer",
                                "description": "Interval between frames"
                            },
                            "ionic_strength": {
                                "type": "number",
                                "description": "Ionic strength for calculation"
                            },
                            "with_entropy": {
                                "type": "boolean",
                                "description": "Whether to include entropy calculation"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_mmpbsa_calculation",
                    "description": "Run MM-PBSA/GBSA calculation for protein-ligand binding free energy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ligand_mol_file": {
                                "type": "string",
                                "description": "The Antechamber output mol2 file of ligand parametrization"
                            },
                            "index_file": {
                                "type": "string",
                                "description": "GROMACS index file containing protein and ligand groups"
                            },
                            "topology_file": {
                                "type": "string",
                                "description": "GROMACS topology file (tpr) for the system"
                            },
                            "protein_group": {
                                "type": "string",
                                "description": "Name or index of the protein group in the index file"
                            },
                            "ligand_group": {
                                "type": "string", 
                                "description": "Name or index of the ligand group in the index file"
                            },
                            "trajectory_file": {
                                "type": "string",
                                "description": "GROMACS trajectory file (xtc) for analysis"
                            },
                            "overwrite": {
                                "type": "boolean",
                                "description": "Whether to overwrite existing output files",
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Whether to print verbose output",
                            }
                        },
                        "required": ["ligand_mol_file", "index_file", "topology_file", "protein_group", "ligand_group", "trajectory_file"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "parse_mmpbsa_results",
                    "description": "Parse MM-PBSA/GBSA results",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    