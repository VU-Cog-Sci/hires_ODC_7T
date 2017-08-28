from spynoza.registration.workflows import create_epi_to_T1_workflow
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio

import os
os.environ['SUBJECTS_DIR'] = '/data/freesurfer'

identity = pe.Node(niu.IdentityInterface(fields=['subject']), name='identity')
identity.iterables = [('subject', ['012'])]

templates = {'EPI_space_file':'/data/tests/unwarped_image/_run_{run}_task_{task}/sub-{subject}_task-{task}_run-{run}_bold_masked_mcf_mean_trans.nii.gz',
             'T1':'/data/freesurfer/sub-{subject}/mri/T1.nii.gz'}

selector = pe.Node(nio.SelectFiles(templates), name='selector')
selector.iterables = [('run', [1,2,3,4]), ('task', ['binoculardots055', 'binoculardots070'])]

init_reg_file = '/data/freesurfer/sub-012/sub-012_task-binoculardots070_run-1_to_T1.lta'
wf = create_epi_to_T1_workflow(init_reg_file=init_reg_file, use_FS=True)
wf.base_dir = '/tmp/'

def make_fs_subject_id(subject):
    return 'sub-%s' % subject

wf.connect(identity, 'subject', selector, 'subject')
wf.connect(selector, 'EPI_space_file', wf.get_node('inputspec'), 'EPI_space_file')
wf.connect(selector, 'T1', wf.get_node('inputspec'), 'T1_file')
wf.connect(identity, ('subject', make_fs_subject_id), wf.get_node('inputspec'), 'freesurfer_subject_ID')

wf.inputs.inputspec.freesurfer_subject_dir = '/data/freesurfer'

ds = pe.Node(nio.DataSink(base_directory='/data/derivatives'), 'datasink')

wf.connect(wf.get_node('outputspec'), 'EPI_T1_register_file', ds, 'EPI_T1_register_file')
wf.connect(wf.get_node('outputspec'), 'EPI_T1_matrix_file', ds, 'EPI_T1_matrix_file')
wf.connect(wf.get_node('outputspec'), 'T1_EPI_matrix_file', ds, 'T1_EPI_matrix_file')

wf.run()
