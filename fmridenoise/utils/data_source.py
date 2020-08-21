from bids import  BIDSLayout
import typing as t

FILTER_FMRI = {
    'extension': ['nii', 'nii.gz'],
    'suffix': 'bold',
    'desc': 'preproc',
    'space': 'MNI152NLin2009cAsym'
}
FILTER_FMRI_AROMA = {
    'extension': ['nii', 'nii.gz'],
    'suffix': 'bold',
    'desc': 'smoothAROMAnonaggr',
}
FILTER_CONF = {
    'extension': 'tsv',
    'suffix': 'regressors',
    'desc': 'confounds',
}
FILTER_CONF_JSON = {
    'extension': 'json',
    'suffix': 'regressors',
    'desc': 'confounds',
}


def get_confounds_image_files_pairs(layout: BIDSLayout, aroma_images: bool) -> t.Tuple[t.List[str], t.List[str]]:
    filters = {
        'conf_raw' : FILTER_CONF,
        'conf_json' : FILTER_CONF_JSON
    }
    if aroma_images:
        filters['fmri_prep_aroma'] = FILTER_FMRI_AROMA
    else:
        filters['fmri_prep'] = FILTER_FMRI
    files = {}
    for name, filter in filters.items():
        files[name] = layout.get(**filter)
    return files


if __name__ == '__main__':
    path = "/mnt/Data/new_dataset"
    layout = BIDSLayout(
            root=path,
            derivatives=[f"{path}/derivatives/fmriprep"],
            validate=True,
            index_metadata=False
        )
    print(get_confounds_image_files_pairs(layout, True))
