<script lang="ts">
	import jsQR from "jsqr";
	import { createEventDispatcher, onMount, onDestroy } from "svelte";
	import { DropdownArrow } from "@gradio/icons";
	import { IconButton, IconButtonWrapper } from "@gradio/atoms";
	import { Maximize, Minimize } from "@gradio/icons";
	import {
		type I18nFormatter,
	} from "@gradio/utils";
	import { StreamingBar } from "@gradio/statustracker";
	import WebcamPermissions from "./WebcamPermissions.svelte";
	import { fade } from "svelte/transition";
	import {
		get_devices,
		get_video_stream,
		set_available_devices
	} from "./stream_utils";

	const include_audio = false;
	let video_source: HTMLVideoElement;
	let available_video_devices: MediaDeviceInfo[] = [];
	let selected_device: MediaDeviceInfo | null = null;
	let time_limit: number | null = null;
	let canvas: HTMLCanvasElement;
	let is_full_screen = false;
	let qrScanTimer: number | null = null;
	
	export let root = "";
	export let mirror_webcam: boolean;
	export let i18n: I18nFormatter;
	export let value: null | string = "aaa";
	export let show_fullscreen_button = true;
	export let scanQREnabled = true;
	export let scanQRinterval = 100;
	export let scanQROnce = true;

	const dispatch = createEventDispatcher<{
		error: string;
		change: undefined;
	}>();

	onMount(() => {
		canvas = document.createElement("canvas");
		document.addEventListener("fullscreenchange", () => {
			is_full_screen = !!document.fullscreenElement;
		});
	});

	const toggle_full_screen = async (): Promise<void> => {
		if (!is_full_screen) {
			await video_source.requestFullscreen();
		} else {
			await document.exitFullscreen();
		}
	};


	const handle_device_change = async (event: InputEvent): Promise<void> => {
		const target = event.target as HTMLInputElement;
		const device_id = target.value;

		await get_video_stream(include_audio, video_source, device_id).then(
			async (local_stream) => {
				stream = local_stream;
				// adjust_video_to_native_resolution(video_source, stream);
				selected_device =
					available_video_devices.find(
						(device) => device.deviceId === device_id
					) || null;
				options_open = false;
				// log_video_resolutions(video_source, local_stream);
			}
		);
	};

	async function access_webcam(): Promise<void> {
		try {
			get_video_stream(include_audio, video_source)
				.then(async (local_stream) => {
					webcam_accessed = true;
					available_video_devices = await get_devices();
					stream = local_stream;
					// adjust_video_to_native_resolution(video_source, stream);
					// log_video_resolutions(video_source, local_stream);
				})
				.then(() => set_available_devices(available_video_devices))
				.then((devices) => {
					available_video_devices = devices;

					const used_devices = stream
						.getTracks()
						.map((track) => track.getSettings()?.deviceId)[0];

					selected_device = used_devices
						? devices.find((device) => device.deviceId === used_devices) ||
							available_video_devices[0]
						: available_video_devices[0];
				})
				.then(() => {
					if (scanQREnabled) startQRScanning();
				});

			if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
				dispatch("error", i18n("image.no_webcam_support"));
			}
		} catch (err) {
			if (err instanceof DOMException && err.name == "NotAllowedError") {
				dispatch("error", i18n("image.allow_webcam_access"));
			} else {
				throw err;
			}
		}
	}

	let stream: MediaStream;
	let webcam_accessed = false;
	let options_open = false;

	export function click_outside(node: Node, cb: any): any {
		const handle_click = (event: MouseEvent): void => {
			if (
				node &&
				!node.contains(event.target as Node) &&
				!event.defaultPrevented
			) {
				cb(event);
			}
		};

		document.addEventListener("click", handle_click, true);

		return {
			destroy() {
				document.removeEventListener("click", handle_click, true);
			}
		};
	}

	function handle_click_outside(event: MouseEvent): void {
		event.preventDefault();
		event.stopPropagation();
		options_open = false;
	}


	function startQRScanning() {
		if (qrScanTimer) return; // already scanning

		console.log("Start scanning for QR codes...");
		
		qrScanTimer = window.setInterval(() => {
			if (!scanQREnabled || !video_source || video_source.readyState !== 4) {
				stopQRScanning();
				return;
			}

			canvas.width = video_source.videoWidth;
			canvas.height = video_source.videoHeight;

			const ctx = canvas.getContext("2d");
			if (!ctx) {
				console.error("Failed to get canvas context for QR scanning");
				return;
			}

			ctx.drawImage(video_source, 0, 0, canvas.width, canvas.height);
			const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

			const code = jsQR(imageData.data, canvas.width, canvas.height);
			if (code) {
				console.log("QR Code Found:", code.data);
				value = code.data;
				dispatch("change");
				if (scanQROnce) {
					stopQRScanning();
				}
			}
		}, scanQRinterval);
	}

	function stopQRScanning() {
		console.log("QR scanning stop");
		if (qrScanTimer) {
			clearInterval(qrScanTimer);
			qrScanTimer = null;
		}
	}
	
	onDestroy(() => {
		stopQRScanning();
	});

	$: {
		if (scanQREnabled) {
			startQRScanning();
		} else {
			stopQRScanning();
		}
	}


</script>

<div class="wrap">
	<StreamingBar {time_limit} />
	<!-- svelte-ignore a11y-media-has-caption -->
	<!-- need to suppress for video streaming https://github.com/sveltejs/svelte/issues/5967 -->

	<IconButtonWrapper>
		{#if !is_full_screen && show_fullscreen_button}
			<IconButton
				Icon={Maximize}
				label={is_full_screen ? "Exit full screen" : "View in full screen"}
				on:click={toggle_full_screen}
			/>
		{/if}

		{#if is_full_screen && show_fullscreen_button}
			<IconButton
				Icon={Minimize}
				label={is_full_screen ? "Exit full screen" : "View in full screen"}
				on:click={toggle_full_screen}
			/>
		{/if}
	</IconButtonWrapper>

	<!-- svelte-ignore a11y-media-has-caption -->
	<video
		bind:this={video_source}
		class:flip={mirror_webcam}
		class:hide={!webcam_accessed}
	/>

	{#if !webcam_accessed}
		<div
			in:fade={{ delay: 100, duration: 200 }}
			title="grant webcam access"
			style="height: 100%"
		>
			<WebcamPermissions on:click={async () => access_webcam()} />
		</div>
	{:else}
		<div class="button-wrap">
				<button
					class="icon"
					on:click={() => (options_open = true)}
					aria-label="select input source"
				>
					<DropdownArrow />
				</button>
		</div>
		{#if options_open && selected_device}
			<select
				class="select-wrap"
				aria-label="select source"
				use:click_outside={handle_click_outside}
				on:change={handle_device_change}
			>
				<button
					class="inset-icon"
					on:click|stopPropagation={() => (options_open = false)}
				>
					<DropdownArrow />
				</button>
				{#if available_video_devices.length === 0}
					<option value="">{i18n("common.no_devices")}</option>
				{:else}
					{#each available_video_devices as device}
						<option
							value={device.deviceId}
							selected={selected_device.deviceId === device.deviceId}
						>
							{device.label}
						</option>
					{/each}
				{/if}
			</select>
		{/if}
	{/if}
</div>

<style>
	.wrap {
		position: relative;
		width: var(--size-full);
		height: var(--size-full);
	}

	.hide {
		display: none;
	}
	
	
	video {
		width: var(--size-full);
		height: var(--size-full);
		object-fit: cover;
	}
	
	video:fullscreen {
		object-fit: contain;
		width: 100%;
		height: 100%;
	}

	.button-wrap {
		position: absolute;
		background-color: var(--block-background-fill);
		border: 1px solid var(--border-color-primary);
		border-radius: var(--radius-xl);
		padding: var(--size-1-5);
		display: flex;
		bottom: var(--size-2);
		left: 50%;
		transform: translate(-50%, 0);
		box-shadow: var(--shadow-drop-lg);
		border-radius: var(--radius-xl);
		line-height: var(--size-3);
		color: var(--button-secondary-text-color);
	}

	@media (--screen-md) {
		button {
			bottom: var(--size-4);
		}
	}

	@media (--screen-xl) {
		button {
			bottom: var(--size-8);
		}
	}

	.icon {
		width: 18px;
		height: 18px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.flip {
		transform: scaleX(-1);
	}

	.select-wrap {
		-webkit-appearance: none;
		-moz-appearance: none;
		appearance: none;
		color: var(--button-secondary-text-color);
		background-color: transparent;
		width: 95%;
		font-size: var(--text-md);
		position: absolute;
		bottom: var(--size-2);
		background-color: var(--block-background-fill);
		box-shadow: var(--shadow-drop-lg);
		border-radius: var(--radius-xl);
		z-index: var(--layer-top);
		border: 1px solid var(--border-color-primary);
		text-align: left;
		line-height: var(--size-4);
		white-space: nowrap;
		text-overflow: ellipsis;
		left: 50%;
		transform: translate(-50%, 0);
		max-width: var(--size-52);
	}

	.select-wrap > option {
		padding: 0.25rem 0.5rem;
		border-bottom: 1px solid var(--border-color-accent);
		padding-right: var(--size-8);
		text-overflow: ellipsis;
		overflow: hidden;
	}

	.select-wrap > option:hover {
		background-color: var(--color-accent);
	}

	.select-wrap > option:last-child {
		border: none;
	}

	.inset-icon {
		position: absolute;
		top: 5px;
		right: -6.5px;
		width: var(--size-10);
		height: var(--size-5);
		opacity: 0.8;
	}

	@media (--screen-md) {
		.wrap {
			font-size: var(--text-lg);
		}
	}
</style>
