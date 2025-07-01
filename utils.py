import tempfile
import time
import uuid
from io import BytesIO

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
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values, color='tab:blue', linewidth=2)
    ax.fill(angles, values, color='tab:blue', alpha=0.25)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    # ax.set_title("", y=1.1)

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


def make_composition(
    img_1: Image.Image,
    img_2: Image.Image,
    img_3: Image.Image,
    width: int,
    height: int,
) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    slot_size = (width // 3, height)

    img_1 = resize_and_pad_rgba(img_1, slot_size)
    img_2 = resize_and_pad_rgba(img_2, slot_size)
    img_3 = resize_and_pad_rgba(img_3, slot_size)

    canvas.paste(img_1, (0, 0),                img_1)
    canvas.paste(img_2, (slot_size[0], 0),     img_2)
    canvas.paste(img_3, (slot_size[0] * 2, 0), img_3)

    return canvas


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
