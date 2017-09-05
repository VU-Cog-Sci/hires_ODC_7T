import nipype.pipeline.engine as pe
from spynoza.io.bids import collect_data
from IPython import embed
from spynoza.io.bids import BIDSGrabber
from nipype.interfaces import mipav
from nipype.interfaces import fsl
from nipype.interfaces import io as nio
from nipype.interfaces import utility as niu
from spynoza.utils import set_postfix
import os

workflow = pe.Workflow(name='mipav_preproc_hybrid')
workflow.base_dir = '/data/workflow_folders'


t1_masker = pe.Node(fsl.ApplyMask(), name='t1_masker')
t1_masker.inputs.mask_file = '/data/workflow_folders/anatomical_wf/anat_preproc_wf/skullstrip_ants_wf/t1_skull_strip/highres001_BrainExtractionMask.nii.gz'

reorient_t1 = pe.Node(fsl.Reorient2Std(), name='reorient_t1')
reorient_t1.inputs.in_file = '/data/sourcedata/sub-012/anat/sub-012_acq-highres_T1.nii.gz'
 
workflow.connect(reorient_t1, 'out_file', t1_masker, 'in_file')


t1w_masker = pe.Node(fsl.ApplyMask(), name='t1w_masker')
t1w_masker.inputs.in_file = '/data/workflow_folders/anatomical_wf/anat_preproc_wf/skullstrip_ants_wf/t1_skull_strip/highres001_N4Corrected0.nii.gz' 
t1w_masker.inputs.mask_file = '/data/workflow_folders/anatomical_wf/anat_preproc_wf/skullstrip_ants_wf/t1_skull_strip/highres001_BrainExtractionMask.nii.gz'

# *** MGDM segmentation ***
ATLAS_DIR = '/home/neuro/mipav/plugins/atlases'
atlas = os.path.join(ATLAS_DIR, 'brain-segmentation-prior3.0',
                                                  'brain-atlas-3.0.3.txt')
    
mgdm_segmenter = pe.Node(mipav.JistBrainMgdmSegmentation(inMax=800,
                                                         inSteps=5,
                                                         inAtlas=atlas,
                                                         inTopology='wcs',
                                                         outSegmented=True,
                                                         inOutput='memberships',
                                                         inData=0.2,
                                                         inCurvature=0.8,
                                                         inPosterior=5,
                                                         inMin=0.001,
                                                         inCompute='true',
                                                         inAdjust='true',
                                                         outLevelset=True,
                                                         xMaxProcess=8), name='mgdm_segmenter')
workflow.connect(t1_masker, 'out_file', mgdm_segmenter, 'inMP2RAGE')
workflow.connect(t1w_masker, 'out_file', mgdm_segmenter, 'inMP2RAGE2')

# Datasink
ds = pe.Node(nio.DataSink(base_directory='/data/derivatives/mipav_hybrid'), name='datasink')
workflow.connect(mgdm_segmenter, 'outLevelset', ds, 'segmenter.@levenset')
workflow.connect(mgdm_segmenter, 'outSegmented', ds, 'segmenter.@segmented')

workflow.run()
embed()


