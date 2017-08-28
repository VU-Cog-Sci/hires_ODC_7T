FROM poldracklab/fmriprep

RUN apt-get update  \
    && apt-get install -yq --no-install-recommends zsh wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

RUN useradd -g root --create-home --shell /bin/bash neuro \
    && usermod -aG sudo neuro \
    && chmod -R 775 /usr/local/miniconda
USER neuro
WORKDIR /home/neuro

RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true && \
 echo TERM=xterm >> /home/neuro/.zshrc

RUN pip install -q --no-cache-dir \
    https://github.com/spinoza-centre/spynoza/archive/7t_hires.zip

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
