import base64
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import shutil
import uuid
from tryon_service import process_tryon
from file_utils import cleanup_old_files
from upload import upload_file_to_s3
from dotenv import load_dotenv
from twilio_service import handle_user_message
import logging

app = Flask(__name__)
CORS(app)

load_dotenv()
os.makedirs("generated_output", exist_ok=True)
os.makedirs('logs', exist_ok = True)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
)

@app.route('/twilio-webhook', methods=['POST'])
def whatsapp_reply():
    sender = request.form.get('From')
    message = request.form.get('Body')
    media_url = request.form.get('MediaUrl0')
    
    logging(f'{sender} sent {message}')
    logging("Printing media url:", media_url)
    
    # Delegate the message handling to the service function
    response = handle_user_message(sender, message, media_url)
    return response

@app.route("/try-on", methods=["POST"])
def try_on():
    try:
        # Get the uploaded files and description
        person_image = request.files['person_image']
        garment_image = request.files['garment_image']
        garment_desc = request.form['garment_desc']
        
        # Save uploaded images locally with unique names
        person_image_path = f"generated_output/{uuid.uuid4().hex}_{person_image.filename}"
        garment_image_path = f"generated_output/{uuid.uuid4().hex}_{garment_image.filename}"
        
        person_image.save(person_image_path)
        garment_image.save(garment_image_path)

        AWS_PERSON_UPLOAD_BUCKET = "upload-person-image-folder"
        AWS_GARMENT_UPLOAD_BUCKET = "upload-germent-image-folder"

        _ = upload_file_to_s3(person_image_path, AWS_PERSON_UPLOAD_BUCKET)
        _ = upload_file_to_s3(garment_image_path, AWS_GARMENT_UPLOAD_BUCKET)

        # Process try-on using Hugging Face API
        output_image, masked_image = process_tryon(person_image_path, garment_image_path, garment_desc)
        
        # Save the generated images in 'generated_output'

        AWS_OUTPUT_IMAGE_BUCKET = "output-person-image-folder"
        AWS_OUTPUT_MASKED_IMAGE_BUCKET = "output-garment-image-folder"

        output_image_dest = f"generated_output/output_{uuid.uuid4().hex}.png"
        masked_image_dest = f"generated_output/masked_{uuid.uuid4().hex}.png"
        shutil.move(output_image, output_image_dest)
        shutil.move(masked_image, masked_image_dest)

        # Encode images for external services (base64)
        with open(output_image_dest, "rb") as image_file:
            output_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        with open(masked_image_dest, "rb") as image_file:
            masked_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        _ = upload_file_to_s3(output_image_dest, AWS_OUTPUT_IMAGE_BUCKET)
        _ = upload_file_to_s3(masked_image_dest, AWS_OUTPUT_MASKED_IMAGE_BUCKET)


        # Return paths for UI and base64 for external service use
        return jsonify({
            "output_image": f"generated_output/{os.path.basename(output_image_dest)}",
            "masked_image": f"generated_output/{os.path.basename(masked_image_dest)}",
            "output_image_base64": output_image_base64,
            "masked_image_base64": masked_image_base64
        })

    except Exception as e:
        logging.error(f"Error in /try-on: {str(e)}")
        return jsonify({"error": f"Error processing the try-on. Error : {str(e)}"}), 500

# Serve the HTML frontend
@app.route("/")
def root():
    return render_template("index.html")

# Serve static and generated files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/generated_output/<path:filename>')
def serve_generated_output(filename):
    return send_from_directory('generated_output', filename)


if __name__ == "__main__":
    # cleanup_old_files("generated_output", hours=1)
    # if os.path.exists("logs/app.log"):
    #     os.remove("logs/app.log")
    app.run(host="127.0.0.1", port=8080, debug=True)
