import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class Guru:
    HEADERS = {"Accept": "application/sparql-results+json"}
    HOW_OLD_IS = "how old is"
    POPULATION_OF = "population of"
    DOB = "date of birth"
    INCEPTION = "inception"
    POPULATION = "population"

    def __init__(self, endpoint: str = "https://query.wikidata.org/sparql"):
        self.endpoint = endpoint

    def ask(self, question: str):
        parsed = self._parse_question(question)
        if not parsed:
            return "Sorry, I couldn't understand the question."
        query, answer_label = parsed
        data = self._run_sparql_query(query)
        if not data:
            return "Sorry, I couldn't find the answer."
        return data[0][answer_label]["value"]

    def _parse_question(self, question: str):
        q_lower = question.lower()
        if self.HOW_OLD_IS in q_lower:
            return self._parse_age_question(question)
        elif self.POPULATION_OF in q_lower:
            return self._parse_population_question(question)
        else:
            return None

    def _parse_age_question(self, question: str):
        idx = self._get_index(question, self.HOW_OLD_IS)
        if idx == -1:
            return None
        entity = question[idx:].strip().rstrip("?")
        entity_type = self._get_entity_type(entity)
        if entity_type == "human":
            query = self._build_human_age_query(entity)
        else:
            query = self._build_object_age_query(entity)
        answer_label = "age"
        return query, answer_label

    def _parse_population_question(self, question: str):
        idx = self._get_index(question, self.POPULATION_OF)
        if idx == -1:
            return None
        entity = question[idx:].strip().rstrip("?")
        query = self._build_population_query(entity)
        answer_label = "population"
        return query, answer_label
    
    def _get_index(self, question: str, keyword: str) -> int:
        """
        Returns the index of the entity in the question.
        If the keyword is not found, returns -1.
        """
        idx = question.lower().find(keyword.lower())
        if idx == -1:
            return -1
        return idx + len(keyword)

    def _build_human_age_query(self, entity: str) -> str:
        return f"""
        SELECT ?age WHERE {{
          ?person rdfs:label "{entity}"@en.
          ?person wdt:{self._get_property_id(self.DOB)}?birthdate.
          BIND((YEAR(NOW()) - YEAR(?birthdate)) AS ?age)
        }}
        LIMIT 1
        """

    def _build_object_age_query(self, entity: str) -> str:
        return f"""
        SELECT ?age WHERE {{
          ?thing rdfs:label "{entity}"@en.
          ?thing wdt:{self._get_property_id(self.INCEPTION)} ?inception.
          BIND((YEAR(NOW()) - YEAR(?inception)) AS ?age)
        }}
        LIMIT 1
        """

    def _build_population_query(self, entity: str) -> str:
        return f"""
        SELECT ?population WHERE {{
          ?city rdfs:label "{entity}"@en.
          ?city wdt:{self._get_property_id(self.POPULATION)} ?population.
        }}
        ORDER BY DESC(?population)
        LIMIT 1
        """

    def _get_entity_type(self, entity: str):
        """ 
        Determines the type of the entity (human, object, etc.) using Wikidata.
        """
        sparql = f"""
        SELECT ?typeLabel WHERE {{
          ?entity rdfs:label "{entity}"@en.
          ?entity wdt:P31 ?type.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        data = self._run_sparql_query(sparql)
        if data:
            return data[0]["typeLabel"]["value"].lower()
        return None
    
    def _get_property_id(self, property_name: str):
        """
        Maps property names to Wikidata property IDs. 
        Source: https://prop-explorer.toolforge.org
        """
        property_id_map = {
            self.POPULATION: "P1082",
            self.DOB: "P569",
            self.INCEPTION: "P571"
        }
        return property_id_map.get(property_name.lower(), None)

    def _run_sparql_query(self, query: str):
        """ 
        Executes a SPARQL query against the Wikidata endpoint. 
        If the query fails on 429 too many requests, it retries up to 3 times.
        """
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=5, status_forcelist=[429])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.get(self.endpoint, params={"query": query}, headers=self.HEADERS)
        if response.status_code != 200:
            return None
        try:
            data = response.json()
        except Exception:
            return None
        return data.get("results", {}).get("bindings", [])
