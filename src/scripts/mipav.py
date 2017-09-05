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

workflow = pe.Workflow(name='mipav_preproc')
workflow.base_dir = '/data/workflow_folders'

subject = '012'
subject_data, layout = collect_data('/data/sourcedata', subject, 'highres')

grabber = pe.Node(BIDSGrabber(anat_only=False), name='bids_grabber')
grabber.inputs.subject_id = '012'
grabber.inputs.subject_data =subject_data

#  *** INTENSITY MP2RAGE MASKING ***
# Set up intensity masker
intensitymasker = pe.Node(mipav.JistIntensityMp2rageMasking(inBackground='half-normal',
                                                            inMasking='binary',
                                                            args='--innoniterative false',
                                                            outSignal=True,
                                                            outSignal2=True,
                                                            outMasked=True,
                                                            outMasked2=True,
                                                            inSkip='true'), name='intensitymasking')
workflow.connect(grabber, 't1', intensitymasker, 'inQuantitative')
workflow.connect(grabber, 't1w', intensitymasker, 'inT1weighted')
workflow.connect(grabber, 'inv2', intensitymasker, 'inSecond')

mask_inv2_signal = pe.Node(fsl.ApplyMask(), name='mask_inv2_signal')
workflow.connect(intensitymasker, 'outSignal2', mask_inv2_signal, 'mask_file')
workflow.connect(grabber, 'inv2', mask_inv2_signal, 'in_file')

# RENAME householding intensity mask
rename_intensity_mask = pe.Node(niu.Rename(), name='rename_intensity_mask')
workflow.connect(grabber, ('inv2', set_postfix, 'intensity_mask.nii'), rename_intensity_mask, 'format_string')
workflow.connect(intensitymasker, 'outSignal', rename_intensity_mask, 'in_file')

rename_t1_intensity_masked = pe.Node(niu.Rename(), name='rename_T1_intensity_masked')
workflow.connect(grabber, ('t1', set_postfix, 'intensity_masked.nii'), rename_t1_intensity_masked, 'format_string')
workflow.connect(intensitymasker, 'outMasked', rename_t1_intensity_masked, 'in_file')

rename_t1w_intensity_masked = pe.Node(niu.Rename(), name='rename_T1w_intensity_masked')
workflow.connect(grabber, ('t1w', set_postfix, 'intensity_masked.nii'), rename_t1w_intensity_masked, 'format_string')
workflow.connect(intensitymasker, 'outMasked2', rename_t1w_intensity_masked, 'in_file')

# *** MP2RAGE SKULL STRIPPING
# SET UP Skull stripping
skullstripper = pe.Node(mipav.JistBrainMp2rageSkullStripping(inSkip='true',
                                                             outMasked=True,
                                                             outMasked2=True,
                                                             outBrain=True), name='skullstripper')
workflow.connect(grabber, 't1', skullstripper, 'inT1')
workflow.connect(grabber, 't1w', skullstripper, 'inT1weighted')
workflow.connect(grabber, 'inv2', skullstripper, 'inSecond')

# RENAME skull stripping
rename_skullstrip_mask = pe.Node(niu.Rename(), name='rename_skullstrip_mask')
workflow.connect(grabber, ('inv2', set_postfix, 'skullstrip_mask.nii'), rename_skullstrip_mask, 'format_string')
workflow.connect(skullstripper, 'outBrain', rename_skullstrip_mask, 'in_file')

rename_t1_skullstrip_masked = pe.Node(niu.Rename(), name='rename_T1_skullstrip_masked')
workflow.connect(grabber, ('t1', set_postfix, 'skullstrip_masked.nii'), rename_t1_skullstrip_masked, 'format_string')
workflow.connect(skullstripper, 'outMasked', rename_t1_skullstrip_masked, 'in_file')

rename_t1w_skullstrip_masked = pe.Node(niu.Rename(), name='rename_T1w_skullstrip_masked')
workflow.connect(grabber, ('t1w', set_postfix, 'skullstrip_masked.nii'), rename_t1w_skullstrip_masked, 'format_string')
workflow.connect(skullstripper, 'outMasked2', rename_t1w_skullstrip_masked, 'in_file')


# *** dura_estimation ***
dura_estimation = pe.Node(mipav.JistBrainMp2rageDuraEstimation(outDura=True,
                                                               inDistance=5,
                                                               inoutput='dura_region'),
                          name='dura_estimation')
workflow.connect(grabber, 'inv2', dura_estimation, 'inSecond')
workflow.connect(skullstripper, 'outBrain', dura_estimation, 'inSkull')


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
workflow.connect(rename_t1_skullstrip_masked, 'out_file', mgdm_segmenter, 'inMP2RAGE')
workflow.connect(rename_t1w_skullstrip_masked, 'out_file', mgdm_segmenter, 'inMP2RAGE2')
workflow.connect(dura_estimation, 'outDura', mgdm_segmenter, 'inPV')

# Datasink
ds = pe.Node(nio.DataSink(base_directory='/data/derivatives/mipav'), name='datasink')
workflow.connect(rename_intensity_mask, 'out_file', ds, 'signalfilter.@intensity_mask')
workflow.connect(rename_t1_intensity_masked, 'out_file', ds, 'signalfilter.@T1_masked_signal')
workflow.connect(rename_t1w_intensity_masked, 'out_file', ds, 'signalfilter.@T1w_masked_signal')
workflow.connect(mask_inv2_signal, 'out_file', ds, 'signalfilter.@inv2_masked_signal')

workflow.connect(rename_skullstrip_mask, 'out_file', ds, 'skullstrip.@skullstrip_mask')
workflow.connect(rename_t1_skullstrip_masked, 'out_file', ds, 'skullstrip.@T1_masked_skullstrip')
workflow.connect(rename_t1w_skullstrip_masked, 'out_file', ds, 'skullstrip.@T1w_masked_skullstrip')

workflow.connect(mgdm_segmenter, 'outLevelset', ds, 'segmenter.@levenset')
workflow.connect(mgdm_segmenter, 'outSegmented', ds, 'segmenter.@segmented')

workflow.connect(dura_estimation, 'outDura', ds, 'dura_estimation.@duramask')

workflow.run()
embed()


