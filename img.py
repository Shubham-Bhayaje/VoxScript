import torch
import os
from datetime import datetime
from controlnet_aux import CannyDetector
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers.utils import load_image, make_image_grid
from PIL import Image
import numpy as np

# Disable CUDA completely
torch.cuda.is_available = lambda: False
device = torch.device("cpu")

# Create output directory
output_dir = os.path.join(os.getcwd(), "generated_images")
os.makedirs(output_dir, exist_ok=True)

# Load ControlNet model on CPU with proper settings
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny",
    torch_dtype=torch.float32,
).to(device)

# Load Stable Diffusion pipeline on CPU
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "Yntec/AbsoluteReality",
    controlnet=controlnet,
    torch_dtype=torch.float32,
).to(device)

# Force-disable safety checker to save memory
pipe.safety_checker = None
pipe.feature_extractor = None

# Load IP Adapter with CPU settings
pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="models",
    weight_name="ip-adapter_sd15.bin"
)

# Disable progress bars to reduce overhead
pipe.set_progress_bar_config(disable=True)

def process_image(input_image_path, style_image_path, prompt, output_prefix="output", 
                  guidance_scale=6, conditioning_scale=0.7, ip_scale=0.5, 
                  steps=20, num_images=1, height=512, width=512):  # Reduced defaults for CPU
    """
    Process an image through the ControlNet pipeline with CPU optimizations
    """
    try:
        # Load input images
        img = load_image(input_image_path)
        ip_adap_img = load_image(style_image_path)
        
        # Apply Canny Edge Detection
        canny = CannyDetector()
        canny_img = canny(img, detect_resolution=512, image_resolution=height)
        
        # Set IP-Adapter scale
        pipe.set_ip_adapter_scale(ip_scale)
        
        # Generate images with CPU-specific settings
        images = pipe(
            prompt=prompt,
            negative_prompt="low quality, blurry, distorted features",
            height=height,
            width=width,
            ip_adapter_image=ip_adap_img,
            image=canny_img,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=conditioning_scale,
            num_inference_steps=steps,
            num_images_per_prompt=num_images,
            generator=torch.Generator(device="cpu")  # Explicit CPU generator
        ).images
        
        # Save images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_paths = []
        
        for i, img in enumerate(images):
            filename = f"{output_prefix}_{timestamp}_{i+1}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            saved_paths.append(filepath)
            print(f"Saved image to {filepath}")
        
        return images, saved_paths
    
    except Exception as e:
        print(f"Error during image generation: {str(e)}")
        return None, None

# Modified example usage with CPU-friendly settings
if __name__ == "__main__":
    # Define input paths (update these to your actual paths)
    input_img_path =r"C:\Users\shubham\Pictures\Saved Pictures\WhatsApp Image 2024-12-08 at 15.11.44_90c2731a.jpg"  # Use a smaller image for CPU
    style_img_path =r"C:\Users\shubham\Downloads\style_input.jpg"  # Use a smaller image for CPU
    
    # Define a simpler prompt for faster CPU processing
    prompt = "anime style, white hair, white beard, ghibli-like"
    
    # Process with conservative settings for CPU
    images, saved_paths = process_image(
        input_img_path,
        style_img_path,
        prompt,
        output_prefix="cpu_output",
        guidance_scale=5,          # Lower than default
        conditioning_scale=0.5,    # Lower than default
        ip_scale=0.5,
        steps=15,                  # Fewer steps
        num_images=1,              # Generate just 1 image
        height=512,                # Smaller resolution
        width=512
    )
    
    if images:
        print("Image generation completed successfully!")
    else:
        print("Image generation failed")