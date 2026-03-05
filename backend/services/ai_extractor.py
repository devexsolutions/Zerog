import os
import json
import logging
from typing import Dict, Any, Optional
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIExtractor:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error inicializando cliente Mistral: {e}")
        else:
            logger.warning("MISTRAL_API_KEY no encontrada en variables de entorno.")

    def extract_data_from_text(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Utiliza Mistral AI para extraer datos estructurados de un texto legal.
        """
        if not self.client:
            logger.warning("Cliente Mistral no disponible. Saltando extracción IA.")
            return {"ai_status": "skipped_no_key"}

        if not text or len(text) < 50:
             return {"ai_status": "skipped_text_too_short"}

        prompt = self._build_prompt(text, doc_type)
        
        try:
            logger.info(f"Enviando solicitud a Mistral para documento tipo {doc_type}...")
            chat_response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={"type": "json_object"},
            )
            
            response_content = chat_response.choices[0].message.content
            logger.info("Respuesta recibida de Mistral.")
            
            # Parsear JSON
            try:
                data = json.loads(response_content)
                data["ai_status"] = "success"
                return data
            except json.JSONDecodeError:
                logger.error("Error parseando JSON de respuesta de Mistral")
                return {"ai_status": "error_json_parse", "raw_response": response_content}
                
        except Exception as e:
            logger.error(f"Error en llamada a Mistral API: {e}")
            return {"ai_status": "error_api_call", "error_details": str(e)}

    def _build_prompt(self, text: str, doc_type: str) -> str:
        base_prompt = """
        Eres un asistente legal experto en herencias y sucesiones en España. 
        Tu tarea es analizar el siguiente texto extraído mediante OCR de un documento legal y extraer la información relevante en formato JSON estricto.
        
        Si algún campo no se encuentra, déjalo como null o una cadena vacía, no inventes datos.
        """
        
        if doc_type == "testamento" or doc_type == "last_will":
            specific_instructions = """
            El documento es un TESTAMENTO o ÚLTIMAS VOLUNTADES. Extrae:
            1. Datos del Testador (nombre, DNI si aparece, estado civil).
            2. Herederos: Lista de herederos mencionados con su parentesco (Hijo, Cónyuge, Sobrino, etc.) y porcentaje o cuota si se especifica.
            3. Albaceas o Contadores-Partidores si los hay.
            4. Cláusulas especiales: Resumen breve de usufructos, legados específicos o condiciones.
            5. Referencias Catastrales: Lista de referencias catastrales (20 caracteres) mencionadas.
            
            Formato JSON esperado:
            {
                "deceased": {"name": "...", "dni": "...", "marital_status": "..."},
                "heirs": [
                    {"name": "...", "relationship": "...", "share": "...", "notes": "..."}
                ],
                "executors": [{"name": "..."}],
                "clauses": ["..."],
                "cadastral_references": ["..."]
            }
            """
        elif doc_type == "deed" or doc_type == "declaracion_herederos":
            specific_instructions = """
            El documento es una ESCRITURA DE ACEPTACIÓN DE HERENCIA o DECLARACIÓN DE HEREDEROS. Extrae:
            1. Datos del Causante (fallecido).
            2. Herederos aceptantes y sus cuotas adjudicadas.
            3. Inventario de Bienes: Lista detallada de bienes inmuebles (descripción, referencia catastral, valor), cuentas bancarias (IBAN, saldo) y otros activos.
            
            Formato JSON esperado:
            {
                "deceased": {"name": "...", "date_of_death": "..."},
                "heirs": [{"name": "...", "share": "..."}],
                "assets": [
                    {"type": "REAL_ESTATE|BANK_ACCOUNT|OTHER", "description": "...", "cadastral_reference": "...", "value": 0.0, "iban": "..."}
                ]
            }
            """
        else:
            specific_instructions = """
            Analiza el documento y extrae cualquier información relevante sobre personas, fechas y cantidades económicas.
            Formato JSON libre pero estructurado.
            """

        return f"{base_prompt}\n\n{specific_instructions}\n\nTEXTO OCR:\n{text}"

# Instancia global
ai_extractor = AIExtractor()
