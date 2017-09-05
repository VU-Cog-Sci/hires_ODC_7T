from spynoza.registration.workflows import create_epi_to_T1_workflow
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from spynoza.io.bids import DerivativesDataSink

import os
identity = pe.Node(niu.IdentityInterface(fields=['subject']), name='identity')
identity.iterables = [('subject', ['012'])]

templates = {'EPI_space_file':'/data/derivatives/topup/sub-{subject}/func/sub-{subject}_task-{task}_run-{run}_bold_unwarped.nii.gz',
             'T1':'/data/derivatives/preproc_anat/fmriprep/sub-{subject}/anat/sub-{subject}_acq-highres_T1w_preproc.nii.gz',
             'manual_transform':'/data/derivatives/manual_transforms/sub-{subject}_task-{task}_run-{run}_to_T1w_preproc.lta'}

selector = pe.Node(nio.SelectFiles(templates), name='selector')
selector.iterables = [('run', [1,2,3,4, 5]), ('task', ['binoculardots055', 'binoculardots070'][:2])]

init_reg_file = '/data/derivatives/manual_transforms/sub-012_task-binoculardots055_run-1_to_T1w_preproc.lta'
wf = create_epi_to_T1_workflow(init_reg_file=init_reg_file, package='ants', apply_transform=True)
wf.base_dir = '/tmp/'

wf.connect(identity, 'subject', selector, 'subject')
wf.connect(selector, 'EPI_space_file', wf.get_node('inputspec'), 'EPI_space_file')
wf.connect(selector, 'T1', wf.get_node('inputspec'), 'T1_file')
wf.connect(selector, 'manual_transform', wf.get_node('convert_to_itk'), 'in_lta')

ds_epi2t1_mat = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1',
                                          suffix='epi2t1'),
                      name='ds_epi2t1_mat')
wf.connect(wf.get_node('outputspec'), 'EPI_T1_matrix_file', ds_epi2t1_mat, 'in_file')
wf.connect(selector, 'EPI_space_file', ds_epi2t1_mat, 'source_file')

ds_epi2t1_warped = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1',
                                          suffix='epi2t1'),
                      name='ds_epi2t1_warped')
wf.connect(wf.get_node('outputspec'), 'transformed_EPI_space_file', ds_epi2t1_warped, 'in_file')
wf.connect(selector, 'EPI_space_file', ds_epi2t1_warped, 'source_file')

ds = pe.Node(nio.DataSink(base_directory='/data/derivatives/epi_to_T1'), 'datasink')

wf.connect(wf.get_node('outputspec'), 'EPI_T1_register_file', ds, 'EPI_T1_register_file')
wf.connect(wf.get_node('outputspec'), 'EPI_T1_matrix_file', ds, 'EPI_T1_matrix_file')
wf.connect(wf.get_node('outputspec'), 'T1_EPI_matrix_file', ds, 'T1_EPI_matrix_file')
wf.connect(wf.get_node('outputspec'), 'transformed_EPI_space_file', ds, 'warped_EPI_file')
wf.run()
