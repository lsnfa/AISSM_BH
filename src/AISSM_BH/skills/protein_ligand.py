"""
Protein-ligand simulation skill for GROMACS Copilot
"""

import os
import logging
from typing import Dict, Any, Optional, List

from AISSM_BH.skills.protein import ProteinSkill
from AISSM_BH.config import FORCE_FIELDS, STANDARD_RESIDUES
from AISSM_BH.utils.shell import check_command_exists


class ProteinLigandSkill(ProteinSkill):
    """Skill for protein-ligand simulations"""

    def __init__(self, workspace: str = "./md_workspace", gmx_bin: str = "gmx"):
        """
        Initialize the protein-ligand simulation protocol.

        Parameters
        ----------
        workspace : str, optional
            Directory to use as the working directory.
        """
        super().__init__(workspace)

        self.ligand_file = None
        self.ligand_name = None
        self.complex_file = None
        self.has_ligand = False
        self.index_file = None
        self.gmx_bin = gmx_bin

        logging.info(f"Protein-ligand skill initialized with workspace: {self.workspace}")

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the protocol.

        Returns
        -------
        Dict[str, Any]
            Dictionary with protocol state information.
        """
        state = super().get_state()

        if state["success"]:
            state.update({
                "ligand_file": self.ligand_file,
                "ligand_name": self.ligand_name,
                "complex_file": self.complex_file,
                "has_ligand": self.has_ligand,
                "index_file": self.index_file
            })

        return state

    def check_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for protein-ligand simulation are met.

        Returns
        -------
        Dict[str, Any]
            Dictionary with prerequisite check information.
        """
        gromacs_check = super().check_prerequisites()
        if not gromacs_check["success"]:
            return gromacs_check

        openbabel_installed = check_command_exists("obabel")
        acpype_installed = check_command_exists("acpype")

        return {
            "success": gromacs_check["success"],
            "gromacs": gromacs_check,
            "openbabel": {
                "installed": openbabel_installed,
                "required": True
            },
            "acpype": {
                "installed": acpype_installed,
                "required": True
            }
        }

    def check_for_ligands(self, pdb_file: str) -> Dict[str, Any]:
        """
        Check for potential ligands in the PDB file.

        Parameters
        ----------
        pdb_file : str
            Path to the PDB file.

        Returns
        -------
        Dict[str, Any]
            Dictionary with ligand information.
        """
        try:
            cmd = f"grep '^ATOM\\|^HETATM' {pdb_file} | awk '{{print $4}}' | sort | uniq"
            result = self.run_shell_command(cmd)

            if not result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to analyze PDB file: {result['stderr']}"
                }

            residues = result["stdout"].strip().split()
            potential_ligands = [res for res in residues if res not in STANDARD_RESIDUES]

            return {
                "success": True,
                "ligands": potential_ligands
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error checking for ligands: {str(e)}"
            }

    def set_ligand(self, ligand_name: str) -> Dict[str, Any]:
        """
        Set the ligand for simulation.

        Parameters
        ----------
        ligand_name : str
            Residue name of the ligand in the PDB file.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.protein_file:
            return {
                "success": False,
                "error": "No protein file has been set"
            }

        self.ligand_name = ligand_name

        mkdir_cmd = "mkdir -p param/receptor param/ligand"
        mkdir_result = self.run_shell_command(mkdir_cmd)
        if not mkdir_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create directories: {mkdir_result['stderr']}"
            }

        extract_protein_cmd = f"grep '^ATOM' {self.protein_file} > param/receptor/receptor.pdb"
        protein_result = self.run_shell_command(extract_protein_cmd)
        if not protein_result["success"]:
            return {
                "success": False,
                "error": f"Failed to extract protein atoms: {protein_result['stderr']}"
            }

        extract_result = self.extract_ligand(os.path.join(self.workspace, self.protein_file), ligand_name)
        if not extract_result["success"]:
            return extract_result

        self.ligand_file = "param/ligand/ligand.pdb"
        self.has_ligand = True

        return {
            "success": True,
            "ligand_name": ligand_name,
            "ligand_file": self.ligand_file,
            "receptor_file": "param/receptor/receptor.pdb"
        }

    def extract_ligand(self, pdb_file: str, ligand_name: str) -> Dict[str, Any]:
        """
        Extract ligand from PDB file and rename it to LIG.

        Parameters
        ----------
        pdb_file : str
            Path to the PDB file.
        ligand_name : str
            Residue name of the ligand.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        try:
            script_content = f"""
ligand_atom = []
keepLine = []
with open("{pdb_file}","r") as file:
    lines = file.readlines()
    for line in lines:
        if '{ligand_name}' in line[17:20]:
            line = line[:17]+"LIG"+line[20:]
            keepLine.append(line)
            ligand_atom.append(int(line[6:11]))
        elif "CONECT" in line[0:6]:
            idx = [int(x) for x in line.split()[1:]]
            if any(id in idx for id in ligand_atom):
                keepLine.append(line)
with open("param/ligand/ligand.pdb","w") as file:
    for line in keepLine:
        file.write(line)
"""
            with open("extract_ligand.py", "w") as f:
                f.write(script_content)

            result = self.run_shell_command("python extract_ligand.py")
            if not result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to extract ligand: {result['stderr']}"
                }

            os.remove("extract_ligand.py")

            return {
                "success": True,
                "ligand_file": "param/ligand/ligand.pdb"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error extracting ligand: {str(e)}"
            }

    def prepare_ligand_topology(self) -> Dict[str, Any]:
        """
        Prepare ligand topology using OpenBabel and ACPYPE.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.has_ligand or not self.ligand_file:
            return {
                "success": False,
                "error": "No ligand has been set"
            }

        prerequisites = self.check_prerequisites()
        if not prerequisites["openbabel"]["installed"]:
            return {
                "success": False,
                "error": "OpenBabel is required for ligand preparation but is not installed"
            }

        if not prerequisites["acpype"]["installed"]:
            return {
                "success": False,
                "error": "ACPYPE is required for ligand preparation but is not installed"
            }

        babel_cmd = "cd param/ligand && obabel -ipdb ligand.pdb -omol2 -h > ligand.mol2"
        babel_result = self.run_shell_command(babel_cmd)
        if not babel_result["success"]:
            return {
                "success": False,
                "error": f"Failed to convert ligand to MOL2 format: {babel_result['stderr']}"
            }

        acpype_cmd = "cd param/ligand && acpype -i ligand.mol2"
        acpype_result = self.run_shell_command(acpype_cmd)
        if not acpype_result["success"]:
            return {
                "success": False,
                "error": f"Failed to generate ligand topology with ACPYPE: {acpype_result['stderr']}"
            }

        copy_cmd = "cp param/ligand/ligand.acpype/ligand_GMX.itp ligand.itp"
        copy_result = self.run_shell_command(copy_cmd)
        if not copy_result["success"]:
            return {
                "success": False,
                "error": f"Failed to copy ligand topology: {copy_result['stderr']}"
            }

        ndx_cmd = f"echo $'r LIG & !a H*\nname 3 LIG-H\nq'| {self.gmx_bin} make_ndx -f param/ligand/ligand.acpype/ligand_NEW.pdb -o lig_noh.ndx"
        ndx_result = self.run_shell_command(ndx_cmd)
        if not ndx_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create index for ligand restraints: {ndx_result['stderr']}"
            }

        posre_cmd = "cp param/ligand/ligand.acpype/posre_ligand.itp ."
        posre_result = self.run_shell_command(posre_cmd)
        if not posre_result["success"]:
            return {
                "success": False,
                "error": f"Failed to generate position restraints for ligand: {posre_result['stderr']}"
            }

        append_cmd = '''echo '
 ; Include Position restraint file
#ifdef POSRES
#include "posre_ligand.itp"
#endif' >> ligand.itp'''
        append_result = self.run_shell_command(append_cmd)
        if not append_result["success"]:
            return {
                "success": False,
                "error": f"Failed to update ligand.itp with position restraints: {append_result['stderr']}"
            }

        return {
            "success": True,
            "ligand_topology": "ligand.itp",
            "ligand_posre": "posre_ligand.itp"
        }

    def prepare_receptor_topology(self, force_field: str, water_model: str = "spc") -> Dict[str, Any]:
        """
        Generate topology for the receptor.

        Parameters
        ----------
        force_field : str
            Name of the force field to use.
        water_model : str, optional
            Water model to use. Default is spc.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not os.path.exists("param/receptor/receptor.pdb"):
            return {
                "success": False,
                "error": "Receptor file not found"
            }

        if force_field not in FORCE_FIELDS:
            return {
                "success": False,
                "error": f"Unknown force field: {force_field}. Available options: {list(FORCE_FIELDS.keys())}"
            }

        ff_name = FORCE_FIELDS[force_field]

        cmd = f"cd param/receptor && {self.gmx_bin} pdb2gmx -f receptor.pdb -o receptor_GMX.pdb -p topol.top -i posre.itp -ff {ff_name} -water {water_model}"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to generate receptor topology: {result['stderr']}"
            }

        copy_cmd = "cp param/receptor/*.itp param/receptor/topol.top ."
        copy_result = self.run_shell_command(copy_cmd)
        if not copy_result["success"]:
            return {
                "success": False,
                "error": f"Failed to copy receptor topology files: {copy_result['stderr']}"
            }

        return {
            "success": True,
            "receptor_topology": "topol.top"
        }

    def merge_protein_ligand(self) -> Dict[str, Any]:
        """
        Merge protein and ligand structures and update the topology.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.has_ligand:
            return {
                "success": False,
                "error": "No ligand has been set"
            }

        merge_cmd = "grep -h ATOM param/receptor/receptor_GMX.pdb param/ligand/ligand.acpype/ligand_NEW.pdb > complex.pdb"
        merge_result = self.run_shell_command(merge_cmd)
        if not merge_result["success"]:
            return {
                "success": False,
                "error": f"Failed to merge protein and ligand structures: {merge_result['stderr']}"
            }

        update_cmd = """sed -i '/forcefield\\.itp"/a\\
#include "ligand.itp"' topol.top"""
        update_result = self.run_shell_command(update_cmd)
        if not update_result["success"]:
            return {
                "success": False,
                "error": f"Failed to update topology file: {update_result['stderr']}"
            }

        add_cmd = """echo "ligand   1" >> topol.top"""
        add_result = self.run_shell_command(add_cmd)
        if not add_result["success"]:
            return {
                "success": False,
                "error": f"Failed to add ligand to topology molecules: {add_result['stderr']}"
            }

        self.complex_file = "complex.pdb"
        self.topology_file = "topol.top"
        self.box_file = self.complex_file

        return {
            "success": True,
            "complex_file": self.complex_file,
            "topology_file": self.topology_file
        }

    def create_index_groups(self) -> Dict[str, Any]:
        """
        Create custom index groups for protein-ligand simulation.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.has_ligand:
            return {
                "success": False,
                "error": "No ligand has been set"
            }

        if not self.solvated_file:
            return {
                "success": False,
                "error": "System must be solvated first"
            }

        ndx_cmd = f"""echo -e "1 | r LIG\\nr SOL | r CL | r NA\\nq" | {self.gmx_bin} make_ndx -f {self.solvated_file} -o index.ndx"""
        ndx_result = self.run_shell_command(ndx_cmd)
        if not ndx_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create index groups: {ndx_result['stderr']}"
            }

        script_content = """
import re
with open('index.ndx', 'r') as file:
    content = file.read()
matches = re.findall(r'\\[ \\w+ \\]', content)
if matches:
    content = content.replace(matches[-1], '[ Water_Ions ]')
    content = content.replace(matches[-2], '[ Protein_Ligand ]')
    with open('index.ndx', 'w') as file:
        file.write(content)
"""
        with open("rename_groups.py", "w") as f:
            f.write(script_content)

        rename_result = self.run_shell_command("python rename_groups.py")
        if not rename_result["success"]:
            return {
                "success": False,
                "error": f"Failed to rename index groups: {rename_result['stderr']}"
            }

        os.remove("rename_groups.py")

        self.create_mdp_file("nvt")
        update_nvt_cmd = "sed -i 's/Protein Non-Protein/Protein_Ligand Water_Ions/g' nvt.mdp"
        nvt_result = self.run_shell_command(update_nvt_cmd)

        self.create_mdp_file("npt")
        update_npt_cmd = "sed -i 's/Protein Non-Protein/Protein_Ligand Water_Ions/g' npt.mdp"
        npt_result = self.run_shell_command(update_npt_cmd)

        self.create_mdp_file("md")
        update_md_cmd = "sed -i 's/Protein Non-Protein/Protein_Ligand Water_Ions/g' md.mdp"
        md_result = self.run_shell_command(update_md_cmd)

        if not (nvt_result["success"] and npt_result["success"] and md_result["success"]):
            return {
                "success": False,
                "error": "Failed to update MDP files with new index groups"
            }

        self.index_file = "index.ndx"

        return {
            "success": True,
            "index_file": self.index_file,
            "groups": ["Protein_Ligand", "Water_Ions"]
        }

    def generate_topology(self, force_field: str, water_model: str = "spc") -> Dict[str, Any]:
        """
        Generate topology for the protein-ligand complex.

        Parameters
        ----------
        force_field : str
            Name of the force field to use.
        water_model : str, optional
            Water model to use. Default is spc.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.protein_file:
            return {
                "success": False,
                "error": "No protein file has been set"
            }

        if self.has_ligand:
            receptor_result = self.prepare_receptor_topology(force_field, water_model)
            if not receptor_result["success"]:
                return receptor_result

            ligand_result = self.prepare_ligand_topology()
            if not ligand_result["success"]:
                return ligand_result

            merge_result = self.merge_protein_ligand()
            if not merge_result["success"]:
                return merge_result

            return {
                "success": True,
                "topology_file": self.topology_file,
                "complex_file": self.complex_file,
                "force_field": force_field,
                "water_model": water_model,
                "has_ligand": self.has_ligand
            }
        else:
            return super().generate_topology(force_field, water_model)

    def solvate_system(self) -> Dict[str, Any]:
        """
        Solvate the protein-ligand complex in water.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        result = super().solvate_system()

        if not result["success"]:
            return result

        if self.has_ligand:
            index_result = self.create_index_groups()
            if not index_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to create index groups: {index_result['error']}"
                }

        return {
            "success": True,
            "solvated_file": self.solvated_file,
            "has_ligand": self.has_ligand,
            "index_file": self.index_file if self.has_ligand else None
        }

    def add_ions(self, concentration: float = .15, neutral: bool = True) -> Dict[str, Any]:
        """
        Add ions to the solvated system.

        Parameters
        ----------
        concentration : float, optional
            Salt concentration in M. Default is .15.
        neutral : bool, optional
            Whether to neutralize the system. Default is True.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        result = super().add_ions(concentration, neutral)

        if not result["success"]:
            return result

        if self.has_ligand:
            index_result = self.create_index_groups()
            if not index_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to update index groups: {index_result['error']}"
                }

        return {
            "success": True,
            "solvated_file": self.solvated_file,
            "concentration": concentration,
            "neutral": neutral,
            "has_ligand": self.has_ligand,
            "index_file": self.index_file if self.has_ligand else None
        }

    def run_energy_minimization(self) -> Dict[str, Any]:
        """
        Run energy minimization.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.solvated_file or not self.topology_file:
            return {
                "success": False,
                "error": "Solvated file or topology file not defined"
            }

        em_mdp = self.create_mdp_file("em")
        if not em_mdp["success"]:
            return em_mdp

        index_option = f"-n {self.index_file}" if self.has_ligand and self.index_file else ""
        cmd = f"{self.gmx_bin} grompp -f em.mdp -c {self.solvated_file} -p {self.topology_file} -o em.tpr {index_option}"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare energy minimization: {result['stderr']}"
            }

        cmd = f"{self.gmx_bin} mdrun -v -deffnm em"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Energy minimization failed: {result['stderr']}"
            }

        self.minimized_file = "em.gro"

        return {
            "success": True,
            "minimized_file": self.minimized_file,
            "log_file": "em.log",
            "energy_file": "em.edr"
        }

    def run_nvt_equilibration(self) -> Dict[str, Any]:
        """
        Run NVT equilibration.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.minimized_file or not self.topology_file:
            return {
                "success": False,
                "error": "Minimized file or topology file not defined"
            }

        nvt_mdp = self.create_mdp_file("nvt")
        if not nvt_mdp["success"]:
            return nvt_mdp

        index_option = f"-n {self.index_file}" if self.has_ligand and self.index_file else ""
        cmd = f"{self.gmx_bin} grompp -f nvt.mdp -c {self.minimized_file} -r {self.minimized_file} -p {self.topology_file} -o nvt.tpr -maxwarn 2 {index_option}"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare NVT equilibration: {result['stderr']}"
            }

        cmd = f"{self.gmx_bin} mdrun -v -deffnm nvt"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"NVT equilibration failed: {result['stderr']}"
            }

        return {
            "success": True,
            "nvt_file": "nvt.gro",
            "nvt_checkpoint": "nvt.cpt",
            "log_file": "nvt.log",
            "energy_file": "nvt.edr"
        }

    def run_npt_equilibration(self) -> Dict[str, Any]:
        """
        Run NPT equilibration.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        npt_mdp = self.create_mdp_file("npt")
        if not npt_mdp["success"]:
            return npt_mdp

        index_option = f"-n {self.index_file}" if self.has_ligand and self.index_file else ""
        cmd = f"{self.gmx_bin} grompp -f npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p {self.topology_file} -o npt.tpr -maxwarn 2 {index_option}"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare NPT equilibration: {result['stderr']}"
            }

        cmd = f"{self.gmx_bin} mdrun -v -deffnm npt"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"NPT equilibration failed: {result['stderr']}"
            }

        self.equilibrated_file = "npt.gro"

        return {
            "success": True,
            "equilibrated_file": self.equilibrated_file,
            "npt_checkpoint": "npt.cpt",
            "log_file": "npt.log",
            "energy_file": "npt.edr"
        }

    def run_production_md(self, length_ns: float = 10.0) -> Dict[str, Any]:
        """
        Run production MD.

        Parameters
        ----------
        length_ns : float, optional
            Length of the simulation in nanoseconds. Default is 10.0.

        Returns
        -------
        Dict[str, Any]
            Dictionary with result information.
        """
        if not self.equilibrated_file or not self.topology_file:
            return {
                "success": False,
                "error": "Equilibrated file or topology file not defined"
            }

        nsteps = int(length_ns * 1000000 / 2)

        md_mdp = self.create_mdp_file("md", {"nsteps": nsteps})
        if not md_mdp["success"]:
            return md_mdp

        index_option = f"-n {self.index_file}" if self.has_ligand and self.index_file else ""
        cmd = f"{self.gmx_bin} grompp -f md.mdp -c {self.equilibrated_file} -t npt.cpt -p {self.topology_file} -o md.tpr -maxwarn 2 {index_option}"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare production MD: {result['stderr']}"
            }

        cmd = f"{self.gmx_bin} mdrun -v -deffnm md"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Production MD failed: {result['stderr']}"
            }

        self.production_file = "md.gro"

        return {
            "success": True,
            "production_file": self.production_file,
            "trajectory_file": "md.xtc",
            "log_file": "md.log",
            "energy_file": "md.edr",
            "length_ns": length_ns
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
                "error": "No ligand has been set"
            }

        mkdir_result = self.run_shell_command("mkdir -p analysis")

        cmd = f"echo 'LIG LIG' | {self.gmx_bin} rms -s md.tpr -f md.xtc -o analysis/ligand_rmsd.xvg -tu ns"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Ligand RMSD analysis failed: {result['stderr']}"
            }

        return {
            "success": True,
            "output_file": "analysis/ligand_rmsd.xvg",
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
                "error": "No ligand has been set"
            }

        mkdir_result = self.run_shell_command("mkdir -p analysis")

        cmd = f"echo -e 'Protein\\nLIG' | {self.gmx_bin} mindist -s md.tpr -f md.xtc -od analysis/protein_ligand_mindist.xvg -tu ns"
        result = self.run_shell_command(cmd)

        if not result["success"]:
            return {
                "success": False,
                "error": f"Protein-ligand contacts analysis failed: {result['stderr']}"
            }

        return {
            "success": True,
            "output_file": "analysis/protein_ligand_mindist.xvg",
            "analysis_type": "Protein-Ligand Minimum Distance"
        }

    def is_applicable(self, user_input: str, context: Dict[str, Any]) -> bool:
        """
        Check if this skill is applicable to the given user input.

        Parameters
        ----------
        user_input : str
            The user input to check.
        context : Dict[str, Any]
            Additional context information.

        Returns
        -------
        bool
            True if the skill is applicable, False otherwise.
        """
        ligand_keywords = ["ligand", "complex", "binding", "drug", "inhibitor", "substrate"]
        if any(kw in user_input.lower() for kw in ligand_keywords):
            return True
        if context.get("has_ligand"):
            return True
        if os.path.exists(os.path.join(self.workspace, "ligand.itp")):
            return True
        return False

    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get the tool schema for this skill.

        Returns
        -------
        List[Dict[str, Any]]
            List of tool definitions for this skill.
        """
        tools = super().get_tool_schema()
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "check_for_ligands",
                    "description": "Check for potential ligands in the PDB file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdb_file": {
                                "type": "string",
                                "description": "Path to the PDB file"
                            }
                        },
                        "required": ["pdb_file"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_ligand",
                    "description": "Set the ligand for simulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ligand_name": {
                                "type": "string",
                                "description": "Residue name of the ligand in the PDB file"
                            }
                        },
                        "required": ["ligand_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_ligand_rmsd",
                    "description": "Perform RMSD analysis focused on the ligand",
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
                    "name": "analyze_protein_ligand_contacts",
                    "description": "Analyze contacts between protein and ligand",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ])
        return tools