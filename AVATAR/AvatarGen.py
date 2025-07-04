import json
import os
import gc
from PIL import Image
import torch
from diffusers import AutoPipelineForText2Image, AutoPipelineForImage2Image
from diffusers.utils import load_image
import sys
import random
from safetensors.torch import load_file
from utils import *

# --- CONFIG ---
json_input_path = "analysis_result.json"

if len(sys.argv) < 2:
    raise ValueError("You must provide the path to the input image as the first argument.")

input_image_path = sys.argv[1]

print(f"Using input image: {input_image_path}")
base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"
refiner_model_path = "stabilityai/stable-diffusion-xl-refiner-1.0"
output_path_refined = "AVATAR/images/Avatar_Finetuned.png"

# --- LOAD ANALYSIS ---
with open(json_input_path, 'r') as f:
    analysis_result = json.load(f)

# Generate prompts from analysis result
prompts = generate_weighted_prompt(analysis_result)
filename = list(prompts.keys())[0]
prompt = prompts[filename]  # Get the prompt for our file
print(f"Using prompt: {prompt}")

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


# --- LOAD MODELS ---
gc.collect()
torch.cuda.empty_cache()

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load base model (now as Image2Image pipeline)
base_pipe = AutoPipelineForImage2Image.from_pretrained(
    base_model_path,
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True
).to(device)

base_pipe.enable_attention_slicing()  # Reduce memory by slicing attention computation
base_pipe.enable_vae_slicing()  # Slice VAE operations to reduce memory
base_pipe.enable_model_cpu_offload()

# Load your UNet
state_dict = load_file("/hhome/uabcru03/Avatar/Avatar_Base_Ref/Good_prompts.safetensors")
base_pipe.unet.load_state_dict(state_dict, strict=False)


# Load refiner model (unchanged)
refiner_pipe = AutoPipelineForImage2Image.from_pretrained(
    refiner_model_path,
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True
).to(device)

refiner_pipe.enable_attention_slicing()  # Reduce memory by slicing attention computation
refiner_pipe.enable_vae_slicing()  # Slice VAE operations to reduce memory
refiner_pipe.enable_model_cpu_offload()

generator = torch.Generator(device).manual_seed(42)

# --- PROCESS IMAGE ---
input_image = load_image(input_image_path)
if input_image.mode != "RGB":
    input_image = input_image.convert("RGB")
input_image = center_crop_to_square(input_image)
input_image = input_image.resize((1024, 1024))

# First pass with base model (now using input image)
print("Generating base image with reference...")
base_result = base_pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=input_image,  # Now using your input image
    strength=0.7,  # Stronger transformation for base model
    guidance_scale=8.5,
    num_inference_steps=30,
    generator=generator
).images

base_image = base_result[0]

# Second pass with refiner (using base output)
print("Refining image...")
refined_result = refiner_pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=base_image,  # Refine the base output
    strength=0.3,  # Subtler refinement
    num_inference_steps=30,
    generator=generator
)
refined_result.images[0].save(output_path_refined)
# image_nobg = remove_background(refined_result.images[0])
# image_nobg.save(output_path_refined_no_bg)