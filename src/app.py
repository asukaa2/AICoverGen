import gradio as gr
import os
import sys
from argparse import ArgumentParser


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
now_dir = os.path.join(BASE_DIR, 'src')
sys.path.append(now_dir)

from tabs.inference import generate_tab
from tabs.inference import download_tab


if __name__ == '__main__':
    parser = ArgumentParser(description='Generate a AI cover song in the song_output/id directory.', add_help=True)
    parser.add_argument("--share", action="store_true", dest="share_enabled", default=False, help="Enable sharing")
    parser.add_argument("--listen", action="store_true", default=False, help="Make the WebUI reachable from your local network.")
    parser.add_argument('--listen-host', type=str, help='The hostname that the server will use.')
    parser.add_argument('--listen-port', type=int, help='The listening port that the server will use.')
    args = parser.parse_args()

    
    with gr.Blocks(title='AICoverGenWebUI') as app:

        gr.Label('AICoverGen WebUI created with ❤️', show_label=False)

        # main tab
        with gr.Tab("Generate"):
            generate_tab()
                            
            
        # Download tab
        with gr.Tab('Download model'):
            download_tab()

            
    app.launch(
        share=args.share_enabled,
        enable_queue=True,
        server_name=None if not args.listen else (args.listen_host or '0.0.0.0'),
        server_port=args.listen_port,
    )
