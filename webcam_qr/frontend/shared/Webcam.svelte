<script lang="ts">
	import jsQR from "jsqr";
	import { createEventDispatcher, onMount, onDestroy } from "svelte";

	let canvas: HTMLCanvasElement;
	let video: HTMLVideoElement;
	let stream: MediaStream | null = null;

	let scanning = false;
	let rafId: number | null = null;

	export let value: null | string;
	export let scanQREnabled = true;
	export let scanQROnce = true;

	const dispatch = createEventDispatcher<{
		error: string;
		change: undefined;
	}>();


	onMount(() => {
		initWebcam();
	});

	onDestroy(() => {
		stopScanning();
		if (stream) {
			stream.getTracks().forEach(track => track.stop());
		}
	});

	async function initWebcam() {
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: "environment" }
			});
			video.srcObject = stream;
			video.setAttribute("playsinline", "true");
			video.play();

			video.onloadedmetadata = () => {
				startScanning();
			};
		} catch (err) {
			console.error("Could not access webcam", err);
		}
	}

	function startScanning() {
		if (scanning) return;
		scanning = true;

		console.log("Starting QR code scanning...");

		function tick() {
			if (!video || video.readyState !== 4) {
				rafId = requestAnimationFrame(tick);
				return;
			}

			const width = video.videoWidth;
			const height = video.videoHeight;

			canvas.width = width;
			canvas.height = height;

			const ctx = canvas.getContext("2d");
			if (!ctx) return;

			ctx.drawImage(video, 0, 0, width, height);
			const imageData = ctx.getImageData(0, 0, width, height);

			const code = jsQR(imageData.data, width, height, {
				inversionAttempts: "dontInvert"
			});

			if (code) {
				console.log("QR Code detected:", value);

				value = code.data;
				dispatch("change");
				
				// Draw the QR bounding box
				const lineColor = "#FF3B58";
				drawLine(ctx, code.location.topLeftCorner, code.location.topRightCorner, lineColor);
				drawLine(ctx, code.location.topRightCorner, code.location.bottomRightCorner, lineColor);
				drawLine(ctx, code.location.bottomRightCorner, code.location.bottomLeftCorner, lineColor);
				drawLine(ctx, code.location.bottomLeftCorner, code.location.topLeftCorner, lineColor);
				
				// To scan only once:
				if (scanQROnce) {
					stopScanning();
					return;
				}
			}
			rafId = requestAnimationFrame(tick);
		}
		tick();
	}

	function stopScanning() {
		console.log("Stopping QR code scanning...");

		scanning = false;
		if (rafId !== null) {
			cancelAnimationFrame(rafId);
			rafId = null;
		}
	}

	function drawLine(ctx: CanvasRenderingContext2D, begin: any, end: any, color: string) {
		ctx.beginPath();
		ctx.moveTo(begin.x, begin.y);
		ctx.lineTo(end.x, end.y);
		ctx.lineWidth = 4;
		ctx.strokeStyle = color;
		ctx.stroke();
	}

	$: {
		if (scanQREnabled) {
			startScanning();
		} else {
			stopScanning();
		}
	}

</script>

<style>
	.container {
		position: relative;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	canvas {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}

	video {
		display: none;
	}
</style>

<div class="container">
	<!-- svelte-ignore a11y-media-has-caption -->
	<video bind:this={video}></video>
	<canvas bind:this={canvas}></canvas>
</div>