<script lang="ts">
	import { createEventDispatcher, tick } from "svelte";
	import { BlockLabel } from "@gradio/atoms";
	import { Image as ImageIcon } from "@gradio/icons";
	import {
		type I18nFormatter,
	} from "@gradio/utils";
	import Webcam from "./Webcam.svelte";

	export let value: null | string = null;
	export let label: string | undefined = undefined;
	export let show_label: boolean;

	export let mirror_webcam: boolean;
	export let root: string;
	export let i18n: I18nFormatter;
	export let show_fullscreen_button = true;

	export let scanQREnabled:boolean;
	export let scanQRinterval: number;
	export let scanQROnce: boolean;

	const dispatch = createEventDispatcher<{
		change: undefined;
	}>();
</script>

<BlockLabel {show_label} Icon={ImageIcon} label={label || "Image"} />

<div data-testid="image" class="image-container">
	<div
		class="upload-container"
		class:reduced-height={true}
		style:width={"auto"}
	>
		<Webcam
			{root}
			bind:value
			on:error
			{mirror_webcam}
			{show_fullscreen_button}
			{i18n}
			{scanQREnabled}
			{scanQRinterval}
			{scanQROnce}
			on:change={() => dispatch("change")}
		/>
	</div>
</div>

<style>
	.upload-container {
		display: flex;
		align-items: center;
		justify-content: center;

		height: 100%;
		flex-shrink: 1;
		max-height: 100%;
	}

	.reduced-height {
		height: calc(100% - var(--size-10));
	}

	.image-container {
		display: flex;
		height: 100%;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		max-height: 100%;
	}
</style>
