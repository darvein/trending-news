# TODOS

* [ ] Need to find websites, blogs urls with RSS related to coding, devops, software development, ai, crypto, information security


## Tensorflow GPU

```bash
nvidia-smi

# have miniconda installed
source /opt/miniconda3/etc/profile.d/conda.sh 
conda activate tf
conda deactivate

conda install -c conda-forge cudatoolkit=11.8.0
pip install nvidia-cudnn-cu11==8.6.0.163

CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib

mkdir -vp $CONDA_PREFIX/etc/conda/activate.d
CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib' > $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh

pip install --upgrade pip
pip install tensorflow=='2.12.*'

# test
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# for Spacey and topic recognition
pip install spacy
python -m spacy download en_core_web_sm
```

### Intsallation of pymovie
pip uninstall moviepy
pip install git+https://github.com/Zulko/moviepy.git

### PIP
pip has to be:
/opt/miniconda3/bin/pip

## New install
```bash
conda create -n ri python=3.9
conda activate ri

conda install -c conda-forge cudatoolkit=11.8.0
pip install nvidia-cudnn-cu11==8.6.0.163

CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib

mkdir -vp $CONDA_PREFIX/etc/conda/activate.d
CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib' > $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh

pip install --upgrade pip
pip install tensorflow=='2.12.*'

# test
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

```
