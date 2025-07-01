from pathlib import Path

root_path = Path(__file__).parent
models_path = root_path / "models"
cache_path = root_path / "cache"

genres = ['Comedy','Art','Chill','Food','Social','Rock','Pop',
          'Soul','Jazz','Electronic','Folk','Reggae','Hip-hop',
          'Punk','Rap','Classical','Indie','Other']

base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"
refiner_model_path = "stabilityai/stable-diffusion-xl-refiner-1.0"
custom_unet_path = models_path / "Good_prompts.safetensors"

input_image_size = (1024, 1024)
seed = 42

base_strength = 0.7
base_guidance_scale = 8.5
base_num_inference_steps = 20

refiner_strength = 0.3
refiner_num_inference_steps = 20