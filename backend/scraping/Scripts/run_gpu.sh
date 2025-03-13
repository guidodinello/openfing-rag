#!/bin/bash
#SBATCH --job-name=transcribe
#SBATCH --ntasks=1
#SBATCH --mem=4096
#SBATCH --time=04:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=guido.dinello@gmail.com

#SBATCH --gres=gpu:1

#SBATCH --partition=normal
#SBATCH --qos=gpu

#https://www.cluster.uy/ayuda/como_ejecutar/#trabajo-normal-con-gpu

cd ~/ProyectoDeGrado/Scripts
conda activate
python Main.py


