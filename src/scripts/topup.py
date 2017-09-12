import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from spynoza.io.bids import BIDSGrabber, collect_data, DerivativesDataSink
from spynoza.hires.workflows import init_hires_unwarping_wf
from IPython import embed
from nipype.utils.filemanip import split_filename
from operator import itemgetter
#from IPython

import nibabel as nb

subject = '012'
subject_data, layout = collect_data('/data/sourcedata', subject, 'highres', task='binoculardots055')

grabber = pe.Node(BIDSGrabber(anat_only=False), name='bids_grabber')
grabber.inputs.subject_id = '012'
grabber.inputs.subject_data = subject_data

bold_epi = subject_data['bold']
epi_op = list([layout.get_fieldmap(e)['epi'] for e in subject_data['bold']])

wf = init_hires_unwarping_wf(method='topup',
                             bold_epi=bold_epi,
                             epi_op=epi_op,
                             bids_layout=layout,
                             topup_package='afni',
                             single_warpfield=True)
wf.base_dir = '/data/workflow_folders'


ds_warpfield = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/topup.new',
                                          suffix='warpfield'),
                          iterfield=['in_file', 'source_file'],
                          name='ds_warpfield')
wf.connect(wf.get_node('inputspec'), 'bold_epi', ds_warpfield,'source_file')
wf.connect(wf.get_node('outputspec'), 'bold_epi_to_T1w_transforms', ds_warpfield,'in_file')


ds_unwarped = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/topup.new',
                                          suffix='unwarped'),
                          iterfield=['in_file', 'source_file'],
                          name='ds_unwarped')
wf.connect(wf.get_node('inputspec'), 'bold_epi', ds_unwarped,'source_file')
wf.connect(wf.get_node('outputspec'), 'mean_epi_in_T1w_space', ds_unwarped,'in_file')


#workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 8})
wf.write_graph()
wf.run()
