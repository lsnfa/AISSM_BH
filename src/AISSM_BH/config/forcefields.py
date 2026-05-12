"""
Force fields, water models, and simulation box types supported by AISSM_BH.
"""

FORCE_FIELDS = {
    "AMBER99SB-ILDN": "amber99sb-ildn",
    "CHARMM36": "charmm36-feb2021",
    "GROMOS96 53a6": "gromos53a6",
    "OPLS-AA/L": "oplsaa"
}

WATER_MODELS = ["spc", "tip3p", "tip4p"]

BOX_TYPES = ["cubic", "dodecahedron", "octahedron"]

MDP_TYPES = ["ions", "em", "nvt", "npt", "md"]