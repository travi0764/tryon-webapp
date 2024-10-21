from gradio_client import Client, file, handle_file
import logging
import os
from dotenv import load_dotenv

load_dotenv()

client = Client("Nymbo/Virtual-Try-On", hf_token=os.getenv("HF_TOKEN"), verbose=False)
def process_tryon(person_image_path, garment_image_path, garment_desc):
    try:
        

        # Call the API to generate try-on images
        result = client.predict(
            dict={"background": handle_file(person_image_path), "layers": [], "composite": None},
            garm_img=handle_file(garment_image_path),
            garment_des=garment_desc,
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            api_name="/tryon"
        )
        
        output_image, masked_image = result  # Paths of the output images
        return output_image, masked_image
        # return True
    
    except Exception as e:
        logging.error(f"Error in process_tryon: {str(e)}")
        raise RuntimeError("Failed to process the try-on request.")
