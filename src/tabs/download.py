import json
import os
import shutil
import urllib.request
import zipfile
import gradio as gr


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rvc_models_dir = os.path.join(BASE_DIR, 'rvc_models')
output_dir = os.path.join(BASE_DIR, 'song_output')


def get_current_models(models_dir):
    models_list = os.listdir(models_dir)
    items_to_remove = ['hubert_base.pt', 'MODELS.txt', 'public_models.json', 'rmvpe.pt']
    return [item for item in models_list if item not in items_to_remove]


def update_models_list():
    models_l = get_current_models(rvc_models_dir)
    return gr.Dropdown.update(choices=models_l)


def load_public_models():
    models_table = []
    for model in public_models['voice_models']:
        if not model['name'] in voice_models:
            model = [model['name'], model['description'], model['credit'], model['url'], ', '.join(model['tags'])]
            models_table.append(model)

    tags = list(public_models['tags'].keys())
    return gr.DataFrame.update(value=models_table), gr.CheckboxGroup.update(choices=tags)


def extract_zip(extraction_folder, zip_name):
    os.makedirs(extraction_folder)
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(extraction_folder)
    os.remove(zip_name)

    index_filepath, model_filepath = None, None
    for root, dirs, files in os.walk(extraction_folder):
        for name in files:
            if name.endswith('.index') and os.stat(os.path.join(root, name)).st_size > 1024 * 100:
                index_filepath = os.path.join(root, name)

            if name.endswith('.pth') and os.stat(os.path.join(root, name)).st_size > 1024 * 1024 * 40:
                model_filepath = os.path.join(root, name)

    if not model_filepath:
        raise gr.Error(f'No .pth model file was found in the extracted zip. Please check {extraction_folder}.')

    # move model and index file to extraction folder
    os.rename(model_filepath, os.path.join(extraction_folder, os.path.basename(model_filepath)))
    if index_filepath:
        os.rename(index_filepath, os.path.join(extraction_folder, os.path.basename(index_filepath)))

    # remove any unnecessary nested folders
    for filepath in os.listdir(extraction_folder):
        if os.path.isdir(os.path.join(extraction_folder, filepath)):
            shutil.rmtree(os.path.join(extraction_folder, filepath))


def download_online_model(url, dir_name, progress=gr.Progress()):
    try:
        progress(0, desc=f'[~] Downloading voice model with name {dir_name}...')
        zip_name = url.split('/')[-1]
        extraction_folder = os.path.join(rvc_models_dir, dir_name)
        if os.path.exists(extraction_folder):
            raise gr.Error(f'Voice model directory {dir_name} already exists! Choose a different name for your voice model.')

        if 'pixeldrain.com' in url:
            url = f'https://pixeldrain.com/api/file/{zip_name}'

        urllib.request.urlretrieve(url, zip_name)

        progress(0.5, desc='[~] Extracting zip...')
        extract_zip(extraction_folder, zip_name)
        return f'[+] {dir_name} Model successfully downloaded!'

    except Exception as e:
        raise gr.Error(str(e))


def upload_local_model(zip_path, dir_name, progress=gr.Progress()):
    try:
        extraction_folder = os.path.join(rvc_models_dir, dir_name)
        if os.path.exists(extraction_folder):
            raise gr.Error(f'Voice model directory {dir_name} already exists! Choose a different name for your voice model.')

        zip_name = zip_path.name
        progress(0.5, desc='[~] Extracting zip...')
        extract_zip(extraction_folder, zip_name)
        return f'[+] {dir_name} Model successfully uploaded!'

    except Exception as e:
        raise gr.Error(str(e))


def filter_models(tags, query):
    models_table = []

    # no filter
    if len(tags) == 0 and len(query) == 0:
        for model in public_models['voice_models']:
            models_table.append([model['name'], model['description'], model['credit'], model['url'], model['tags']])

    # filter based on tags and query
    elif len(tags) > 0 and len(query) > 0:
        for model in public_models['voice_models']:
            if all(tag in model['tags'] for tag in tags):
                model_attributes = f"{model['name']} {model['description']} {model['credit']} {' '.join(model['tags'])}".lower()
                if query.lower() in model_attributes:
                    models_table.append([model['name'], model['description'], model['credit'], model['url'], model['tags']])

    # filter based on only tags
    elif len(tags) > 0:
        for model in public_models['voice_models']:
            if all(tag in model['tags'] for tag in tags):
                models_table.append([model['name'], model['description'], model['credit'], model['url'], model['tags']])

    # filter based on only query
    else:
        for model in public_models['voice_models']:
            model_attributes = f"{model['name']} {model['description']} {model['credit']} {' '.join(model['tags'])}".lower()
            if query.lower() in model_attributes:
                models_table.append([model['name'], model['description'], model['credit'], model['url'], model['tags']])

    return gr.DataFrame.update(value=models_table)


def pub_dl_autofill(pub_models, event: gr.SelectData):
    return gr.Text.update(value=pub_models.loc[event.index[0], 'URL']), gr.Text.update(value=pub_models.loc[event.index[0], 'Model Name'])


def swap_visibility():
    return gr.update(visible=True), gr.update(visible=False), gr.update(value=''), gr.update(value=None)


def process_file_upload(file):
    return file.name, gr.update(value=file.name)



voice_models = get_current_models(rvc_models_dir)
    
with open(os.path.join(rvc_models_dir, 'public_models.json'), encoding='utf8') as infile:
  public_models = json.load(infile)

def download_tab():
  with gr.Tab('From HuggingFace/Pixeldrain URL'):
    with gr.Row():
      model_zip_link = gr.Text(label='Download link to model', info='Should be a zip file containing a .pth model file and an optional .index file.')
      model_name = gr.Text(label='Name your model', info='Give your new model a unique name from your other voice models.')

    with gr.Row():
      download_btn = gr.Button('Download 🌐', variant='primary', scale=19)
      dl_output_message = gr.Text(label='Output Message', interactive=False, scale=20)

      download_btn.click(download_online_model, inputs=[model_zip_link, model_name], outputs=dl_output_message)

      gr.Markdown('## Input Examples')
      gr.Examples(
        [
          ['https://huggingface.co/phant0m4r/LiSA/resolve/main/LiSA.zip', 'Lisa'],
          ['https://pixeldrain.com/u/3tJmABXA', 'Gura'],
          ['https://huggingface.co/Kit-Lemonfoot/kitlemonfoot_rvc_models/resolve/main/AZKi%20(Hybrid).zip', 'Azki']
        ],
        [model_zip_link, model_name],
        [],
        download_online_model,
      )

    with gr.Tab('From Public Index'):
      gr.Markdown('## How to use')

      gr.Markdown('- Click Initialize public models table')
      gr.Markdown('- Filter models using tags or search bar')
      gr.Markdown('- Select a row to autofill the download link and model name')
      gr.Markdown('- Click Download')
      
      with gr.Row():
        pub_zip_link = gr.Text(label='Download link to model')
        pub_model_name = gr.Text(label='Model name')
      
      with gr.Row():
        download_pub_btn = gr.Button('Download 🌐', variant='primary', scale=19)
        pub_dl_output_message = gr.Text(label='Output Message', interactive=False, scale=20)
        filter_tags = gr.CheckboxGroup(value=[], label='Show voice models with tags', choices=[])               
        search_query = gr.Text(label='Search')
               
        load_public_models_button = gr.Button(value='Initialize public models table', variant='primary')

        public_models_table = gr.DataFrame(value=[], headers=['Model Name', 'Description', 'Credit', 'URL', 'Tags'], label='Available Public Models', interactive=False)
        public_models_table.select(pub_dl_autofill, inputs=[public_models_table], outputs=[pub_zip_link, pub_model_name])
        load_public_models_button.click(load_public_models, outputs=[public_models_table, filter_tags])
        search_query.change(filter_models, inputs=[filter_tags, search_query], outputs=public_models_table)
        filter_tags.change(filter_models, inputs=[filter_tags, search_query], outputs=public_models_table)
        download_pub_btn.click(download_online_model, inputs=[pub_zip_link, pub_model_name], outputs=pub_dl_output_message)

        # Upload tab
      with gr.Tab('Upload model'):
        gr.Markdown('## Upload locally trained RVC v2 model and index file')
        gr.Markdown('- Find model file (weights folder) and optional index file (logs/[name] folder)')
        gr.Markdown('- Compress files into zip file')
        gr.Markdown('- Upload zip file and give unique name for voice')
        gr.Markdown('- Click Upload model')
        
        with gr.Row():
          with gr.Column():
            zip_file = gr.File(label='Zip file')

            local_model_name = gr.Text(label='Model name')

        with gr.Row():
          model_upload_button = gr.Button('Upload model', variant='primary', scale=19)
          local_upload_output_message = gr.Text(label='Output Message', interactive=False, scale=20)                
          model_upload_button.click(upload_local_model, inputs=[zip_file, local_model_name], outputs=local_upload_output_message)

    
