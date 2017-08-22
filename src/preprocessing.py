# from nipype import config
# config.enable_debug_mode()
# Importing necessary packages
import os
import sys
import os.path as op
import glob
import json
import nipype
from nipype import config, logging
import matplotlib.pyplot as plt
import nipype.interfaces.fsl as fsl
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nibabel as nib
from nipype.interfaces.utility import Function, Merge, IdentityInterface
from nipype.interfaces.io import SelectFiles, DataSink

from workflows.hires_workflow import create_hires_workflow
from IPython import embed as shell

# the subject id is a commandline arguments to this script.
sub_id = str(sys.argv[1])
# the experiment variable is given here.
# experiment = 'nprf'
experiment = str(sys.argv[2])

# from nPRF.parameters import *
# execfile('nPRF/parameters.py')
exec(open("parameters.py").read())

# we set up the folders and logging there.
if not op.isdir(preprocessed_data_dir):
    try:
        os.makedirs(preprocessed_data_dir)
    except OSError:
        pass

try:
    os.makedirs(op.join(opd, 'log'))
except OSError:
    pass

config.update_config({'logging': {
    'log_directory': op.join(opd, 'log'),
    'log_to_file': True,
    'workflow_level': 'INFO',
    'interface_level': 'DEBUG'
},
    'execution': {
    'stop_on_first_crash': True
}
})
logging.update_logging(config)

# the actual workflow
hires_workflow = create_hires_workflow(analysis_info, name='hires')

# standard output variables
hires_workflow.inputs.inputspec.raw_directory = raw_data_dir
hires_workflow.inputs.inputspec.sub_id = sub_id
hires_workflow.inputs.inputspec.output_directory = opd
hires_workflow.base_dir = '/tmp/hires/' + experiment

# the config file for topup
hires_workflow.inputs.inputspec.topup_conf_file = op.join(
    os.environ['FSL_DIR'], 'etc/flirtsch/b02b0.cnf')

# to what file do we motion correct?
# if not 'all' in experiment:     # motion correct other experiments to 'all_B0',
#                                 # so we overwrite analysis_info['which_file_is_EPI_space']
#     basic_preprocessed_directory = os.path.split(preprocessed_data_dir)[0]
#     example_func_path = os.path.join(basic_preprocessed_directory, 'all_B0', sub_id, 'reg', 'example_func.nii.gz')
#     analysis_info['which_file_is_EPI_space'] = example_func_path

hires_workflow.inputs.inputspec.which_file_is_EPI_space = analysis_info[
    'which_file_is_EPI_space']

# registration details
hires_workflow.inputs.inputspec.FS_ID = sub_id
hires_workflow.inputs.inputspec.FS_subject_dir = FS_subject_dir
hires_workflow.inputs.inputspec.standard_file = op.join(
    os.environ['FSL_DIR'], 'data/standard/MNI152_T1_1mm_brain.nii.gz')

# percent signal change and average-across-runs settings
hires_workflow.inputs.inputspec.psc_func = analysis_info['psc_func']
hires_workflow.inputs.inputspec.av_func = analysis_info['av_across_runs_func']

hires_workflow.inputs.inputspec.exp = experiment


# all the input variables for retroicor functionality
# the key 'retroicor_order_or_timing' determines whether slice timing
# or order is used for regressor creation
# hires_workflow.inputs.inputspec.MB_factor = acquisition_parameters['MultiBandFactor']
hires_workflow.inputs.inputspec.nr_dummies = acquisition_parameters['NumberDummyScans']
hires_workflow.inputs.inputspec.tr = acquisition_parameters['RepetitionTime']
hires_workflow.inputs.inputspec.slice_direction = acquisition_parameters['SliceDirection']
hires_workflow.inputs.inputspec.phys_sample_rate = acquisition_parameters['PhysiologySampleRate']
hires_workflow.inputs.inputspec.slice_order = acquisition_parameters['SliceOrder']
hires_workflow.inputs.inputspec.acceleration = acquisition_parameters['SenseFactor']
hires_workflow.inputs.inputspec.epi_factor = acquisition_parameters['EpiFactor']
hires_workflow.inputs.inputspec.wfs = acquisition_parameters['WaterFatShift']
hires_workflow.inputs.inputspec.te_diff = acquisition_parameters['EchoTimeDifference']


hires_workflow.inputs.inputspec.sg_filter_window_length = analysis_info[
    'sg_filter_window_length']
hires_workflow.inputs.inputspec.sg_filter_order = analysis_info['sg_filter_order']

# hires_workflow.inputs.inputspec.bd_design_matrix_file = op.join(
#     raw_data_dir, 'blockdesign_GLM_designmatrix.tsv')

# write out the graph and run
hires_workflow.write_graph(opd + '.png')
hires_workflow.run('MultiProc', plugin_args={'n_procs': 24})
