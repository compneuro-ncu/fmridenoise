import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib


def create_carpetplot(time_series: np.ndarray, out_fname: str,
                      dpi=300, figsize=(8, 2), format='png'):
    """Generates and saves carpet plot for rois timecourses.

    Args:
        time_series: Timecourse array of size N_timepoints x N_rois. Output of
            fit_transform() NiftiLabelsMasker method.
        out_fname: Carpetplot output filename.
        dpi (:obj:`int`, optional): Dots per inch (default 300).
        figsize (:obj:`tuple`, optional): Size of the figure in inches
            (default (3,8))
        format (:obj:`str`, optional): Image format. Available options include
            'png', 'pdf', 'ps', 'eps' and 'svg'.
    """
    if not isinstance(time_series, np.ndarray):
        raise TypeError('time series should be np.ndarray')

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111)

    ax.imshow(time_series.T, cmap='gray')
    ax.set_xlabel('volume')
    ax.set_ylabel('roi')
    ax.set_yticks([])

    try:
        fig.savefig(out_fname, format=format,
                    transparent=True, bbox_inches='tight')
    except FileNotFoundError:
        print(f'{out_fname} directory not found')



if __name__ == '__main__':

    from nilearn.input_data import NiftiLabelsMasker

    path = 'testdata/sub-01_bold.nii.gz'
    img = nib.load(path)
    parcellation = 'parcellation/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm.nii.gz'
    masker = NiftiLabelsMasker(labels_img=parcellation, standardize=True)
    time_series = masker.fit_transform(img, confounds=None)

    create_carpetplot(time_series, 'testadata/carpet.png')