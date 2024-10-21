import os
import requests
from twilio.twiml.messaging_response import MessagingResponse
from tryon_service import process_tryon
from twilio.rest import Client
import shutil
import asyncio
import uuid
from upload import upload_file_to_s3
from dotenv import load_dotenv

load_dotenv()

# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")  # Replace with your SID
auth_token = os.getenv("AUTH_TOKEN")    # Replace with your auth token

# State to store user flow (In-memory for simplicity; use a DB for production)
user_state = {}
client = Client(username=account_sid,password = auth_token)

def save_image(media_url, sender, message):
    """Download and save an image from Twilio media URL."""
    # Authenticate the media request
    r = requests.get(media_url, auth=(account_sid, auth_token), stream=True)
    content_type = r.headers['Content-Type']
    username = sender.split(':')[1]  # Remove 'whatsapp:' prefix
    
    # Determine the file extension based on content type
    if content_type == 'image/jpeg':
        filename = f'uploads/{username}/{uuid.uuid4()}.jpg'
    elif content_type == 'image/png':
        filename = f'uploads/{username}/{uuid.uuid4()}.png'
    elif content_type == 'image/gif':
        filename = f'uploads/{username}/{uuid.uuid4()}.gif'
    else:
        return None, 'Unsupported media type'
    
    # Create directories and save the file
    if not os.path.exists(f'uploads/{username}'):
        os.makedirs(f'uploads/{username}')
    
    with open(filename, 'wb') as f:
        f.write(r.content)
    
    return filename, None

def respond(message, image_url = None):
    """Create a Twilio MessagingResponse."""
    response = MessagingResponse()
    response.message(message)
    if image_url:
        response.media(image_url)
    return str(response)



def handle_user_message(sender, message, media_url):
    """Handle the incoming message and guide the user through the flow."""
    username = sender.split(':')[1]  
    print(username)
    
    user_flow = user_state.get(username, {})
    
    
    if media_url:
        # Save the image
        saved_filename, error = save_image(media_url, sender, message)
        if error:
            return respond('Unsupported image type. Please send a JPEG, PNG, or GIF.')
        
        if 'person_image' not in user_flow:
            user_flow['person_image'] = saved_filename
            user_state[username] = user_flow
            return respond('Is this a person image or garment image? (Reply with "person" or "garment")')
        
        elif 'garment_image' not in user_flow:
            user_flow['garment_image'] = saved_filename
            user_state[username] = user_flow
            return respond('Please send the garment description.')
        
        
        elif 'garment_desc_image' not in user_flow:
            user_flow['garment_desc_image'] = saved_filename
            user_state[username] = user_flow
            return call_try_on_api(user_flow)

    
    if 'person_image' in user_flow and 'garment_image' in user_flow and 'garment_desc_image' not in user_flow:
        user_flow['garment_desc_image'] = message  # Save the text description
        user_state[username] = user_flow
        return call_try_on_api(user_flow, username)

   
    if message.lower() in ['p', 'person']:
        return respond('Please send the garment image.')
    elif message.lower() in ['g', 'garment']:
        return respond('Please send the person image.')
    else:
        return respond('Please send a valid command: "person" or "garment".')


    
def send_message(image_path, username):
    from_whatsapp_number='whatsapp:+14155238886'

    to_whatsapp_number = f'whatsapp:{username}'
    print("Sending images")
    client.messages.create(
        body="Generated Image !!",
        media_url=image_path,
        from_=from_whatsapp_number,
        to = to_whatsapp_number
    )

def call_try_on_api(user_flow, username):
    """Placeholder for the try-on API logic."""
    person_image = user_flow['person_image']
    garment_image = user_flow['garment_image']
    garment_desc_image = user_flow['garment_desc_image']
    
    output_image,masked_image  = process_tryon(person_image, garment_image, garment_desc_image)
    # Save the generated images in 'generated_output'
    output_image_dest = f"generated_output/output_{uuid.uuid4().hex}.png"
    masked_image_dest = f"generated_output/masked_{uuid.uuid4().hex}.png"
    shutil.move(output_image, output_image_dest)
    shutil.move(masked_image, masked_image_dest)

    public_url = upload_file_to_s3(output_image_dest)
    print(f"Public url : {public_url}")
    try:
        send_message(public_url)
    except Exception as e:
        print(e)
    return respond('Try-on process Ended!', public_url)

