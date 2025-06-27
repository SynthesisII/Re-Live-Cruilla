<svelte:options accessors={true} />

<script lang="ts">
	import type { Gradio } from "@gradio/utils";
	import ImageUploader from "./shared/ImageUploader.svelte";

	import { Block, Empty } from "@gradio/atoms";
	import { Image } from "@gradio/icons";

	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible = true;
	export let value: null | string = null;
	export let label: string;
	export let show_label: boolean;
	export let root: string;

	export let height: number | undefined;
	export let width: number | undefined;

	export let container = true;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let mirror_webcam: boolean;
	export let show_fullscreen_button: boolean;

	export let scan_qr_enabled:boolean;
	export let scan_qr_interval: number;
	export let scan_qr_once: boolean;

	export let gradio: Gradio<{
		error: string;
		change: undefined;
	}>;

	let upload_component: ImageUploader;
</script>

<Block
	{visible}
	variant={"solid"}
	border_mode={"base"}
	padding={false}
	{elem_id}
	{elem_classes}
	height={height || undefined}
	{width}
	allow_overflow={false}
	{container}
	{scale}
	{min_width}
>
	<ImageUploader
		bind:this={upload_component}
		bind:value
		{root}
		on:error={({ detail }) => gradio.dispatch("error", detail)}
		on:change={() => gradio.dispatch("change")}
		{label}
		{show_label}
		{mirror_webcam}
		{show_fullscreen_button}
		scanQREnabled={scan_qr_enabled}
		scanQRinterval={scan_qr_interval}
		scanQROnce={scan_qr_once}
		i18n={gradio.i18n}
	>
		<Empty unpadded_box={true} size="large"><Image /></Empty>
	</ImageUploader>
</Block>
