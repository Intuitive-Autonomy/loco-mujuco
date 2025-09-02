"""
Setup script for BVH to SMPL-H Retargeting Pipeline
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements

# Read long description from README
def read_long_description():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name="bvh2smplh",
    version="1.0.0",
    author="Claude Code Assistant",
    author_email="noreply@anthropic.com",
    description="Professional BVH to SMPL-H retargeting pipeline for LocoMuJoCo",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Intuitive-Autonomy/loco-mujuco",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'bvh2smplh=mocap_retarget:main',
            'bvh-parse=proper_bvh_retargeting:main',
        ],
    },
    keywords="bvh motion-capture smpl-h retargeting mujoco locomotion",
    project_urls={
        "Bug Reports": "https://github.com/Intuitive-Autonomy/loco-mujuco/issues",
        "Source": "https://github.com/Intuitive-Autonomy/loco-mujuco",
        "Documentation": "https://github.com/Intuitive-Autonomy/loco-mujuco/blob/master/BVH2SMPLH/README.md",
    },
)