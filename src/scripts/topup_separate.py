import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.interfaces import fsl
from spynoza.io.bids import BIDSGrabber, collect_data, DerivativesDataSink
from spynoza.hires.workflows import init_hires_unwarping_wf
from IPython import embed
from nipype.utils.filemanip import split_filename
from operator import itemgetter
#from IPython

import nibabel as nb

subject = '012'


for package in ['fsl', 'afni']:
    for task in ['binoculardots055', 'binoculardots070']:

        subject_data, layout = collect_data('/data/sourcedata', subject, 'highres', task=task)

        grabber = pe.Node(BIDSGrabber(anat_only=False), name='bids_grabber')
        grabber.inputs.subject_id = '012'
        grabber.inputs.subject_data = subject_data

        bold_epi = subject_data['bold']
        epi_op = list([layout.get_fieldmap(e)['epi'] for e in subject_data['bold']])
        init_reg_file = sorted(glob.glob('/data/derivatives/manual_transforms/sub-012_task-{task}_run-*_to_T1w_preproc.lta'.format(**locals())))

        t1w = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
        t1w_mask = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_brainmask.nii.gz'

        mask_t1w = pe.Node(fsl.ApplyMask(), name='mask_t1w')
        mask_t1w.inputs.in_file = t1w
        mask_t1w.inputs.mask_file = t1w_mask

        wf = init_hires_unwarping_wf(name='hires_topup_separate',
                                     method='topup',
                                     bold_epi=bold_epi,
                                     epi_op=epi_op,
                                     init_reg_file=init_reg_file,
                                     linear_registration_parameters='linear_precise.json',
                                     bids_layout=layout,
                                     topup_package=package,
                                     single_warpfield=False)
        wf.base_dir = '/data/workflow_folders'

        wf.connect(mask_t1w, 'out_file', wf.get_node('inputspec'), 'T1w')


        ds_warpfield = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/topup.new.{package}.separate'.format(**locals()),
                                                  suffix='warpfield'),
                                  iterfield=['in_file', 'source_file'],
                                  name='ds_warpfield')
        wf.connect(wf.get_node('inputspec'), 'bold_epi', ds_warpfield,'source_file')
        wf.connect(wf.get_node('outputspec'), 'bold_epi_to_T1w_transforms', ds_warpfield,'in_file')


        ds_unwarped = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/topup.new.{package}.separate'.format(**locals()),
                                                  suffix='unwarped'),
                                  iterfield=['in_file', 'source_file'],
                                  name='ds_unwarped')
        wf.connect(wf.get_node('inputspec'), 'bold_epi', ds_unwarped,'source_file')
        wf.connect(wf.get_node('outputspec'), 'mean_epi_in_T1w_space', ds_unwarped,'in_file')


        wf.write_graph()
        wf.run(plugin='MultiProc', plugin_args={'n_procs' : 8})
        #wf.run()
