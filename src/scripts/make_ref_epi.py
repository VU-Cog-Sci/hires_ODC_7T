import nipype.pipeline.engine as pe
from nipype.interfaces import fsl
from nipype.interfaces import afni
from nipype.interfaces import io as nio
from spynoza.io.bids import DerivativesDataSink

workflow = pe.Workflow(name='make_ref_epi')
workflow.base_dir = '/data/workflow_folders'

mc_bold = pe.MapNode(fsl.MCFLIRT(cost='normcorr',
                                 interpolation='sinc',
                                 save_mats=True,
                                 mean_vol=True),
                     iterfield=['in_file'],
                     name='mc_bold')

templates = {'raw_EPI':'/data/sourcedata/sub-012/func/sub-012_task-{task}_run-{run}_bold.nii.gz'}

selector = pe.Node(nio.SelectFiles(templates), name='selector')
selector.iterables = [('run', [1,2,3,4, 5]), ('task', ['binoculardots055', 'binoculardots070'])]

mask_bold_EPIs = pe.Node(afni.Automask(outputtype='NIFTI_GZ'),
                           iterfield=['in_file'],
                           name='mask_bold_epi')

mc_bold = pe.Node(fsl.MCFLIRT(cost='normcorr',
                                 interpolation='sinc',
                                 save_mats=True,
                                 save_plots=True,
                                 mean_vol=True),
                     iterfield=['in_file'],
                     name='mc_bold')

meaner_bold = pe.Node(fsl.MeanImage(), iterfield=['in_file'], name='meaner_bold')

workflow.connect(selector, 'raw_EPI', mc_bold, 'in_file')
workflow.connect(mc_bold, 'out_file', mask_bold_EPIs, 'in_file')
workflow.connect(mc_bold, 'out_file', meaner_bold, 'in_file')

# STORE MEAN DS
mean_ds = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/mean_epi',
                                         suffix='mean_ref'),
                     name='mean_ds')

workflow.connect(selector, 'raw_EPI', mean_ds, 'source_file')
workflow.connect(meaner_bold, 'out_file', mean_ds, 'in_file')

# Store motion-corrected data
mc_ds = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/mc_epi',
                                         suffix='mc'),
                     name='mc_ds')

workflow.connect(selector, 'raw_EPI', mc_ds, 'source_file')
workflow.connect(mc_bold, 'out_file', mc_ds, 'in_file')


# Store motion parameters
mcpar_ds = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/mc_epi',
                                         suffix='mc'),
                     name='mcpar_ds')

workflow.connect(selector, 'raw_EPI', mcpar_ds, 'source_file')
workflow.connect(mc_bold, 'par_file', mcpar_ds, 'in_file')

workflow.run()
