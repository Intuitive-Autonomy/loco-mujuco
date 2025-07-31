#!/usr/bin/env python3
"""
Simple motion viewer using LocoMuJoCo's built-in capabilities
"""

import argparse
import numpy as np
import time
from pathlib import Path

from loco_mujoco.environments import LocoEnv
from loco_mujoco.smpl.retargeting import load_robot_conf_file
from loco_mujoco.trajectory import Trajectory

def play_motion(traj_file, env_name='SkeletonTorque'):
    """Play motion using environment's trajectory handler"""
    
    print(f"🎬 Loading trajectory: {traj_file}")
    
    # Load trajectory
    traj = Trajectory.load(traj_file)
    print(f"✓ Loaded trajectory: {traj.data.qpos.shape[0]} timesteps, {traj.info.frequency} Hz")
    
    # Create environment with rendering
    env_cls = LocoEnv.registered_envs[env_name]
    robot_conf = load_robot_conf_file(env_name)
    
    # Create environment without render_mode parameter
    env_params = robot_conf.env_params.copy()
    
    env = env_cls(**env_params, th_params=dict(random_start=False, fixed_start_conf=(0, 0)))
    print(f"✓ Created {env_name} environment with rendering")
    
    # Load trajectory into environment
    env.load_trajectory(traj, warn=False)
    print(f"✓ Loaded trajectory into environment")
    
    # Reset environment to start of trajectory
    obs = env.reset()
    print(f"✓ Environment reset, observation shape: {obs.shape}")
    
    print("\n🎮 Playing motion...")
    print("Press Ctrl+C to stop")
    
    try:
        # Play the trajectory
        for step in range(traj.data.qpos.shape[0]):
            # Get current state from trajectory
            qpos = traj.data.qpos[step]
            if traj.data.qvel is not None:
                qvel = traj.data.qvel[step]
            else:
                qvel = np.zeros(traj.data.qpos.shape[1] - 1)
            
            # Set the state directly
            env._data.qpos[:] = qpos
            env._data.qvel[:] = qvel
            
            # Forward dynamics
            import mujoco
            mujoco.mj_forward(env._model, env._data)
            
            # Render
            if hasattr(env, 'render'):
                env.render()
            
            # Print progress
            if step % 50 == 0:
                root_height = env._data.qpos[2]  # Z position
                print(f"  Step {step:3d}/{traj.data.qpos.shape[0]}: Root height = {root_height:7.3f}m")
            
            # Control playback speed
            time.sleep(1.0 / traj.info.frequency * 0.5)  # Half speed for better viewing
            
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped by user")
    
    print("👋 Motion playback ended")

def main():
    parser = argparse.ArgumentParser(description="Simple motion viewer for LocoMuJoCo")
    parser.add_argument("--input_file", required=True, help="Path to NPZ trajectory file")
    parser.add_argument("--env_name", default="SkeletonTorque", help="Environment name")
    
    args = parser.parse_args()
    
    if not Path(args.input_file).exists():
        print(f"❌ File not found: {args.input_file}")
        return
    
    print("🎥 SIMPLE MOTION VIEWER")
    print("=" * 30)
    print(f"📁 Input: {args.input_file}")
    print(f"🤖 Environment: {args.env_name}")
    print()
    
    try:
        play_motion(args.input_file, args.env_name)
    except Exception as e:
        print(f"❌ Playback failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()