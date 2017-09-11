from spynoza.registration.workflows import create_epi_to_T1_workflow
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.interfaces import fsl
from spynoza.io.bids import DerivativesDataSink

import os

for package in ['fsl', 'afni']:

    identity = pe.Node(niu.IdentityInterface(fields=['subject']), name='identity')
    identity.iterables = [('subject', ['012'])]

    templates = {'EPI_space_file':'/data/derivatives/topup.%s/sub-{subject}/func/sub-{subject}_task-{task}_run-{run}_bold_unwarped.nii.gz' % package,
                 'T1':'/data/derivatives/preproc_anat/fmriprep/sub-{subject}/anat/sub-{subject}_acq-highres_T1w_preproc.nii.gz',
                 'wm_seg_file':'/data/derivatives/preproc_anat/fmriprep/sub-{subject}/anat/sub-{subject}_acq-highres_T1w_dtissue.nii.gz',
                 'manual_transform':'/data/derivatives/manual_transforms/sub-{subject}_task-{task}_run-{run}_to_T1w_preproc.lta'}

    selector = pe.Node(nio.SelectFiles(templates), name='selector')
    selector.iterables = [('run', [1,2,3,4, 5]), ('task', ['binoculardots055', 'binoculardots070'])]

    init_reg_file = '/data/derivatives/manual_transforms/sub-012_task-binoculardots055_run-1_to_T1w_preproc.lta'
    wf = create_epi_to_T1_workflow(init_reg_file=init_reg_file, package='ants', apply_transform=True, parameter_file='linear_hires.json', do_FAST=False, do_BET=False, name='epi2t1_%s' % package)
    wf.base_dir = '/tmp/'


    wf.connect(identity, 'subject', selector, 'subject')
    wf.connect(selector, 'EPI_space_file', wf.get_node('inputspec'), 'EPI_space_file')
    wf.connect(selector, 'T1', wf.get_node('inputspec'), 'T1_file')
    wf.connect(selector, 'manual_transform', wf.get_node('convert_to_itk'), 'in_lta')
    #wf.connect(selector, 'manual_transform', wf.get_node('convert_init_reg_to_fsl'), 'in_lta')
    #threshold = pe.Node(fsl.Threshold(thresh=3), name='threshold')
    #wf.connect(selector, 'wm_seg_file', threshold, 'in_file')
    #wf.connect(threshold, 'out_file', wf.get_node('inputspec'), 'wm_seg_file')

    ds_epi2t1_mat = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1',
                                              suffix='epi2t1'),
                          name='ds_epi2t1_mat')
    wf.connect(wf.get_node('outputspec'), 'EPI_T1_matrix_file', ds_epi2t1_mat, 'in_file')
    wf.connect(selector, 'EPI_space_file', ds_epi2t1_mat, 'source_file')

    ds_epi2t1_warped = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1.%s' % package,
                                              suffix='epi2t1'),
                          name='ds_epi2t1_warped')
    wf.connect(wf.get_node('outputspec'), 'transformed_EPI_space_file', ds_epi2t1_warped, 'in_file')
    wf.connect(selector, 'EPI_space_file', ds_epi2t1_warped, 'source_file')

    try:
        wf.run(plugin='MultiProc', plugin_args={'n_procs':8})
    except Exception as e:
        pass
