from fastapi import HTTPException
import openai
import os

def generate_cover_letter(company_name: str, subject: str,nb_experience: int,activite: str, poste:str, skills:str):
    cover_letter_prompt = f"""
    "Please ignore all previous instructions.

     Output langage: French

     I want you to write a motivation letter, as a person, hoping to get a job.
     You will add examples how my profile could bring value in the {activite}, and say 2 positive things about: {company_name}
   
     Objet: Lettre de motivation
     subject: {subject}
     Entreprise destinataire : {company_name}
     Nombre d'années d'expérience: {nb_experience}
     Domaine d'activité : {activite}
     competences: {skills}
     Poste souhaité : {poste}

     Make this text less than 600 tokens, Please don´t explain anything of what your are going to do before
     or after you stop writing and make sure to add the back to lines also. Just do it."
    """
    api_key = os.environ.get('OPENAI_API_KEY')  # Retrieve your API key from an environment variable
    
    cover_letter_response = openai.Completion.create(
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

    if "choices" not in cover_letter_response or len(cover_letter_response.choices) == 0:
        raise HTTPException(status_code=500, detail="Failed to generate cover letter description")

    description = cover_letter_response.choices[0].text.strip()

    return {"description": description}





