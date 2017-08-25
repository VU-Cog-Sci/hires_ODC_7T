import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from spynoza.io import BIDSGrabber
from spynoza.unwarping.topup.workflows import create_bids_topup_workflow

dg = pe.Node(BIDSGrabber(), name='datagrabber')
dg.inputs.subject = '012'

dg.iterables = [('task', ['binoculardots055', 'binoculardots070']),
                ('run', [1,2,3,4])]

workflow = create_bids_topup_workflow(mode='average')

for var in ['bold', 'bold_metadata', 'fieldmap', 'fieldmap_metadata']:
    workflow.connect(dg, var, workflow.get_node('inputnode'), var)

ds = pe.Node(nio.DataSink(base_directory='/data/tests'),
             name='datasink')

workflow.connect(workflow.get_node('outputnode'), 'out_field', ds, 'out_field')
workflow.connect(workflow.get_node('outputnode'), 'out_warp', ds, 'out_warp')
workflow.connect(workflow.get_node('outputnode'), 'unwarped_image', ds, 'unwarped_image')
workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 8})

