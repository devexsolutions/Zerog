import requests
import xmltodict

class CatastroService:
    BASE_URL = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx"

    @staticmethod
    def get_property_by_ref(ref_catastral: str):
        """
        Consulta datos de un inmueble por Referencia Catastral usando Consulta_DNPRC.
        """
        # Limpiar referencia de espacios, guiones y caracteres no alfanuméricos
        ref_catastral = "".join(filter(str.isalnum, ref_catastral)).upper()
        
        url = f"{CatastroService.BASE_URL}/Consulta_DNPRC"
        params = {
            "Provincia": "",
            "Municipio": "",
            "RC": ref_catastral
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            data = xmltodict.parse(response.content)
            
            # Check for errors in Catastro response
            if 'consulta_dnprc' in data and 'lerr' in data['consulta_dnprc']:
                 return {
                    "error": "Referencia Catastral no encontrada o inválida",
                    "raw": data
                }

            # Extract relevant info
            # Structure usually: consulta_dnprc -> bico -> bi -> (dt, ldt)
            if 'consulta_dnprc' in data and 'bico' in data['consulta_dnprc']:
                bi = data['consulta_dnprc']['bico']['bi']
                ldt = bi.get('ldt', "") # Dirección completa
                de = bi.get('de', {}) # Datos económicos/uso
                
                # Extract usage and surface
                usage = ""
                surface = 0
                
                # 'de' can be a list or a dict, although for a single RC it's usually a dict inside 'bi'
                # But 'bi' itself might be a list if multiple matches (rare for unique RC but possible)
                if isinstance(de, dict):
                     usage = de.get('luso', "")
                     surface = de.get('sfc', 0)
                
                # Check for address in 'ldt' (Localización Descriptiva Texto)
                # It's usually a string directly in 'bi' -> 'ldt'
                
                return {
                    "reference": ref_catastral,
                    "address": ldt,
                    "usage": usage,
                    "surface": surface,
                    "raw": data,
                    "info_link": "https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx"
                }
            
            return {"error": "Datos no estructurados como se esperaba", "raw": data}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_reference_value_url(ref_catastral: str, nif: str = None) -> str:
        """
        Devuelve la URL directa para consultar el Valor de Referencia.
        Actualmente la consulta automatizada requiere certificado digital (Client SSL),
        por lo que proporcionamos el enlace directo a la Sede Electrónica.
        """
        # Enlace general a la consulta de valor de referencia
        base_url = "https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx"
        return base_url
