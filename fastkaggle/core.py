# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['iskaggle', 'import_kaggle', 'setup_comp', 'nb_meta', 'push_notebook', 'mk_dataset', 'get_dataset', 'get_pip_library',
           'push_dataset']

# %% ../00_core.ipynb 3
import os,json,subprocess
from fastcore.utils import *

# %% ../00_core.ipynb 4
iskaggle = os.environ.get('KAGGLE_KERNEL_RUN_TYPE', '')

# %% ../00_core.ipynb 5
def import_kaggle():
    "Import kaggle API, using Kaggle secrets `kaggle_username` and `kaggle_key` if needed"
    if iskaggle:
        from kaggle_secrets import UserSecretsClient
        sec = UserSecretsClient()
        os.environ['KAGGLE_USERNAME'] = sec.get_secret("kaggle_username")
        if not os.environ['KAGGLE_USERNAME']: raise Exception("Please insert your Kaggle username and key into Kaggle secrets")
        os.environ['KAGGLE_KEY'] = sec.get_secret("kaggle_key")
    from kaggle import api
    return api

# %% ../00_core.ipynb 7
def setup_comp(competition, install=''):
    "Get a path to data for `competition`, downloading it if needed"
    if iskaggle:
        if install:
            os.system(f'pip install -Uqq {install}')
        return Path('../input')/competition
    else:
        path = Path(competition)
        api = import_kaggle()
        if not path.exists():
            import zipfile
            api.competition_download_cli(str(competition))
            zipfile.ZipFile(f'{competition}.zip').extractall(str(competition))
        return path

# %% ../00_core.ipynb 10
def nb_meta(user, id, title, file, competition=None, private=True, gpu=False, internet=True):
    "Get the `dict` required for a kernel-metadata.json file"
    d = {
      "id": f"{user}/{id}",
      "title": title,
      "code_file": file,
      "language": "python",
      "kernel_type": "notebook",
      "is_private": private,
      "enable_gpu": gpu,
      "enable_internet": internet,
      "keywords": [],
      "dataset_sources": [],
      "kernel_sources": []
    }
    if competition: d["competition_sources"] = [f"competitions/{competition}"]
    return d

# %% ../00_core.ipynb 12
def push_notebook(user, id, title, file, path='.', competition=None, private=True, gpu=False, internet=True):
    "Push notebook `file` to Kaggle Notebooks"
    meta = nb_meta(user, id, title, file=file, competition=competition, private=private, gpu=gpu, internet=internet)
    path = Path(path)
    nm = 'kernel-metadata.json'
    path.mkdir(exist_ok=True, parents=True)
    with open(path/nm, 'w') as f: json.dump(meta, f, indent=2)
    api = import_kaggle()
    api.kernels_push_cli(str(path))

# %% ../00_core.ipynb 15
def mk_dataset(dataset_path, # Local path to create dataset in
               title, # Name of the dataset
               force=False, # Should it overwrite or error if exists?
               upload=True # Should it upload and create on kaggle
              ):
    '''Creates minimal dataset metadata needed to push new dataset to kaggle'''
    dataset_path = Path(dataset_path)
    dataset_path.mkdir(exist_ok=force,parents=True)
    api = import_kaggle()
    api.dataset_initialize(dataset_path)
    md = json.load(open(dataset_path/'dataset-metadata.json'))
    md['title'] = title
    md['id'] = md['id'].replace('INSERT_SLUG_HERE',title)
    json.dump(md,open(dataset_path/'dataset-metadata.json','w'))
    if upload: (dataset_path/'empty.txt').touch()
    api.dataset_create_new(str(dataset_path),public=True,dir_mode='zip')

# %% ../00_core.ipynb 17
def get_dataset(dataset_path, # Local path to download dataset to
                dataset_slug, # Dataset slug (ie "zillow/zecon")
                unzip=True, # Should it unzip after downloading?
                force=False # Should it overwrite or error if dataset_path exists?
               ):
    '''Downloads an existing dataset and metadata from kaggle'''
    if not force: assert not Path(dataset_path).exists()
    api = import_kaggle()
    api.dataset_metadata(dataset_slug,str(dataset_path))
    api.dataset_download_files(dataset_slug,str(dataset_path))
    if unzip:
        zipped_file = Path(dataset_path)/f"{dataset_slug.split('/')[-1]}.zip"
        import zipfile
        with zipfile.ZipFile(zipped_file, 'r') as zip_ref:
            zip_ref.extractall(Path(dataset_path))
        zipped_file.unlink()
    

# %% ../00_core.ipynb 19
def get_pip_library(dataset_path, # Local path to download pip library to
                    pip_library, # name of library for pip to install
                    pip_cmd="pip" # pip base to use (ie "pip3" or "pip")
                   ):    
    '''Download the whl files for pip_library and store in dataset_path'''
    bashCommand = f"{pip_cmd} download {pip_library} -d {dataset_path}"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

# %% ../00_core.ipynb 21
def push_dataset(dataset_path, # Local path where dataset is stored 
                 version_comment # Comment associated with this dataset update
                ):
    '''Push dataset update to kaggle.  Dataset path must contain dataset metadata file'''
    api = import_kaggle()
    api.dataset_create_version(str(dataset_path),version_comment,dir_mode='zip')
