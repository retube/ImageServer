from PIL import Image, ExifTags
import sys
import os


def extract_exif_data(image_path):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Extract EXIF data
            exif_data = img._getexif()

            if exif_data is None:
                print("No EXIF data found in the image.")
                return

            # Map EXIF IDs to their tag names and decode values where possible
            decoded_exif = {}
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                # Handle GPS info separately
                if tag_name == "GPSInfo":
                    gps_data = {}
                    for gps_tag in value:
                        gps_tag_name = ExifTags.GPSTAGS.get(gps_tag, gps_tag)
                        gps_data[gps_tag_name] = value[gps_tag]
                    decoded_exif[tag_name] = gps_data
                else:
                    # Try to decode other tags
                    try:
                        if isinstance(value, bytes):
                            decoded_exif[tag_name] = value.decode('utf-8', errors='replace')
                        else:
                            decoded_exif[tag_name] = value
                    except:
                        decoded_exif[tag_name] = value

            # Pretty print the EXIF data
            print(f"\nEXIF Data for {os.path.basename(image_path)}:")
            print("-" * 40)
            for key, val in decoded_exif.items():
                if isinstance(val, dict):
                    print(f"{key}:")
                    for sub_key, sub_val in val.items():
                        print(f"  {sub_key}: {sub_val}")
                else:
                    print(f"{key}: {val}")

    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
    except Exception as e:
        print(f"Error processing image: {str(e)}")


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python exif_extractor.py <image_path>")
    #     sys.exit(1)
    #
    # image_path = sys.argv[1]

    image_path = r"D:\Card backups\backup\Card1\100CANON\IMG_2567.JPG"

    extract_exif_data(image_path)