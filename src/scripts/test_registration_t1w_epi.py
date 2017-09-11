import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import spynoza
from spynoza.registration.sub_workflows import create_epi_to_T1_workflow

derivatives_folder = '/data/derivatives/registration_tests/epi_to_T1w_epi'

def invert_image(input_image):
    import nibabel as nb
    import os
    from spynoza.utils import fname_presuffix
    
    image = nb.load(input_image)
    
    
    data = image.get_data()
    
    data = -data
    
    new_image = nb.Nifti1Image(data, image.affine, image.header)
    
    new_fn = spynoza.utils.fname_presuffix(input_image, suffix='_inv', newpath='.')
    new_image.to_filename(new_fn)
    
    return new_fn

for method in ['linear_hires', 'linear_precise', 'linear_hires_intramodal.original', 'linear_hires_intramodal.invert']:
    for run in [1,2,3,4, 5]:

        name = 'test_registration_method-%s_run-%s' % (method, run)

        parameter_file = '%s.json' % method.split('.')[0]
        source_file =  '/data/derivatives/mean_epi/sub-012/func/sub-012_task-binoculardots055_run-{run}_bold_mean_ref.nii.gz'.format(**locals())
        
        
        wf = create_epi_to_T1_workflow(package='ants', 
                                       parameter_file=parameter_file,
                                       apply_transform=True)
        
        wf.get_node('ants_registration').inputs.num_threads = 8
        
        if len(method.split('.')) > 1:
            if method.split('.')[1] == 'invert':                
                inverter = pe.Node(util.Function(function=invert_image), name='inverter')                
                wf.connect(inverter, 'out', wf.get_node('inputspec'), 'EPI_space_file')
        else:
            wf.inputs.inputspec.EPI_space_file = source_file
            
        wf.inputs.inputspec.T1_file = '/data/derivatives/epi_to_T1.3depi/sub-012/anat/sub-012_acq-3DEPI_T1w_ras_masked.nii.gz'
        
        ds_transformed = pe.Node(spynoza.io.bids.DerivativesDataSink(base_directory=derivatives_folder, 
                                 suffix='bold_epi2t1w_epi'), 
                                 name='ds_transformed',)
        ds_transformed.inputs.source_file = source_file        
        wf.connect(wf.get_node("outputspec"), 'transformed_EPI_space_file', ds_transformed, 'in_file')
        
        ds_transforms = pe.Node(spynoza.io.bids.DerivativesDataSink(base_directory=derivatives_folder,
                                                                   suffix='bold_epi2t1w_epi'), 
                                 name='ds_transforms')        
        ds_transforms.inputs.source_file = source_file        
        wf.connect(wf.get_node("outputspec"), 'EPI_T1_matrix_file', ds_transforms, 'in_file') 
        
        
        from nipype.interfaces import ants
        measure_similarity = pe.Node(ants.MeasureImageSimilarity(dimension=3,
                                    metric='CC',
                                    metric_weight=1.0,
                                    radius_or_number_of_bins=4,
                                    sampling_strategy='Regular',
                                    sampling_percentage=1.0,
                                    fixed_image_mask='/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_brainmask.nii.gz',
                                    fixed_image='/data/derivatives/preproc_anat/fmriprep/sub-012/anat/sub-012_acq-highres_T1w_preproc.nii.gz'),
                          name='measure_similarity')
        wf.connect(wf.get_node("outputspec"), 'transformed_EPI_space_file', measure_similarity, 'moving_image')
        
        
        json_similarity = pe.Node(nio.JSONFileSink(input_names=['similarity', 'method']),
                               name='json_similarity')
        
        json_similarity.inputs.method = method
        wf.connect(measure_similarity, 'similarity', json_similarity, 'similarity')
        
        ds_similarity = pe.Node(spynoza.io.bids.DerivativesDataSink(base_directory=derivatives_folder,
                                                                   suffix='similarity'),
                             name='ds_similarity')
        ds_similarity.inputs.source_file = source_file        
        wf.connect(json_similarity, 'json_measure', ds_similarity, 'in_file')
        
        
        
        wf.run()
