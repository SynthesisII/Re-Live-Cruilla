
import gradio as gr
from app import demo as app
import os

_docs = {'webcam_qr': {'description': 'A base class for defining methods that all input/output components should have.', 'members': {'__init__': {'height': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'width': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'label': {'type': 'str | None', 'default': 'None', 'description': None}, 'inputs': {'type': 'gradio.components.base.Component\n    | Sequence[gradio.components.base.Component]\n    | set[gradio.components.base.Component]\n    | None', 'default': 'None', 'description': None}, 'show_label': {'type': 'bool | None', 'default': 'None', 'description': None}, 'container': {'type': 'bool', 'default': 'True', 'description': None}, 'scale': {'type': 'int | None', 'default': 'None', 'description': None}, 'min_width': {'type': 'int', 'default': '160', 'description': None}, 'visible': {'type': 'bool', 'default': 'True', 'description': None}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': None}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': None}, 'render': {'type': 'bool', 'default': 'True', 'description': None}, 'key': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'placeholder': {'type': 'str | None', 'default': 'None', 'description': None}, 'scan_qr_enabled': {'type': 'bool', 'default': 'True', 'description': None}, 'scan_qr_once': {'type': 'bool', 'default': 'True', 'description': None}, 'show_detection': {'type': 'bool', 'default': 'True', 'description': None}}, 'postprocess': {'value': {'type': 'str', 'description': "The output data received by the component from the user's function in the backend."}}, 'preprocess': {'return': {'type': 'None', 'description': "The preprocessed input data sent to the user's function in the backend."}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': 'Triggered when the value of the webcam_qr changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'webcam_qr': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_webcam_qr`

<div style="display: flex; gap: 7px;">
<img alt="Static Badge" src="https://img.shields.io/badge/version%20-%200.0.9%20-%20orange">  
</div>

Python library for easily interacting with trained machine learning models
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_webcam_qr
```

## Usage

```python
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

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `webcam_qr`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["webcam_qr"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["webcam_qr"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, the preprocessed input data sent to the user's function in the backend.
- **As output:** Should return, the output data received by the component from the user's function in the backend.

 ```python
def predict(
    value: None
) -> str:
    return value
```
""", elem_classes=["md-custom", "webcam_qr-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          webcam_qr: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
