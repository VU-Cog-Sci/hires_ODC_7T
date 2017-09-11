from fmriprep.workflows import base
import os
from niworkflows.nipype.pipeline import engine as pe
from fmriprep.interfaces import BIDSFreeSurferDir



os.environ['SUBJECTS_DIR'] = '/data/freesurfer'

skull_strip_ants = True
output_spaces = ['T1w', 'template', 'fsnative']
template = 'MNI152NLin2009cAsym'
debug = False
freesurfer = False
longitudinal = False
omp_nthreads = 10
hires = True
reportlets_dir = '/data/reportlets/anat'
output_dir = '/data/derivatives/preproc_anat'
output_spaces = ['T1w', 'template']

fsdir = pe.Node(BIDSFreeSurferDir(derivatives=output_dir,
                                  freesurfer_home=os.getenv('FREESURFER_HOME'),
                                  spaces=output_spaces),
                        name='fsdir', run_without_submitting=True)

wf = base.init_single_subject_wf(subject_id='012',
                                 task_id='binoculardots055',
                                 name='anatomical_wf',
                                 ignore=[],
                                 debug=False,
                                 anat_only=True,
                                 longitudinal=False,
                                 skull_strip_ants=skull_strip_ants,
                                 reportlets_dir='/data/reportlets/anat',
                                 output_dir=output_dir,
                                 bids_dir='/data/sourcedata/',
                                 freesurfer=freesurfer,
                                 output_spaces=output_spaces,
                                 hires=True,
                                 bold2t1w_dof=12,
                                 fmap_bspline=False,
                                 fmap_demean=False,
                                 use_syn=False,
                                 force_syn=False,
                                 output_grid_ref=None,
                                 use_aroma=False,
                                 ignore_aroma_err=True,
                                 omp_nthreads=4,
                                 template='MNI152NLin2009cAsym')

wf.connect(fsdir, 'subjects_dir', wf.get_node('inputnode'), 'subjects_dir')


wf.base_dir = '/data/workflow_folders/'

plugin_settings = {}
plugin_settings['plugin'] = 'MultiProc'
plugin_settings['plugin_args'] = {'n_procs': 10}

plugin_settings['plugin'] = 'Linear'


wf.write_graph()
wf.run(**plugin_settings)
