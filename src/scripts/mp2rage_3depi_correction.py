from spynoza.unwarping.mp2rage_3depi.workflows import create_3DEPI_registration_workflow

wf = create_3DEPI_registration_workflow()
wf.base_dir = '/tmp'

wf.inputs.inputnode.INV2 = '/data/sourcedata/sub-012/anat/sub-012_acq-3DEPI_INV2.nii'
wf.inputs.inputnode.T1_EPI_file = '/data/sourcedata/sub-012/anat/sub-012_acq-3DEPI_T1w.nii'
wf.inputs.inputnode.T1_file = '/data/sourcedata/sub-012/anat/sub-012_acq-highres_T1w.nii.gz'

wf.run()
