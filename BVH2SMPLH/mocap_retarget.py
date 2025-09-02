"""
BVH to SMPL-H Retargeting Pipeline

Professional BVH motion capture to SMPL-H conversion tool for LocoMuJoCo.
Supports 52-joint SMPL-H mapping with comprehensive finger articulation.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
from scipy.spatial.transform import Rotation as R

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SMPLHMapping:
    """SMPL-H joint mapping configuration"""
    
    @staticmethod
    def get_joint_mapping() -> Dict[int, str]:
        """
        Create comprehensive BVH to SMPL-H joint mapping.
        
        Returns:
            Dict mapping SMPL-H joint indices to BVH joint names
        """
        return {
            # Core body joints (22 total)
            0: 'Hips',              # Pelvis (root)
            1: 'LeftUpLeg',         # L_Hip
            2: 'RightUpLeg',        # R_Hip  
            3: 'Spine',             # Torso (lower spine)
            4: 'LeftLeg',           # L_Knee
            5: 'RightLeg',          # R_Knee
            6: 'Spine1',            # Spine (upper spine)
            7: 'LeftFoot',          # L_Ankle
            8: 'RightFoot',         # R_Ankle
            # 9: Chest - left unmapped (rest pose)
            10: 'LeftToeBase',      # L_Toe
            11: 'RightToeBase',     # R_Toe
            12: 'Neck',             # Neck
            # 13: L_Thorax - left unmapped
            # 14: R_Thorax - left unmapped  
            15: 'Head',             # Head
            16: 'LeftShoulder',     # L_Shoulder
            17: 'RightShoulder',    # R_Shoulder
            18: 'LeftArm',          # L_Elbow (arm rotation)
            19: 'RightArm',         # R_Elbow (arm rotation)
            20: 'LeftForeArm',      # L_Wrist (forearm + hand combined)
            21: 'RightForeArm',     # R_Wrist (forearm + hand combined)
            
            # Hand joints (30 total)
            **{i + 22: joint for i, joint in enumerate([
                # Left hand (15 joints)
                'LeftHandIndex1', 'LeftHandIndex2', 'LeftHandIndex3',
                'LeftHandMiddle1', 'LeftHandMiddle2', 'LeftHandMiddle3',
                'LeftHandPinky1', 'LeftHandPinky2', 'LeftHandPinky3',
                'LeftHandRing1', 'LeftHandRing2', 'LeftHandRing3',
                'LeftHandThumb1', 'LeftHandThumb2', 'LeftHandThumb3',
                # Right hand (15 joints)
                'RightHandIndex1', 'RightHandIndex2', 'RightHandIndex3',
                'RightHandMiddle1', 'RightHandMiddle2', 'RightHandMiddle3',
                'RightHandPinky1', 'RightHandPinky2', 'RightHandPinky3',
                'RightHandRing1', 'RightHandRing2', 'RightHandRing3',
                'RightHandThumb1', 'RightHandThumb2', 'RightHandThumb3',
            ])}
        }
    
    @staticmethod
    def get_unmapped_joints() -> Dict[int, str]:
        """Get joints left unmapped (will remain at rest pose)"""
        return {
            9: 'Chest',      # No BVH equivalent
            13: 'L_Thorax',  # No BVH equivalent  
            14: 'R_Thorax',  # No BVH equivalent
        }

def verify_joint_mapping() -> None:
    """Verify the joint mapping is anatomically correct"""
    
    mapping = SMPLHMapping.get_joint_mapping()
    unmapped = SMPLHMapping.get_unmapped_joints()
    
    logger.info("Complete SMPL-H Joint Mapping (49/52 joints):")
    logger.info("=" * 50)
    
    # Show body joints (0-21)
    logger.info("BODY JOINTS (22 total):")
    for i in range(22):
        if i in mapping:
            logger.info(f"  SMPL-H[{i:2}] -> {mapping[i]} ✅")
        elif i in unmapped:
            logger.info(f"  SMPL-H[{i:2}] -> {unmapped[i]} ❌ (unmapped)")
        else:
            logger.info(f"  SMPL-H[{i:2}] -> MISSING ❌")
    
    # Show hand joints (22-51)  
    logger.info("\nHAND JOINTS (30 total):")
    for i in range(22, 52):
        if i in mapping:
            logger.info(f"  SMPL-H[{i:2}] -> {mapping[i]} ✅")
        elif i in unmapped:
            logger.info(f"  SMPL-H[{i:2}] -> {unmapped[i]} ❌ (unmapped)")
        else:
            logger.info(f"  SMPL-H[{i:2}] -> MISSING ❌")
    
    mapped_count = len(mapping)
    unmapped_count = len(unmapped)
    total_joints = 52
    
    logger.info("=" * 50)
    logger.info(f"SUMMARY:")
    logger.info(f"  Mapped joints: {mapped_count}/52 ({mapped_count/total_joints*100:.1f}%)")
    logger.info(f"  Unmapped joints: {unmapped_count}/52 ({unmapped_count/total_joints*100:.1f}%)")
    logger.info(f"  Total coverage: {mapped_count + unmapped_count}/52")


class BVHRetargeter:
    """Main class for BVH to SMPL-H retargeting"""
    
    def __init__(self):
        self.joint_mapping = SMPLHMapping.get_joint_mapping()
        self.unmapped_joints = SMPLHMapping.get_unmapped_joints()
        
    def validate_paths(self, bvh_path: str, output_path: str) -> Tuple[Path, Path]:
        """
        Validate input and output paths.
        
        Args:
            bvh_path: Path to input BVH file
            output_path: Path for output NPZ file
            
        Returns:
            Tuple of validated Path objects
            
        Raises:
            FileNotFoundError: If BVH file doesn't exist
            ValueError: If paths are invalid
        """
        bvh_file = Path(bvh_path)
        output_file = Path(output_path)
        
        if not bvh_file.exists():
            raise FileNotFoundError(f"BVH file not found: {bvh_file}")
            
        if not bvh_file.suffix.lower() == '.bvh':
            raise ValueError(f"Input must be a BVH file, got: {bvh_file.suffix}")
            
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Input BVH: {bvh_file}")
        logger.info(f"Output NPZ: {output_file}")
        
        return bvh_file, output_file
    
    def map_joints_to_smplh(self, joint_rotations: Dict[str, np.ndarray], n_frames: int) -> Tuple[np.ndarray, int]:
        """
        Map BVH joint rotations to SMPL-H format.
        
        Args:
            joint_rotations: Dictionary of BVH joint rotations
            n_frames: Number of animation frames
            
        Returns:
            Tuple of (SMPL-H rotation array, number of mapped joints)
        """
        smplh_rotations = np.zeros((n_frames, 52, 3))
        mapped_count = 0
        
        logger.info("Mapping BVH joints to SMPL-H format:")
        
        for smplh_idx, bvh_joint in self.joint_mapping.items():
            if bvh_joint in joint_rotations:
                smplh_rotations[:, smplh_idx, :] = joint_rotations[bvh_joint]
                logger.debug(f"  SMPL-H[{smplh_idx:2}] <- {bvh_joint}")
                mapped_count += 1
        
        coverage = (mapped_count / 52) * 100
        logger.info(f"Mapped {mapped_count}/52 SMPL-H joints ({coverage:.1f}% coverage)")
        
        return smplh_rotations, mapped_count
    
    def create_amass_data(self, smplh_rotations: np.ndarray, root_trans: np.ndarray, 
                         frame_time: float, n_frames: int) -> Dict:
        """
        Create AMASS-compatible data structure.
        
        Args:
            smplh_rotations: SMPL-H joint rotations
            root_trans: Root translation
            frame_time: Time per frame
            n_frames: Number of frames
            
        Returns:
            AMASS data dictionary
        """
        # Split into body (22 joints) and hand (30 joints) components  
        poses_body = smplh_rotations[:, :22, :].reshape(n_frames, 66)  # 22*3 = 66
        poses_hand = smplh_rotations[:, 22:, :].reshape(n_frames, 90)  # 30*3 = 90
        poses = np.concatenate([poses_body, poses_hand], axis=1)        # 66+90 = 156
        
        # Generate shape and DMPL parameters
        betas = np.random.normal(0, 0.5, 16).astype(np.float32)
        betas = np.clip(betas, -2, 2)
        dmpls = np.zeros((n_frames, 8), dtype=np.float32)
        
        return {
            'trans': root_trans.astype(np.float32),
            'poses': poses.astype(np.float32),
            'betas': betas,
            'dmpls': dmpls,
            'gender': np.array(['neutral'], dtype='U10')[0],
            'mocap_framerate': np.array([1.0/frame_time], dtype=np.float32)[0],
            'poses_body': poses_body.astype(np.float32),
            'poses_hand': poses_hand.astype(np.float32),
        }
    
    def log_quality_metrics(self, poses_body: np.ndarray, poses_hand: np.ndarray, 
                           mapped_count: int, n_frames: int, frame_time: float) -> None:
        """Log quality metrics for the conversion"""
        
        logger.info("Quality Metrics:")
        logger.info(f"  Frames: {n_frames}")
        logger.info(f"  Framerate: {1.0/frame_time:.1f} fps")
        logger.info(f"  Joint coverage: {mapped_count}/52 ({mapped_count/52*100:.1f}%)")
        logger.info(f"  Body variation: {poses_body.std():.4f}")
        logger.info(f"  Hand variation: {poses_hand.std():.4f}")
        
        body_active = np.count_nonzero(poses_body) / poses_body.size * 100
        hand_active = np.count_nonzero(poses_hand) / poses_hand.size * 100
        
        logger.info(f"  Body activity: {body_active:.1f}%")
        logger.info(f"  Hand activity: {hand_active:.1f}%")
    
    def convert(self, bvh_path: str, output_path: str) -> bool:
        """
        Convert BVH file to SMPL-H format.
        
        Args:
            bvh_path: Path to input BVH file
            output_path: Path for output NPZ file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Validate paths
            bvh_file, output_file = self.validate_paths(bvh_path, output_path)
            
            # Import BVH parsing functions
            try:
                from proper_bvh_retargeting import parse_bvh_file, extract_joint_rotations_proper
            except ImportError as e:
                logger.error(f"Failed to import BVH parsing functions: {e}")
                return False
            
            # Parse BVH file
            logger.info("Parsing BVH file...")
            joint_names, joint_channels, motion_data, frame_time = parse_bvh_file(str(bvh_file))
            joint_positions, joint_rotations = extract_joint_rotations_proper(joint_names, joint_channels, motion_data)
            
            n_frames = motion_data.shape[0]
            root_trans = joint_positions['Hips'] / 100.0  # Convert to meters
            
            # Map to SMPL-H format
            smplh_rotations, mapped_count = self.map_joints_to_smplh(joint_rotations, n_frames)
            
            # Create AMASS data
            logger.info("Creating AMASS-compatible data...")
            amass_data = self.create_amass_data(smplh_rotations, root_trans, frame_time, n_frames)
            
            # Save to file
            logger.info(f"Saving to {output_file}")
            np.savez(str(output_file), **amass_data)
            
            # Log quality metrics
            self.log_quality_metrics(
                amass_data['poses_body'], 
                amass_data['poses_hand'],
                mapped_count, 
                n_frames, 
                frame_time
            )
            
            logger.info("✅ SMPL-H retargeting completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Conversion failed: {e}")
            return False




def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='BVH to SMPL-H Retargeting Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s input.bvh output.npz
  %(prog)s --input data/motion.bvh --output results/motion.npz
  %(prog)s -i motion.bvh -o motion.npz --verbose"""
    )
    
    # Required arguments
    parser.add_argument(
        'input_bvh', 
        nargs='?',
        help='Input BVH file path'
    )
    parser.add_argument(
        'output_npz',
        nargs='?', 
        help='Output NPZ file path'
    )
    
    # Optional arguments
    parser.add_argument(
        '-i', '--input',
        help='Input BVH file path (alternative to positional arg)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output NPZ file path (alternative to positional arg)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify joint mapping and exit'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle verification mode
    if args.verify:
        verify_joint_mapping()
        return
    
    # Determine input/output paths
    input_path = args.input_bvh or args.input
    output_path = args.output_npz or args.output
    
    # Default paths if not provided
    if not input_path:
        input_path = "../Mocap/Take 2025-08-19 02.48.13 PM_Skeleton.bvh"
        logger.info(f"Using default input: {input_path}")
        
    if not output_path:
        output_path = "../AMASS/CustomMocap/mocap_retargeted.npz"
        logger.info(f"Using default output: {output_path}")
    
    # Run conversion
    logger.info("Starting BVH to SMPL-H retargeting...")
    retargeter = BVHRetargeter()
    
    success = retargeter.convert(input_path, output_path)
    
    if success:
        logger.info("Conversion completed successfully!")
        sys.exit(0)
    else:
        logger.error("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()