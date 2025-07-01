
import numpy as np
import tensorflow.keras
import torch
from deepface import DeepFace
from diffusers import AutoPipelineForImage2Image
from loguru import logger
from PIL import Image
from safetensors.torch import load_file

from . import config
from .utils import (center_crop_to_square, generate_weighted_prompt,
                    remove_background)


class AvatarGenCruilla:

    negative_prompt = """
        deformed, blurry, bad anatomy, disfigured,
        poorly drawn face, mutation, extra limbs,
        ugly, duplicate, morbid, mutilated,
        cluttered background, busy background, detailed background,
        colorful background, textured background, patterned background,
        shadows, gradients, scenery, objects, furniture, environment,
        landscape, people in background, background elements, depth of field,
        photo background, realistic background, 3D background, noise, artifacts
    """

    def __init__(
        self,
        device: str = "cuda",
        cpu_offload: bool = True,
        attention_slicing: bool = True,
        xformers_attention: bool = False,
    ):
        """Create a Cruilla avatar generator and load the models.

        Args:
            device (str, optional): Models device. Defaults to "cuda".
            cpu_offload (bool, optional): Reduce memory usage by selectively
                moving the not required models to CPU. Defaults to True.
            attention_slicing (bool, optional): Reduces memory usage by
                splitting attention computation into smaller chunks.
                Defaults to True.
            xformers_attention (bool, optional): Optimization that speedups the
                inference and lowers the memory usage, only on compatible GPUs.
                Defaults to False.
        """
        self.device = device
        
        logger.info("Loading stable diffusion models...")

        # Load base model
        self.base_pipe = AutoPipelineForImage2Image.from_pretrained(
            config.base_model_path,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            cache_dir=config.cache_path,
        ).to(device)
        if attention_slicing:
            self.base_pipe.enable_attention_slicing()
        if cpu_offload:
            self.base_pipe.enable_model_cpu_offload()
            # self.base_pipe.enable_sequential_cpu_offload()
        if xformers_attention:
            self.base_pipe.enable_xformers_memory_efficient_attention()
        
        # Load fine-tuned UNet
        state_dict = load_file(config.custom_unet_path)
        self.base_pipe.unet.load_state_dict(state_dict, strict=False)

        # Load refiner model
        self.refiner_pipe = AutoPipelineForImage2Image.from_pretrained(
            config.refiner_model_path,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            cache_dir=config.cache_path,
        ).to(device)
        if attention_slicing:
            self.refiner_pipe.enable_attention_slicing()
        if cpu_offload:
            self.refiner_pipe.enable_model_cpu_offload()
            # self.refiner_pipe.enable_sequential_cpu_offload()
        if xformers_attention:
            self.refiner_pipe.enable_xformers_memory_efficient_attention()

    def _get_top_genres(self, user_vector: np.ndarray) -> list:
        top_indices = np.argsort(user_vector)[-3:][::-1]
        return [
            (config.genres[i], user_vector[i])
            for i in top_indices
        ]

    def _analyze_face_image(
        self,
        image: np.ndarray,
    ) -> dict:
        """Extract features from a face image.

        Args:
            image (np.ndarray): A numpy image in BGR format.

        Returns:
            dict: A dictionary with the analysis results.
        """
        demography = DeepFace.analyze(
            image,
            actions=['gender', 'race'],
            enforce_detection=False
        )
        features = {
            "race": demography[0]['dominant_race'] if demography else "unknown",
            "gender": demography[0]['dominant_gender'] if demography else "unknown"
        }
        return {0: features}

    def generate_avatar(
        self,
        image: np.ndarray,
        user_vector: np.ndarray
    ) -> Image.Image:
        """Generate an avatar image.

        Args:
            image (np.ndarray): A numpy image in BGR format.
            user_vector (np.ndarray): The user genre vector.

        Returns:
            Image.Image: The generated avatar image.
        """
        analysis_result = self._analyze_face_image(image)
        analysis_result[0]["top_genres"] = self._get_top_genres(user_vector)
        prompts = generate_weighted_prompt(analysis_result)
        prompt = prompts[0]
        logger.debug(f"Using prompt: {prompt}")

        rgb_img = image[:,:,::-1]
        pil_img = Image.fromarray(rgb_img)
        input_image = center_crop_to_square(pil_img)
        input_image = input_image.resize(config.input_image_size)

        # First pass with base model (now using input image)
        logger.debug("Generating avatar image with reference image...")
        base_result = self.base_pipe(
            prompt=prompt,
            negative_prompt=self.negative_prompt,
            image=input_image,
            strength=config.base_strength,
            guidance_scale=config.base_guidance_scale,
            num_inference_steps=config.base_num_inference_steps,
            generator=torch.Generator(self.device).manual_seed(config.seed)
        ).images
        base_image = base_result[0]
        
        # Second pass with refiner (using base output)
        logger.debug("Refining avatar image...")
        refined_result = self.refiner_pipe(
            prompt=prompt,
            negative_prompt=self.negative_prompt,
            image=base_image,
            strength=config.refiner_strength,
            num_inference_steps=config.refiner_num_inference_steps,
            generator=torch.Generator(self.device).manual_seed(config.seed)
        )
        return remove_background(refined_result.images[0])


if __name__ == "__main__":
    import cv2
    image = cv2.imread("/home/egracia/Pictures/People/Coen.jpg")
    user_vector = np.array([0.5, 0.9, 0.11, 0.1, 0.3, 0.1, 0.1, 0.26, 0.23, 0.8, 0.7, 0.23, 0.21, 0.02, 0.23, 0.52, 0.34, 0.2])
    avatar_generator = AvatarGenCruilla()
    # print(avatar_generator._analyze_face_image(image, user_vector))
    image = avatar_generator.generate_avatar(image, user_vector)
    image.save("avatar.png")
