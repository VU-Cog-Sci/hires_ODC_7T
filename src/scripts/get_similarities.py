import glob, re
import pandas as pd

from nipype.interfaces import ants

def get_similarity(fn):
    measure_sim = ants.MeasureImageSimilarity(num_threads=4)
    measure_sim.inputs.moving_image = fn
    measure_sim.inputs.fixed_image = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'
    measure_sim.inputs.fixed_image_mask = '/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_brainmask.nii.gz'    
    measure_sim.inputs.metric = 'CC'
    measure_sim.inputs.radius_or_number_of_bins = 4
    measure_sim.inputs.sampling_percentage = 1.0
    measure_sim.inputs.dimension = 3
    
    print(measure_sim.inputs)

    return measure_sim.run().outputs.similarity

fns = glob.glob('/data/derivatives/topup.new.*/sub-012/func/sub-012_task-binoculardots*_run-*_bold_unwarped.nii.gz')
print(fns)

reg = re.compile('.*/topup\.(?P<method>.+)/sub-012/func/sub-012_task-(?P<task>[a-z0-9]+)_run-(?P<run>[0-9])_bold_unwarped\.nii\.gz')
df = pd.DataFrame(reg.match(fn).groupdict() for fn in fns)
df['fn'] = fns
df['similarity'] = df.fn.apply(get_similarity)
df.to_csv('/data/derivatives/similarities.csv')

