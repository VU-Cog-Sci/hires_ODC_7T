from spynoza.registration.workflows import create_epi_to_T1_workflow
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.interfaces import fsl


init_reg_file = '/data/derivatives/manual_transforms/sub-012_epi_bold-to-T1w.lta'

wf = create_epi_to_T1_workflow(init_reg_file=init_reg_file,
                               use_FS=False,
                               do_FAST=False,
                               apply_transform=True)
wf.base_dir = '/data/workflow_folders'

wf.inputs.inputspec.T1_file = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
wf.inputs.inputspec.EPI_space_file = '/data/derivatives/topup/sub-012/func/sub-012_task-binoculardots070_run-1_bold_unwarped.nii.gz'

get_wm_seg = pe.Node(fsl.Threshold(thresh=3), name='get_wm_seg')
get_wm_seg.inputs.in_file = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_dtissue.nii.gz'

wf.connect(get_wm_seg, 'out_file', wf.get_node('inputspec'), 'wm_seg_file')
ds = pe.Node(nio.DataSink(base_directory='/data/derivatives/epi2T1'), 'datasink')

wf.connect(wf.get_node('outputspec'), 'EPI_T1_matrix_file', ds, 'EPI_T1_matrix_file')
wf.connect(wf.get_node('outputspec'), 'T1_EPI_matrix_file', ds, 'T1_EPI_matrix_file')
wf.connect(wf.get_node('outputspec'), 'transformed_EPI_space_file', ds, 'transformed_EPI')

wf.get_node('flirt_e2t').inputs.searchr_x = [-5, 5]
wf.get_node('flirt_e2t').inputs.searchr_y = [-5, 5]
wf.get_node('flirt_e2t').inputs.searchr_z = [-5, 5]
wf.get_node('flirt_e2t').inputs.dof = 6

plugin_settings = {}
plugin_settings['plugin'] = 'MultiProc'
plugin_settings['plugin_args'] = {'n_procs': 4}

#wf.write_graph()
wf.run(**plugin_settings)
