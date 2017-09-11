from spynoza.unwarping.mp2rage_3depi.workflows import create_3DEPI_registration_workflow
import nipype.pipeline.engine as pe
from spynoza.io.bids import DerivativesDataSink


init_reg_file = '/data/derivatives/manual_transforms/sub-012_from-3DEPI_to-highres_ras.lta'

wf = create_3DEPI_registration_workflow(init_reg_file=init_reg_file)
wf.base_dir = '/data/workflow_folders'

wf.inputs.inputnode.INV2 = '/data/derivatives/reorient/sub-012/anat/sub-012_acq-3DEPI_INV2_ras.nii.gz'
wf.inputs.inputnode.T1w_EPI_file = '/data/derivatives/reorient/sub-012/anat/sub-012_acq-3DEPI_T1w_ras.nii.gz'
wf.inputs.inputnode.T1w_file = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
wf.inputs.inputnode.bold_EPIs = ['/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-1_bold.nii.gz',
                                 '/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-2_bold.nii.gz',
                                 '/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-3_bold.nii.gz',]
                                 #'/data/sourcedata/sub-012/func/sub-012_task-binoculardots070_run-1_bold.nii.gz']

ds_epi2t1w_epi_warped = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1.3depi',
                                          suffix='epi2t1w_epi'),
                              iterfield=['source_file', 'in_file'],
                      name='ds_epi2t1w_epi_warped')

ds_epi2t1_warped = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1.3depi',
                                          suffix='epi2t1'),
                              iterfield=['source_file', 'in_file'],
                      name='ds_epi2t1_warped')

ds_epi_t1w2t1w_warped = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/epi_to_T1.3depi',
                                          suffix='t1w_epi2t1'),
                      name='ds_epi_t1w2t1w_warped')

wf.connect(wf.get_node('outputnode'), 'T1w_epi_to_T1w_transformed', ds_epi_t1w2t1w_warped, 'in_file')
wf.connect(wf.get_node('outputnode'), 'bold_epi_to_T1w_transformed', ds_epi2t1_warped, 'in_file')
wf.connect(wf.get_node('outputnode'), 'bold_epi_to_T1w_epi_transformed', ds_epi2t1w_epi_warped, 'in_file')

wf.connect(wf.get_node('inputnode'), 'bold_EPIs', ds_epi2t1_warped, 'source_file')
wf.connect(wf.get_node('inputnode'), 'T1w_EPI_file', ds_epi_t1w2t1w_warped, 'source_file')
wf.connect(wf.get_node('inputnode'), 'bold_EPIs', ds_epi2t1w_epi_warped, 'source_file')

wf.inputs.register_t1wepi_to_t1w.num_threads = 8

wf.run(plugin='MultiProc', plugin_args={'n_procs':8})
