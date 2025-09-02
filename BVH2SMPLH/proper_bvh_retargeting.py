"""
BVH Parsing Utilities for SMPL-H Retargeting

Provides professional BVH parsing functions with proper:
- ZXY Euler rotation order handling
- Skeleton structure parsing
- Motion data extraction
- Coordinate system conversion

These utilities are used by mocap_retarget.py for BVH to SMPL-H conversion.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
from scipy.spatial.transform import Rotation as R

# Configure logging
logger = logging.getLogger(__name__)

def parse_bvh_file(bvh_file_path: Union[str, Path]) -> Tuple[List[str], List[Tuple[int, List[str]]], np.ndarray, float]:
    """
    Parse BVH file with proper ZXY rotation order handling.
    
    Args:
        bvh_file_path: Path to BVH file
        
    Returns:
        Tuple containing:
        - joint_names: List of joint names in hierarchy order
        - joint_channels: List of (channel_count, channel_types) tuples
        - motion_data: Motion data array (frames x channels)
        - frame_time: Time per frame in seconds
        
    Raises:
        FileNotFoundError: If BVH file doesn't exist
        ValueError: If BVH file format is invalid
    """
    bvh_path = Path(bvh_file_path)
    
    if not bvh_path.exists():
        raise FileNotFoundError(f"BVH file not found: {bvh_path}")
        
    logger.info(f"Parsing BVH file: {bvh_path}")
    
    try:
        with open(bvh_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(bvh_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()
    
    # Parse skeleton structure
    joint_names = []
    joint_channels = []
    
    # Parse hierarchy section
    hierarchy_mode = True
    motion_start = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line == "MOTION":
            hierarchy_mode = False
            motion_start = i + 1
            break
            
        if hierarchy_mode:
            if line.startswith("ROOT") or line.startswith("JOINT"):
                joint_name = line.split()[1]
                joint_names.append(joint_name)
                logger.debug(f"Found joint: {joint_name}")
            elif "CHANNELS" in line:
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    channels = int(parts[1])
                    channel_types = parts[2:]
                    joint_channels.append((channels, channel_types))
                    logger.debug(f"Channels: {channels} {channel_types}")
                except ValueError:
                    logger.warning(f"Invalid channel line: {line}")
    
    # Parse motion data
    if motion_start >= len(lines) or motion_start + 1 >= len(lines):
        raise ValueError("Invalid BVH format: missing motion data headers")
        
    frames_line = lines[motion_start].strip()
    frame_time_line = lines[motion_start + 1].strip()
    
    try:
        n_frames = int(frames_line.split()[1])
        frame_time = float(frame_time_line.split()[2])
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid BVH motion headers: {e}")
    
    logger.info(f"Motion data: {n_frames} frames, {frame_time} seconds per frame")
    
    # Parse frame data
    motion_data = []
    for i in range(motion_start + 2, motion_start + 2 + n_frames):
        if i >= len(lines):
            logger.warning(f"Missing frame data at line {i}")
            break
        try:
            frame_data = [float(x) for x in lines[i].strip().split()]
            motion_data.append(frame_data)
        except ValueError as e:
            logger.warning(f"Invalid frame data at line {i}: {e}")
            continue
    
    if not motion_data:
        raise ValueError("No valid motion data found")
        
    motion_data = np.array(motion_data)
    logger.info(f"Motion data shape: {motion_data.shape}")
    
    return joint_names, joint_channels, motion_data, frame_time

def extract_joint_rotations_proper(joint_names: List[str], joint_channels: List[Tuple[int, List[str]]], 
                                  motion_data: np.ndarray) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Extract joint rotations with proper ZXY Euler handling.
    
    Args:
        joint_names: List of joint names from BVH hierarchy
        joint_channels: List of (channel_count, channel_types) tuples
        motion_data: Motion data array (frames x channels)
        
    Returns:
        Tuple containing:
        - joint_positions: Dictionary mapping joint names to position arrays
        - joint_rotations: Dictionary mapping joint names to rotation arrays (axis-angle)
        
    Raises:
        ValueError: If motion data is inconsistent with joint structure
    """
    n_frames = motion_data.shape[0]
    joint_rotations = {}
    joint_positions = {}
    
    channel_idx = 0
    expected_channels = sum(channels for channels, _ in joint_channels)
    
    if motion_data.shape[1] != expected_channels:
        raise ValueError(f"Motion data has {motion_data.shape[1]} channels but expected {expected_channels}")
    
    logger.debug(f"Extracting rotations from {n_frames} frames, {expected_channels} channels")
    
    for joint_name, (n_channels, channel_types) in zip(joint_names, joint_channels):
        
        if joint_name == "Hips":  # Root joint with position and rotation
            if n_channels != 6:
                logger.warning(f"Root joint {joint_name} has {n_channels} channels, expected 6")
                
            # Extract root position (first 3 channels: Xposition Yposition Zposition)
            if channel_idx + 3 <= motion_data.shape[1]:
                root_pos = motion_data[:, channel_idx:channel_idx+3]
                joint_positions[joint_name] = root_pos
                
            # Extract root rotation (next 3 channels: Zrotation Xrotation Yrotation)
            if channel_idx + 6 <= motion_data.shape[1]:
                root_rot_zxy = motion_data[:, channel_idx+3:channel_idx+6]
                joint_rotations[joint_name] = _convert_euler_to_rotvec(root_rot_zxy)
                
            channel_idx += 6
            
        else:
            # Regular joint with rotation channels only
            if n_channels == 3 and channel_idx + 3 <= motion_data.shape[1]:
                rot_zxy = motion_data[:, channel_idx:channel_idx+3]
                joint_rotations[joint_name] = _convert_euler_to_rotvec(rot_zxy)
                channel_idx += 3
            else:
                logger.debug(f"Skipping joint {joint_name} with {n_channels} channels")
                channel_idx += n_channels
    
    logger.info(f"Extracted rotations for {len(joint_rotations)} joints")
    return joint_positions, joint_rotations


def _convert_euler_to_rotvec(euler_data: np.ndarray) -> np.ndarray:
    """
    Convert ZXY Euler angles to axis-angle representation.
    
    Args:
        euler_data: Array of Euler angles in degrees (frames x 3)
        
    Returns:
        Array of axis-angle rotations (frames x 3)
    """
    rotations = []
    
    for frame_euler in euler_data:
        # BVH uses degrees, convert to radians
        z_rot = np.deg2rad(frame_euler[0])  # Z rotation
        x_rot = np.deg2rad(frame_euler[1])  # X rotation  
        y_rot = np.deg2rad(frame_euler[2])  # Y rotation
        
        # Apply ZXY rotation order (critical for proper BVH conversion)
        rot = R.from_euler('ZXY', [z_rot, x_rot, y_rot])
        rotations.append(rot.as_rotvec())  # Convert to axis-angle
    
    return np.array(rotations)

def validate_bvh_structure(joint_names: List[str], expected_joints: List[str]) -> bool:
    """
    Validate that BVH contains expected joint structure.
    
    Args:
        joint_names: Joint names found in BVH file
        expected_joints: Expected joint names
        
    Returns:
        True if structure is valid, False otherwise
    """
    missing_joints = set(expected_joints) - set(joint_names)
    if missing_joints:
        logger.warning(f"Missing expected joints: {missing_joints}")
        return False
    return True


def get_bvh_joint_info(joint_names: List[str], joint_channels: List[Tuple[int, List[str]]]) -> Dict[str, Dict]:
    """
    Get detailed information about BVH joint structure.
    
    Args:
        joint_names: Joint names from BVH
        joint_channels: Channel information for each joint
        
    Returns:
        Dictionary with joint information
    """
    joint_info = {}
    
    for name, (n_channels, channel_types) in zip(joint_names, joint_channels):
        joint_info[name] = {
            'channels': n_channels,
            'channel_types': channel_types,
            'is_root': name == 'Hips',
            'has_position': 'position' in ' '.join(channel_types).lower(),
            'has_rotation': any(rot in ' '.join(channel_types).lower() for rot in ['rotation', 'rot'])
        }
    
    return joint_info


def main():
    """Main CLI entry point for BVH parsing utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BVH Parsing Utilities Test')
    parser.add_argument('bvh_file', help='Path to BVH file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        joint_names, joint_channels, motion_data, frame_time = parse_bvh_file(args.bvh_file)
        joint_positions, joint_rotations = extract_joint_rotations_proper(joint_names, joint_channels, motion_data)
        
        print(f"Successfully parsed BVH file:")
        print(f"  Joints: {len(joint_names)}")
        print(f"  Frames: {motion_data.shape[0]}")
        print(f"  Frame time: {frame_time}")
        print(f"  Rotation data: {len(joint_rotations)} joints")
        
        # Show joint info
        joint_info = get_bvh_joint_info(joint_names, joint_channels)
        print(f"\nJoint structure:")
        for name, info in joint_info.items():
            print(f"  {name}: {info['channels']} channels {info['channel_types']}")
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

