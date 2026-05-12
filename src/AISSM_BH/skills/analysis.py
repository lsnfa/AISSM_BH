"""
Analysis skill for GROMACS Copilot
"""

import os
import logging
from typing import Dict, Any, List, Optional

from AISSM_BH.skills.base import BaseSkill
from AISSM_BH.utils.shell import check_command_exists


class AnalysisSkill(BaseSkill):
    """Skill for analysis of MD simulation results"""
    
    def __init__(self, workspace: str = "./md_workspace", has_ligand: bool = False, gmx_bin: str = "gmx"):
        """
        Initialize the analysis protocol.

        Parameters
        ----------
        workspace : str
            Directory to use as the working directory. Default is "./md_workspace".
        has_ligand : bool
            Whether the system includes a ligand. Default is False.
        """
        super().__init__(workspace)
        self.has_ligand = has_ligand
        self.production_file = None
        self.trajectory_file = None
        self.topology_file = None
        self.energy_file = None
        self.analysis_dir = os.path.join(workspace, "analysis")
        self.gmx_bin = gmx_bin
        
        # Create analysis directory if it doesn't exist
        if not os.path.exists(self.analysis_dir):
            os.makedirs(self.analysis_dir)
        
        logging.info(f"Analysis skill initialized with workspace: {self.workspace}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the protocol.

        Returns
        -------
        Dict[str, Any]
            Dictionary with protocol state information.
        """
        try:
            analysis_files = []
            if os.path.exists(self.analysis_dir):
                analysis_files = os.listdir(self.analysis_dir)
            
            return {
                "success": True,
                "workspace_path": self.workspace,
                "analysis_directory": self.analysis_dir,
                "has_ligand": self.has_ligand,
                "production_file": self.production_file,
                "trajectory_file": self.trajectory_file,
                "topology_file": self.topology_file,
                "energy_file": self.energy_file,
                "analysis_files": analysis_files
            }
        except Exception as e:
            logging.error(f"Error getting analysis state: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workspace_path": self.workspace
            }
    
    def check_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for analysis are met.

        Returns
        -------
        Dict[str, Any]
            Dictionary with prerequisite check information.
        """
        # Check GROMACS installation
        gromacs_result = self.run_shell_command(f"{self.gmx_bin} --version", capture_output=True)
        gromacs_installed = gromacs_result["success"]
        
        # Check DSSP installation (optional)
        dssp_installed = check_command_exists("dssp") or check_command_exists("mkdssp")
        
        # Check for required files
        required_files = ["md.xtc", "md.tpr", "md.edr"]
        missing_files = [file for file in required_files if not os.path.exists(os.path.join(self.workspace, file))]
        
        if missing_files:
            return {
                "success": False,
                "installed": {
                    "gromacs": gromacs_installed,
                    "dssp": dssp_installed
                },
                "missing_files": missing_files,
                "error": f"Missing required files: {', '.join(missing_files)}"
            }
        
        # Set file paths if all required files exist
        self.production_file = "md.gro"
        self.trajectory_file = "md.xtc"
        self.topology_file = "topol.top"
        self.energy_file = "md.edr"
        
        return {
            "success": True,
            "installed": {
                "gromacs": gromacs_installed,
                "dssp": dssp_installed
            }
        }
    
    def clean_trajectory(self) -> Dict[str, Any]:
        """
        Clean the trajectory file by removing PBC effects and centering.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        # Create clean trajectory
        cmd = f"echo 'Protein System' | {self.gmx_bin} trjconv -s md.tpr -f md.xtc -o analysis/clean_full.xtc -pbc nojump -ur compact -center"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to clean trajectory: {result['stderr']}"
            }
        
        # Create no-water trajectory
        cmd = f"echo 'Protein non-Water' |{self.gmx_bin} trjconv -s md.tpr -f analysis/clean_full.xtc -o analysis/clean_nowat.xtc -fit rot+trans"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to create no-water trajectory: {result['stderr']}"
            }
        
        # Extract last frame as PDB
        cmd = f"echo 'Protein Protein' |{self.gmx_bin} trjconv -s md.tpr -f analysis/clean_nowat.xtc -o analysis/protein_lastframe.pdb -pbc nojump -ur compact -center -dump 9999999999999999"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to extract last frame: {result['stderr']}"
            }
        
        return {
            "success": True,
            "clean_trajectory": "analysis/clean_full.xtc",
            "nowat_trajectory": "analysis/clean_nowat.xtc",
            "last_frame": "analysis/protein_lastframe.pdb"
        }
    
    def analyze_rmsd(self, selection: str = "Backbone", reference: str = "Backbone") -> Dict[str, Any]:
        """
        Perform RMSD analysis.

        Parameters
        ----------
        selection : str
            Selection to analyze. Default is "Backbone".
        reference : str
            Reference selection for fitting. Default is "Backbone".

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        output_file = f"analysis/rmsd_{selection.lower()}.xvg"
        
        cmd = f"echo '{reference} {selection}' |{self.gmx_bin} rms -s md.tpr -f analysis/clean_nowat.xtc -o {output_file} -tu ns"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"RMSD analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "RMSD",
            "selection": selection,
            "reference": reference
        }
    
    def analyze_rmsf(self, selection: str = "Backbone") -> Dict[str, Any]:
        """
        Perform RMSF analysis.

        Parameters
        ----------
        selection : str
            Selection to analyze. Default is "Backbone".

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        output_file = f"analysis/rmsf_{selection.lower()}.xvg"
        
        cmd = f"echo '{selection}' |{self.gmx_bin} rmsf -s md.tpr -f analysis/clean_nowat.xtc -o {output_file} -res"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"RMSF analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "RMSF",
            "selection": selection
        }
    
    def analyze_gyration(self, selection: str = "Protein") -> Dict[str, Any]:
        """
        Perform radius of gyration analysis.

        Parameters
        ----------
        selection : str
            Selection to analyze. Default is "Protein".

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        output_file = f"analysis/gyrate_{selection.lower()}.xvg"
        
        cmd = f"echo '{selection}' |{self.gmx_bin} gyrate -s md.tpr -f analysis/clean_nowat.xtc -o {output_file}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Radius of gyration analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "Radius of Gyration",
            "selection": selection
        }
    
    def analyze_hydrogen_bonds(self, selection1: str = "Protein", selection2: str = "Protein") -> Dict[str, Any]:
        """
        Perform hydrogen bond analysis.

        Parameters
        ----------
        selection1 : str
            First selection. Default is "Protein".
        selection2 : str
            Second selection. Default is "Protein".

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        output_file = f"analysis/hbnum_{selection1.lower()}_{selection2.lower()}.xvg"
        
        cmd = f"echo -e '{selection1}\\n{selection2}' |{self.gmx_bin} hbond -s md.tpr -f analysis/clean_nowat.xtc -num {output_file}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Hydrogen bond analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "Hydrogen Bonds",
            "selection1": selection1,
            "selection2": selection2
        }
    
    def analyze_secondary_structure(self) -> Dict[str, Any]:
        """
        Perform secondary structure analysis using DSSP.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        # Check if DSSP is installed
        dssp_executable = None
        if check_command_exists("dssp"):
            dssp_executable = "dssp"
        elif check_command_exists("mkdssp"):
            dssp_executable = "mkdssp"
        
        if not dssp_executable:
            return {
                "success": False,
                "error": "DSSP is not installed. Please install DSSP or mkdssp."
            }
        
        # Set environment variable for GROMACS to find DSSP
        os.environ["DSSP"] = dssp_executable
        
        cmd = f"echo 'Protein' |{self.gmx_bin} do_dssp -s md.tpr -f analysis/clean_nowat.xtc -o analysis/ss.xpm -ver 3 -tu ns -dt 0.05"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Secondary structure analysis failed: {result['stderr']}"
            }
        
        # Convert XPM to PS for better visualization
        cmd = f"{self.gmx_bin} xpm2ps -f analysis/ss.xpm -o analysis/ss.ps -by 10 -bx 3"
        ps_result = self.run_shell_command(cmd)
        
        return {
            "success": True,
            "output_file": "analysis/ss.xpm",
            "ps_file": "analysis/ss.ps" if ps_result["success"] else None,
            "analysis_type": "Secondary Structure"
        }
    
    def analyze_energy(self, terms: List[str] = ["Potential", "Temperature", "Pressure"]) -> Dict[str, Any]:
        """
        Perform energy analysis.

        Parameters
        ----------
        terms : List[str]
            Energy terms to analyze. Default is ["Potential", "Temperature", "Pressure"].

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        results = {}
        
        for term in terms:
            # Map energy term to its typical number in GROMACS
            term_map = {
                "Potential": "10",
                "Kinetic": "11",
                "Total": "12",
                "Temperature": "16",
                "Pressure": "17",
                "Volume": "22"
            }
            
            if term not in term_map:
                results[term] = {
                    "success": False,
                    "error": f"Unknown energy term: {term}"
                }
                continue
            
            output_file = f"analysis/energy_{term.lower()}.xvg"
            
            cmd = f"echo '{term_map[term]} 0' |{self.gmx_bin} energy -f md.edr -o {output_file}"
            result = self.run_shell_command(cmd)
            
            if not result["success"]:
                results[term] = {
                    "success": False,
                    "error": f"Energy analysis for {term} failed: {result['stderr']}"
                }
            else:
                results[term] = {
                    "success": True,
                    "output_file": output_file,
                    "analysis_type": "Energy",
                    "term": term
                }
        
        return {
            "success": all(results[term]["success"] for term in terms),
            "results": results
        }
    
    def analyze_ligand_rmsd(self) -> Dict[str, Any]:
        """
        Perform RMSD analysis focused on the ligand.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.has_ligand:
            return {
                "success": False,
                "error": "No ligand in the system"
            }
        
        output_file = "analysis/ligand_rmsd.xvg"
        
        cmd = f"echo 'LIG LIG' |{self.gmx_bin} rms -s md.tpr -f analysis/clean_nowat.xtc -o analysis/ligand_rmsd.xvg -tu ns"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Ligand RMSD analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "Ligand RMSD"
        }
    
    def analyze_protein_ligand_contacts(self) -> Dict[str, Any]:
        """
        Analyze contacts between protein and ligand.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.has_ligand:
            return {
                "success": False,
                "error": "No ligand in the system"
            }
        
        output_file = "analysis/protein_ligand_mindist.xvg"
        
        cmd = f"echo -e 'Protein\\nLIG' |{self.gmx_bin} mindist -s md.tpr -f analysis/clean_nowat.xtc -od analysis/protein_ligand_mindist.xvg -tu ns"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Protein-ligand contacts analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": output_file,
            "analysis_type": "Protein-Ligand Minimum Distance"
        }
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        # Create analysis directory if it doesn't exist
        if not os.path.exists(self.analysis_dir):
            os.makedirs(self.analysis_dir)
        
        # Clean trajectories
        clean_result = self.clean_trajectory()
        if not clean_result["success"]:
            return clean_result
        
        # Perform various analyses
        analyses = [
            self.analyze_rmsd(selection="Backbone", reference="Backbone"),
            self.analyze_rmsd(selection="Protein", reference="Backbone"),
            self.analyze_rmsf(selection="C-alpha"),
            self.analyze_gyration(selection="Protein"),
            self.analyze_energy(terms=["Potential", "Temperature", "Pressure"]),
            self.analyze_hydrogen_bonds(selection1="Protein", selection2="Protein")
        ]
        
        # Add ligand-specific analyses if applicable
        if self.has_ligand:
            analyses.extend([
                self.analyze_ligand_rmsd(),
                self.analyze_protein_ligand_contacts()
            ])
        
        # Try to do secondary structure analysis if DSSP is available
        if check_command_exists("dssp") or check_command_exists("mkdssp"):
            analyses.append(self.analyze_secondary_structure())
        
        # Count successful analyses
        successful_analyses = sum(1 for analysis in analyses if analysis["success"])
        
        return {
            "success": successful_analyses > 0,
            "total_analyses": len(analyses),
            "successful_analyses": successful_analyses,
            "analyses": analyses,
            "report_directory": self.analysis_dir
        }

    def is_applicable(self, user_input: str, context: Dict[str, Any]) -> bool:
        """
        Check if this skill is applicable to the user input.

        Parameters
        ----------
        user_input : str
            The user input to check.
        context : Dict[str, Any]
            The context dictionary.

        Returns
        -------
        bool
            True if the skill is applicable, False otherwise.
        """
        keywords = ["analyze", "analysis", "rmsd", "rmsf", "gyration", "hbond", "report"]
        if any(kw in user_input.lower() for kw in keywords):
            return True
        if context.get("phase") in ["PRODUCTION", "COMPLETED"]:
            return True
        return False

    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get the tool schema for this skill.

        Returns
        -------
        List[Dict[str, Any]]
            The tool schema list.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "clean_trajectory",
                    "description": "Clean the trajectory file by removing PBC effects and centering",
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
                    "name": "analyze_rmsd",
                    "description": "Perform RMSD analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "Selection to analyze"
                            },
                            "reference": {
                                "type": "string",
                                "description": "Reference selection for fitting"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_rmsf",
                    "description": "Perform RMSF analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "Selection to analyze"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_gyration",
                    "description": "Perform radius of gyration analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "Selection to analyze"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_hydrogen_bonds",
                    "description": "Perform hydrogen bond analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selection1": {
                                "type": "string",
                                "description": "First selection"
                            },
                            "selection2": {
                                "type": "string",
                                "description": "Second selection"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_secondary_structure",
                    "description": "Perform secondary structure analysis using DSSP",
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
                    "name": "analyze_energy",
                    "description": "Perform energy analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "terms": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Energy terms to analyze"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_analysis_report",
                    "description": "Generate a comprehensive analysis report",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]