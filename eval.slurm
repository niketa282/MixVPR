#!/bin/bash
#SBATCH --job-name=eval
#SBATCH --partition=a100,swarm_a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=logs/%x_%j.out

source /iridisfs/ixsoftware/conda/miniconda-py3/etc/profile.d/conda.sh
conda activate mixvpr
cd /iridisfs/home/ng3n18/projects/MixVPR

echo "git commit: $(git rev-parse HEAD)"
nvidia-smi

# extra arguments are passed through, e.g. sbatch eval.slurm --conditions none --datasets pitts30k_test
python eval.py "$@"
