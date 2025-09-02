"""
BVH to SMPL-H Retargeting Pipeline

Professional BVH motion capture to SMPL-H conversion tools for LocoMuJoCo.
Provides production-ready CLI tools with comprehensive error handling.
"""

__version__ = "1.0.0"
__author__ = "Choon Pin"
__license__ = "MIT"

# Import main classes for easy access
from .mocap_retarget import BVHRetargeter, SMPLHMapping
from .proper_bvh_retargeting import (
    parse_bvh_file, 
    extract_joint_rotations_proper,
    validate_bvh_structure,
    get_bvh_joint_info
)

__all__ = [
    "BVHRetargeter",
    "SMPLHMapping", 
    "parse_bvh_file",
    "extract_joint_rotations_proper",
    "validate_bvh_structure",
    "get_bvh_joint_info"
]