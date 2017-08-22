# Ultra-high resolution, laminar 7 T Binocular Rivalry study

This is a repository for a ultra-high-resolution 7T study in the Knapen lab (https://tknapen.github.io/).

All the analysis in this repository can (should) be run using the included Docker image.


# Installation
## Install Docker
You need to install Docker on your MacBook/server/workstation. See [here](https://www.docker.com/get-docker) for instructions

## Install image
To run the docker image, do the following:
 * First, clone this repository:

```
git clone https://github.com/VU-Cog-Sci/hires_ODC_7T
```

 * Then, build the Docker image (this will take a while, but has to be done only once):
```
docker build . -t "knapenlab/hiresbinocularrivalry"
```

## Run image
You now can run the Docker, it is important that you specify the path where the relevant
data can be found: 

```
export DATA_PATH="/path/to/the/data"
```

### Notebook server
 * There are multiple ways to run the docker. By default, the image starts a Jupyter Notebook server:

```
docker run -it -p 8888:8888 -v $DATA_PATH:/data knapenlab/hiresbinocularrivalry
```

When you are developing, it can be useful to link /home/neuro/notebooks and/or /home/neuro/src to folders on the host machine. You can do that as follows:

```
docker run -P -it -v DATA_PATH:/data knapenlab/hiresbinocularrivalry \
                  -v /path/to/notebooks/:/home/neuro/notebooks \
                  -v /path/to/src/:/home/neuro/src
```


You can now open the Jupyter Notebook using your favorite browser (Chrome) with the following URL:
http://localhost:8888/

### Shell

 * Another option is to start a (z)shell and peek around yourself
```
docker run -it -v $DATA_PATH:/data knapenlab/hiresbinocularrivalry zsh
```

### Jupyterhub
In principle, this Docker image can be started using [Jupyterhub](https://github.com/jupyterhub/jupyterhub)
in a similar way as the standard [https://github.com/jupyter/docker-stacks](Docker-stacks).

### Jupyter-lab 
 * Lastly, an experimental feature is to stary jupyter-lab
```
docker run -it -p 8888:8888 -v $DATA_PATH:/data knapenlab/hiresbinocularrivalry jupyter-lab
```
