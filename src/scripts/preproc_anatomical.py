from fmriprep.workflows import base
import os


os.environ['SUBJECTS_DIR'] = '/data/freesurfer'

skull_strip_ants = True
output_spaces = ['T1w', 'template', 'fsnative']
template = 'MNI152NLin2009cAsym'
debug = False
freesurfer = True
longitudinal = False
omp_nthreads = 4
hires = True
reportlets_dir = '/data/reportlets/anat'
output_dir = '/data/derivative/anat'

wf = base.init_single_subject_wf(subject_id='012',
                                 task_id='binoculardots055',
                                 name='anatomical_wf',
                                 ignore=[],
                                 debug=False,
                                 anat_only=True,
                                 longitudinal=False,
                                 skull_strip_ants=True,
                                 reportlets_dir='/data/reportlets/anat',
                                 output_dir='/data/derivative/anat',
                                 bids_dir='/data/sourcedata/',
                                 freesurfer=True,
                                 output_spaces=['T1w', 'template', 'fsnative'],
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


wf.base_dir = '/data/workflow_folders/'

plugin_settings = {}
plugin_settings['plugin'] = 'MultiProc'
plugin_settings['plugin_args'] = {'n_procs': 3}


#wf.write_graph()
wf.run(**plugin_settings)
