"""
Skill routing strategy for AISSM_BH.
"""

from AISSM_BH.skills.protein import ProteinSkill
from AISSM_BH.skills.protein_ligand import ProteinLigandSkill
from AISSM_BH.skills.mmpbsa import MMPBSASkill
from AISSM_BH.skills.analysis import AnalysisSkill


class SkillRouter:
    """
    Evaluate and switch between simulation skills based on user input and context.

    - Evaluation uses lightweight instances that only call ``is_applicable``.
    - Switching creates a **new** skill instance each time (mirroring the
      original ``BHMDAgent`` behaviour), preventing instance reuse and state
      contamination.
    """

    PRIORITY = ["mmpbsa", "protein_ligand", "analysis", "protein"]

    def __init__(self, workspace: str, gmx_bin: str = "gmx"):
        """
        Parameters
        ----------
        workspace : str
            Workspace path.
        gmx_bin : str, optional
            GROMACS executable. Default is "gmx".
        """
        self.workspace = workspace
        self.gmx_bin = gmx_bin

        self.skill_classes = {
            "protein": ProteinSkill,
            "protein_ligand": ProteinLigandSkill,
            "mmpbsa": MMPBSASkill,
            "analysis": AnalysisSkill,
        }

        self.class_to_name = {v: k for k, v in self.skill_classes.items()}

        self._eval_instances = {
            name: cls(self.workspace, self.gmx_bin)
            for name, cls in self.skill_classes.items()
        }

    def evaluate(self, user_input: str, context: dict) -> str:
        """
        Return the **name** of the most applicable skill.

        Parameters
        ----------
        user_input : str
            The user's natural-language request.
        context : dict
            Current context (keys: ``phase``, ``has_ligand``, ``workspace``).

        Returns
        -------
        str
            Skill key (e.g. "protein", "mmpbsa", ...).
        """
        for name in self.PRIORITY:
            skill = self._eval_instances[name]
            if skill.is_applicable(user_input, context):
                return name
        return "protein"

    def switch_to(self, target: str, current_skill):
        """
        Create a **fresh** skill instance and transfer relevant state.

        Parameters
        ----------
        target : str
            Skill key (one of the keys in ``self.skill_classes``).
        current_skill : BaseSkill
            The skill currently in use (state will be copied).

        Returns
        -------
        tuple
            ``(new_skill_instance, previous_skill_class_name)``.
        """
        new_skill = self.skill_classes[target](self.workspace, self.gmx_bin)

        if hasattr(current_skill, "topology_file"):
            new_skill.topology_file = current_skill.topology_file
        if hasattr(current_skill, "trajectory_file"):
            new_skill.trajectory_file = current_skill.trajectory_file

        return new_skill, current_skill.__class__.__name__