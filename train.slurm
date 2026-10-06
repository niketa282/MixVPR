#!/bin/bash
#SBATCH --job-name=mixvpr
#SBATCH --partition=a100,swarm_a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=16:00:00
#SBATCH --output=logs/%x_%j.out

source /iridisfs/ixsoftware/conda/miniconda-py3/etc/profile.d/conda.sh
conda activate mixvpr
cd /iridisfs/home/ng3n18/projects/MixVPR

nvidia-smi
python main.py --geo_aug ${1:-none}
