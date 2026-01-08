"""
Ported to SDK 2.0+: uses Synapse client and v2 predictions API.
"""

# Create a new project with several tasks and brush preannotations
# Contributed by https://github.com/berombau:
# https://github.com/synapse/synapse-sdk/issues/19#issuecomment-992327281

import numpy as np

import os
import synapse_sdk.converter.brush as brush
from synapse_sdk.client import Synapse

SYNAPSE_URL = os.getenv("SYNAPSE_URL", "http://localhost:8080")
SYNAPSE_API_KEY = os.getenv("SYNAPSE_API_KEY")
LABEL = "Mitochondria"

client = Synapse(base_url=SYNAPSE_URL, api_key=SYNAPSE_API_KEY)

project = client.projects.create(
    title=LABEL,
    label_config=f"""
    <View>
    <Image name="image" value="$image" zoom="true"/>
    <BrushLabels name="brush_labels_tag" toName="image">
        <Label value="{LABEL}" background="#8ff0a4"/>
    </BrushLabels>
    </View>
    """,
)

ids = [
    ls.tasks.create(
        project=project.id, data={"image": f"http://example.com/data_{i:04}.png"}
    ).id
    for i in range(64)
]

mask = (np.random.random([512, 512]) * 255).astype(np.uint8)  # just a random 2D mask
mask = (mask > 128).astype(
    np.uint8
) * 255  # better to threshold, it reduces output annotation size
rle = brush.mask2rle(mask)  # mask image in RLE format

ls.predictions.create(
    task=ids[0],
    model_version="seed",
    result=[
        {
            "from_name": "brush_labels_tag",
            "to_name": "image",
            "type": "brushlabels",
            "value": {"format": "rle", "rle": rle, "brushlabels": [LABEL]},
        }
    ],
)
