import gradio as gr
from gradio_webcam_qr import webcam_qr


def on_qr_read(qr_code):
    print(qr_code)


with gr.Blocks() as demo:
    with gr.Row():
        input_img = webcam_qr(
            mirror_webcam=False,
            show_fullscreen_button=False,
            show_label=False,
            scan_qr_enabled=True,
            scan_qr_once=False,
            scan_qr_interval=0,
        )
    input_img.change(
        on_qr_read,
        input_img
    )


if __name__ == "__main__":
    demo.launch()
