from nodes import TopupScanParameters, BIDSDataGrabber

import nipype.pipeline as pe
from nipype.interfaces import fsl
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio

def create_bids_topup_workflow(name='bids_topup_workflow', base_dir='/home/neuro/workflow_folders'):

    inputspec = pe.Node(util.IdentityInterface(fields=['bold',
                                                       'bold_metadata',
                                                       'fieldmap',
                                                       'fieldmap_metadata']),
                        name='inputspec')

    workflow = pe.Workflow(name=name, base_dir=base_dir)

    topup_parameters = pe.Node(TopupScanParameters, name='topup_scanparameters')

    workflow.connect(inputspec, 'bold_metadata', topup_parameters, 'bold_metadata')
    workflow.connect(inputspec, 'fieldmap_metadata', topup_parameters, 'fieldmap_metadata')

    merge_list = pe.Node(util.Merge(2), name='merge_lists')
    workflow.connect(inputspec, 'bold', merge_list, 'in1') 
    workflow.connect(inputspec, 'fieldmap', merge_list, 'in2') 

    merger = pe.Node(fsl.Merge(dimension='t'), name='merger')
    workflow.connect(merge_list, 'out', merger, 'in_files')

    topup_node = pe.Node(fsl.TOPUP(args='-v'),
                            name='topup')


    workflow.connect(merger, 'merged_file', topup_node, 'in_file')
    workflow.connect(topup_parameters, 'encoding_file', topup_node, 'encoding_file')

    outputspec = pe.Node(util.IdentityInterface(fields=['out_corrected',
                                                        'out_field',
                                                        'out_movpar']),
                         name='outputspec')
                                                         
    workflow.connect(topup_node, 'out_corrected', outputspec, 'out_corrected')
    workflow.connect(topup_node, 'out_field', outputspec, 'out_field')
    workflow.connect(topup_node, 'out_movpar', outputspec, 'out_movpar')

    return workflow


    
if __name__ == '__main__':
    

    dg = pe.Node(BIDSDataGrabber, name='datagrabber')
    dg.inputs.subject = '012'
    dg.inputs.task = 'binoculardots055'
    dg.inputs.run = 1

    workflow = create_bids_topup_workflow()

    for var in ['bold', 'bold_metadata', 'fieldmap', 'fieldmap_metadata']:
        workflow.connect(dg, var, workflow.get_node('inputspec'), var)

    ds = pe.Node(nio.DataSink(base_directory='/data/derivatives'),
                 name='datasink')

    workflow.connect(workflow.get_node('outputspec'), 'out_corrected', ds, 'out_corrected')
    workflow.connect(workflow.get_node('outputspec'), 'out_field', ds, 'out_field')
    workflow.connect(workflow.get_node('outputspec'), 'out_movpar', ds, 'out_movpar')
    workflow.run()


