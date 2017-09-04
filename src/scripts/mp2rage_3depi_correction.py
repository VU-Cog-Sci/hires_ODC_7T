from spynoza.unwarping.mp2rage_3depi.workflows import create_3DEPI_registration_workflow


init_reg_file = '/data/derivatives/manual_transforms/sub-012_from-3DEPI_to-highres_ras.lta'

wf = create_3DEPI_registration_workflow(init_reg_file=init_reg_file)
wf.base_dir = '/tmp'

wf.inputs.inputnode.INV2 = '/data/derivatives/reorient/sub-012/anat/sub-012_acq-3DEPI_INV2_ras.nii.gz'
wf.inputs.inputnode.T1w_EPI_file = '/data/derivatives/reorient/sub-012/anat/sub-012_acq-3DEPI_T1w_ras.nii.gz'
wf.inputs.inputnode.T1w_file = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
wf.inputs.inputnode.bold_EPIs = ['/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-1_bold.nii.gz',
                                 '/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-2_bold.nii.gz',
                                 '/data/sourcedata/sub-012/func/sub-012_task-binoculardots055_run-3_bold.nii.gz']

wf.run()
