# hires_ODC_7T

This is a repository for a High-resolution 7T study in the Knapen lab (https://tknapen.github.io/).

All the analysis in this repository can (should) be run using the included Docker image.


To run the docker image, do the following:
 * First, clone this repository:

```
git clone https://github.com/VU-Cog-Sci/hires_ODC_7T
```
<br>
 * Build the Docker image (this will take a while, but has to be done only once):
```
docker build . -t "knapenlab/hiresbinocularrivalry"
```

* You now can run the Docker, it is important that you specify the path where the relevant
data can be found: 

```
export DATA_PATH="/path/to/the/data"
```

<br>
* There are multiple ways to run the docker. By default, the image starts a Jupyter Notebook server:
```
docker run -it -v DATA_PATH:/data knapenlab/hiresbinocularrivalry
```
  * Another option is to start a (z)shell and peek around yourself
```
docker run -it -v DATA_PATH:/data knapenlab/hiresbinocularrivalry zsh
```
  * Lastly, an experimental feature is to stary jupyter-lab
```
docker run -it -v DATA_PATH:/data knapenlab/hiresbinocularrivalry jupyter-lab
```

###Analysis of hires fMRI project

T
