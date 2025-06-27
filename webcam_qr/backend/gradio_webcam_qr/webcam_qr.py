from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from gradio.components.base import Component
from gradio.events import Events

class webcam_qr(Component):

    EVENTS = [
        Events.change,
    ]

    def __init__(
        self,
        height: int | str | None = None,
        width: int | str | None = None,
        label: str | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        show_label: bool | None = None,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | None = None,
        mirror_webcam: bool = True,
        placeholder: str | None = None,
        show_fullscreen_button: bool = True,
        scan_qr_enabled: bool = True,
        scan_qr_interval: int = 100,
        scan_qr_once: bool = True,
    ):
        self.mirror_webcam = mirror_webcam
        self.height = height
        self.width = width
        self.show_fullscreen_button = show_fullscreen_button
        self.placeholder = placeholder
        self.scan_qr_enabled = scan_qr_enabled
        self.scan_qr_interval = scan_qr_interval
        self.scan_qr_once = scan_qr_once
        super().__init__(
            label=label,
            inputs=inputs,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            key=key,
        )

    def preprocess(self, payload: None) -> None:
        return payload

    def postprocess(self, value: str) -> str:
        return value
    
    @property
    def skip_api(self):
        return True

    def example_payload(self) -> Any:
        return None

    def example_value(self) -> Any:
        return None
