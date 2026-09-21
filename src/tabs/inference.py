from gradio import gr
import os
from core import song_cover_pipeline




def swap_visibility():
    return gr.update(visible=True), gr.update(visible=False), gr.update(value=''), gr.update(value=None)


def process_file_upload(file):
    return file.name, gr.update(value=file.name)


def show_hop_slider(pitch_detection_algo):
    if pitch_detection_algo == 'mangio-crepe':
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)

def generate_tab():
  rvc_model = gr.Dropdown(voice_models, label='Voice Models', info='Models folder "AICoverGen --> rvc_models". After new models are added into this folder, click the refresh button')
  ref_btn = gr.Button('Refresh Models 🔁', variant='primary')

  with gr.Column() as yt_link_col:
    song_input = gr.Text(label='Song input', info='Link to a song on YouTube or full path to a local file. For file upload, click the button below.')
    show_file_upload_button = gr.Button('Upload file instead')
    
  with gr.Column(visible=False) as file_upload_col:
    local_file = gr.File(label='Audio file')
    song_input_file = gr.UploadButton('Upload 📂', file_types=['audio'], variant='primary')
    show_yt_link_button = gr.Button('Paste YouTube link/Path to local file instead')
    song_input_file.upload(process_file_upload, inputs=[song_input_file], outputs=[local_file, song_input])

    with gr.Column():
      pitch = gr.Slider(-3, 3, value=0, step=1, label='Pitch Change (Vocals ONLY)', info='Generally, use 1 for male to female conversions and -1 for vice-versa. (Octaves)')
      pitch_all = gr.Slider(-12, 12, value=0, step=1, label='Overall Pitch Change', info='Changes pitch/key of vocals and instrumentals together. Altering this slightly reduces sound quality. (Semitones)')
    show_file_upload_button.click(swap_visibility, outputs=[file_upload_col, yt_link_col, song_input, local_file])
    show_yt_link_button.click(swap_visibility, outputs=[yt_link_col, file_upload_col, song_input, local_file])

    with gr.Accordion('Voice conversion options', open=False):
      with gr.Row():
        index_rate = gr.Slider(0, 1, value=0.5, label='Index Rate', info="Controls how much of the AI voice's accent to keep in the vocals")
        filter_radius = gr.Slider(0, 7, value=3, step=1, label='Filter radius', info='If >=3: apply median filtering median filtering to the harvested pitch results. Can reduce breathiness')
        rms_mix_rate = gr.Slider(0, 1, value=0.25, label='RMS mix rate', info="Control how much to mimic the original vocal's loudness (0) or a fixed loudness (1)")
      with gr.Row():
        protect = gr.Slider(0, 0.5, value=0.33, label='Protect rate', info='Protect voiceless consonants and breath sounds. Set to 0.5 to disable.')
        f0_method = gr.Dropdown(['rmvpe', 'mangio-crepe'], value='rmvpe', label='Pitch detection algorithm', info='Best option is rmvpe (clarity in vocals), then mangio-crepe (smoother vocals)')
        crepe_hop_length = gr.Slider(32, 320, value=128, step=1, visible=False, label='Crepe hop length', info='Lower values leads to longer conversions and higher risk of voice cracks, but better pitch accuracy.')
        f0_method.change(show_hop_slider, inputs=f0_method, outputs=crepe_hop_length)
      keep_files = gr.Checkbox(label='Keep intermediate files', info='Keep all audio files generated in the song_output/id directory, e.g. Isolated Vocals/Instrumentals. Leave unchecked to save space')

      output_format = gr.Dropdown(['mp3', 'wav'], value='mp3', label='Output file type', info='mp3: small file size, decent quality. wav: Large file size, best quality')

      with gr.Row():
        clear_btn = gr.ClearButton(value='Clear', components=[song_input, rvc_model, keep_files, local_file])
        generate_btn = gr.Button("Generate", variant='primary')
      ai_cover = gr.Audio(label='AI Cover', show_share_button=False)
      
      ref_btn.click(update_models_list, None, outputs=rvc_model)
      is_webui = gr.Number(value=1, visible=False)
      generate_btn.click(song_cover_pipeline,
                         inputs=[song_input, rvc_model, pitch, keep_files, is_webui, main_gain, backup_gain,
                                 inst_gain, index_rate, filter_radius, rms_mix_rate, f0_method, crepe_hop_length,
                                 protect, pitch_all, reverb_rm_size, reverb_wet, reverb_dry, reverb_damping,
                                 output_format],
                         outputs=[ai_cover])
      clear_btn.click(lambda: [0, 0, 0, 0, 0.5, 3, 0.25, 0.33, 'rmvpe', 128, 0, 0.15, 0.2, 0.8, 0.7, 'mp3', None],
                      outputs=[pitch, main_gain, backup_gain, inst_gain, index_rate, filter_radius, rms_mix_rate,
                               protect, f0_method, crepe_hop_length, pitch_all, reverb_rm_size, reverb_wet,
                               reverb_dry, reverb_damping, output_format, ai_cover])
