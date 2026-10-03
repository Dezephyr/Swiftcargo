import random
import string


def generate_tracking_id(length=6):
    """Generate a tracking ID like SHP-A3K9Z2."""
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=length))
    return f"SHP-{code}"