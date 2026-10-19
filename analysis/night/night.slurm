#!/bin/bash
#SBATCH --job-name=night_tt
#SBATCH --partition=a100,swarm_a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out

# Test-time interventions on existing checkpoints (no training). Does not modify eval.py / main.py.
source /iridisfs/ixsoftware/conda/miniconda-py3/etc/profile.d/conda.sh
conda activate mixvpr
cd /iridisfs/home/ng3n18/projects/MixVPR

echo "git commit: $(git rev-parse HEAD)"
python analysis/night/test_time.py --input rgb  --conditions none
python analysis/night/test_time.py --input gray --conditions none
