import os
import json

if 'experiments' not in locals():
    experiment = '055'


if 'aeneas' in ''.join(os.uname()[1].split('.')):
    raw_disk = '/home/raw_data/'
    pp_disk = '/home/shared/'
    # FS subject directory made up of links to actual FS directory for
    # anonimization purposes
    if experiment in ('055','07'):
    #     FS_subject_dir = os.path.join(
    #         raw_disk, '2017/visual/nPRF/bids/FS_SJID')
    # elif 'all' in experiment:
        FS_subject_dir = os.path.join(
            raw_disk, '2016/visual/whole_brain_MB_pRF/data/FS_SJID')
elif os.uname()[0] == 'Darwin':  # laptop
    raw_disk = '/Users/knapen/disks/ae_R/'
    pp_disk = '/Users/knapen/disks/ae_S/'
    # FS subject directory made up of links to actual FS directory for
    # anonimization purposes is copied as files to the laptop's hard drive
    # while the functional data etc are pointed to across sshfs
    FS_subject_dir = '/Users/knapen/FS_SJID'

os.environ["SUBJECTS_DIR"] = FS_subject_dir

# a project directory that we assume has already been created contains the raw data.
raw_data_dir = os.path.join(raw_disk, '2017/visual/hires/')

# where to put everything
preprocessed_data_dir = os.path.join(pp_disk, '2017/visual', 'hires', experiment)
opd = os.path.join(preprocessed_data_dir, sub_id)

# load the analysis parameters from json file
with open('analysis_settings.json') as f:
    json_s = f.read()
    analysis_info = json.loads(json_s)

# non-mandatory participant-specific settings, like rsquared threshold
try:
    with open(os.path.join(raw_data_dir, sub_id, sub_id + '.json')) as f:
        json_s = f.read()
        analysis_info.update(json.loads(json_s))
except:
    pass

# this 'experiment' variable is set by commandline
# and refers to which experiment: whole-brain (all), nPRF or RS
# this will play a slight role in the preprocessing, in terms of
# the selection and averaging across files in a given condition
analysis_info.update({'experiment': experiment})

# load the sequence parameters from json file
with open(os.path.join(raw_disk, '2017/visual/hires', 'hires-%s.json'%experiment)) as f:
    json_s = f.read()
    acquisition_parameters = json.loads(json_s)


print('------------------------------------------------------------------------')
print('.  Running analysis for subject "%s"' % sub_id)
print('.  Running analysis for experiment "%s"' % experiment)
print('------------------------------------------------------------------------')
print('.  Running analysis at "%s"' % opd)
print('------------------------------------------------------------------------')
