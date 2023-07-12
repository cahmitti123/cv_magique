from fastapi import HTTPException,Request
import asyncio
import openai
import os
from datetime import datetime, timedelta

async def generate_cover_letter(company_name: str, subject: str, nb_experience: int, activite: str, poste: str, skills: str):
    cover_letter_prompt = f"""
    "Please ignore all previous instructions.

     Output langage: French

     I want you to write a motivation letter, as a person without saying the name of the person, hoping to get a job.
     You will add examples how my profile could bring value in the {activite}, and say 2 positive things about: {company_name}
   
     Objet: Lettre de motivation
     subject: {subject}
     Entreprise destinataire : {company_name}
     Nombre d'années d'expérience: {nb_experience}
     Domaine d'activité : {activite}
     competences: {skills}
     Poste souhaité : {poste}
     Please don´t explain anything of what your are going to do .Just do it."
    """
    api_key = os.environ.get('OPENAI_API_KEY')  # Retrieve your API key from an environment variable

    def generate_cover_letter_async():
        return openai.Completion.create(
            engine="text-davinci-003",
            prompt=cover_letter_prompt,
            max_tokens=500,  # Adjust the value as per your requirements
            n=1,
            stop=None,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            api_key=api_key
        )

    cover_letter_response = await asyncio.to_thread(generate_cover_letter_async)

    if "choices" not in cover_letter_response or len(cover_letter_response.choices) == 0:
        raise Exception("Failed to generate cover letter description")

    description = cover_letter_response.choices[0].text.strip()

    return {"description": description}


requests_per_device = {}


async def limitLetterGenerator(request: Request):
    # Get the current date
    today = datetime.now().date().isoformat()
    device_id = request.client.host
    # Check if the device ID exists in the requests_per_device dictionary
    if device_id in requests_per_device:
        # Get the requests made for the device today
        requests_made = requests_per_device[device_id].get(today, 0)

        # Check if the number of requests made exceeds the limit
        if requests_made >= 2:
            raise HTTPException(status_code=429, detail="You have reached your today's quota. Please try again later.")

        # Increment the number of requests made for the device today
        requests_per_device[device_id][today] = requests_made + 1
    else:
        # If it's a new device, initialize the requests_per_device entry
        requests_per_device[device_id] = {today: 1}

    # Get the client's IP address
    client_ip = request.client.host

    # Get the client's user agent (e.g., OS name)
    client_user_agent = request.headers.get("user-agent", "")

    return {"msg":"Letter generated successfull","client_ip": client_ip, "device_id":device_id, "OS":client_user_agent}



