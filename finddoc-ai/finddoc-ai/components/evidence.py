
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io


def highlight_region(image: Image.Image, bbox: dict, padding: int = 15) -> Image.Image:
    """
    Draw a red rectangle + yellow highlight around the evidence region.

    Args:
        image: Original document image (PIL Image)
        bbox: {"x": int, "y": int, "w": int, "h": int}
        padding: Extra space around the bbox
    Returns:
        Highlighted image (PIL Image)
    """
    # Work on a copy
    img = image.copy().convert("RGBA")

    x = bbox["x"]
    y = bbox["y"]
    w = bbox["w"]
    h = bbox["h"]

    # Create yellow semi-transparent highlight overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [x - padding, y - padding, x + w + padding, y + h + padding],
        fill=(255, 255, 0, 45)  # Yellow, semi-transparent
    )
    img = Image.alpha_composite(img, overlay)

    # Draw red border rectangle
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [x - padding, y - padding, x + w + padding, y + h + padding],
        outline=(255, 0, 0, 255),
        width=3
    )

    # Draw corner markers for extra visual effect
    corner_len = 15
    corners = [
        # Top-left
        [(x - padding, y - padding), (x - padding + corner_len, y - padding)],
        [(x - padding, y - padding), (x - padding, y - padding + corner_len)],
        # Top-right
        [(x + w + padding - corner_len, y - padding),
         (x + w + padding, y - padding)],
        [(x + w + padding, y - padding),
         (x + w + padding, y - padding + corner_len)],
        # Bottom-left
        [(x - padding, y + h + padding - corner_len),
         (x - padding, y + h + padding)],
        [(x - padding, y + h + padding),
         (x - padding + corner_len, y + h + padding)],
        # Bottom-right
        [(x + w + padding - corner_len, y + h + padding),
         (x + w + padding, y + h + padding)],
        [(x + w + padding, y + h + padding - corner_len),
         (x + w + padding, y + h + padding)],
    ]
    for start, end in corners:
        draw.line([start, end], fill=(255, 50, 50, 255), width=5)

    return img


def crop_evidence(image: Image.Image, bbox: dict, context_padding: int = 60) -> Image.Image:
    """
    Crop a zoomed-in region around the evidence for detail view.

    Args:
        image: The highlighted image
        bbox: {"x": int, "y": int, "w": int, "h": int}
        context_padding: Extra area to include for context
    Returns:
        Cropped image (PIL Image)
    """
    x = bbox["x"]
    y = bbox["y"]
    w = bbox["w"]
    h = bbox["h"]

    # Calculate crop area with context
    left = max(0, x - context_padding)
    top = max(0, y - context_padding)
    right = min(image.width, x + w + context_padding)
    bottom = min(image.height, y + h + context_padding)

    cropped = image.crop((left, top, right, bottom))
    return cropped


def render_evidence_display(image: Image.Image, bbox: dict, evidence_text: str = ""):
    """
    Render the visual evidence component in Streamlit.
    Shows highlighted full image + zoomed crop side by side.

    Args:
        image: Original document image
        bbox: Bounding box coordinates from backend
        evidence_text: The text that was found as evidence
    """
    if bbox is None or image is None:
        return

    # Generate highlighted images
    highlighted_img = highlight_region(image, bbox)
    cropped_img = crop_evidence(highlighted_img, bbox)

    # Display in an expander for clean UI
    with st.expander("**Visual Evidence** — Click to see source", expanded=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Zoomed Evidence:**")
            # Convert RGBA to RGB for display
            cropped_rgb = cropped_img.convert("RGB")
            st.image(cropped_rgb, use_container_width=True)

            if evidence_text:
                st.markdown(f"**Found text:** `{evidence_text}`")

        with col2:
            st.markdown("**Full Document:**")
            highlighted_rgb = highlighted_img.convert("RGB")
            st.image(highlighted_rgb, use_container_width=True)
