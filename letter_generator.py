from fastapi import HTTPException, Request
import asyncio
import openai
import os
from datetime import datetime, timedelta
import json
from datetime import datetime


async def generate_cover_letter(company_name: str, subject: str, nb_experience: int, activite: str, poste: str, skills: str):
    cover_letter_prompt = f"""
    s'Il vous plaît, ignorez toutes les instructions précédentes.
    Sujet : Rédaction d'une Lettre de Motivation pour une Demande d'Emploi

    Instruction :
    
    Je sollicite votre aide pour rédiger une lettre de motivation convaincante pour une demande d'emploi. Veuillez m'aider à créer une lettre de motivation personnalisée en tenant compte des détails suivants :

    Commencez la lettre par 'Cher Monsieur/Madame'.
    je veux que la lettre de motivation soit rédigée en trois paragraphes distincts.
    Chaque paragraphe devrait mettre en évidence des aspects spécifiques de ma candidature, notamment mes compétences, mon expérience et mon enthousiasme pour le poste. Merci de bien vouloir structurer la lettre en conséquence pour assurer une présentation claire et concise de mes qualifications
    
    Nom de l'Entreprise : {company_name}
    Sujet : {subject}
    Nombre d'Années d'Expérience : {nb_experience}
    Industrie/Activité : {activite}
    Poste Souhaité : {poste}
    Compétences et Qualités : {skills}

    Je souhaite que la lettre de motivation mette en avant mon enthousiasme pour le poste, en mettant en avant mes compétences et mon expérience, en les alignant avec les valeurs et les besoins de l'entreprise. Merci de mettre en lumière mes réalisations et d'expliquer en quoi mon parcours fait de moi le candidat idéal pour ce poste.

    Je vous remercie de votre compréhension et de votre assistance dans ce processus.
    
    """
    api_key = os.environ.get(
        'OPENAI_API_KEY')  # Retrieve your API key from an environment variable

    def generate_cover_letter_async():
        return openai.Completion.create(
            engine="text-davinci-003",
            prompt=cover_letter_prompt,
            max_tokens=800,  # Adjust the value as per your requirements
            n=1,
            stop=None,
            temperature=0,
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


REQUESTS_FILE_PATH = "requests_file.json"

# Load the requests_per_device dictionary from the file, if it exists
if os.path.exists(REQUESTS_FILE_PATH):
    try:
        with open(REQUESTS_FILE_PATH, "r") as file:
            requests_per_device = json.load(file)
    except json.JSONDecodeError:
        # If the file is empty or contains invalid JSON data, initialize an empty dictionary
        requests_per_device = {}
else:
    requests_per_device = {}


async def limitLetterGenerator(request: Request):
    # Get the current date and month
    today = datetime.now()
    current_month = today.strftime("%Y-%m")

    device_id = request.client.host

    # Check if the device ID exists in the requests_per_device dictionary
    if device_id in requests_per_device:
        # Get the requests made for the device this month
        requests_made = requests_per_device[device_id].get(current_month, 0)

        # Check if the number of requests made exceeds the limit
        if requests_made >= 20:
            raise HTTPException(
                status_code=429, detail="Vous avez atteint le nombre maximal de requêtes pour ce mois!")

        # Increment the number of requests made for the device this month
        requests_per_device[device_id][current_month] = requests_made + 1
    else:
        # If it's a new device, initialize the requests_per_device entry for this month
        requests_per_device[device_id] = {current_month: 1}

    # Save the updated requests_per_device dictionary to the file
    with open(REQUESTS_FILE_PATH, "w") as file:
        json.dump(requests_per_device, file)

    # Get the client's IP address
    client_ip = request.client.host

    # Get the client's user agent (e.g., OS name)
    client_user_agent = request.headers.get("user-agent", "")

    return {"msg": "Letter generated successfully", "client_ip": client_ip, "device_id": device_id, "OS": client_user_agent}
