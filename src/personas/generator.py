"""Swiss persona generator."""

import json
import random
from typing import List, Dict
from .models import Persona


class SwissPersonaGenerator:
    """Generates realistic Swiss personas for market research."""
    
    def __init__(self):
        # Swiss demographics data
        self.cantons = {
            'Zurich': {'language': 'German', 'population_weight': 1.3},
            'Bern': {'language': 'German', 'population_weight': 1.0},
            'Geneva': {'language': 'French', 'population_weight': 0.5},
            'Vaud': {'language': 'French', 'population_weight': 0.8},
            'Ticino': {'language': 'Italian', 'population_weight': 0.35},
            'Basel-Stadt': {'language': 'German', 'population_weight': 0.2},
            'Valais': {'language': 'French', 'population_weight': 0.3},
            'Lucerne': {'language': 'German', 'population_weight': 0.4},
            'St. Gallen': {'language': 'German', 'population_weight': 0.5},
            'Aargau': {'language': 'German', 'population_weight': 0.7},
            'Fribourg': {'language': 'French', 'population_weight': 0.3},
            'Thurgau': {'language': 'German', 'population_weight': 0.27},
            'Solothurn': {'language': 'German', 'population_weight': 0.27},
            'Neuchâtel': {'language': 'French', 'population_weight': 0.18},
            'Zug': {'language': 'German', 'population_weight': 0.14},
            'Schwyz': {'language': 'German', 'population_weight': 0.16},
            'Jura': {'language': 'French', 'population_weight': 0.07},
            'Schaffhausen': {'language': 'German', 'population_weight': 0.08},
            'Uri': {'language': 'German', 'population_weight': 0.04},
            'Obwalden': {'language': 'German', 'population_weight': 0.04},
            'Nidwalden': {'language': 'German', 'population_weight': 0.03},
            'Glarus': {'language': 'German', 'population_weight': 0.04},
            'Appenzell Ausserrhoden': {'language': 'German', 'population_weight': 0.05},
            'Appenzell Innerrhoden': {'language': 'German', 'population_weight': 0.02},
            'Graubünden': {'language': 'German', 'population_weight': 0.2}  # Mixed German/Romansh/Italian
        }
        
        # Weighted canton selection based on population
        self.weighted_cantons = []
        for canton, data in self.cantons.items():
            self.weighted_cantons.extend([canton] * int(data['population_weight'] * 10))
        
        self.genders = ['Male', 'Female', 'Non-binary']
        self.occupations = [
            'Teacher', 'Engineer', 'Farmer', 'Doctor', 'Student', 'Retired', 
            'IT Specialist', 'Artist', 'Banker', 'Nurse', 'Chef', 'Mechanic',
            'Lawyer', 'Architect', 'Scientist', 'Entrepreneur', 'Social Worker',
            'Journalist', 'Electrician', 'Pharmacist', 'Accountant', 'Police Officer'
        ]
        
        self.educations = [
            'Compulsory School', 'Vocational Training', 'High School', 
            'Bachelor', 'Master', 'PhD'
        ]
        
        # Swiss political parties and leanings
        self.political_data = [
            {'party': 'SVP', 'leaning': 'Right', 'weight': 0.3},
            {'party': 'SP', 'leaning': 'Left', 'weight': 0.2},
            {'party': 'FDP', 'leaning': 'Center-Right', 'weight': 0.15},
            {'party': 'The Center', 'leaning': 'Center', 'weight': 0.12},
            {'party': 'Greens', 'leaning': 'Left', 'weight': 0.1},
            {'party': 'GLP', 'leaning': 'Center-Left', 'weight': 0.08},
            {'party': 'Apolitical', 'leaning': 'Apolitical', 'weight': 0.05}
        ]
        
        self.weighted_political = []
        for data in self.political_data:
            self.weighted_political.extend([data['leaning']] * int(data['weight'] * 20))
        
        # Persona templates for realistic descriptions
        self.description_templates = {
            'urban': [
                "A {age}-year-old {gender} from {canton} who works as a {occupation} and values {values}. Lives in the city and enjoys {hobbies}.",
                "Urban professional {gender} aged {age} from {canton}. Working in {occupation} with {education} background. Passionate about {values}.",
                "City-dweller from {canton}, {age} years old. {occupation} who cares deeply about {values} and spends free time {hobbies}."
            ],
            'rural': [
                "A {age}-year-old {gender} from rural {canton}. Works as {occupation} and values {values}. Enjoys {hobbies} and community life.",
                "Rural {gender} aged {age} from {canton} canton. {occupation} who appreciates {values} and traditional Swiss culture.",
                "From the countryside of {canton}, this {age}-year-old {gender} works in {occupation}. Values {values} and enjoys {hobbies}."
            ]
        }
        
        self.values = [
            'sustainability', 'tradition', 'innovation', 'family', 'community', 
            'privacy', 'efficiency', 'quality', 'security', 'freedom'
        ]
        
        self.hobbies = [
            'hiking in the Alps', 'skiing', 'local politics', 'reading', 
            'cooking traditional Swiss food', 'watching football', 'volunteering',
            'gardening', 'technology', 'classical music'
        ]

    def generate_persona(self, persona_id: int) -> Persona:
        """Generate a single realistic Swiss persona."""
        # Select canton with population weighting
        canton = random.choice(self.weighted_cantons)
        language = self.cantons[canton]['language']
        
        # Age distribution - more working age population
        if random.random() < 0.65:  # 65% working age (25-64)
            age = random.randint(25, 64)
        elif random.random() < 0.85:  # 20% seniors (65+)
            age = random.randint(65, 90)
        else:  # 15% young adults (18-24)
            age = random.randint(18, 24)
        
        gender = random.choice(self.genders)
        occupation = random.choice(self.occupations)
        
        # Education correlated with age and occupation
        if occupation == 'Student':
            education = random.choice(['High School', 'Bachelor', 'Master'])
        elif occupation == 'Retired':
            education = random.choice(['Compulsory School', 'Vocational Training', 'High School'])
        elif occupation in ['Doctor', 'Lawyer', 'Scientist', 'Architect']:
            education = random.choice(['Master', 'PhD'])
        else:
            education = random.choice(self.educations)
        
        political_leaning = random.choice(self.weighted_political)
        
        # Determine if urban or rural based on canton
        urban_cantons = ['Zurich', 'Geneva', 'Basel-Stadt', 'Vaud', 'Bern']
        is_urban = canton in urban_cantons and random.random() < 0.7
        
        template_type = 'urban' if is_urban else 'rural'
        template = random.choice(self.description_templates[template_type])
        
        values = random.choice(self.values)
        hobbies = random.choice(self.hobbies)
        
        description = template.format(
            age=age,
            gender=gender,
            canton=canton,
            occupation=occupation,
            education=education,
            values=values,
            hobbies=hobbies
        )[:150]  # Ensure max 150 characters
        
        return Persona(
            id=persona_id,
            age=age,
            gender=gender,
            canton=canton,
            language=language,
            occupation=occupation,
            education=education,
            political_leaning=political_leaning,
            description=description
        )

    def generate_personas(self, count: int = 100) -> List[Persona]:
        """Generate multiple diverse Swiss personas."""
        personas = []
        
        # Ensure linguistic diversity
        german_target = int(count * 0.65)  # 65% German-speaking
        french_target = int(count * 0.23)  # 23% French-speaking
        italian_target = int(count * 0.08)  # 8% Italian-speaking
        romansh_target = count - german_target - french_target - italian_target  # ~4% Romansh
        
        language_counts = {'German': 0, 'French': 0, 'Italian': 0, 'Romansh': 0}
        
        for i in range(1, count + 1):
            persona = self.generate_persona(i)
            
            # Adjust for linguistic diversity
            if language_counts['German'] < german_target and persona.language == 'German':
                language_counts['German'] += 1
            elif language_counts['French'] < french_target and persona.language == 'French':
                language_counts['French'] += 1
            elif language_counts['Italian'] < italian_target and persona.language == 'Italian':
                language_counts['Italian'] += 1
            elif persona.language in ['German', 'French', 'Italian']:
                language_counts[persona.language] += 1
            else:
                persona.language = 'Romansh'
                language_counts['Romansh'] += 1
            
            personas.append(persona)
        
        return personas

    def save_personas(self, personas: List[Persona], filename: str = 'personas.json'):
        """Save personas to JSON file."""
        personas_dict = [persona.model_dump() for persona in personas]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(personas_dict, f, indent=4, ensure_ascii=False)
        
        print(f"Generated {len(personas)} personas in {filename}")
        
        # Print demographic summary
        languages = {}
        cantons = {}
        political_leanings = {}
        
        for persona in personas:
            languages[persona.language] = languages.get(persona.language, 0) + 1
            cantons[persona.canton] = cantons.get(persona.canton, 0) + 1
            political_leanings[persona.political_leaning] = political_leanings.get(persona.political_leaning, 0) + 1
        
        print("\nDemographic Summary:")
        print(f"Languages: {languages}")
        print(f"Top 5 Cantons: {dict(sorted(cantons.items(), key=lambda x: x[1], reverse=True)[:5])}")
        print(f"Political Leanings: {political_leanings}")

    def load_personas(self, filename: str = 'personas.json') -> List[Persona]:
        """Load personas from JSON file."""
        with open(filename, 'r', encoding='utf-8') as f:
            personas_data = json.load(f)
            return [Persona(**p) for p in personas_data]
