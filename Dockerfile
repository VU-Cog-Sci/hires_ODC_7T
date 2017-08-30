FROM poldracklab/fmriprep

RUN apt-get update  \
    && apt-get install -yq --no-install-recommends zsh wget vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

RUN useradd -g root --create-home --shell /bin/bash neuro \
    && usermod -aG sudo neuro \
    && chmod -R 775 /usr/local/miniconda

RUN apt-get update \
    && apt-get install -y python python-pip python-dev build-essential software-properties-common \
    && add-apt-repository ppa:openjdk-r/ppa && apt-get update -qq && apt-get install -y openjdk-8-jdk \ 
    && pip install --allow-all-external --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nighres

USER neuro
WORKDIR /home/neuro

RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true && \
 echo TERM=xterm >> /home/neuro/.zshrc

RUN conda install -c conda-forge \
     --quiet --yes \
    'notebook=5.0.*' \
    'jupyterhub=0.7.*' \
    'jupyterlab=0.27.*' \
    && conda clean -tipsy

COPY jupyter_notebook_config.py /etc/jupyter/

EXPOSE 8888

ENTRYPOINT ["/bin/zsh"]  

COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/

COPY spynoza/ /home/neuro/spynoza
RUN cd /home/neuro/spynoza && \
    pip install . && \
    rm -rf ~/.cache/pip
    
COPY nipype.cfg /home/neuro/.nipype
ENV MIPAV=/home/neuro/mipav
RUN mkdir $MIPAV \
    && curl -sSL 'https://www.dropbox.com/s/fc9tt7rp19wy0hx/mipav.tar.gz' \
    | tar -xzC $MIPAV --strip-components 1

ENV JAVALIB=$MIPAV/jre/lib/ext
ENV PLUGINS=$MIPAV/plugins
ENV CLASSPATH=$JAVALIB/*:$MIPAV:$MIPAV/lib/*:$PLUGINS



