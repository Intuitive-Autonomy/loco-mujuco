# BVH to SMPL-H Retargeting Pipeline

Professional BVH to SMPL-H retargeting solution for LocoMuJoCo SkeletonTorque environments with production-ready CLI tools.

## Overview

This pipeline converts BVH motion capture data to SMPL-H format for use with LocoMuJoCo humanoid robots. Features object-oriented architecture, comprehensive error handling, and professional CLI interfaces.

## Features

- ✅ **Professional CLI Tools** - Configurable paths, verbose logging, help documentation
- ✅ **52-joint SMPL-H support** - Full body + finger articulation
- ✅ **94.2% joint coverage** - Maps 49/52 SMPL-H joints
- ✅ **Proper ZXY rotation handling** - Correct Euler angle conversion
- ✅ **Robust error handling** - File validation, format checking, encoding support
- ✅ **Production-ready code** - Type hints, logging, modular architecture
- ✅ **Multiple motion support** - Enhanced viewer with motion selection
- ✅ **High-quality motion** - Natural full-body movement with finger articulation

## Pipeline Flow

```
BVH File → mocap_retarget.py → NPZ File → LocoMuJoCo → SkeletonTorque Simulation
```

## Usage

### **1. Convert BVH to NPZ (Multiple Options)**

**Default conversion:**
```bash
cd /Users/choonspin/loco-mujoco/BVH2SMPLH
python mocap_retarget.py
```

**Custom input/output paths:**
```bash
python mocap_retarget.py input.bvh output.npz
python mocap_retarget.py --input ../Mocap/motion.bvh --output ../AMASS/CustomMocap/motion.npz
```

**With verbose logging:**
```bash
python mocap_retarget.py -i motion.bvh -o motion.npz --verbose
```

**Verify joint mapping:**
```bash
python mocap_retarget.py --verify
```

**Get help:**
```bash
python mocap_retarget.py --help
```

### **2. Test BVH Parsing (Standalone)**

**Analyze BVH structure:**
```bash
python proper_bvh_retargeting.py ../Mocap/motion.bvh
python proper_bvh_retargeting.py ../Mocap/motion.bvh --verbose
```

### **3. View Motion in LocoMuJoCo**

**Default motion:**
```bash
cd /Users/choonspin/loco-mujoco/examples/replay_datasets
python test_proper_motion_only.py
```

**Select specific motion:**
```bash
python test_proper_motion_only.py --motion mocap_test_02_55_48
python test_proper_motion_only.py -m mocap_retargeted --seed 42
```

**List available motions:**
```bash
python test_proper_motion_only.py --list
```

## Files

### **Core Scripts**
- `mocap_retarget.py` - **Main conversion script** with professional CLI
- `proper_bvh_retargeting.py` - **BVH parsing utilities** with standalone testing
- `test_proper_motion_only.py` - **Motion viewer** with NPZ selection (in `../examples/replay_datasets/`)

### **Input/Output**
- Input: `../Mocap/*.bvh` files (BVH motion capture data)
- Output: `../AMASS/CustomMocap/*.npz` files (SMPL-H format for LocoMuJoCo)

## Installation

### **Quick Setup**
```bash
# Clone the repository (if not already done)
git clone https://github.com/Intuitive-Autonomy/loco-mujuco.git
cd loco-mujuco/BVH2SMPLH

# Install dependencies
pip install -r requirements.txt
```

### **Manual Installation**
```bash
pip install numpy>=1.21.0 scipy>=1.7.0 loco-mujoco
pip install mujoco==3.2.7 mujoco-mjx==3.2.7  # Specific version required
```

### **Important Notes**
- **MuJoCo 3.2.7 required** - Version 3.3.0+ has API changes that break LocoMuJoCo
- **Python 3.8+** recommended for full type hint support
- Install in a virtual environment to avoid conflicts

### **Package Installation (Optional)**
```bash
# Install as editable package (for development)
pip install -e .

# Install as package (from setup.py)
pip install .

# After installation, use console commands
bvh2smplh --help
bvh-parse ../Mocap/motion.bvh
```

### **Verify Installation**
```bash
# Test BVH parsing
python proper_bvh_retargeting.py --help

# Test main converter
python mocap_retarget.py --verify

# Check dependencies
python -c "import mujoco; print(f'MuJoCo: {mujoco.__version__}')"

# Test package import (if installed)
python -c "from BVH2SMPLH import BVHRetargeter; print('Package imported successfully!')"
```

## Architecture

### **Object-Oriented Design**
- `BVHRetargeter` - Main conversion class with modular methods
- `SMPLHMapping` - Joint mapping configuration with static methods
- Professional error handling and logging throughout

### **Key Classes & Methods**
```python
# Main conversion
retargeter = BVHRetargeter()
success = retargeter.convert(input_bvh, output_npz)

# Joint mapping verification  
SMPLHMapping.get_joint_mapping()    # Get full 52-joint mapping
SMPLHMapping.get_unmapped_joints()  # Get unmapped joints

# BVH utilities
parse_bvh_file(bvh_path)           # Parse BVH with error handling
extract_joint_rotations_proper()   # Extract rotations with ZXY handling
```

## Quality Metrics

- **Joint Coverage**: 49/52 SMPL-H joints mapped (excellent coverage)
- **Motion Quality**: Natural full-body movement with comprehensive finger articulation
- **Frame Rate Support**: Variable fps support (commonly 60-120 fps)
- **Rotation Accuracy**: Proper ZXY Euler angle conversion prevents motion artifacts
- **Error Handling**: Comprehensive validation and logging for robust operation

## Troubleshooting

### **Common Issues**

1. **MuJoCo API Error** (`'MjsJoint' object has no attribute 'delete'`)
   ```bash
   pip install mujoco==3.2.7 mujoco-mjx==3.2.7
   ```

2. **File Not Found** - Use absolute paths or check file locations:
   ```bash
   python mocap_retarget.py --verify  # Check joint mapping
   python test_proper_motion_only.py --list  # Check available motions
   ```

3. **Invalid BVH Format** - Test BVH structure:
   ```bash
   python proper_bvh_retargeting.py your_file.bvh --verbose
   ```

## Development

### **Code Quality**
- Type hints throughout
- Comprehensive docstrings  
- Professional logging
- Error handling with specific exceptions
- Modular, testable functions

### **Testing**
```bash
# Test conversion
python mocap_retarget.py --verify

# Test BVH parsing
python proper_bvh_retargeting.py ../Mocap/test.bvh

# Test motion viewing
python test_proper_motion_only.py --list
```