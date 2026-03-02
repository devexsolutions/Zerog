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
            # Note: Depending on the endpoint version, the root might be 'consulta_dnp' or 'consulta_dnprc'
            root = data.get('consulta_dnp') or data.get('consulta_dnprc')
            
            if not root:
                 return {"error": "Respuesta inesperada de Catastro", "raw": data}

            if 'lerr' in root:
                 # Check if lerr has err inside
                 err_info = root['lerr'].get('err', {})
                 # If err is a list or dict, convert to string safely
                 return {
                    "error": f"Error Catastro: {err_info}",
                    "raw": data
                }

            # Extract relevant info
            # Structure usually: root -> bico -> bi -> (dt, ldt, debi)
            if 'bico' in root and 'bi' in root['bico']:
                bi = root['bico']['bi']
                ldt = bi.get('ldt', "") # Dirección completa
                
                # Datos económicos/uso usually in 'debi' (Datos Económicos Bien Inmueble)
                # Fallback to 'de' just in case
                de = bi.get('debi') or bi.get('de', {})
                
                # Extract usage and surface
                usage = ""
                surface = 0
                
                if isinstance(de, dict):
                     usage = de.get('luso', "")
                     surface = de.get('sfc', 0)
                
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
