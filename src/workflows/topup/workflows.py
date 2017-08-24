from nodes import TopupScanParameters, BIDSDataGrabber

import nipype.pipeline as pe
from nipype.interfaces import fsl
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio

def create_bids_topup_workflow(mode='concatenate',
                               name='bids_topup_workflow', 
                               base_dir='/home/neuro/workflow_folders'):

    inputspec = pe.Node(util.IdentityInterface(fields=['bold',
                                                       'bold_metadata',
                                                       'fieldmap',
                                                       'fieldmap_metadata']),
                        name='inputspec')

    workflow = pe.Workflow(name=name, base_dir=base_dir)

    topup_parameters = pe.Node(TopupScanParameters, name='topup_scanparameters')
    topup_parameters.inputs.mode = mode
    workflow.connect(inputspec, 'bold_metadata', topup_parameters, 'bold_metadata')
    workflow.connect(inputspec, 'fieldmap_metadata', topup_parameters, 'fieldmap_metadata')

    topup_node = pe.Node(fsl.TOPUP(args='-v'),
                            name='topup')

    workflow.connect(topup_parameters, 'encoding_file', topup_node, 'encoding_file')

    merge_list = pe.Node(util.Merge(2), name='merge_lists')

    if mode == 'concatenate':
        workflow.connect(inputspec, 'bold', merge_list, 'in1') 
        workflow.connect(inputspec, 'fieldmap', merge_list, 'in2') 


    elif mode == 'average':
        mc_bold = pe.Node(fsl.MCFLIRT(cost='normcorr',
                          interpolation='sinc',
                          mean_vol=True), name='mc_bold')

        meaner_bold = pe.Node(fsl.MeanImage(), name='meaner_bold')
        workflow.connect(inputspec, 'bold', mc_bold, 'in_file') 
        workflow.connect(mc_bold, 'out_file', meaner_bold, 'in_file') 

        mc_fieldmap = pe.Node(fsl.MCFLIRT(cost='normcorr',
                          interpolation='sinc',
                          mean_vol=True), name='mc_fieldmap')

        workflow.connect(meaner_bold, 'out_file', mc_fieldmap, 'ref_file')

        meaner_fieldmap = pe.Node(fsl.MeanImage(), name='meaner_fieldmap')
        workflow.connect(mc_fieldmap, 'out_file', meaner_fieldmap, 'in_file') 

        workflow.connect(meaner_bold, 'out_file', merge_list, 'in1')
        workflow.connect(meaner_bold, 'out_file', merge_list, 'in2')

    merger = pe.Node(fsl.Merge(dimension='t'), name='merger')
    workflow.connect(merge_list, 'out', merger, 'in_files')
    workflow.connect(merger, 'merged_file', topup_node, 'in_file')

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

    workflow = create_bids_topup_workflow(mode='average')

    for var in ['bold', 'bold_metadata', 'fieldmap', 'fieldmap_metadata']:
        workflow.connect(dg, var, workflow.get_node('inputspec'), var)

    ds = pe.Node(nio.DataSink(base_directory='/data/derivatives'),
                 name='datasink')

    workflow.connect(workflow.get_node('outputspec'), 'out_corrected', ds, 'out_corrected')
    workflow.connect(workflow.get_node('outputspec'), 'out_field', ds, 'out_field')
    workflow.connect(workflow.get_node('outputspec'), 'out_movpar', ds, 'out_movpar')
    workflow.run()


