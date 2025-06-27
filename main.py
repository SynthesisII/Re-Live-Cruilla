import argparse
import tempfile
import time
from typing import Literal
from enum import Enum, auto
from functools import partial
from pathlib import Path

import gradio as gr
import qrcode
from loguru import logger
from PIL import Image

import config


class State(Enum):
    home = auto()
    take_photo = auto()
    generating = auto()
    results = auto()


# Global app state
state: State = State.results
user_image: Image.Image | None = None
result_qr_image: Image.Image | None = None


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
logger.warning("TODO")


# Assets paths
root_path = Path(__file__).parent
favicon_path = str(root_path / "images/favicon.png").replace('\\', '/')
home_background_path = str(root_path / "images/home_background.png").replace('\\', '/')
photo_background_path = str(root_path / "images/photo_background.png").replace('\\', '/')
results_background_path = str(root_path / "images/results_background.png").replace('\\', '/')
camera_button_path = str(root_path / "images/camera.png").replace('\\', '/')
clear_camera_path = str(root_path / "images/clear_image.png").replace('\\', '/')
end_button_path = str(root_path / "images/end.png").replace('\\', '/')


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

.webcam {{
    border-width: 0px !important;
    pointer-events: none;
}}
#webcam_qr video {{
    width: 34vw;
    position: fixed;
    top: -26vh;
    right: 8vw;
}}
#webcam_photo video {{
    width: 57vw;
    position: fixed;
    bottom: -14vh;
    right: 50%;
    transform: translateX(50%);
}}
#webcam_photo img {{
    width: 57vw;
    position: fixed;
    bottom: -14vh;
    right: 50%;
    transform: translateX(50%);
}}
.webcam [title="grant webcam access"] {{
    display: none !important;
}}

#qr_survey img {{
    position: fixed;
    bottom: 3vh;
    right: -25vw;
    visibility: visible;
    pointer-events: none;
    height: 25vh;
}}
#qr_survey {{
    visibility: hidden;
}}

#camera_button {{
    background-image: url("/gradio_api/file={camera_button_path}");
    background-size: contain;
    background-position: center;
    background-repeat: no-repeat;
    background-color: transparent;
    position: fixed;
    bottom: 5vh;
    z-index: 100;
    height: 15%;
    width: 11%;
    right: 50%;
    transform: translateX(50%);
}}
#clear_button {{
    background-image: url("/gradio_api/file={clear_camera_path}");
    background-size: contain;
    background-position: center;
    background-repeat: no-repeat;
    background-color: transparent;
    position: fixed;
    bottom: 5vh;
    z-index: 100;
    height: 15%;
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

#button_restart {{
    background-image: url("/gradio_api/file={end_button_path}");
    background-size: contain;
    background-position: center;
    background-repeat: no-repeat;
    background-color: transparent;
    position: fixed;
    bottom: 3vh;
    left: 35%;
    z-index: 100;
    height: 6%;
    width: 10%;
}}

#output_image {{
    visibility: hidden;
}}
#output_image img {{
    position: fixed;
    height: 90vh;
    right: -23vw;
    z-index: 1;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    visibility: visible;
}}

#qr_image img {{
    position: fixed;
    height: 29vh;
    left: -27vw;
    z-index: 10;
    top: 50%;
    transform: translateY(41%);
    pointer-events: none;
    visibility: visible;
}}
#qr_image {{
    visibility: hidden;
}}

#loading_container_qr {{
    position: fixed;
    z-index: 100;
    bottom: 22%;
    left: 21vw;
}}
#loading_container_results {{
    position: fixed;
    z-index: 100;
    right: 45vh;
    top: 50%;
    transform: translateY(-50%);
}}

#blur-results {{
    position: fixed;
    z-index: 2;
    top: 0%;
    left: 0%;
    width: 100vw;
    height: 100vh;
    backdrop-filter: blur(3px);
    -webkit-backdrop-filter: blur(3px); /* for Safari */
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


clear_photo_js = """
() => {
    const imageInputDiv = document.getElementById("webcam_photo");
    if (imageInputDiv) {
        const clearButton = imageInputDiv.querySelector('[aria-label="Remove Image"]');
        if (clearButton) {
            clearButton.click();
        } else {
            console.warn('Clear button not found inside #webcam');
        }
    } else {
        console.warn('Div with ID "webcam" not found');
    }
}
"""


html_home = """
<div id="home_background"></div>
"""


html_take_photo = """
<div id="take_photo_background"></div>
"""


html_results = """
<div id="results_background"></div>
"""


html_count_down = """<div id="countdown" class="countdown-container"></div>"""


html_blur_results = """
<div id="blur-results"></div>
"""


# html_loading = """
# <div class="loading_container" id="loading_container_{id}">
#   <div class="dot"></div>
#   <div class="dot"></div>
#   <div class="dot"></div>
#   <div class="dot"></div>
# </div>

# <style>
#     .loading_container {{
#         --uib-size: 100px;
#         --uib-color: #eedc00;
#         --uib-speed: 1s;
#         --uib-dot-size: calc(var(--uib-size) * 0.18);
#         display: flex;
#         align-items: flex-end;
#         justify-content: space-between;
#         height: calc(var(--uib-size) * 0.5);
#         width: var(--uib-size);
#     }}

#     .dot {{
#         flex-shrink: 0;
#         width: calc(var(--uib-size) * 0.17);
#         height: calc(var(--uib-size) * 0.17);
#         border-radius: 50%;
#         background-color: var(--uib-color);
#         transition: background-color 0.3s ease;
#     }}

#     .dot:nth-child(1) {{
#         animation: jump var(--uib-speed) ease-in-out calc(var(--uib-speed) * -0.45)
#         infinite;
#     }}

#     .dot:nth-child(2) {{
#         animation: jump var(--uib-speed) ease-in-out calc(var(--uib-speed) * -0.3)
#         infinite;
#     }}

#     .dot:nth-child(3) {{
#         animation: jump var(--uib-speed) ease-in-out calc(var(--uib-speed) * -0.15)
#         infinite;
#     }}

#     .dot:nth-child(4) {{
#         animation: jump var(--uib-speed) ease-in-out infinite;
#     }}

#     @keyframes jump {{
#         0%,
#         100% {{
#         transform: translateY(0px);
#         }}

#         50% {{
#         transform: translateY(-200%);
#         }}
#     }}
# </style>
# """


# def get_html_loading(position: Literal["qr", "results"]):
#     return html_loading.format(id=position)


def set_state(new_state: State):
    global state
    logger.info(f"Setting state: {new_state}")
    state = new_state


def set_user_image(image: Image.Image | None):
    global user_image
    logger.debug(f"Set user image: {image}")
    user_image = image


def get_user_image() -> Image.Image:
    global user_image
    if user_image is not None:
        return user_image.copy()
    return None


def set_result_image(image: Image.Image | None):
    global result_image
    logger.debug(f"Set result image: {image}")
    result_image = image


def get_result_image():
    return result_image


def reset_state():
    set_user_image(None)
    set_result_image(None)
    set_state(State.home)


# def on_button_gen():
#     user_image = get_user_image()

#     if user_image is None:
#         raise gr.Error(labels.error_no_user_image)

#     logger.info("Starting generation...")
#     set_state(State.generating)

#     # Save the user image in a temporal file
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
#         # Rotate the image
#         if config.cam_rotation == 90:
#             user_image = user_image.transpose(Image.ROTATE_270)
#         elif config.cam_rotation == -90:
#             user_image = user_image.transpose(Image.ROTATE_90)
#         elif config.cam_rotation != 0:
#             logger.warning("Consider using one of the following camera "
#                            "rotations for better results: [0, 90, -90]")
#             user_image = user_image.rotate(-config.cam_rotation, expand=True)
        
#         # Save the image
#         user_image.save(tmp_img, format="PNG")
#         tmp_img.flush()  # Ensure it's written to disk

#         # Stat generation
#         image_result = cruilla_generator.generate(
#             input_image_path=tmp_img.name,
#             role=selected_role,
#             steps=config.generation_steps,
#         )
#         set_result_image(image_result)
#         # TODO: Upload image and set QR image
    
#     set_state(State.results)


# def on_button_result_restart():
#     reset_state()
#     gr_col_home = gr.Column(visible=True)
#     gr_col_result = gr.Column(visible=False)
#     gr_html_home = gr.HTML(get_html_home())
#     gr_image_gen_cam = None
#     gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer = on_set_role()
#     gr_button_gen_cam = gr.Button(visible=True)
#     gr_button_gen_clear = gr.Button(visible=False)
#     gr_image_result = gr.Image(None)
#     gr_image_result_qr = gr.Image(None)
#     return (gr_col_home, gr_col_result, gr_html_home, gr_image_gen_cam,
#             gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer,
#             gr_button_gen_cam, gr_button_gen_clear, gr_image_result,
#             gr_image_result_qr)


def on_gr_image_photo(gr_image_photo):
    set_user_image(gr_image_photo)
    gr_button_take_photo = gr.Button(visible=gr_image_photo is None)
    gr_button_clear_photo = gr.Button(visible=gr_image_photo is not None)
    return gr_button_take_photo, gr_button_clear_photo


def on_timer_update_state():
    gr_col_home = gr.Column(visible=False)
    gr_col_take_photo = gr.Column(visible=False)

    if state is State.home:
        gr_col_home = gr.Column(visible=True)
    elif state is State.take_photo:
        gr_col_take_photo = gr.Column(visible=True)

    return (gr_col_home, gr_col_take_photo)


# def on_progress_step(current, total, preview_image):
#     logger.info(f"Generation step: {current}/{total}")
#     if preview_image:
#         preview_image = preview_image[1]
#         resized_image = preview_image.resize(
#             (cruilla_generator.latent_width, cruilla_generator.latent_height),
#             resample=Image.NEAREST
#         )
#         set_result_image(resized_image)


def on_demo_load():
    # Create a QR image with the survey link
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(config.survey_link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    gr_image_survey_qr = gr.Image(qr_img)

    return gr_image_survey_qr


with gr.Blocks(js=main_js, css=main_css) as demo:
    gr_timer_update_state = gr.Timer(config.ui_update_state_interval)
    with gr.Column(visible=state is State.home) as gr_col_home:
        gr.HTML(html_home)
        gr_webcam_qr = gr.Image(
            sources="webcam",
            elem_id="webcam_qr",
            elem_classes="webcam",
        )
        gr_image_survey_qr = gr.Image(
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="qr_survey"
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
            elem_classes="webcam",
            interactive=True,
            type="pil",
            webcam_options=gr.WebcamOptions(mirror=False),
        )
        gr_button_take_photo = gr.Button(
            "",
            elem_id="camera_button"
        )
        gr_button_clear_photo = gr.Button(
            "",
            elem_id="clear_button",
            visible=False
        )

    with gr.Column(visible=state is State.results) as gr_col_result:
        gr.HTML(html_results)
        gr_image_avatar = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="avatar_image",
        )
        gr_image_pet = gr.Image(
            None,
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="pet_image",
        )
        gr_image_result_qr = gr.Image(
            show_download_button=False,
            show_share_button=False,
            show_fullscreen_button=False,
            show_label=False,
            elem_id="qr_result_image"
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
        [gr_col_home, gr_col_take_photo]
    )
    # gr_button_gen.click(on_button_gen, show_progress=False)
    # gr_button_result_restart.click(
    #     on_button_result_restart,
    #     None,
    #     [gr_col_home, gr_col_result, gr_html_home, gr_image_gen_cam,
    #      gr_html_radio_dj, gr_html_radio_guitar, gr_html_radio_singer,
    #      gr_button_gen_cam, gr_button_gen_clear, gr_image_result,
    #      gr_image_result_qr],
    #     show_progress=False,
    # )
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
    gr_button_clear_photo.click(
        lambda: None,
        js=clear_photo_js,
    )
    gr_image_photo.input(
        on_gr_image_photo,
        gr_image_photo,
        [gr_button_take_photo, gr_button_clear_photo],
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
