import argparse
import json
import tempfile
import time
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Literal

import gradio as gr
import numpy as np
import qrcode
from gradio_webcam_qr import webcam_qr
from loguru import logger
from PIL import Image

import config
import labels
from PET.PetGenCruilla import PetGenCruilla


class State(Enum):
    home = auto()
    take_photo = auto()
    generating = auto()
    results = auto()


# Global app state
state: State = State.home
user_image: Image.Image | None = None
result_qr_image: Image.Image | None = None
user_vector: np.ndarray | None = None
pet_image: Image.Image | None = None


# Parse arguments
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-p",
        "--port",
        type=int,
        default=7860,
    )
    ap.add_argument(
        "--ssl",
        action="store_true"
    )
    args = ap.parse_args()


# Load models
logger.info("Loading models")
pet_generator = PetGenCruilla()
logger.warning("TODO")


# Assets paths
root_path = Path(__file__).parent
favicon_path = str(root_path / "res/favicon.png").replace('\\', '/')
home_background_path = str(root_path / "res/home_background.png").replace('\\', '/')
photo_background_path = str(root_path / "res/photo_background.png").replace('\\', '/')
results_background_path = str(root_path / "res/results_background.png").replace('\\', '/')
generating_background_path = str(root_path / "res/generating_background.png").replace('\\', '/')
camera_button_path = str(root_path / "res/camera.png").replace('\\', '/')
clear_camera_path = str(root_path / "res/clear_image.png").replace('\\', '/')
end_button_path = str(root_path / "res/end.png").replace('\\', '/')
generating_video_path = str(root_path / "res/generating_video.mp4").replace('\\', '/')


# Page CSS
main_css = f"""
/* Stop Gradio from fading elements during function execution */
.pending {{
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}}

/* Prevent clicking the bottom Gradio buttons since they are not visible */
footer {{
    pointer-events: none;
    visibility: hidden;
}}

#home_background {{
    background-image:url("/gradio_api/file={home_background_path}");
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-size: cover;
    background-position: top left;
    background-repeat: no-repeat;
    z-index: 0;
    pointer-events: none;
}}

#take_photo_background {{
    background-image:url("/gradio_api/file={photo_background_path}");
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-size: cover;
    background-position: top left;
    background-repeat: no-repeat;
    z-index: 0;
    pointer-events: none;
}}

#generating_background {{
    background-image:url("/gradio_api/file={generating_background_path}");
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-size: cover;
    background-position: top left;
    background-repeat: no-repeat;
    z-index: 0;
    pointer-events: none;
}}

#results_background {{
    background-image:url("/gradio_api/file={results_background_path}");
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-size: cover;
    background-position: top left;
    background-repeat: no-repeat;
    z-index: 0;
    pointer-events: none;
}}

#webcam_qr canvas {{
    position: fixed;
    width: 37vw;
    height: 37vh;
    top: 5vh;
    right: 7vw;
    visibility: visible;
}}
#webcam_qr {{
    visibility: hidden;
}}

#webcam_photo {{
    border-width: 0px !important;
    pointer-events: none;
}}
#webcam_photo [title="grant webcam access"] {{
    display: none !important;
}}
#webcam_photo video {{
    width: 62vw;
    position: fixed;
    bottom: -14vh;
    right: 50%;
    transform: translateX(50%);
}}
#webcam_photo img {{
    width: 62vw;
    position: fixed;
    bottom: -14vh;
    right: 50%;
    transform: translateX(50%);
}}

#qr_survey img {{
    position: fixed;
    bottom: 3vh;
    right: -25vw;
    visibility: visible;
    pointer-events: none;
    height: 25vh;
}}

#camera_button {{
    background-image: url("/gradio_api/file={camera_button_path}");
    background-size: contain;
    background-position: center;
    background-repeat: no-repeat;
    background-color: transparent;
    position: fixed;
    bottom: 8vh;
    z-index: 100;
    height: 14%;
    width: 11%;
    right: 50%;
    transform: translateX(50%);
}}

.countdown-container {{
    position: fixed;
    bottom: 28%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 20px 40px;
    border-radius: 10px;
    font-size: 48px;
    font-family: Arial, sans-serif;
    display: none;
    z-index: 1000;
}}

#generating_video {{
    position: fixed;
    width: 59vw;
    transform: translate(-50%, -50%);
    left: 50%;
    top: 60%;
}}

#button_restart {{
    background-image: url("/gradio_api/file={end_button_path}");
    background-size: contain;
    background-position: center;
    background-repeat: no-repeat;
    background-color: transparent;
    position: fixed;
    top: 4vh;
    right: 4vw;
    z-index: 100;
    height: 6%;
    width: 10%;
}}

.static_image {{
    visibility: hidden;
}}

#avatar_image img {{
    position: fixed;
    height: 55vh;
    left: -31vw;
    z-index: 10;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    visibility: visible;
}}

#pet_image img {{
    position: fixed;
    height: 55vh;
    right: -31vw;
    z-index: 10;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    visibility: visible;
}}

#qr_result_image img {{
    position: fixed;
    height: 29vh;
    left: 50%;
    z-index: 10;
    top: 50%;
    transform: translateY(50%);
    transform: translateX(50%);
    pointer-events: none;
    visibility: visible;
}}

"""


# Page JS
main_js = f"""
() => {{
    const checkWebcamInterval = 1000;
    const restartInterval = 3000;
    const restartWait = {config.reset_wait_time} * 1000;

    function checkAndClickWebcam() {{
        const selector = 'div[title="grant webcam access"]';
        const divs = document.querySelectorAll(selector);

        divs.forEach(div => {{
            const button = div.querySelector('button');
            if (button) {{
                button.click();
                console.log("Grant webcam access");
            }}
        }});
    }}
    setInterval(checkAndClickWebcam, checkWebcamInterval);
    
    function waitForRestart() {{
        selector = '#button_restart'
        const watch = () => {{
            const interval = setInterval(() => {{
                const button = document.querySelector(selector);
                if (button && !button.disabled) {{
                    clearInterval(interval);
                    console.log(`Restart button found. Waiting ${{restartWait / 1000}} seconds before clicking.`);

                    setTimeout(() => {{
                        button.click();
                        console.log('Restart button clicked');
                        watch();
                    }}, restartWait);
                }}
            }}, restartInterval);
        }};
        watch();
    }}
    waitForRestart();
}}
"""


take_photo_js = f"""
() => {{
    let count = {config.cam_count_down};
    const countdownElement = document.getElementById('countdown');
    
    // Show the countdown
    countdownElement.style.display = 'block';
    countdownElement.textContent = count;

    // Update countdown every second
    const timer = setInterval(() => {{
        count--;
        if (count > 0) {{
            countdownElement.textContent = count;
        }} else {{
            // Hide when countdown reaches 0
            countdownElement.style.display = 'none';
            clearInterval(timer);
            
            // Take a photo
            const imageInputDiv = document.getElementById("webcam_photo");
            if (imageInputDiv) {{
                const captureButton = imageInputDiv.querySelector('[aria-label="capture photo"]');

                if (captureButton) {{
                    captureButton.click();
                }} else {{
                    console.warn('Capture button not found inside #webcam');
                }}
            }} else {{
                console.warn('Div with ID "webcam" not found');
            }}
        }}
    }}, 1000);
}}
"""


html_home = """
<div id="home_background"></div>
"""


html_take_photo = """
<div id="take_photo_background"></div>
"""


html_generating = """
<div id="generating_background"></div>
"""


html_generating_video = f"""
<video id="generating_video" src="/gradio_api/file={generating_video_path}" autoplay loop muted playsinline></video>
"""


html_results = """
<div id="results_background"></div>
"""


html_count_down = """<div id="countdown" class="countdown-container"></div>"""


def set_state(new_state: State):
    global state
    logger.info(f"Setting state: {new_state}")
    state = new_state


def set_user_image(image: Image.Image | None):
    global user_image
    logger.debug(f"Set user image: {image}")
    user_image = image


def set_pet_image(image: Image.Image | None):
    global pet_image
    logger.debug(f"Set pet image: {image}")
    pet_image = image
    

def set_user_vector(vector: np.ndarray | None):
    global user_vector
    logger.debug(f"Set user vector: {vector}")
    user_vector = vector


def generate():
    logger.info("Generating pet image")
    pet_image = pet_generator.generate_pet_image(user_vector)
    set_pet_image(pet_image)

    
    logger.info("Generating avatar image")
    logger.warning("TODO")
    
    logger.success("Generation done")
    set_state(State.results)


def on_image_photo(gr_image_photo):
    set_user_image(gr_image_photo)
    if gr_image_photo is not None:
        set_state(State.generating)
        generate()
    return pet_image


def on_timer_update_state():
    gr_col_home = gr.Column(visible=False)
    gr_col_take_photo = gr.Column(visible=False)
    gr_col_generating = gr.Column(visible=False)
    gr_col_result = gr.Column(visible=False)
    gr_html_generating = gr.HTML(html_generating)
    gr_webcam_qr = webcam_qr(scan_qr_enabled=False)

    if state is State.home:
        gr_col_home = gr.Column(visible=True)
        gr_webcam_qr = webcam_qr(scan_qr_enabled=True)
    elif state is State.take_photo:
        gr_col_take_photo = gr.Column(visible=True)
    elif state is State.generating:
        gr_col_generating = gr.Column(visible=True)
        gr_html_generating = gr.HTML(html_generating + html_generating_video)
    elif state is State.results:
        gr_col_result = gr.Column(visible=True)

    return (gr_col_home, gr_col_take_photo, gr_col_generating, gr_col_result,
            gr_html_generating, gr_webcam_qr)


def on_demo_load():
    # Create a QR image with the survey link
    gr_image_survey_qr = qrcode.make(config.survey_link).get_image()
    return gr_image_survey_qr


def parse_qr(qr_data: str) -> np.ndarray:
    data = json.loads(qr_data)
    vector = np.array(data["vector"])
    vector = vector.astype(np.float64)
    # TODO: Remove this!!
    vector = vector + np.random.normal(loc=0.0, scale=0.0001, size=vector.shape)
    return vector


def on_webcam_qr(gr_webcam_qr):
    if gr_webcam_qr:
        logger.info(f"Detected QR: {gr_webcam_qr}")
        try:
            user_vector =parse_qr(gr_webcam_qr)
            set_user_vector(user_vector)
            set_state(State.take_photo)
            return webcam_qr(scan_qr_enabled=False)
        except Exception as e:
            logger.exception("Error parsing the QR data")
            raise gr.Error(labels.error_qr_data)
    return webcam_qr()


def on_button_restart():
    logger.info("Resetting state")
    set_user_image(None)
    set_pet_image(None)
    set_user_vector(None)
    set_state(State.home)


with gr.Blocks(js=main_js, css=main_css) as demo:
    gr_timer_update_state = gr.Timer(config.ui_update_state_interval)
    with gr.Column(visible=state is State.home) as gr_col_home:
        gr.HTML(html_home)
        gr_webcam_qr = webcam_qr(
            elem_id="webcam_qr",
            scan_qr_once=False,
        )
        gr_image_survey_qr = gr.Image(
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="qr_survey",
            elem_classes="static_image",
        )
   
    with gr.Column(visible=state is State.take_photo) as gr_col_take_photo:
        gr.HTML(html_take_photo)
        gr.HTML(html_count_down)
        gr_image_photo = gr.Image(
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            sources=["webcam"],
            elem_id="webcam_photo",
            interactive=True,
            type="pil",
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        gr_button_take_photo = gr.Button(
            "",
            elem_id="camera_button"
        )

    with gr.Column(visible=state is State.generating) as gr_col_generating:
        gr_html_generating = gr.HTML(html_generating)

    with gr.Column(visible=state is State.results) as gr_col_result:
        gr.HTML(html_results)
        gr_image_avatar = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="avatar_image",
            elem_classes="static_image",
        )
        gr_image_pet = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="pet_image",
            elem_classes="static_image"
        )
        gr_image_result_qr = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="qr_result_image",
            elem_classes="static_image",
        )
        gr_button_result_restart = gr.Button(
            "",
            elem_id="button_restart",
        )

    demo.load(
        on_demo_load,
        None,
        [gr_image_survey_qr]
    )
    gr_timer_update_state.tick(
        on_timer_update_state,
        None,
        [gr_col_home, gr_col_take_photo, gr_col_generating, gr_col_result,
         gr_html_generating, gr_webcam_qr]
    )
    gr_webcam_qr.change(
        on_webcam_qr,
        gr_webcam_qr,
        gr_webcam_qr,
        show_progress=False,
    )
    gr_button_result_restart.click(
        on_button_restart,
        show_progress=False,
    )
    # gr_button_gen_dj.click(
    #     partial(on_set_role, role=config.role_dj),
    #     None,
    #     [gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer]
    # )
    # gr_button_gen_guitar.click(
    #     partial(on_set_role, role=config.role_guitar),
    #     None,
    #     [gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer]
    # )
    # gr_button_gen_singer.click(
    #     partial(on_set_role, role=config.role_singer),
    #     None,
    #     [gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer]
    # )
    gr_button_take_photo.click(
        lambda: None,
        js=take_photo_js,
    )
    gr_image_photo.input(
        on_image_photo,
        gr_image_photo,
        [gr_image_pet],
        # None, # [gr_button_take_photo, gr_button_clear_photo],
        show_progress=False,
    )

if __name__ == "__main__":
    logger.info("Launching Gradio app")
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        allowed_paths=[str(root_path)],
        pwa=True,
        favicon_path=favicon_path,
        ssl_verify=False,
        ssl_keyfile="key.pem" if args.ssl else None,
        ssl_certfile="cert.pem" if args.ssl else None,
    )
