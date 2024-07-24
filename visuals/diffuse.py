import datetime
import os.path
from functools import lru_cache
from typing import Optional

import torch
from PIL.Image import Image
from diffusers import AutoencoderKL, UNet2DConditionModel, DiffusionPipeline
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from numpy.random import randint
from transformers import CLIPTextModel, CLIPTokenizer

from prompts import IMAGE_STYLES


def wrap_story(story: str, style: str = "") -> str:
    # Warning: we put story at the end as truncation might occur
    # ( The following part of your input was truncated because CLIP can only handle sequences up to 77 tokens)
    story = story.replace(",", " ")

    focus = "no text, WS wide shot large perspective, wide-angle view"

    return f"{style}, {focus}, {story}"


def text2image_manual(prompt: str) -> Image:
    vae = AutoencoderKL.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="vae", use_safetensors=True)
    tokenizer = CLIPTokenizer.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(
        "CompVis/stable-diffusion-v1-4", subfolder="text_encoder", use_safetensors=True
    )
    unet = UNet2DConditionModel.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="unet", use_safetensors=True)
    from diffusers import UniPCMultistepScheduler

    # To speed up inference, move the models to a GPU since, unlike the scheduler, they have trainable weights:
    scheduler = UniPCMultistepScheduler.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="scheduler")

    torch_device = "cuda"
    vae.to(torch_device)
    text_encoder.to(torch_device)
    unet.to(torch_device)

    height = 512  # default height of Stable Diffusion
    width = 512  # default width of Stable Diffusion
    num_inference_steps = 50  # Number of denoising steps
    guidance_scale = 7.5  # Scale for classifier-free guidance
    generator = torch.Generator(device="cuda")  # Seed generator to create the initial latent noise
    batch_size = len(prompt)

    # Tokenize the text and generate the embeddings from the prompt:
    text_input = tokenizer(
        prompt, padding="max_length", max_length=tokenizer.model_max_length, truncation=True, return_tensors="pt"
    )
    with torch.no_grad():
        text_embeddings = text_encoder(text_input.input_ids.to(torch_device))[0]

    # You’ll also need to generate the unconditional text embeddings which are the embeddings for the padding token.
    # These need to have the same shape (batch_size and seq_length) as the conditional text_embeddings:
    max_length = text_input.input_ids.shape[-1]
    uncond_input = tokenizer([""] * batch_size, padding="max_length", max_length=max_length, return_tensors="pt")
    uncond_embeddings = text_encoder(uncond_input.input_ids.to(torch_device))[0]

    # Let’s concatenate the conditional and unconditional embeddings into a batch to avoid doing two forward passes:
    text_embeddings = torch.cat([uncond_embeddings, text_embeddings])

    # Next, generate some initial random noise as a starting point for the diffusion process.
    # This is the latent representation of the image, and it’ll be gradually denoised.
    # At this point, the latent image is smaller than the final image size but that’s okay though
    # because the model will transform it into the final 512x512 image dimensions later.
    # The height and width are divided by 8 because the vae model has 3 down-sampling layers.
    # You can check by running `2 ** (len(vae.config.block_out_channels) - 1) == 8`
    latents = torch.randn(
        (batch_size, unet.config.in_channels, height // 8, width // 8),
        generator=generator,
        device=torch_device,
    )

    # Start by scaling the input with the initial noise distribution, sigma, the noise scale value,
    # which is required for improved schedulers like UniPCMultistepScheduler:
    latents = latents * scheduler.init_noise_sigma

    from tqdm.auto import tqdm

    scheduler.set_timesteps(num_inference_steps)

    for t in tqdm(scheduler.timesteps):
        # expand the latents if we are doing classifier-free guidance to avoid doing two forward passes.
        latent_model_input = torch.cat([latents] * 2)

        latent_model_input = scheduler.scale_model_input(latent_model_input, timestep=t)

        # predict the noise residual
        with torch.no_grad():
            noise_pred = unet(latent_model_input, t, encoder_hidden_states=text_embeddings).sample

        # perform guidance
        noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
        noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

        # compute the previous noisy sample x_t -> x_t-1
        latents = scheduler.step(noise_pred, t, latents).prev_sample

    # The final step is to use the vae to decode the latent representation into an image and get the decoded output with sample:

    # scale and decode the image latents with vae
    latents = 1 / 0.18215 * latents
    with torch.no_grad():
        image = vae.decode(latents).sample

    # Lastly, convert the image to a PIL.Image to see your generated image!
    image = (image / 2 + 0.5).clamp(0, 1).squeeze()
    image = (image.permute(1, 2, 0) * 255).to(torch.uint8).cpu().numpy()
    image = Image.fromarray(image)
    return image


def text2image_v2(prompt: str, num_inference_steps: int = 150, height=512, width=512) -> Image:
    print(f"Running T2I v2: {prompt}")
    generator, pipe = init_v2(num_inference_steps)

    image = pipe(
        prompt,
        guidance_scale=7.5,
        height=height,
        width=width,
        negative_prompt="text, hands",
        num_inference_steps=num_inference_steps,
        generator=generator,
    ).images[0]

    return image


@lru_cache(maxsize=1)
def init_v2(num_inference_steps) -> tuple[torch.Generator, StableDiffusionPipeline]:
    """
    Initialize and cache the Generator and Pipeline used for our V2 StableDiffusion back-end.
    """
    print("Initializing Text2ImageV2 components.")
    model_id = "stabilityai/stable-diffusion-2-1"
    # Use the DPMSolverMultistepScheduler (DPM-Solver++) scheduler here instead
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    scheduler.set_timesteps(num_inference_steps)
    generator = torch.Generator(device="cuda")
    generator.manual_seed(randint(0, 64000))  # Diverse results at each run
    pipe.scheduler = scheduler
    pipe = pipe.to("cuda")
    return generator, pipe


def text2image_hyper(prompt: str, num_inference_steps: int = 1) -> Image:
    import torch
    from diffusers import DiffusionPipeline, TCDScheduler
    from huggingface_hub import hf_hub_download

    base_model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    repo_name = "ByteDance/Hyper-SD"
    ckpt_name = "Hyper-SDXL-1step-lora.safetensors"
    # Load model.
    pipe = DiffusionPipeline.from_pretrained(base_model_id, torch_dtype=torch.float16, variant="fp16").to("cuda")
    pipe.load_lora_weights(hf_hub_download(repo_name, ckpt_name))
    pipe.fuse_lora()
    # Use TCD scheduler to achieve better image quality
    pipe.scheduler = TCDScheduler.from_config(pipe.scheduler.config)
    # Lower eta results in more detail for multi-steps inference
    eta = 1.0
    image = pipe(prompt=prompt, num_inference_steps=num_inference_steps, guidance_scale=0, eta=eta).images[0]
    return image


def text2image_peft(prompt: str, num_inference_steps: int = 100) -> Image:
    # See https://github.com/huggingface/diffusers/issues/5489
    import torch

    # Load SDXL.
    pipe = load_lora_pipe()

    # Perform inference.
    # Notice how the prompt is constructed.
    image = pipe(
        prompt,
        num_inference_steps=num_inference_steps,
        cross_attention_kwargs={"scale": 1.0},
        generator=torch.manual_seed(0),
    ).images[0]

    return image


def upscale(prompt: str, image: Image) -> Image:
    from diffusers import StableDiffusionUpscalePipeline
    import torch

    print(f"Upscaling image with prompt {prompt}...")

    # load model and scheduler
    model_id = "stabilityai/stable-diffusion-x4-upscaler"
    pipeline = StableDiffusionUpscalePipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipeline = pipeline.to("cuda")

    upscaled_image = pipeline(prompt=prompt, image=image).images[0]
    # upscaled_image.save("upsampled_cat.png")
    return upscaled_image


@lru_cache(maxsize=1)
def load_lora_pipe():
    pipe_id = "stabilityai/stable-diffusion-xl-base-1.0"
    pipe = DiffusionPipeline.from_pretrained(pipe_id, torch_dtype=torch.float16).to("cuda")
    # Load LoRAs.
    pipe.load_lora_weights("CiroN2022/toy-face", weight_name="toy_face_sdxl.safetensors", adapter_name="toy")
    pipe.load_lora_weights("nerijs/pixel-art-xl", weight_name="pixel-art-xl.safetensors", adapter_name="pixel")
    # Combine them.
    pipe.set_adapters(["pixel", "toy"], adapter_weights=[0.5, 1.0])
    return pipe


def text2image(story: str, style: str = "", fast=False, save: bool = True) -> Optional[Image]:
    """Use our current best text2image model, with wrapping of story."""
    try:
        prompt = wrap_story(story, style)
        image: Image = text2image_v2(prompt, 50 if fast else 150)
        if save:
            key = (
                f"{story[:80]}".strip()
                .replace(" ", "_")
                .replace("#", "")
                .replace(",", "")
                .replace(":", "")
                .replace(";", "")
                .replace(".", "")
                .replace("\n", "")
                .replace("\t", "")
                .replace("\\", "")
                .replace("/10", "")  # Dice rolls don't make great filenames :')
                .replace("/", "")
            )
            time = int(datetime.datetime.now().timestamp())
            if not os.path.exists("./generated/images/"):
                os.mkdir("./generated/images/")
            image.save(f"./generated/images/{key}_{time}.png")
        return image
    except Exception as e:
        print(f"Error generating image: {e}")
        return None  # No big deal


def main_diffusion():
    story = "a man flying a parachute above yellow sunflower fields"
    mugshot: Image = text2image(story, style=IMAGE_STYLES["MOEBIUS"], save=False)
    mugshot.show()
    improved = upscale(story, mugshot)
    improved.show()
    # mugshot.save("mugshot.png")


if __name__ == "__main__":
    main_diffusion()
