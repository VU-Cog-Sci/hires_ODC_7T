import unittest
import glob
import os.path as op


def fit_BD_glm(
    in_file,
    sg_filter_order,
    sg_filter_window_length,
    design_matrix_file
):
    """Performs a GLM on nifti-file in_file, then performs CV prediction on test_file
    the stimulus definition is taken from ../cartesius/all_prf.py.
    Uses standard HRF.
    Assumes slices to be the last spatial dimension of nifti in_file,
    and time to be the last of all dimensions of nifti in_file.

    Parameters
    ----------
    in_file : str
        Absolute path to nifti-file.

    Returns
    -------
    res_file : str
        Absolute path to nifti-file containing residuals after regression.
    rsq_file : str
        Absolute path to nifti-file containing rsq of regression.
    beta_file : str
        Absolute path to nifti-file containing betas from regression.
    T_file : str
        Absolute path to nifti-file containing T-values from regression.
    p_file : str
        Absolute path to nifti-file containing -log10(p) from regression.

    """

    import nibabel as nib
    import numpy as np
    import numpy.linalg as LA
    import os
    from sklearn import decomposition
    from scipy.signal import savgol_filter, fftconvolve
    from scipy.stats import t
    from spynoza.nodes.utils import get_scaninfo
    import pandas as pd
    import tempfile
    from math import sin, cos
    # from hrf_estimation import spmt

    out_folder = tempfile.mkdtemp()

    in_nii = nib.load(in_file)
    TR, dims, dyns, voxsize, affine = get_scaninfo(in_file)
    header = in_nii.header

    # import data and convert nans to numbers
    func_data = np.nan_to_num(in_nii.get_data())

    # visual design matrix
    visual_dm = pd.read_csv(design_matrix_file, sep='\t')
    visual_dm = visual_dm[['red','blue','constant']]

    # data containers
    residual_data = np.zeros_like(func_data)
    rsq_data = np.zeros(list(dims[:-1]))
    # there's always an intercept, and the visual design is also first.
    nr_regressors = visual_dm.shape[0]

    beta_data = np.zeros(list(dims[:-1]) + [nr_regressors])
    T_data = np.zeros(list(dims[:-1]) + [nr_regressors])
    p_data = np.zeros(list(dims[:-1]) + [nr_regressors])

    reshaped_data = func_data.reshape((-1, dyns))

    # fit
    betas, sse, rank, svs = LA.lstsq(visual_dm, reshaped_data.T)

    # predicted data, rsq and residuals
    prediction = np.dot(betas.T, visual_dm.T)
    rsq = 1.0 - np.sum((prediction - reshaped_data)**2, axis=-1) / \
        np.sum(reshaped_data.squeeze()**2, axis=-1)
    residuals = reshaped_data - prediction

    # and do stats
    design_matrix_rank = np.linalg.matrix_rank(visual_dm.T)
    df = residuals.shape[-1] - design_matrix_rank

    contrasts = np.matrix(np.eye(visual_dm.shape[1]))
    contrasts_in_dm = [np.array(contrast * np.linalg.pinv(np.dot(
        visual_dm.T, visual_dm)) * contrast.T).squeeze() for contrast in contrasts]

    standard_errors = [np.sqrt((sse / df) * contrast_in_dm)
                       for contrast_in_dm in contrasts_in_dm]
    T_stats = np.array([np.squeeze(np.array(np.dot(contrast, betas) / standard_error))
                        for contrast, standard_error in zip(contrasts, standard_errors)])

    p_vals = -np.log10(np.array([np.squeeze([t.cdf(-np.abs(ts), df)
                                             for ts in T_stat]) for T_stat in T_stats]))

    # reshape and save
    residual_data = residuals.T.reshape((dims[0], dims[1], dims[2], dims[-1]))
    rsq_data = rsq.reshape((dims[0], dims[1], dims[2]))
    beta_data = betas.T.reshape(
        (dims[0], dims[1], dims[2], visual_dm.shape[0]))
    p_data = p_vals.T.reshape((dims[0], dims[1], dims[2], visual_dm.shape[0]))
    T_data = T_stats.T.reshape((dims[0], dims[1], dims[2], visual_dm.shape[0]))

    # save files
    residual_img = nib.Nifti1Image(np.nan_to_num(
        residual_data), affine=affine, header=header)
    res_file = os.path.abspath(os.path.join(
        out_folder, os.path.split(in_file)[1][:-7] + '_BD-GLM_res.nii.gz'))
    nib.save(residual_img, res_file)

    rsq_img = nib.Nifti1Image(np.nan_to_num(
        rsq_data), affine=affine, header=header)
    rsq_file = os.path.abspath(os.path.join(
        out_folder, os.path.split(in_file)[1][:-7] + '_BD-GLM_rsq.nii.gz'))
    nib.save(rsq_img, rsq_file)

    beta_img = nib.Nifti1Image(np.nan_to_num(
        beta_data), affine=affine, header=header)
    beta_file = os.path.abspath(os.path.join(
        out_folder, os.path.split(in_file)[1][:-7] + '_BD-GLM_betas.nii.gz'))
    nib.save(beta_img, beta_file)

    T_img = nib.Nifti1Image(np.nan_to_num(
        T_data), affine=affine, header=header)
    T_file = os.path.abspath(os.path.join(
        out_folder, os.path.split(in_file)[1][:-7] + '_BD-GLM_T.nii.gz'))
    nib.save(T_img, T_file)

    p_img = nib.Nifti1Image(np.nan_to_num(
        p_data), affine=affine, header=header)
    p_file = os.path.abspath(os.path.join(out_folder, os.path.split(
        in_file)[1][:-7] + '_BD-GLM_logp.nii.gz'))
    nib.save(p_img, p_file)

    del(residual_data)
    del(func_data)

    ########################################################################################
    # at this point, we will perform the cross-validation to get the CV rsq
    ########################################################################################

    test_nii = nib.load(test_file)
    TR, dims, dyns, voxsize, affine = get_scaninfo(test_file)
    header = test_nii.header

    test_data = np.nan_to_num(test_nii.get_data())
    reshaped_test_data = test_data.reshape((-1, dyns))
    cv_rsq = 1.0 - np.sum((prediction - reshaped_test_data)**2,
                          axis=-1) / np.sum(reshaped_test_data.squeeze()**2, axis=-1)
    cv_rsq_data = cv_rsq.reshape((dims[0], dims[1], dims[2]))

    cv_rsq_img = nib.Nifti1Image(np.nan_to_num(
        cv_rsq_data), affine=affine, header=header)
    cv_rsq_file = os.path.abspath(os.path.join(
        out_folder, os.path.split(in_file)[1][:-7] + '_BD-GLM_cv_rsq.nii.gz'))
    nib.save(cv_rsq_img, cv_rsq_file)

    out_files = [res_file, rsq_file, beta_file, T_file, p_file, cv_rsq_file]
    print("saved CV block design GLM results as %s" % (str(out_files)))
    # return paths
    return out_files
