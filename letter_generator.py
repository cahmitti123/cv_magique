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
    The Letter must be format HTML
    
    Je sollicite votre aide pour rédiger une lettre de motivation convaincante pour une demande d'emploi. Veuillez m'aider à créer une lettre de motivation personnalisée en tenant compte des détails suivants :

    Commencez la lettre par '<p>Cher Monsieur/Madame</p>'.

    je veux que la lettre de motivation soit rédigée en trois paragraphes pour chaque paragraphe dans une balise <p> </p> distincts.
    Chaque paragraphe devrait mettre en évidence des aspects spécifiques de ma candidature, notamment mes compétences,
    mon expérience et mon enthousiasme pour le poste. Merci de bien vouloir structurer la lettre en conséquence pour assurer une présentation 
    claire et concise de mes qualifications:

    premier paragraphe:

    Je vous écris pour exprimer mon vif intérêt à rejoindre {company_name} en tant que {poste}. 
    Fort de {nb_experience} années d'expérience dans l'industrie {activite}, je suis convaincu que mes compétences et ma passion pour 
    {subject} font de moi un candidat idéal pour ce poste. Mon parcours professionnel m'a permis de développer des compétences exceptionnelles 
    en {skills}, que je suis enthousiaste à l'idée de mettre au service de votre entreprise.
     
    deuxième paragraphe:

    Je suis particulièrement attiré par {company_name} en raison de son engagement envers {subject} et de sa réputation exceptionnelle dans l'industrie.
    Au cours de mes années d'expérience, j'ai réussi à atteindre des résultats remarquables,
    Mon approche proactive et ma capacité à résoudre les problèmes ont été des atouts majeurs dans mes rôles précédents, 
    et je suis convaincu que ces compétences seront précieuses pour {company_name}.

    troisième paragraphe:
    
    Je suis convaincu que ma passion pour {subject} et mon engagement envers l'excellence, combinés à mon expérience professionnelle,
    font de moi le candidat idéal pour ce poste chez {company_name}. J'espère avoir l'opportunité de discuter en détail de ma candidature
    avec vous et d'expliquer en personne comment je peux contribuer de manière significative à votre entreprise. 
    Je vous remercie de l'attention que vous porterez à ma demande et je me tiens à votre disposition pour toute information supplémentaire.
    

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
    return {"description": description.replace('\n\n', ' ').replace('\n', ' ')} 
  

    # cover_letter_response = await asyncio.to_thread(generate_cover_letter_async)

    # if "choices" not in cover_letter_response or len(cover_letter_response.choices) == 0:
    #     raise Exception("Failed to generate cover letter description")

    # description = cover_letter_response.choices[0].text.strip()
    # description = description.replace("\\n", "\n")

    # paragraphs = description.split('\n')
    # html_paragraphs = "\n".join([f'<p>{paragraph}</p>' for paragraph in paragraphs])
    # return {"description": html_paragraphs}


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
