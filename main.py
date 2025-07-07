import argparse
import json
from enum import Enum, auto
from pathlib import Path

import gradio as gr
import numpy as np
import qrcode
from gradio_webcam_qr import webcam_qr
from loguru import logger
from PIL import Image

import config
import labels
from AVATAR.AvatarGenCruilla import AvatarGenCruilla
from PET.PetGenCruilla import PetGenCruilla
from utils import (make_avatar_composition, make_final_composition,
                   make_pet_composition, plot_user_vector, upload_image)


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
avatar_image: Image.Image | None = None


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
avatar_generator = AvatarGenCruilla()


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
    height: 11%;
    width: 10%;
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
    height: 70vh;
    left: -30vw;
    z-index: 10;
    top: 50%;
    transform: translateY(-38%);
    pointer-events: none;
    visibility: visible;
}}

#pet_image img {{
    position: fixed;
    height: 70vh;
    right: -30vw;
    z-index: 10;
    top: 50%;
    transform: translateY(-38%);
    pointer-events: none;
    visibility: visible;
}}

#qr_result_image img {{
    position: fixed;
    height: 30vh;
    left: 50%;
    z-index: 29;
    top: 51%;
    transform: translateX(-50%);
    pointer-events: none;
    visibility: visible;
}}

#photo_roi{{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -25%);
    width: 443px;
    height: 624px;
    border: 2px solid rgba(0, 0, 0, 0.5);
    border-radius: 4px;
    background-color: transparent;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
    z-index: 100;
}}

#qr_code_text {{
    position: fixed;
    left: -9999px;
}}
"""


# Page JS
main_js = f"""
() => {{
    const enableQRInput = {'true' if config.enable_qr_scanner_input else 'false'};
    const checkWebcamInterval = 1000;
    const focusQRInterval = 1000;
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
        const selector = '#button_restart';
        let clickTimeout = null;
        let hasClicked = false;

        setInterval(() => {{
            const button = document.querySelector(selector);

            if (button && !button.disabled) {{
                if (!clickTimeout) {{
                    console.log(`Button found. Will click in ${{restartWait / 1000}} seconds.`);
                    clickTimeout = setTimeout(() => {{
                        const btn = document.querySelector(selector);
                        if (btn && !btn.disabled) {{
                            btn.click();
                            console.log('Button clicked.');
                            // Reset for future clicks
                            hasClicked = true;
                        }} else {{
                            console.log('Button no longer available at click time.');
                        }}
                        clickTimeout = null;
                    }}, restartWait);
                }}
            }} else {{
                if (clickTimeout) {{
                    clearTimeout(clickTimeout);
                    clickTimeout = null;
                    console.log('Button not found or disabled. Click timeout cancelled.');
                }}

                // Reset click flag when button disappears so we can click again next time
                if (hasClicked) {{
                    hasClicked = false;
                }}
            }}
        }}, restartInterval);
    }}
    waitForRestart();

    if (enableQRInput) {{
        document.addEventListener('keydown', (event) => {{
            if (event.key === 'Enter') {{
                console.log("Enter key pressed");
                const qr_input_button = document.getElementById("qr_input_button");
                if (qr_input_button) {{
                    console.log("qr_input_button click");
                    qr_input_button.click();
                }} else {{
                    console.log("qr_input_button not found");
                }}
            }}
        }});

        function focusQRInput() {{
            const column_home = document.getElementById("column_home");
            if (!column_home || column_home.classList.contains('hide')) {{
                return;
            }}
            const qr_code_text = document.querySelector('#qr_code_text textarea');
            if (qr_code_text) {{
                if (document.activeElement !== qr_code_text) {{
                    console.log("QR code text input focus");
                    qr_code_text.focus();
                }}
            }} else {{
                console.log("QR code text input not found");
            }}
        }}
        setInterval(focusQRInput, focusQRInterval);
    }}
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
<div id="photo_roi"></div>
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


def set_avatar_image(image: Image.Image | None):
    global avatar_image
    logger.debug(f"Set avatar image: {image}")
    avatar_image = image


def set_result_qr_image(image: Image.Image | None):
    global result_qr_image
    logger.debug(f"Set result qr image: {image}")
    result_qr_image = image


def set_user_vector(vector: np.ndarray | None):
    global user_vector
    logger.debug(f"Set user vector: {vector}")
    user_vector = vector


def generate():
    try:
        # Generate pet
        logger.info("Generating pet image")
        pet_image = pet_generator.generate_pet_image(user_vector)
        comp_pet_image = make_pet_composition(pet_image)
        set_pet_image(comp_pet_image)

        # Generate avatar
        logger.info("Generating avatar image")
        user_image_np = np.array(user_image)[:,:,::-1]
        avatar_image = avatar_generator.generate_avatar(user_image_np, user_vector)
        comp_avatar_image = make_avatar_composition(avatar_image)
        set_avatar_image(comp_avatar_image)

        # Generate plot
        user_vector_plot_img = plot_user_vector(user_vector)

        # Create composition
        final_image = make_final_composition(
            avatar_image=avatar_image,
            pet_image=pet_image,
            plot_image=user_vector_plot_img,
        )

        # Upload composition image
        image_link = upload_image(final_image)
        logger.info(f"Image uploaded to: {image_link}")
        image_result_qr = qrcode.make(image_link).get_image()
        set_result_qr_image(image_result_qr)

        logger.success("Generation done")
    except Exception as e:
        logger.exception("Error generating images")
        gr.Warning("Error generating images")
    set_state(State.results)


def on_image_photo(gr_image_photo):
    set_user_image(gr_image_photo)
    if gr_image_photo is not None:
        set_state(State.generating)
        generate()
    return pet_image, avatar_image, result_qr_image


def on_timer_update_state():
    gr_col_home = gr.Column(visible=False)
    gr_col_take_photo = gr.Column(visible=False)
    gr_col_generating = gr.Column(visible=False)
    gr_col_result = gr.Column(visible=False)
    gr_html_generating = gr.HTML(html_generating)
    gr_webcam_qr = webcam_qr(scan_qr_enabled=False)
    gr_button_result_restart = gr.Button(interactive=False)

    if state is State.home:
        gr_col_home = gr.Column(visible=True)
        if config.enable_qr_camera_reader:
            gr_webcam_qr = webcam_qr(scan_qr_enabled=True)
    elif state is State.take_photo:
        gr_col_take_photo = gr.Column(visible=True)
    elif state is State.generating:
        gr_col_generating = gr.Column(visible=True)
        gr_html_generating = gr.HTML(html_generating + html_generating_video)
    elif state is State.results:
        gr_col_result = gr.Column(visible=True)
        gr_button_result_restart = gr.Button(interactive=True)

    return (gr_col_home, gr_col_take_photo, gr_col_generating, gr_col_result,
            gr_html_generating, gr_webcam_qr, gr_button_result_restart)


def on_demo_load():
    # Create a QR image with the survey link
    gr_image_survey_qr = qrcode.make(config.survey_link).get_image()
    return gr_image_survey_qr


def parse_qr(qr_data: str) -> np.ndarray:
    vector_shape = (18,)
    vector = (np.array([float(i) for i in qr_data.split(",")]) / 100) .astype(np.float64)
    vector = vector + np.random.normal(loc=0.0, scale=1e-6, size=vector.shape)
    vector = np.clip(vector, 0, 10)
    if vector.shape != vector_shape:
        raise ValueError(f"Invalid QR vector size: {vector.shape}, expected {vector_shape}")
    return vector


def on_webcam_qr(gr_webcam_qr):
    if gr_webcam_qr and state is State.home and config.enable_qr_camera_reader:
        logger.info(f"Detected QR: {gr_webcam_qr}")
        try:
            user_vector = parse_qr(gr_webcam_qr)
            set_user_vector(user_vector)
            set_state(State.take_photo)
            return webcam_qr(scan_qr_enabled=False)
        except Exception as e:
            logger.exception("Error parsing the QR data")
            gr.Warning(labels.error_qr_data)
    return webcam_qr()


def on_button_qr_input(gr_text_qr_code):
    if gr_text_qr_code and state is State.home and config.enable_qr_scanner_input:
        logger.info(f"QR code text input: {gr_text_qr_code}")
        try:
            user_vector = parse_qr(gr_text_qr_code)
            set_user_vector(user_vector)
            set_state(State.take_photo)
        except Exception as e:
            logger.exception("Error parsing the QR data")
            gr.Warning(labels.error_qr_data)
    return ""


def on_button_restart():
    logger.info("Resetting state")
    set_user_image(None)
    set_pet_image(None)
    set_user_vector(None)
    set_state(State.home)
    set_result_qr_image(None)
    
    gr_image_photo = gr.Image(None)
    gr_button_result_restart = gr.Button(interactive=False)
    return gr_image_photo, gr_button_result_restart


with gr.Blocks(js=main_js, css=main_css) as demo:
    gr_timer_update_state = gr.Timer(config.ui_update_state_interval)
    with gr.Column(visible=state is State.home, elem_id="column_home") as gr_col_home:
        gr.HTML(html_home)
        gr_webcam_qr = webcam_qr(
            elem_id="webcam_qr",
            scan_qr_once=False,
            show_detection=False,
            visible=config.enable_qr_camera_reader,
        )
        gr_text_qr_code = gr.Textbox(
            elem_id="qr_code_text",
        )
        gr_button_qr_input = gr.Button(
            visible=False,
            elem_id="qr_input_button",
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
        gr_result_qr_image = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="qr_result_image",
            elem_classes="static_image"
        )
        gr_button_result_restart = gr.Button(
            "",
            elem_id="button_restart",
            interactive=False,
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
         gr_html_generating, gr_webcam_qr, gr_button_result_restart]
    )
    gr_webcam_qr.change(
        on_webcam_qr,
        gr_webcam_qr,
        gr_webcam_qr,
        show_progress=False,
    )
    gr_button_qr_input.click(
        on_button_qr_input,
        gr_text_qr_code,
        gr_text_qr_code,
        show_progress=False,
    )
    gr_button_result_restart.click(
        on_button_restart,
        None,
        [gr_image_photo, gr_button_result_restart],
        show_progress=False,
    )
    gr_button_take_photo.click(
        lambda: None,
        js=take_photo_js,
    )
    gr_image_photo.input(
        on_image_photo,
        gr_image_photo,
        [gr_image_pet, gr_image_avatar, gr_result_qr_image],
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
