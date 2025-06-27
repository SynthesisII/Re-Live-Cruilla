import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from io import BytesIO

# Data
user_vector = [0.5, 0.9, 0.11, 0.1, 0.3, 0.1, 0.1, 0.26, 0.23, 0.8, 0.7, 0.23, 0.21, 0.02, 0.23, 0.52, 0.34, 0.2]
genres = ['Comedy', 'Art', 'Chill', 'Food', 'Social', 'Rock', 'Pop', 'Soul', 'Jazz', 'Electronic',
          'Folk', 'Reggae', 'Hip-hop', 'Punk', 'Rap', 'Classical', 'Indie', 'Other']

# Radar chart setup
labels = np.array(genres)
values = np.array(user_vector)
num_vars = len(labels)

# Compute angle for each axis
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
values = np.concatenate((values, [values[0]]))  # close the loop
angles += angles[:1]

# Plot
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, values, color='tab:blue', linewidth=2)
ax.fill(angles, values, color='tab:blue', alpha=0.25)
ax.set_yticklabels([])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=8)
ax.set_title("User Genre Preferences", y=1.1)

# Convert to PIL Image
buf = BytesIO()
plt.tight_layout()
plt.savefig(buf, format='PNG', bbox_inches='tight', transparent=True)
buf.seek(0)
image = Image.open(buf)
plt.close()

image.show()
image
