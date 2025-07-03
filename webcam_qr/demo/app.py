import gradio as gr
from gradio_webcam_qr import webcam_qr
import time


def on_qr_read(qr_code):
    return f"{time.time()}: {qr_code}"


with gr.Blocks() as demo:
    input_img = webcam_qr(
        scan_qr_enabled=True,
        scan_qr_once=False,
        show_label=False,
        show_detection=False,
    )
    text_qr = gr.Textbox(label="QR Code")
    button_on = gr.Button("Enable QR Scanning")
    button_off = gr.Button("Disable QR Scanning")
    button_on.click(
        lambda: webcam_qr(scan_qr_enabled=True),
        outputs=input_img
    )
    button_off.click(
        lambda: webcam_qr(scan_qr_enabled=False),
        outputs=input_img
    )
    input_img.change(
        on_qr_read,
        input_img,
        text_qr,
        show_progress=False,
    )


if __name__ == "__main__":
    demo.launch()
