import phonenumbers

class Helper:
    
    @staticmethod
    def number_parsed(number: str) -> str:
        parsed_number = phonenumbers.parse(number, None)
        country_code = f"+{parsed_number.country_code}"
        national_number = parsed_number.national_number
        return country_code, national_number
    
