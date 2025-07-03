import tempfile
import time
import uuid
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import paramiko
from loguru import logger
from PIL import Image
from scp import SCPClient

import config

genres = ['Comedy', 'Art', 'Chill', 'Food', 'Social', 'Rock', 'Pop', 'Soul',
          'Jazz', 'Electronic', 'Folk', 'Reggae', 'Hip-hop', 'Punk', 'Rap',
          'Classical', 'Indie', 'Other']


def plot_user_vector(user_vector: np.ndarray) -> Image.Image:
    labels = np.array(genres)
    values = user_vector.copy()

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False
    ).tolist()
    
    # close the loop
    values = np.concatenate((values, [values[0]]))  
    angles += angles[:1]

    # Plot
    fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw=dict(polar=True))
    ax.plot(angles, values, color='tab:blue', linewidth=2)
    ax.fill(angles, values, color='tab:blue', alpha=0.25)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    # ax.set_title("", y=1.1)

    ax.set_xticklabels(labels, fontsize=18)

    # Convert to PIL Image
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='PNG', bbox_inches='tight', transparent=True)
    buf.seek(0)
    plot_image = Image.open(buf)
    plt.close()
    
    return plot_image


def resize_and_pad_rgba(
    img: Image.Image,
    target_size: int,
    background_color=(255, 255, 255, 255)
) -> Image.Image:
    img = img.convert("RGBA")
    img.thumbnail(target_size, Image.LANCZOS)
    new_img = Image.new("RGBA", target_size, background_color)
    left = (target_size[0] - img.width) // 2
    top = (target_size[1] - img.height) // 2
    new_img.paste(img, (left, top), img)
    return new_img


def make_final_composition(
    avatar_image: Image.Image,
    pet_image: Image.Image,
    plot_image: Image.Image,
) -> Image.Image:
    avatar_image = avatar_image.convert("RGBA")
    pet_image = pet_image.convert("RGBA")
    plot_image = plot_image.convert("RGBA")

    res_path = Path(__file__).parent / "res/"
    final_frame_path = res_path / "composition_background.png"
    final_frame = Image.open(final_frame_path).convert("RGBA")

    final_canvas = Image.new("RGBA", final_frame.size, (255, 255, 255, 255))
    final_canvas.paste(avatar_image, (20, 33), avatar_image)
    final_canvas.paste(final_frame, (0, 0), final_frame)

    pet_size = 800
    pet_image_resized = pet_image.resize((pet_size, pet_size))
    pet_w, pet_h = pet_image_resized.size
    canvas_w, canvas_h = final_canvas.size
    x = canvas_w - pet_w
    y = canvas_h - pet_h - 150
    final_canvas.paste(pet_image_resized, (x, y), pet_image_resized)

    x = 800
    y = 500
    final_canvas.paste(plot_image, (x, y), plot_image)
    return final_canvas


def make_pet_composition(pet_image: Image.Image) -> Image.Image:
    pet_frame_path = Path(__file__).parent / "res/frame_pet.png"
    pet_size = 800
    frame_pet = Image.open(pet_frame_path).convert("RGBA")
    pet_image_resized = pet_image.resize((pet_size, pet_size))
    pet_canvas = Image.new("RGBA", frame_pet.size, (255, 255, 255, 255))
    pet_w, pet_h = pet_image_resized.size
    canvas_w, canvas_h = pet_canvas.size
    x = int((canvas_w/2)-(pet_w/2))
    y = canvas_h - pet_h - 50
    pet_canvas.paste(pet_image_resized, (x, y), pet_image_resized)
    pet_canvas.paste(frame_pet, (0, 0), frame_pet)
    return pet_canvas


def make_avatar_composition(avatar_image: Image.Image) -> Image.Image:
    avatar_image = avatar_image.convert("RGBA")
    avatar_frame_path = Path(__file__).parent / "res/frame_avatar.png"
    frame_avatar = Image.open(avatar_frame_path).convert("RGBA")
    avatar_canvas = Image.new("RGBA", frame_avatar.size, (255, 255, 255, 255))
    avatar_canvas.paste(avatar_image, (2, 0), avatar_image)
    avatar_canvas.paste(frame_avatar, (0, 0), frame_avatar)
    return avatar_canvas


def upload_image(image: Image.Image) -> str:
    image_suffix = ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=image_suffix) as tmp_img:
        image.save(tmp_img, format="PNG")
        tmp_img.flush()

        target_filename = f"{int(time.time() * 1000)}_{uuid.uuid4()}{image_suffix}"
        target_file_path = config.server_root_path.format(target_filename)
    
        # Create SSH tunnel
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_ssh.connect(
            hostname=config.ssh_jump_server_ip,
            port=config.ssh_jump_server_port,
            username=config.ssh_jump_server_user,
            password=config.ssh_jump_server_pwd,
        )
        transport = jump_ssh.get_transport()
        channel = transport.open_channel(
            "direct-tcpip",
            (config.ssh_images_server_ip, config.ssh_images_server_port),
            ("127.0.0.1", 0)
        )
        
        # Connect to the images storage server through SSH
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target_ssh.connect(
            hostname=config.ssh_images_server_ip,
            port=config.ssh_images_server_port,
            username=config.ssh_images_server_user,
            password=config.ssh_images_server_pwd,
            sock=channel,
        )

        # Upload the image
        with SCPClient(target_ssh.get_transport()) as scp:
            scp.put(tmp_img.name, target_file_path)
        
        # Change permissions
        cmd = f"chmod 644 {target_file_path}"
        stdin, stdout, stderr = target_ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            logger.error(f"Failed to set permissions on image server: "
                         f"{stderr.read().decode()}")

        target_ssh.close()
        jump_ssh.close()
        
        return config.server_public_url.format(target_filename)
