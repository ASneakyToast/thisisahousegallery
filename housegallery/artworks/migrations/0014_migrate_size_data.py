import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from django.db import migrations


def parse_fraction(value_str):
    """Parse a value that may contain fractions like '6 1/4' or '1/2'."""
    value_str = value_str.strip()

    # Handle leading dot (e.g., ".75" -> "0.75")
    if value_str.startswith('.'):
        value_str = '0' + value_str

    # Check for mixed number (e.g., "6 1/4")
    mixed_match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', value_str)
    if mixed_match:
        whole = int(mixed_match.group(1))
        numer = int(mixed_match.group(2))
        denom = int(mixed_match.group(3))
        return Decimal(str(whole + numer / denom))

    # Check for simple fraction (e.g., "1/2")
    frac_match = re.match(r'^(\d+)/(\d+)$', value_str)
    if frac_match:
        numer = int(frac_match.group(1))
        denom = int(frac_match.group(2))
        return Decimal(str(numer / denom))

    # Plain decimal or integer
    try:
        return Decimal(value_str)
    except InvalidOperation:
        return None


def parse_size_string(size_str):
    """
    Parse size strings in various formats:
    - '25" x 6" x 1"' (inches with quotes, 3D)
    - '30" x 22"' (inches with quotes, 2D)
    - "8' x 4'" (feet, 2D)
    - "16 x 98 x 16" (plain numbers, assumed inches)
    - "6 1/4 x 6 1/4 x 2" (fractions)
    - "H 8" x W 6.5" x D 6.5"" (labeled H/W/D)
    - "4"h x 4"w x .75"d" (h/w/d suffix)
    - "24in x 36in" (in suffix)
    - "30"x30"" (no spaces)

    Returns: (width, height, depth) tuple of Decimals or None
    """
    if not size_str or not isinstance(size_str, str):
        return None, None, None

    # Clean the string
    size_str = size_str.strip()

    # Normalize smart quotes to regular quotes
    # Right double quotation mark (U+201D) and left (U+201C) -> "
    # Right single quotation mark (U+2019) and left (U+2018) -> '
    size_str = size_str.replace('\u201c', '"').replace('\u201d', '"')
    size_str = size_str.replace('\u2018', "'").replace('\u2019', "'")

    # Skip strings with mm (metric) - too complex to handle
    if 'mm' in size_str.lower():
        return None, None, None

    # Skip descriptive strings
    if any(word in size_str.lower() for word in ['unknown', 'vary', 'about', 'approx']):
        return None, None, None

    # Pattern 1: H/W/D labeled format (e.g., "H 8" x W 6.5" x D 6.5"")
    hwd_pattern = r'H\s*(\d+(?:\.\d+)?)"?\s*x\s*W\s*(\d+(?:\.\d+)?)"?\s*x\s*D\s*(\d+(?:\.\d+)?)"?'
    hwd_match = re.search(hwd_pattern, size_str, re.IGNORECASE)
    if hwd_match:
        try:
            height = Decimal(hwd_match.group(1))
            width = Decimal(hwd_match.group(2))
            depth = Decimal(hwd_match.group(3))
            return width, height, depth
        except InvalidOperation:
            pass

    # Pattern 2: h/w/d suffix format (e.g., "4"h x 4"w x .75"d")
    hwd_suffix_pattern = r'(\d+(?:\.\d+)?)"?\s*h\s*x\s*(\d+(?:\.\d+)?)"?\s*w\s*x\s*(\d+(?:\.\d+)?)"?\s*d'
    hwd_suffix_match = re.search(hwd_suffix_pattern, size_str, re.IGNORECASE)
    if hwd_suffix_match:
        try:
            height = Decimal(hwd_suffix_match.group(1))
            width = Decimal(hwd_suffix_match.group(2))
            depth = Decimal(hwd_suffix_match.group(3))
            return width, height, depth
        except InvalidOperation:
            pass

    # Pattern 3: Feet notation (e.g., "8' x 4'" or "10' x 10' x 10'")
    feet_pattern = r"^(\d+(?:\.\d+)?)\s*'\s*x\s*(\d+(?:\.\d+)?)\s*'(?:\s*x\s*(\d+(?:\.\d+)?)\s*')?$"
    feet_match = re.match(feet_pattern, size_str, re.IGNORECASE)
    if feet_match:
        try:
            dim1 = Decimal(feet_match.group(1)) * 12
            dim2 = Decimal(feet_match.group(2)) * 12
            dim3 = Decimal(feet_match.group(3)) * 12 if feet_match.group(3) else None
            return dim2, dim1, dim3
        except InvalidOperation:
            pass

    # Pattern 4: "in" suffix (e.g., "24in x 36in" or "11inX11inX1in")
    in_pattern = r'^(\d+(?:\.\d+)?)\s*in\s*[xX]\s*(\d+(?:\.\d+)?)\s*in(?:\s*[xX]\s*(\d+(?:\.\d+)?)\s*in)?$'
    in_match = re.match(in_pattern, size_str, re.IGNORECASE)
    if in_match:
        try:
            dim1 = Decimal(in_match.group(1))
            dim2 = Decimal(in_match.group(2))
            dim3 = Decimal(in_match.group(3)) if in_match.group(3) else None
            return dim2, dim1, dim3
        except InvalidOperation:
            pass

    # Pattern 5a: w/h suffix format (e.g., "11"w x 14"h" or "33"h x 41"w x 1"")
    # Height first, then width
    wh_pattern = r'(\d+(?:\.\d+)?)"?\s*h\s*x\s*(\d+(?:\.\d+)?)"?\s*w(?:\s*x\s*(\d+(?:\.\d+)?)"?)?'
    wh_match = re.search(wh_pattern, size_str, re.IGNORECASE)
    if wh_match:
        try:
            height = Decimal(wh_match.group(1))
            width = Decimal(wh_match.group(2))
            depth = Decimal(wh_match.group(3)) if wh_match.group(3) else None
            return width, height, depth
        except InvalidOperation:
            pass

    # Pattern 5b: Width first, then height (e.g., "11"w x 14"h")
    hw_pattern = r'(\d+(?:\.\d+)?)"?\s*w\s*x\s*(\d+(?:\.\d+)?)"?\s*h'
    hw_match = re.search(hw_pattern, size_str, re.IGNORECASE)
    if hw_match:
        try:
            width = Decimal(hw_match.group(1))
            height = Decimal(hw_match.group(2))
            return width, height, None
        except InvalidOperation:
            pass

    # Pattern 5c: Inches with quotes - flexible spacing (e.g., '25" x 6" x 1"' or '30"x30"')
    inches_pattern = r'^(\d+(?:\.\d+)?)\s*"\s*[xX]\s*(\d+(?:\.\d+)?)\s*"(?:\s*[xX]\s*(\d+(?:\.\d+)?)\s*")?$'
    inches_match = re.match(inches_pattern, size_str, re.IGNORECASE)
    if inches_match:
        try:
            dim1 = Decimal(inches_match.group(1))
            dim2 = Decimal(inches_match.group(2))
            dim3 = Decimal(inches_match.group(3)) if inches_match.group(3) else None
            return dim2, dim1, dim3
        except InvalidOperation:
            pass

    # Pattern 6: Plain numbers with fractions (e.g., "6 1/4 x 6 1/4 x 2" or "16 x 98 x 16")
    # Split by 'x' or 'X' and parse each dimension
    parts = re.split(r'\s*[xX]\s*', size_str)
    if len(parts) in [2, 3]:
        # Check if parts look like dimensions (no unit markers needed)
        dims = []
        for part in parts:
            # Remove any trailing quote marks
            part = part.strip().rstrip('"\'')
            dim = parse_fraction(part)
            if dim is not None:
                dims.append(dim)
            else:
                break

        if len(dims) == len(parts):
            if len(dims) == 2:
                return dims[1], dims[0], None  # width, height, depth
            elif len(dims) == 3:
                return dims[1], dims[0], dims[2]  # width, height, depth

    return None, None, None


def migrate_size_data(apps, schema_editor):
    """Migrate existing size CharField data to new dimension fields."""
    Artwork = apps.get_model('artworks', 'Artwork')

    total = 0
    migrated = 0
    skipped = 0
    failed = 0
    failed_items = []

    for artwork in Artwork.objects.all():
        total += 1
        if artwork.size:
            width, height, depth = parse_size_string(artwork.size)
            if width is not None and height is not None:
                artwork.width_inches = width
                artwork.height_inches = height
                artwork.depth_inches = depth
                artwork.save(update_fields=['width_inches', 'height_inches', 'depth_inches'])
                migrated += 1
            else:
                failed += 1
                failed_items.append(f"ID {artwork.id}: '{artwork.size}'")
        else:
            skipped += 1

    # Log results
    print(f"\n{'='*60}")
    print("Size Migration Complete")
    print(f"{'='*60}")
    print(f"  Total artworks: {total}")
    print(f"  Successfully migrated: {migrated}")
    print(f"  Skipped (no size): {skipped}")
    print(f"  Failed to parse: {failed}")
    if failed_items:
        print(f"\nFailed items (manual review needed):")
        for item in failed_items:
            print(f"  - {item}")
    print(f"{'='*60}\n")


def reverse_migration(apps, schema_editor):
    """Reverse migration - clear the dimension fields."""
    Artwork = apps.get_model('artworks', 'Artwork')
    Artwork.objects.update(width_inches=None, height_inches=None, depth_inches=None)
    print("Dimension fields cleared.")


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0013_add_dimension_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_size_data, reverse_migration),
    ]
