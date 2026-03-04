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
        
        # Corrección: Endpoint correcto para consulta por RC
        url = f"{CatastroService.BASE_URL}/Consulta_DNPRC"
        params = {
            "Provincia": "",
            "Municipio": "",
            "RC": ref_catastral
        }
        
        try:
            print(f"Consultando Catastro: {url} con RC={ref_catastral}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            data = xmltodict.parse(response.content)
            
            # Check for errors in Catastro response
            # Note: Depending on the endpoint version, the root might be 'consulta_dnp' or 'consulta_dnprc'
            root = data.get('consulta_dnp') or data.get('consulta_dnprc')
            
            if not root:
                 return None # No se pudo parsear respuesta esperada

            if 'lerr' in root:
                 # Check if lerr has err inside
                 err_info = root['lerr'].get('err', {})
                 print(f"Error Catastro para {ref_catastral}: {err_info}")
                 return None

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
                     try:
                        surface = float(de.get('sfc', 0))
                     except:
                        surface = 0
                
                return {
                    "reference": ref_catastral,
                    "address": ldt,
                    "usage": usage,
                    "surface": surface,
                    "raw": data,
                    "info_link": "https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx"
                }
            
            return None # Estructura no reconocida
            
        except Exception as e:
            print(f"Excepción consultando Catastro: {e}")
            return None

    @staticmethod
    def get_reference_value_url(ref_catastral: str, nif: str = None):
        """
        Devuelve información sobre el valor de referencia.
        Como requiere certificado, devolvemos un objeto base.
        """
        # Enlace general a la consulta de valor de referencia
        base_url = "https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx"
        
        return {
            "value": 0, # Valor por defecto ya que no podemos consultarlo sin certificado
            "url": base_url,
            "message": "Consultar valor manualmente en Sede Electrónica"
        }