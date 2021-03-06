""" Example of a relatively simple GLM fit

The script defines a General Linear Model and fits it to fMRI data.

Author: Bertrand Thirion, dohmatob elvis dopgima, 2015
"""

import os
import numpy as np
import pandas as pd

import nibabel as nib
from nilearn.plotting import plot_stat_map, show
from nilearn.image import mean_img

from nistats.design_matrix import make_design_matrix
from nistats.glm import FirstLevelGLM
from nistats.datasets import fetch_spm_auditory

# fetch spm auditory data
subject_data = fetch_spm_auditory()
fmri_img = nib.concat_images(subject_data.func)
# compute bg unto which activation will be projected
mean_img = mean_img(fmri_img)

# construct experimental paradigm
tr = 7.
n_scans = 96
epoch_duration = 6 * tr  # duration in seconds
conditions = ['rest', 'active'] * 8
n_blocks = len(conditions)
duration = epoch_duration * np.ones(n_blocks)
onset = np.linspace(0, (n_blocks - 1) * epoch_duration, n_blocks)
paradigm = pd.DataFrame(
    {'onset': onset, 'duration': duration, 'name': conditions})

# construct design matrix
frame_times = np.linspace(0, (n_scans - 1) * tr, n_scans)
drift_model = 'Cosine'
hrf_model = 'Canonical With Derivative'
period_cut = 4. * epoch_duration
design_matrix = make_design_matrix(
    frame_times, paradigm, hrf_model=hrf_model, drift_model=drift_model,
    period_cut=period_cut)

# specify contrasts
contrast_matrix = np.eye(design_matrix.shape[1])
contrasts = dict([(column, contrast_matrix[i])
                  for i, column in enumerate(design_matrix.columns)])

# Specify one interesting contrast
contrasts = {'active-rest': contrasts['active'] - contrasts['rest']}

# fit GLM
print('\r\nFitting a GLM (this takes time) ..')
fmri_glm = FirstLevelGLM(noise_model='ar1', standardize=False).fit(
    [fmri_img], design_matrix)

print("Computing contrasts ..")
output_dir = 'results'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

for contrast_id, contrast_val in contrasts.items():
    print("\tcontrast id: %s" % contrast_id)
    z_map, t_map, eff_map, var_map = fmri_glm.transform(
        contrasts[contrast_id], contrast_name=contrast_id, output_z=True,
        output_stat=True, output_effects=True, output_variance=True)

    # store stat maps to disk
    for dtype, out_map in zip(['z', 't', 'effects', 'variance'],
                              [z_map, t_map, eff_map, var_map]):
        map_dir = os.path.join(output_dir, '%s_maps' % dtype)
        if not os.path.exists(map_dir):
            os.makedirs(map_dir)
        map_path = os.path.join(map_dir, '%s.nii.gz' % contrast_id)
        nib.save(out_map, map_path)
        print("\t\t%s map: %s" % (dtype, map_path))

    # plot one activation map
    display = plot_stat_map(z_map, bg_img=mean_img, threshold=3.0,
                            display_mode='z', cut_coords=3, black_bg=True,
                            title=contrast_id)

show()
