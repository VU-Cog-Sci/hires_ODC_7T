def create_hires_workflow(analysis_info, name='hires'):
    import os.path as op
    import nipype.pipeline as pe
    from nipype.interfaces import fsl
    from nipype.interfaces.utility import Function, Merge, IdentityInterface
    from spynoza.nodes.utils import get_scaninfo, dyns_min_1, topup_scan_params, apply_scan_params
    from nipype.interfaces.io import SelectFiles, DataSink

    # Importing of custom nodes from spynoza packages; assumes that spynoza is installed:
    # pip install git+https://github.com/spinoza-centre/spynoza.git@develop
    from spynoza.nodes.filtering import savgol_filter
    from spynoza.nodes.utils import get_scaninfo, pickfirst, percent_signal_change, average_over_runs, pickle_to_json, set_nifti_intercept_slope, non_uniformity_correct_4D_file
    from spynoza.workflows.topup_unwarping import create_topup_workflow
    from spynoza.workflows.B0_unwarping import create_B0_workflow
    from spynoza.workflows.motion_correction import create_motion_correction_workflow
    from spynoza.workflows.registration import create_registration_workflow
    from spynoza.workflows.retroicor import create_retroicor_workflow
    from spynoza.workflows.sub_workflows.masks import create_masks_from_surface_workflow
    from spynoza.nodes.fit_nuisances import fit_nuisances

    # from ..utils.GLM import fit_BD_glm_CV_one_fold
    # from ..utils.utils import convert_edf_2_hdf5, leave_one_out_lists, suff_file_name
    # from ..utils.eye import convert_hdf_eye_to_tsv, blinks_saccades_from_hdf, plot_hdf_eye
    # from ..utils.behavior import convert_pickle_to_tsvs, plot_staircases

    from .motion_correction import create_motion_correction_workflow
    # from ..surf.masks import avg_label_to_subject_label

    imports = ['from ..utils.eye import convert_gaze_to_deg']

    ########################################################################################
    # nodes
    ########################################################################################

    input_node = pe.Node(IdentityInterface(
        fields=['raw_directory',
                'output_directory',
                'exp',
                'FS_ID',
                'FS_subject_dir',
                'sub_id',
                'topup_conf_file',
                'which_file_is_EPI_space',
                'standard_file',
                'psc_func',
                'av_func',
                'tr',
                'slice_direction',
                'phys_sample_rate',
                'slice_order',
                'nr_dummies',
                'wfs',
                'epi_factor',
                'acceleration',
                'te_diff',
                'echo_time',
                'phase_encoding_direction',
                # 'bd_design_matrix_file',
                'sg_filter_window_length',
                'sg_filter_order']), name='inputspec')

    # i/o node
    datasource_templates = dict(func='{sub_id}/{exp}/func/*_bold.nii.gz')
                                # magnitude='{sub_id}/fmap/*magnitude.nii.gz',
                                # phasediff='{sub_id}/fmap/*phasediff.nii.gz',
                                # topup='{sub_id}/fmap/*_topup.nii.gz',
                                # physio='{sub_id}/func/*physio.*',
                                # events='{sub_id}/func/*_events.pickle',
                                # eye='{sub_id}/func/*_eyedata.edf')
    datasource = pe.Node(SelectFiles(datasource_templates, sort_filelist=True, raise_on_empty=False),
                         name='datasource')

    output_node = pe.Node(IdentityInterface(fields=([
        'temporal_filtered_files',
        'percent_signal_change_files'])), name='outputspec')

    bet_epi = pe.MapNode(interface=fsl.BET(frac=analysis_info['bet_f_value'], vertical_gradient=analysis_info['bet_g_value'],
                                           functional=True, mask=True), name='bet_epi', iterfield=['in_file'])
    # bet_topup = pe.MapNode(interface=
    #     fsl.BET(frac=analysis_info['bet_f_value'], vertical_gradient = analysis_info['bet_g_value'],
    #             functional=True, mask = True), name='bet_topup', iterfield=['in_file'])

    # node for converting pickle files to json
    sgfilter = pe.MapNode(Function(input_names=['in_file', 'window_length', 'polyorder'],
                                   output_names=['out_file'],
                                   function=savgol_filter),
                          name='sgfilter', iterfield=['in_file'])
    sgfilter.inputs.window_length = analysis_info['sg_filter_window_length']
    sgfilter.inputs.polyorder = analysis_info['sg_filter_order']

    # node for percent signal change
    psc = pe.MapNode(Function(input_names=['in_file', 'func'],
                              output_names=['out_file'],
                              function=percent_signal_change),
                     name='percent_signal_change', iterfield=['in_file'])

    # nodes for averaging across runs
    av = pe.Node(Function(input_names=['in_files', 'func'], output_names=['out_file'], function=average_over_runs),
                 name='average_over_runs')

    # and for CV GLM
    # cv_bd_glm = pe.MapNode(Function(input_names=['train_file', 'test_file', 'design_matrix_file'], output_names=['out_files'], function=fit_BD_glm_CV_one_fold),
    #                        iterfield=['train_file', 'test_file'], name='cv_bd_glm')

    datasink = pe.Node(DataSink(), name='sinker')
    datasink.inputs.parameterization = False

    ########################################################################################
    # workflow
    ########################################################################################

    # the actual top-level workflow
    hires_workflow = pe.Workflow(name=name)

    # data source
    hires_workflow.connect(input_node, 'raw_directory',
                            datasource, 'base_directory')
    hires_workflow.connect(input_node, 'sub_id', datasource, 'sub_id')
    hires_workflow.connect(input_node, 'exp', datasource, 'exp')
    # and data sink
    hires_workflow.connect(
        input_node, 'output_directory', datasink, 'base_directory')

    if analysis_info['perform_mri'] == 1:
        # still have to decide on BET for correction.
        # point for intern, to decide on topup and B0 correction
        # BET
        # hires_workflow.connect(datasource, 'func', bet_epi, 'in_file')

        # non-uniformity correction
        # hires_workflow.connect(bet_epi, 'out_file', nuc, 'in_file')

        # motion correction
        motion_proc = create_motion_correction_workflow(
            'moco', method=analysis_info['moco_method'])
        hires_workflow.connect(input_node, 'tr', motion_proc, 'inputspec.tr')
        hires_workflow.connect(
            input_node, 'output_directory', motion_proc, 'inputspec.output_directory')
        hires_workflow.connect(input_node, 'which_file_is_EPI_space',
                                motion_proc, 'inputspec.which_file_is_EPI_space')

        # spatial correction
        if analysis_info['B0_or_topup'] == 'topup':

            hires_workflow.connect(datasource, 'topup', bet_topup, 'in_file')
            # hires_workflow.connect(bet_topup, 'out_file', nuc_t, 'in_file')
            # topup
            tua_wf = create_topup_workflow(analysis_info, name='topup')
            hires_workflow.connect(
                input_node, 'output_directory', tua_wf, 'inputspec.output_directory')
            hires_workflow.connect(
                input_node, 'topup_conf_file', tua_wf, 'inputspec.conf_file')
            hires_workflow.connect(
                bet_epi, 'out_file', tua_wf, 'inputspec.in_files')
            hires_workflow.connect(
                bet_topup, 'out_file', tua_wf, 'inputspec.alt_files')
            hires_workflow.connect(
                input_node, 'epi_factor', tua_wf, 'inputspec.epi_factor')
            hires_workflow.connect(
                input_node, 'echo_time', tua_wf, 'inputspec.echo_time')
            hires_workflow.connect(
                input_node, 'phase_encoding_direction', tua_wf, 'inputspec.phase_encoding_direction')

            hires_workflow.connect(
                tua_wf, 'outputspec.out_files', motion_proc, 'inputspec.in_files')

            hires_workflow.connect(
                tua_wf, 'outputspec.field_coefs', datasink, 'topup.fieldcoef')
            hires_workflow.connect(
                tua_wf, 'outputspec.out_files', datasink, 'topup.unwarped')

        elif analysis_info['B0_or_topup'] == 'B0':
            # B0
            # set slope/intercept to unity for B0 map
            hires_workflow.connect(
                datasource, 'magnitude', int_slope_B0_magnitude, 'in_file')
            hires_workflow.connect(
                datasource, 'phasediff', int_slope_B0_phasediff, 'in_file')

            B0_wf = create_B0_workflow(name='B0')
            hires_workflow.connect(
                bet_epi, 'out_file', B0_wf, 'inputspec.in_files')
            hires_workflow.connect(
                int_slope_B0_magnitude, 'out_file', B0_wf, 'inputspec.fieldmap_mag')
            hires_workflow.connect(
                int_slope_B0_phasediff, 'out_file', B0_wf, 'inputspec.fieldmap_pha')
            hires_workflow.connect(input_node, 'wfs', B0_wf, 'inputspec.wfs')
            hires_workflow.connect(
                input_node, 'epi_factor', B0_wf, 'inputspec.epi_factor')
            hires_workflow.connect(
                input_node, 'acceleration', B0_wf, 'inputspec.acceleration')
            hires_workflow.connect(
                input_node, 'te_diff', B0_wf, 'inputspec.te_diff')
            hires_workflow.connect(
                input_node, 'phase_encoding_direction', B0_wf, 'inputspec.phase_encoding_direction')

            hires_workflow.connect(
                B0_wf, 'outputspec.out_files', motion_proc, 'inputspec.in_files')

            hires_workflow.connect(
                B0_wf, 'outputspec.field_coefs', datasink, 'B0.fieldcoef')
            hires_workflow.connect(
                B0_wf, 'outputspec.out_files', datasink, 'B0.unwarped')

        elif analysis_info['B0_or_topup'] == 'neither':
            hires_workflow.connect(
                datasource, 'func', motion_proc, 'inputspec.in_files')

        # registration
        reg = create_registration_workflow(analysis_info, name='reg')
        hires_workflow.connect(
            input_node, 'output_directory', reg, 'inputspec.output_directory')
        hires_workflow.connect(
            motion_proc, 'outputspec.EPI_space_file', reg, 'inputspec.EPI_space_file')
        hires_workflow.connect(input_node, 'FS_ID', reg,
                                'inputspec.freesurfer_subject_ID')
        hires_workflow.connect(
            input_node, 'FS_subject_dir', reg, 'inputspec.freesurfer_subject_dir')
        hires_workflow.connect(
            input_node, 'standard_file', reg, 'inputspec.standard_file')

        # temporal filtering
        hires_workflow.connect(
            motion_proc, 'outputspec.motion_corrected_files', sgfilter, 'in_file')

        # node for percent signal change
        hires_workflow.connect(input_node, 'psc_func', psc, 'func')
        hires_workflow.connect(sgfilter, 'out_file', psc, 'in_file')

        # connect filtering and psc results to output node
        hires_workflow.connect(sgfilter, 'out_file',
                                output_node, 'temporal_filtered_files')
        hires_workflow.connect(
            psc, 'out_file', output_node, 'percent_signal_change_files')

        # retroicor functionality
        # if analysis_info['perform_physio'] == 1:
        #     retr = create_retroicor_workflow(
        #         name='retroicor', order_or_timing=analysis_info['retroicor_order_or_timing'])

        #     # # retroicor can take the crudest form of epi file, so that it proceeds quickly
        #     hires_workflow.connect(
        #         sgfilter, 'out_file', retr, 'inputspec.in_files')

        #     hires_workflow.connect(
        #         datasource, 'physio', retr, 'inputspec.phys_files')
        #     hires_workflow.connect(
        #         input_node, 'nr_dummies', retr, 'inputspec.nr_dummies')
        #     hires_workflow.connect(
        #         input_node, 'MB_factor', retr, 'inputspec.MB_factor')
        #     hires_workflow.connect(input_node, 'tr', retr, 'inputspec.tr')
        #     hires_workflow.connect(
        #         input_node, 'slice_direction', retr, 'inputspec.slice_direction')
        #     hires_workflow.connect(
        #         input_node, 'slice_timing', retr, 'inputspec.slice_timing')
        #     hires_workflow.connect(
        #         input_node, 'slice_order', retr, 'inputspec.slice_order')
        #     hires_workflow.connect(
        #         input_node, 'phys_sample_rate', retr, 'inputspec.phys_sample_rate')

        #     # fit nuisances from retroicor
        #     hires_workflow.connect(
        #         retr, 'outputspec.evs', fit_nuis, 'slice_regressor_list')
        #     hires_workflow.connect(
        #         motion_proc, 'outputspec.extended_motion_correction_parameters', fit_nuis, 'vol_regressors')
        #     hires_workflow.connect(psc, 'out_file', fit_nuis, 'in_file')

        #     hires_workflow.connect(fit_nuis, 'res_file', av_r, 'in_files')

        #     hires_workflow.connect(
        #         retr, 'outputspec.new_phys', datasink, 'phys.log')
        #     hires_workflow.connect(
        #         retr, 'outputspec.fig_file', datasink, 'phys.figs')
        #     hires_workflow.connect(
        #         retr, 'outputspec.evs', datasink, 'phys.evs')

        #     hires_workflow.connect(fit_nuis, 'res_file', datasink, 'phys.res')
        #     hires_workflow.connect(fit_nuis, 'rsq_file', datasink, 'phys.rsq')
        #     hires_workflow.connect(
        #         fit_nuis, 'beta_file', datasink, 'phys.betas')

        #     hires_workflow.connect(av_r, 'out_file', datasink, 'av_r')

    ########################################################################################
    # masking stuff if doing mri analysis
    ########################################################################################

        # all_mask_opds = ['dc'] + analysis_info[u'avg_subject_RS_label_folders']
        # all_mask_lds = [''] + analysis_info[u'avg_subject_RS_label_folders']

        # # loop across different folders to mask
        # # untested as yet.
        # masking_list = []
        # dilate_list = []
        # for opd, label_directory in zip(all_mask_opds, all_mask_lds):
        #     dilate_list.append(
        #         pe.MapNode(interface=fsl.maths.DilateImage(
        #             operation='mean', kernel_shape='sphere', 
        #             kernel_size=analysis_info['dilate_kernel_size']),
        #             name='dilate_' + label_directory, iterfield=['in_file']))

        #     masking_list.append(create_masks_from_surface_workflow(
        #         name='masks_from_surface_' + label_directory))

        #     masking_list[-1].inputs.inputspec.label_directory = label_directory
        #     masking_list[-1].inputs.inputspec.fill_thresh = 0.005
        #     masking_list[-1].inputs.inputspec.re = '*.label'

        #     hires_workflow.connect(
        #         motion_proc, 'outputspec.EPI_space_file', 
        #         masking_list[-1], 'inputspec.EPI_space_file')
        #     hires_workflow.connect(
        #         input_node, 'output_directory', 
        #         masking_list[-1], 'inputspec.output_directory')
        #     hires_workflow.connect(
        #         input_node, 'FS_subject_dir', 
        #         masking_list[-1], 'inputspec.freesurfer_subject_dir')
        #     hires_workflow.connect(
        #         input_node, 'FS_ID', 
        #         masking_list[-1], 'inputspec.freesurfer_subject_ID')
        #     hires_workflow.connect(
        #         reg, 'rename_register.out_file', 
        #         masking_list[-1], 'inputspec.reg_file')

        #     hires_workflow.connect(
        #         masking_list[-1], 'outputspec.masks', dilate_list[-1], 'in_file')
        #     hires_workflow.connect(
        #         dilate_list[-1], 'out_file', datasink, 'masks.' + opd)

        # # # surface-based label import in to EPI space, but now for RS labels
        # # these should have been imported to the subject's FS folder,
        # # see scripts/annot_conversion.sh
        # RS_masks_from_surface = create_masks_from_surface_workflow(
        #     name='RS_masks_from_surface')
        # RS_masks_from_surface.inputs.inputspec.label_directory = analysis_info[
        #     'avg_subject_label_folder']
        # RS_masks_from_surface.inputs.inputspec.fill_thresh = 0.005
        # RS_masks_from_surface.inputs.inputspec.re = '*.label'

        # hires_workflow.connect(motion_proc, 'outputspec.EPI_space_file',
        #     RS_masks_from_surface, 'inputspec.EPI_space_file')
        # hires_workflow.connect(input_node, 'output_directory',
        #     RS_masks_from_surface, 'inputspec.output_directory')
        # hires_workflow.connect(input_node, 'FS_subject_dir',
        #     RS_masks_from_surface, 'inputspec.freesurfer_subject_dir')
        # hires_workflow.connect(input_node, 'FS_ID', 
        #     RS_masks_from_surface, 'inputspec.freesurfer_subject_ID')
        # hires_workflow.connect(reg, 'rename_register.out_file', 
        #     RS_masks_from_surface, 'inputspec.reg_file')

        # hires_workflow.connect(RS_masks_from_surface,
        #                         'outputspec.masks', RS_dilate_cortex, 'in_file')
        # hires_workflow.connect(RS_dilate_cortex, 'out_file', datasink,
        #                         'masks.' + analysis_info['avg_subject_label_folder'])

    ########################################################################################
    # wrapping up, sending data to datasink
    ########################################################################################

        # hires_workflow.connect(bet_epi, 'out_file', datasink, 'bet.epi')
        # hires_workflow.connect(bet_epi, 'mask_file', datasink, 'bet.epimask')
        # hires_workflow.connect(bet_topup, 'out_file', datasink, 'bet.topup')
        # hires_workflow.connect(bet_topup, 'mask_file', datasink, 'bet.topupmask')

        # hires_workflow.connect(nuc, 'out_file', datasink, 'nuc')
        hires_workflow.connect(sgfilter, 'out_file', datasink, 'tf')
        hires_workflow.connect(psc, 'out_file', datasink, 'psc')

        # hires_workflow.connect(datasource, 'physio', datasink, 'phys')

        # average across all nprf files
        hires_workflow.connect(input_node, 'av_func', av, 'func')
        # hires_workflow.connect(psc, 'out_file', scf_PRF, 'in_files')
        hires_workflow.connect(psc, 'out_file', av, 'in_files')
        hires_workflow.connect(av, 'out_file', datasink, 'av')

        # # leave one out averaging
        # hires_workflow.connect(scf_PRF, 'out_files', rename_loo, 'in_file')
        # hires_workflow.connect(scf_PRF, 'out_files', loo, 'input_list')

        # hires_workflow.connect(input_node, 'av_func', av_loo, 'func')
        # hires_workflow.connect(loo, 'out_lists', av_loo, 'in_files')
        # hires_workflow.connect(rename_loo, 'out_file',
        #                         av_loo, 'output_filename')

        # hires_workflow.connect(av_loo, 'out_file', datasink, 'av.loo')

        # if analysis_info['perform_blockdesign_glm'] == 1:
        #     hires_workflow.connect(
        #         av_loo, 'out_file', cv_bd_glm, 'train_file')
        #     hires_workflow.connect(psc, 'out_file', cv_bd_glm, 'test_file')
        #     hires_workflow.connect(
        #         input_node, 'bd_design_matrix_file', 
        #         cv_bd_glm, 'design_matrix_file')

        #     hires_workflow.connect(cv_bd_glm, 'out_files', 
        #         datasink, 'cv.glm')

        # # ica on all PRF runs
        # hires_workflow.connect(input_node, 'tr', mel_PRF, 'tr_sec')
        # hires_workflow.connect(sgfilter, 'out_file', scf_PRF_sg, 'in_files')
        # hires_workflow.connect(scf_PRF_sg, 'out_files', mel_PRF, 'in_files')
        # hires_workflow.connect(mel_PRF, 'out_dir', datasink, 'ica.PRF')
        # hires_workflow.connect(mel_PRF, 'report_dir',
        #                         datasink, 'ica.PRF.report')

        # # ica on all RS runs
        # hires_workflow.connect(input_node, 'tr', mel_RS, 'tr_sec')
        # hires_workflow.connect(sgfilter, 'out_file', scf_RS, 'in_files')
        # hires_workflow.connect(scf_RS, 'out_files', mel_RS, 'in_files')
        # hires_workflow.connect(mel_RS, 'out_dir', datasink, 'ica.RS')
        # hires_workflow.connect(mel_RS, 'report_dir',
        #                         datasink, 'ica.RS.report')

    return hires_workflow
