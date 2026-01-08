from synapse_sdk.synapse_interface.region import Region
from synapse_sdk.synapse_interface.object_tags import ImageTag
from synapse_sdk.synapse_interface.control_tags import RectangleTag


def test_li():
    """Test using Label Interface to label things
    """
    img = ImageTag(
        name="img", tag="image", value="http://example.com/image.jpg", attr={}
    )
    rect = RectangleTag(name="rect", to_name=["img"], tag="rectangle", attr={})
    rect.set_object(img)

    region = rect.label(x=10, y=10, width=10, height=10, rotation=10)










