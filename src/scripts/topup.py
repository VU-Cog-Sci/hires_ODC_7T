import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from spynoza.io.bids import BIDSGrabber, collect_data, DerivativesDataSink
from spynoza.unwarping.topup.workflows import create_bids_topup_workflow
from IPython import embed
from nipype.utils.filemanip import split_filename
from operator import itemgetter

import nibabel as nb

subject = '012'
subject_data, layout = collect_data('/data/sourcedata', subject, 'highres')

grabber = pe.Node(BIDSGrabber(anat_only=False), name='bids_grabber')
grabber.inputs.subject_id = '012'
grabber.inputs.subject_data =subject_data

workflow = pe.Workflow(name='topup')
workflow.base_dir = '/data/workflow_folders'

subworkflows = []

def get_item(l, idx):
    return l[idx]

for i, bold_file in enumerate(subject_data['bold']):

    # Get different names for indivdiual workflows, based on sid/run/task
    fname = split_filename(bold_file)[1]
    fname_nosub = '_'.join(fname.split("_")[1:])
    name = "func_topup_" + fname_nosub.replace(
        ".", "_").replace(" ", "").replace("-", "_").replace("_bold", "_wf")

    # Create sub-topup-workflow
    subworkflows.append(create_bids_topup_workflow(mode='average', name=name))
    workflow.connect(grabber, ('bold', get_item, i), subworkflows[i], 'inputnode.bold')

    # Find fieldmap and metadata
    fieldmap = layout.get_fieldmap(bold_file)['epi']
    subworkflows[i].inputs.inputnode.fieldmap = fieldmap
    bold_metadata = layout.get_metadata(bold_file)
    bold_metadata['NDynamics'] = nb.load(bold_file).shape[-1]

    fieldmap_metadata = layout.get_metadata(fieldmap)
    fieldmap_metadata['NDynamics'] = nb.load(fieldmap).shape[-1]

    subworkflows[i].inputs.inputnode.bold_metadata = bold_metadata
    subworkflows[i].inputs.inputnode.fieldmap_metadata = fieldmap_metadata

    ds_warpfield = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/topup',
                                              source_file=bold_file,
                                              suffix='warpfield'),
                              name='ds_warpfield')
    subworkflows[i].connect(subworkflows[i].get_node('outputnode'), 'out_warp', ds_warpfield,'in_file')
    
    
    ds_unwarped = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/topup',
                                              source_file=bold_file,
                                              suffix='unwarped'),
                              name='ds_unwarped')
    subworkflows[i].connect(subworkflows[i].get_node('outputnode'), 'unwarped_image', ds_unwarped,'in_file')


workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 8})
