import nipype.pipeline.engine as pe
from spynoza.io.bids import DerivativesDataSink
import pkg_resources
from nipype.interfaces import ants
from spynoza.utils import ComputeEPIMask

wf = pe.Workflow('polish_nonlinear')

source = '/data/sourcedata/sub-012/func/sub-012_task-binoculardots070_run-5_bold.nii.gz'
moving_image = '/data/derivatives/topup.new.afni.separate/sub-012/func/sub-012_task-binoculardots070_run-5_bold_unwarped.nii.gz'
fixed_image = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
fixed_image_mask = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_brainmask.nii.gz'

json = pkg_resources.resource_filename('spynoza.data.ants_json', 'nonlinear_precise.json')
reg = pe.Node(ants.Registration(from_file=json),
              name='reg')

get_mask = pe.Node(ComputeEPIMask(), name='get_mask')
get_mask.inputs.in_file = moving_image

reg.inputs.moving_image = moving_image
reg.inputs.fixed_image = fixed_image
reg.inputs.fixed_image_masks = fixed_image_mask
reg.inputs.num_threads = 8
reg.inputs.verbose = True

wf.connect(get_mask, 'mask_file', reg, 'moving_image_masks')

ds_warpfield = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/non_linear_polish'), 
                      name='ds_warpfield')
ds_warpfield.inputs.source_file = source

wf.connect(reg, 'forward_transforms', ds_warpfield, 'in_file')

ds_warped = pe.Node(DerivativesDataSink(base_directory='/data/derivatives/non_linear_polish'), 
                      name='ds_warped')
ds_warped.inputs.source_file = source

wf.connect(reg, 'warped_image', ds_warped, 'in_file')

wf.run()
