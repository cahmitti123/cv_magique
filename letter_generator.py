from fastapi import HTTPException
import asyncio
import openai
import os

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







