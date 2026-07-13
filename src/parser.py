import re

class ClinicalParser:
    def __init__(self):
        # Build keyword mappings to search inside note texts and return matched spans
        self.code_keywords = {
            "I50.23": [r"chronic systolic heart failure", r"systolic chronic heart failure", r"systolic heart failure"],
            "I50.33": [r"chronic diastolic heart failure", r"diastolic chronic heart failure", r"diastolic heart failure"],
            "I50.9": [r"heart failure", r"congestive heart failure"],
            "E03.9": [r"hypothyroidism", r"thyroid deficiency"],
            "E11.9": [r"diabetic mellitus type 2", r"diabetes", r"type 2 diabetes", r"t2dm"],
            "M23.22": [r"knee arthroscopy", r"meniscus tear", r"torn meniscus"],
            "93451": [r"cardiac catheterization", r"heart cath"],
            "99213": [r"cardiovascular evaluation", r"routine visit", r"established patient visit"],
            "97110": [r"physical therapy evaluation", r"rehabilitation", r"therapeutic exercises"],
            "45378": [r"colonoscopy"],
            "K21.9": [r"gastroesophageal reflux disease", r"gerd"],
            "G43.909": [r"migraine headaches", r"migraine"],
            "J44.9": [r"chronic obstructive pulmonary disease", r"copd"],
            "N18.3": [r"chronic kidney disease", r"ckd"],
            "C50.919": [r"breast cancer"]
        }

    def parse_note(self, text):
        """
        Parses note text to identify matching entity codes and returns character spans for highlighting.
        Returns a list of dicts: [{'code': 'I50.23', 'start': 45, 'end': 75, 'match': 'chronic systolic heart failure'}]
        """
        matches = []
        for code, patterns in self.code_keywords.items():
            for pattern in patterns:
                for m in re.finditer(pattern, text, re.IGNORECASE):
                    # Prevent overlapping matches on the same code for simplicity
                    if not any(x["code"] == code and x["start"] == m.start() for x in matches):
                        matches.append({
                            "code": code,
                            "start": m.start(),
                            "end": m.end(),
                            "match": m.group(0)
                        })
        return matches

    def extract_dosages(self, text):
        """
        Finds medication dosages and extracts value, units (mg vs mcg, etc.)
        Returns a list of dicts: [{'medication': 'Lisinopril', 'value': 10.0, 'unit': 'mg', 'start': 120, 'end': 135}]
        """
        # Matches patterns like: Lisinopril 10 mg or levothyroxine 100 mcg
        pattern = r"\b([A-Za-z]+)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|units)\b"
        dosages = []
        for m in re.finditer(pattern, text, re.IGNORECASE):
            dosages.append({
                "medication": m.group(1),
                "value": float(m.group(2)),
                "unit": m.group(3).lower(),
                "start": m.start(),
                "end": m.end(),
                "match": m.group(0)
            })
        return dosages
