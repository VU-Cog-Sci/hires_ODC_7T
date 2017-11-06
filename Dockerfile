FROM poldracklab/fmriprep

RUN apt-get update  \
    && apt-get install -yq --no-install-recommends zsh wget vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

RUN useradd -g root --create-home --shell /bin/bash neuro \
    && usermod -aG sudo neuro \
    && usermod -aG users neuro \
    && chmod -R 775 /usr/local/miniconda \
    && chown -R neuro:users /niworkflows_data

RUN apt-get update \
    && apt-get install -y python python-pip python-dev build-essential software-properties-common \
    && add-apt-repository ppa:openjdk-r/ppa && apt-get update -qq && apt-get install -y openjdk-8-jdk 

RUN ln -svT "/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)" /docker-java-home
ENV JAVA_HOME /docker-java-home
ENV JCC_JDK /docker-java-home

RUN conda install python=2.7

RUN pip install --upgrade wheel JCC twine urllib3 pip
RUN cd /home/neuro && git clone https://github.com/nighres/nighres && cd nighres && ./build.sh && pip install .

RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true && \
 echo TERM=xterm >> /home/neuro/.zshrc

RUN conda install -c conda-forge \
     --quiet --yes \
    'notebook' \
    && conda clean -tipsy

COPY jupyter_notebook_config.py /etc/jupyter/

EXPOSE 8888

ENTRYPOINT ["/bin/zsh"]  

USER root
RUN rm -rf $ANTSPATH/* \
    && curl -sSL "https://dl.dropbox.com/s/f3rvpefq9oq65ki/ants.tar.gz" \
    | tar -xzC $ANTSPATH --strip-components 2

COPY nipype/ /home/neuro/nipype

RUN pip install -e /home/neuro/nipype && \
    pip install bottleneck && \
    rm -rf ~/.cache/pip

COPY nipype.cfg /home/neuro/.nipype

RUN pip install nilearn git+https://github.com/INCF/pybids

RUN touch test.py

COPY spynoza/ /home/neuro/spynoza
RUN cd /home/neuro/spynoza && \
    pip install -e . && \
    rm -rf ~/.cache/pip
    
USER neuro

