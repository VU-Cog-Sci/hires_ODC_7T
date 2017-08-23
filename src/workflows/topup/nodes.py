import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util


def get_topup_data(subject, task, run, data_dir='/data/sourcedata'):
    from bids.grabbids import BIDSLayout
    import nibabel as nb
    
    layout = BIDSLayout(data_dir)    
    bold = layout.get(subject=subject, task=task, run=run, type='bold')
    
    # Make sure there is only one nifti-file for this subject/task/run
    assert(len(bold) == 1)
    
    bold = bold[0].filename    
    fieldmap = layout.get_fieldmap(bold)
    
    # Make sure we are dealing with an EPI ('topup') fieldmap here
    assert(fieldmap['type'] == 'epi')    
    fieldmap = fieldmap['epi']
    
    bold_metadata = layout.get_metadata(bold)
    
    if 'NDynamics' not in bold_metadata:
        bold_metadata['NDynamics'] = nb.load(bold).shape[-1]
        
    fieldmap_metadata = layout.get_metadata(fieldmap)
    
    if 'NDynamics' not in fieldmap_metadata:
        fieldmap_metadata['NDynamics'] = nb.load(fieldmap).shape[-1]    
    
    return bold, bold_metadata, fieldmap, fieldmap_metadata

BIDSDataGrabber = util.Function(function=get_topup_data,
                                input_names=['subject',
                                             'task',
                                             'run'],
                                output_names=['bold',
                                              'bold_metadata',
                                              'fieldmap',
                                              'fieldmap_metadata'])



def topup_scan_params(bold_metadata, fieldmap_metadata, mode='concatenate'):
    import numpy as np
    import os
    
    n_bold_volumes = bold_metadata['NDynamics']
    n_epi_volumes = fieldmap_metadata['NDynamics']
    
    bold_total_readouttime = bold_metadata['TotalReadoutTime']
    epi_total_readouttime = fieldmap_metadata['TotalReadoutTime']
    
    bold_phaseEncodingDirection = bold_metadata['PhaseEncodingDirection']
    epi_phaseEncodingDirection = fieldmap_metadata['PhaseEncodingDirection']
    
    if type(bold_phaseEncodingDirection) is str:
        bold_phaseEncodingDirection = [bold_phaseEncodingDirection]
        
    if type(epi_phaseEncodingDirection) is str:
        epi_phaseEncodingDirection = [epi_phaseEncodingDirection]
    
    if mode == 'concatenate':
        bold_idx = n_bold_volumes
        scan_param_array = np.zeros((n_bold_volumes + n_epi_volumes, 4))
    elif mode == 'average':
        bold_idx = 1
        scan_param_array = np.zeros((2, 4))

    
    for encoding_direction in bold_phaseEncodingDirection:
        if encoding_direction.endswith('-'):
            scan_param_array[:bold_idx, ['i', 'j', 'k'].index(encoding_direction[0])] = -1
        else:
            scan_param_array[:bold_idx, ['i', 'j', 'k'].index(encoding_direction[0])] = 1
            
    for encoding_direction in epi_phaseEncodingDirection:
        if encoding_direction.endswith('-'):
            scan_param_array[bold_idx:, ['i', 'j', 'k'].index(encoding_direction[0])] = -1
        else:
            scan_param_array[bold_idx:, ['i', 'j', 'k'].index(encoding_direction[0])] = 1
            
    
    # Vectors should be unity length
    scan_param_array[:, :3] /= np.sqrt((scan_param_array[:, :3]**2).sum(1))[:, np.newaxis]
    
    scan_param_array[:bold_idx, 3] = bold_total_readouttime
    scan_param_array[bold_idx:, 3] = epi_total_readouttime
                

    fn = os.path.abspath('scan_params.txt')
    
    np.savetxt(fn, scan_param_array, fmt='%1.6f')
    
    return fn


TopupScanParameters = util.Function(function=topup_scan_params,
                                    input_names=['mode',
                                                 'bold_metadata',
                                                 'fieldmap_metadata'],
                                    output_names=['encoding_file'])
