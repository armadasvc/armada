import re
import os
import random
from faker import Factory
from password_generator import PasswordGenerator
from .utils import get_value_or_default, load_config


class Identity:

    def __init__(self, identity_params=None):
        self.identity_params = identity_params if identity_params is not None else {}
        self.enable_special_character_password = 1
        self.language = 'fr_FR'
        self.min_year = 18
        self.max_year = 80
        self.min_len_password = 12
        self.max_len_password = 14
        self.parse_identity_params()

    def parse_identity_params(self):
        self.identity_params = load_config(self.identity_params) if self.identity_params else {}
        self.enable_special_character_password = get_value_or_default(self.identity_params.get("enable_special_character_password"), self.enable_special_character_password)
        self.language = get_value_or_default(self.identity_params.get("language"), self.language)
        self.min_year = get_value_or_default(self.identity_params.get("min_year"), self.min_year)
        self.max_year = get_value_or_default(self.identity_params.get("max_year"), self.max_year)
        self.min_len_password = get_value_or_default(self.identity_params.get("min_len_password"), self.min_len_password)
        self.max_len_password = get_value_or_default(self.identity_params.get("max_len_password"), self.max_len_password)

    def launch_identity_creation(self):
        self.fake = Factory.create(self.language)
        self.seed = int.from_bytes(os.urandom(4), 'little')
        random.seed(self.seed)
        self.fake.seed_instance(self.seed)
        first_name = self.clean_name(self.fake.first_name())
        last_name = self.clean_name(self.fake.last_name())
        birth = self.fake.date_of_birth(None, self.min_year, self.max_year)
        birthday = birth.day
        birthmonth = birth.month
        birthyear = birth.year
        postalcode = self.fake.postcode()
        prefix = (first_name + last_name + postalcode).lower()
        password = self.create_password()
        identity_data = {
            'first_name': first_name,
            'name': last_name,
            'alias': prefix,
            'birth_day': birthday,
            'birth_month': birthmonth,
            'birth_year': birthyear,
            'password': password
        }
        return identity_data
    
    def create_password(self):
        pwo = PasswordGenerator()
        pwo.minlen = self.min_len_password
        pwo.maxlen = self.max_len_password
        password = pwo.generate()
        if self.enable_special_character_password == 1:
            password = re.sub(r'[^a-zA-Z0-9]', '', password)
        return password
    
    def clean_name(self,name_to_clean):
        # Remove hyphens and apostrophes
        name_to_clean = re.sub(r"[-' ]", '', name_to_clean)
        # Remove accents from characters
        name_to_clean = remove_accents(name_to_clean)
        return name_to_clean


def remove_accents(text):
    accents = {
        'à': 'a', 'â': 'a', 'ä': 'a', 'á': 'a', 'ã': 'a', 'å': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'î': 'i', 'ï': 'i', 'ì': 'i', 'í': 'i',
        'ô': 'o', 'ö': 'o', 'ò': 'o', 'ó': 'o', 'õ': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u', 'ú': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ç': 'c', 'ñ': 'n',
        'À': 'A', 'Â': 'A', 'Ä': 'A', 'Á': 'A', 'Ã': 'A', 'Å': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Î': 'I', 'Ï': 'I', 'Ì': 'I', 'Í': 'I',
        'Ô': 'O', 'Ö': 'O', 'Ò': 'O', 'Ó': 'O', 'Õ': 'O',
        'Ù': 'U', 'Û': 'U', 'Ü': 'U', 'Ú': 'U',
        'Ý': 'Y',
        'Ç': 'C', 'Ñ': 'N'
    }
    
    return ''.join(accents.get(c, c) for c in text)

