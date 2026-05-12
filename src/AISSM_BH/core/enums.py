"""
Enumerations for GROMACS Copilot
"""

from enum import Enum, auto

class SimulationPhase(Enum):
    """Stages of the MD simulation workflow"""
    SETUP = auto()
    PREPARE_PROTEIN = auto()
    PREPARE_LIGAND = auto()  # For protein-ligand simulations
    PREPARE_COMPLEX = auto() # For protein-ligand simulations
    SOLVATION = auto()
    ENERGY_MINIMIZATION = auto()
    EQUILIBRATION = auto()
    PRODUCTION = auto()
    ANALYSIS = auto()
    COMPLETED = auto()

class MessageType(Enum):
    """Types of messages for terminal output"""
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    TITLE = auto()
    SYSTEM = auto()
    USER = auto()
    COMMAND = auto()
    TOOL = auto()
    FINAL = auto()
