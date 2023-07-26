from fastapi import HTTPException,Request
import asyncio
import openai
import os
from datetime import datetime, timedelta
import json
from datetime import datetime

async def generate_cover_letter(company_name: str, subject: str, nb_experience: int, activite: str, poste: str, skills: str):
    cover_letter_prompt = f"""
    "
    Rédige-moi une lettre de motivation en suivant les étapes suivantes:

    Introduction : Dans le premier paragraphe, présentation brève. Indiquer le {subject} et le {poste} pour lequel on postule ou le motif de la candidature.
    
    Corps de la lettre : Dans les paragraphes suivants, mettre en avant les {skills}, les {nb_experience} expériences professionnelles et les réalisations pertinentes.
    Faire le lien entre les {skills} et les exigences du poste visé. Éviter de simplement répéter ce qui est déjà dans le CV, mais plutôt,
    apporter des exemples concrets des réalisations et expliquer comment contribuer à {company_name} dans le domaine de {activite}.

    Expliquer pourquoi le candidat est intéressé par le {poste} et {company_name}. Mettez en évidence ce qui peut attirer dans le travail proposé.

    Dans le dernier paragraphe, exprimer de l'enthousiasme pour rejoindre l'entreprise {company_name} et réitérer l'intérêt pour le poste. 
    Mentionner que le candidat serait ravi de discuter plus en détail de sa candidature lors d'un entretien.

    Formule de politesse : Utiliser une formule de politesse appropriée pour conclure la lettre, 
   
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
            raise HTTPException(status_code=429, detail="Vous avez atteint le nombre maximal de requêtes pour ce mois!")

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
