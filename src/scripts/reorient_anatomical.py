from spynoza.io.bids import DerivativesDataSink
import nipype.pipeline.engine as pe
from bids.grabbids import BIDSLayout
from spynoza.utils import Reorient


layout = BIDSLayout('/data/sourcedata')

anatomical = layout.get(modality='anat', extensions=['nii', 'nii.gz'])

filenames = [a.filename for a in anatomical]

workflow = pe.Workflow(name='reorient_anatomical_data',
                      base_dir='/data/workflow_folders/')


identity = pe.Node(niu.IdentityInterface(fields=['in_files']),
                  name='identity')
identity.inputs.in_files = filenames

reorient = pe.MapNode(Reorient(), 
                      iterfield=['in_file'],
                      name='reorient')
workflow.connect(identity, 'in_files', reorient, 'in_file')

datasink = pe.MapNode(DerivativesDataSink(base_directory='/data/derivatives/reorient',
                                          suffix='ras'),
                      iterfield=['source_file', 'in_file'],
                      compress=True,
                      name='datasink')
workflow.connect(identity, 'in_files', datasink, 'source_file')

workflow.connect(reorient, 'out_file', datasink, 'in_file')

workflow.run()                    
