# Generated by Neurodocker v0.3.0-dev0.
#
# Thank you for using Neurodocker. If you discover any issues 
# or ways to improve this software, please submit an issue or 
# pull request on our GitHub repository:
#     https://github.com/kaczmarj/neurodocker
#
# Timestamp: 2017-08-25 13:47:29

FROM ubuntu:xenial-20161213

ARG DEBIAN_FRONTEND=noninteractive

#----------------------------------------------------------
# Install common dependencies and create default entrypoint
#----------------------------------------------------------
ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN apt-get update -qq && apt-get install -yq --no-install-recommends  \
    	bzip2 ca-certificates curl unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> $ND_ENTRYPOINT \
         && echo 'set +x' >> $ND_ENTRYPOINT \
         && echo 'if [ -z "$*" ]; then /usr/bin/env bash; else $*; fi' >> $ND_ENTRYPOINT; \
       fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker
ENTRYPOINT ["/neurodocker/startup.sh"]

RUN apt-get update -qq && apt-get install -yq --no-install-recommends git vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#--------------------
# Install AFNI latest
#--------------------
ENV PATH=/opt/afni:$PATH
RUN apt-get update -qq && apt-get install -yq --no-install-recommends ed gsl-bin libglu1-mesa-dev libglib2.0-0 libglw1-mesa \
    libgomp1 libjpeg62 libxm4 netpbm tcsh xfonts-base xvfb \
    && libs_path=/usr/lib/x86_64-linux-gnu \
    && if [ -f $libs_path/libgsl.so.19 ]; then \
           ln $libs_path/libgsl.so.19 $libs_path/libgsl.so.0; \
       fi \
    # Install libxp (not in all ubuntu/debian repositories) \
    && apt-get install -yq --no-install-recommends libxp6 \
    || /bin/bash -c " \
       curl --retry 5 -o /tmp/libxp6.deb -sSL http://mirrors.kernel.org/debian/pool/main/libx/libxp/libxp6_1.0.2-2_amd64.deb \
       && dpkg -i /tmp/libxp6.deb && rm -f /tmp/libxp6.deb" \
    # Install libpng12 (not in all ubuntu/debian repositories) \
    && apt-get install -yq --no-install-recommends libpng12-0 \
    || /bin/bash -c " \
       curl -o /tmp/libpng12.deb -sSL http://mirrors.kernel.org/debian/pool/main/libp/libpng/libpng12-0_1.2.49-1%2Bdeb7u2_amd64.deb \
       && dpkg -i /tmp/libpng12.deb && rm -f /tmp/libpng12.deb" \
    # Install R \
    && apt-get install -yq --no-install-recommends \
    	r-base-dev r-cran-rmpi \
     || /bin/bash -c " \
        curl -o /tmp/install_R.sh -sSL https://gist.githubusercontent.com/kaczmarj/8e3792ae1af70b03788163c44f453b43/raw/0577c62e4771236adf0191c826a25249eb69a130/R_installer_debian_ubuntu.sh \
        && /bin/bash /tmp/install_R.sh" \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && echo "Downloading AFNI ..." \
    && mkdir -p /opt/afni \
    && curl -sSL --retry 5 https://afni.nimh.nih.gov/pub/dist/tgz/linux_openmp_64.tgz \
    | tar zx -C /opt/afni --strip-components=1 \
    && /opt/afni/rPkgsInstall -pkgs ALL \
    && rm -rf /tmp/*

#-------------------
# Install ANTs 2.2.0
#-------------------
RUN echo "Downloading ANTs ..." \
    && curl -sSL --retry 5 https://dl.dropbox.com/s/2f4sui1z6lcgyek/ANTs-Linux-centos5_x86_64-v2.2.0-0740f91.tar.gz \
    | tar zx -C /opt
ENV ANTSPATH=/opt/ants \
    PATH=/opt/ants:$PATH

#--------------------------
# Install FreeSurfer v6.0.0
#--------------------------
RUN apt-get update -qq && apt-get install -yq --no-install-recommends bc libgomp1 libxmu6 libxt6 tcsh perl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && echo "Downloading FreeSurfer ..." \
    && curl -sSL --retry 5 https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.0/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.0.tar.gz \
    | tar xz -C /opt \
    --exclude='freesurfer/trctrain' \
    --exclude='freesurfer/subjects/fsaverage_sym' \
    --exclude='freesurfer/subjects/fsaverage3' \
    --exclude='freesurfer/subjects/fsaverage4' \
    --exclude='freesurfer/subjects/fsaverage5' \
    --exclude='freesurfer/subjects/fsaverage6' \
    --exclude='freesurfer/subjects/cvs_avg35' \
    --exclude='freesurfer/subjects/cvs_avg35_inMNI152' \
    --exclude='freesurfer/subjects/bert' \
    --exclude='freesurfer/subjects/V1_average' \
    --exclude='freesurfer/average/mult-comp-cor' \
    --exclude='freesurfer/lib/cuda' \
    --exclude='freesurfer/lib/qt' \
    && sed -i '$isource $FREESURFER_HOME/SetUpFreeSurfer.sh' $ND_ENTRYPOINT
ENV FREESURFER_HOME=/opt/freesurfer

#-----------------------------------------------------------
# Install FSL v5.0.10
# FSL is non-free. If you are considering commerical use
# of this Docker image, please consult the relevant license:
# https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Licence
#-----------------------------------------------------------
RUN echo "Downloading FSL ..." \
    && curl -sSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-5.0.10-centos6_64.tar.gz \
    | tar zx -C /opt \
    && /bin/bash /opt/fsl/etc/fslconf/fslpython_install.sh -q -f /opt/fsl \
    && sed -i '$iecho Some packages in this Docker container are non-free' $ND_ENTRYPOINT \
    && sed -i '$iecho If you are considering commercial use of this container, please consult the relevant license:' $ND_ENTRYPOINT \
    && sed -i '$iecho https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Licence' $ND_ENTRYPOINT \
    && sed -i '$isource $FSLDIR/etc/fslconf/fsl.sh' $ND_ENTRYPOINT
ENV FSLDIR=/opt/fsl \
    PATH=/opt/fsl/bin:$PATH

# Create new user: neuro
RUN useradd --no-user-group --create-home --shell /bin/bash neuro
USER neuro

USER root

#----------------
# Install MRtrix3
#----------------
RUN echo "Downloading MRtrix3 ..." \
    && curl -sSL --retry 5 https://dl.dropbox.com/s/2g008aaaeht3m45/mrtrix3-Linux-centos6.tar.gz \
    | tar zx -C /opt
ENV PATH=/opt/mrtrix3/bin:$PATH

#--------------------------------------------------
# Add NeuroDebian repository
# Please note that some packages downloaded through
# NeuroDebian may have restrictive licenses.
#--------------------------------------------------
RUN apt-get update -qq && apt-get install -yq --no-install-recommends dirmngr gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && curl -sSL http://neuro.debian.net/lists/jessie.us-nh.full \
    > /etc/apt/sources.list.d/neurodebian.sources.list \
    && curl -sSL https://dl.dropbox.com/s/zxs209o955q6vkg/neurodebian.gpg \
    | apt-key add - \
    && (apt-key adv --refresh-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9 || true) \
    && apt-get update

# Install NeuroDebian packages
RUN apt-get update -qq && apt-get install -yq --no-install-recommends dcm2niix git-annex-standalone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER neuro

#------------------
# Install Miniconda
#------------------
ENV CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH
RUN echo "Downloading Miniconda installer ..." \
    && miniconda_installer=/tmp/miniconda.sh \
    && curl -sSL -o $miniconda_installer https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && /bin/bash $miniconda_installer -f -b -p $CONDA_DIR \
    && rm -f $miniconda_installer \
    && conda config --system --prepend channels conda-forge \
    && conda config --system --set auto_update_conda false \
    && conda config --system --set show_channel_urls true \
    && conda update -y -q --all && sync \
    && conda clean -tipsy && sync

#-------------------------
# Create conda environment
#-------------------------
RUN conda create -y -q --name default --channel vida-nyu python=3.5.1 \
    	numpy scipy matplotlib pandas reprozip traits jupyter \
    && sync && conda clean -tipsy && sync \
    && /bin/bash -c "source activate default \
    	&& pip install -q --no-cache-dir \
    	nipype" \
    && sync
ENV PATH=/opt/conda/envs/default/bin:$PATH

#-------------------------
# Create conda environment
#-------------------------
RUN conda create -y -q --name py27 python=2.7 \
    && sync && conda clean -tipsy && sync

EXPOSE 8888

USER root

# User-defined instruction
RUN apt-get update &&  	    apt-get install -y zsh wget

# User-defined instruction
RUN apt-get install -y npm nodejs-legacy &&  	    rm -rf /tmp/* /etc/apk/cache/*

# User-defined instruction
RUN npm install -g configurable-http-proxy

USER neuro

# User-defined instruction
ENV SHELL /bin/zsh

WORKDIR /home/neuro

ENV NB_USER neuro
ENV HOME /home/$NB_USER

USER root

# Install Tini
RUN wget --quiet https://github.com/krallin/tini/releases/download/v0.10.0/tini && \
    echo "1361527f39190a7338a0b434bd8c88ff7233ce7b9a4876f3315c22fce7eca1b0 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini


WORKDIR /home/$NB_USER

RUN conda install --quiet --yes \
    'notebook=5.0.*' \
    'jupyterhub=0.7.*' \
    'jupyterlab=0.24.*' \
    && conda clean -tipsy

RUN pip install -q --no-cache-dir \
    sklearn nilearn pybids fmriprep

# Configure container startup
# ENTRYPOINT ["tini", "--"]*
CMD ["start-notebook.sh"]

# Add local files as late as possible to avoid cache busting
COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /etc/jupyter/

RUN chown -R $NB_USER:users /etc/jupyter/

USER $NB_USER

#COPY notebooks $HOME/notebooks
#COPY src $HOME/src

COPY license.txt /opt/freesurfer

USER root
RUN mkdir /data && chown -R $NB_USER:users /data
RUN chown -R $NB_USER:users $HOME
USER $NB_USER

ENV FSLOUTPUTTYPE NIFTI_GZ
COPY nipype.cfg /home/neuro/.nipype
RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
RUN echo TERM=xterm >> /home/neuro/.zshrc

RUN pip install -q --no-cache-dir \
    https://github.com/spinoza-centre/spynoza/archive/7t_hires.zip
