import random
from rembg import remove
from PIL import Image
import io

def center_crop_to_square(img):
    """
    Crops a rectangular image to a centered square shape. This yields better results when using SDXL

    Parameters:
        img (PIL.Image): The input image.

    Returns:
        PIL.Image: A square image cropped from the center of the original.
    """

    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = (width + min_dim) // 2
    bottom = (height + min_dim) // 2
    return img.crop((left, top, right, bottom))

def generate_weighted_prompt(analysis_result):
    """
    Generates a descriptive prompt for an avatar based on user analysis data.

    The prompt reflects the user's top two music genres by combining outfit elements
    associated with those genres and formatting them into a rich visual prompt.

    Parameters:
        analysis_result (dict): Dictionary mapping image filenames to user metadata, 
                                including race, gender, and a list of top genres with scores.

    Returns:
        dict: Mapping from filename to generated text prompt.
    """
    prompts = {}
    genre_style_elements = {
        'Comedy': [
            ('quirky patterned shirt', 'torso', 1.0),
            ('suspenders', 'torso', 0.9),
            ('bow tie', 'neck', 0.8),
            ('colorful braces', 'torso', 0.7),
            ('oversized prop glasses', 'face', 0.6)
        ],
        'Art': [
            ('paint-splattered smock', 'torso', 1.0),
            ('beret', 'head', 0.95),
            ('eccentric scarf', 'neck', 0.85),
            ('artist\'s gloves', 'hands', 0.7),
            ('palette necklace', 'neck', 0.6)
        ],
        'Chill': [
            ('oversized knit sweater', 'torso', 1.0),
            ('soft cotton scarf', 'neck', 0.8),
            ('slouchy beanie', 'head', 0.7),
            ('layered t-shirts', 'torso', 0.6),
            ('wool cardigan', 'torso', 0.5)
        ],
        'Food': [
            ('chef-inspired apron', 'torso', 1.0),
            ('rolled-up sleeves', 'arms', 0.9),
            ('food-print shirt', 'torso', 0.8),
            ('kitchen towel on shoulder', 'shoulders', 0.6),
            ('chef\'s hat', 'head', 0.5)
        ],
        'Social': [
            ('tailored blazer', 'torso', 1.0),
            ('crisp button-down shirt', 'torso', 0.95),
            ('silk pocket square', 'torso', 0.8),
            ('minimalist watch', 'wrist', 0.7),
            ('statement cufflinks', 'wrist', 0.6)
        ],
        'Rock': [
            ('leather jacket', 'torso', 1.0),
            ('band t-shirt', 'torso', 0.9),
            ('fingerless gloves', 'hands', 0.8),
            ('studded belt', 'waist', 0.6),
            ('tattoo sleeves', 'arms', 0.5)
        ],
        'Pop': [
            ('colorful bomber jacket', 'torso', 1.0),
            ('metallic top', 'torso', 0.9),
            ('statement sunglasses', 'face', 0.8),
            ('logo belt', 'waist', 0.6),
            ('sequined accessories', 'misc', 0.5)
        ],
        'Soul': [
            ('velvet blazer', 'torso', 1.0),
            ('turtleneck', 'neck', 0.95),
            ('gold hoop earrings', 'ears', 0.8),
            ('wide collar shirt', 'neck', 0.7),
            ('statement necklace', 'neck', 0.6)
        ],
        'Jazz': [
            ('vintage three-piece suit', 'torso', 1.0),
            ('fedora', 'head', 0.9),
            ('pocket square', 'torso', 0.85),
            ('saxophone pin', 'torso', 0.7),
            ('silk vest', 'torso', 0.6)
        ],
        'Electronic': [
            ('neon windbreaker', 'torso', 1.0),
            ('LED wristbands', 'wrist', 0.9),
            ('reflective vest', 'torso', 0.8),
            ('futuristic goggles', 'face', 0.7),
            ('glow-in-the-dark makeup', 'face', 0.6)
        ],
        'Folk': [
            ('flannel shirt', 'torso', 1.0),
            ('denim jacket', 'torso', 0.95),
            ('handmade knit scarf', 'neck', 0.8),
            ('leather wrist cuffs', 'wrist', 0.7),
            ('embroidered vest', 'torso', 0.6)
        ],
        'Reggae': [
            ('rasta-colored beanie', 'head', 1.0),
            ('loose linen shirt', 'torso', 0.95),
            ('dreadlocks', 'hair', 0.9),
            ('wooden bead necklace', 'neck', 0.8),
            ('crochet vest', 'torso', 0.6)
        ],
        'Hip-hop': [
            ('oversized hoodie', 'torso', 1.0),
            ('gold chains', 'neck', 0.95),
            ('snapback hat', 'head', 0.9),
            ('designer logo shirt', 'torso', 0.8),
            ('puffy jacket', 'torso', 0.7)
        ],
        'Punk': [
            ('studded leather jacket', 'torso', 1.0),
            ('mohawk hairstyle', 'hair', 0.95),
            ('torn fishnet shirt', 'torso', 0.9),
            ('safety pin accessories', 'misc', 0.8),
            ('spiked choker', 'neck', 0.7)
        ],
        'Rap': [
            ('designer tracksuit top', 'torso', 1.0),
            ('diamond-encrusted watch', 'wrist', 0.95),
            ('oversized sunglasses', 'face', 0.9),
            ('grillz', 'mouth', 0.8),
            ('fur-lined hood', 'head', 0.7)
        ],
        'Classical': [
            ('tailored suit', 'torso', 1.0),
            ('pocket watch chain', 'torso', 0.9),
            ('silk tie', 'neck', 0.85),
            ('opera gloves', 'hands', 0.7),
            ('ruffled shirt', 'torso', 0.6)
        ],
        'Indie': [
            ('vintage band t-shirt', 'torso', 1.0),
            ('thrifted cardigan', 'torso', 0.95),
            ('geek-chic glasses', 'face', 0.9),
            ('flannel overshirt', 'torso', 0.8),
            ('handmade jewelry', 'misc', 0.7)
        ],
        'Other': [
            ('eclectic layered outfit', 'torso', 1.0),
            ('unique handmade accessories', 'misc', 0.9),
            ('mixed pattern clothing', 'torso', 0.8),
            ('avant-garde headpiece', 'head', 0.7),
            ('upcycled fabric jewelry', 'misc', 0.6)
        ]
    }

    all_categories = ['head', 'face', 'neck', 'torso', 'arms', 'wrist', 'shoulders', 'hands', 'waist', 'hair', 'ears', 'mouth', 'misc']

    for filename, data in analysis_result.items():
        if not all(k in data for k in ['race', 'gender', 'top_genres']):
            continue

        race = data['race']
        gender = data['gender'].lower()
        top_genres = data['top_genres']

        # Escoger los 2 géneros principales
        top_2_genres = [g for g, _ in sorted(top_genres, key=lambda x: -x[1])[:2]]
        genre1, genre2 = top_2_genres

        # Recolectar elementos por categoría desde ambos géneros
        category_elements = {cat: [] for cat in all_categories}
        for genre in [genre1, genre2]:
            for element, category, _ in genre_style_elements.get(genre, []):
                category_elements[category].append(element)

        selected_elements = []
        used_categories = set()

        # Para cada categoría, si hay elementos en al menos un género, elegir uno aleatorio
        random.shuffle(all_categories)  # Para variar qué partes se seleccionan
        for category in all_categories:
            options = category_elements.get(category, [])
            if options:
                selected = random.choice(options)
                selected_elements.append((selected, category))
                used_categories.add(category)
            if len(selected_elements) >= 4:
                break

        # Formatear el outfit
        element_names = [e for e, _ in selected_elements]
        if not element_names:
            outfit = "stylish contemporary clothes"
        elif len(element_names) == 1:
            outfit = element_names[0]
        else:
            outfit = ", ".join(element_names[:-1]) + f" and {element_names[-1]}"

        primary_genre = genre1
        background = "white plain background with no detail"

        prompt = (
            f"A {race} {gender}, waist up portrait, wearing {outfit}, "
            f"reflecting their music preferences (primarily {primary_genre}). "
            f"{'They have ' + element_names[0] + ' as their most prominent feature. ' if element_names else ''}"
            f"anime style, cartoon drawing, 2D illustration, cel shading, clean lineart, colorful, "
            f"{background}, dramatic lighting, ultra-detailed, digital painting, vibrant, highly stylized, high quality"
        )

        prompts[filename] = prompt

    return prompts

def remove_background(img: Image.Image) -> Image.Image:
    """
    Removes the background from a PIL image using the rembg model.

    Parameters:
        img (PIL.Image): Input image.

    Returns:
        PIL.Image: Image with background removed (transparent background).
    """
    # Convert PIL image to bytes
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    # Remove background
    output_bytes = remove(img_bytes)

    # Convert bytes back to PIL image
    output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    return output_img
