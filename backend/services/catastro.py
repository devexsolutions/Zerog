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
            # Construct SOAP URL directly for property data
            url = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"
            params = {
                "Provincia": "",
                "Municipio": "",
                "RC": ref_catastral
            }
            
            print(f"Consultando Catastro: {url} con RC={ref_catastral}")
            response = requests.get(url, params=params, timeout=10) # Added timeout
            response.raise_for_status()
            
            # Parse XML response
            try:
                data = xmltodict.parse(response.content)
            except Exception as e:
                print(f"Error parseando XML de Catastro: {e}")
                return {"error": "Invalid XML from Catastro"}

            # Debug response structure
            # print(f"Catastro Response Keys: {data.keys()}")
            
            # Check for errors in Catastro response
            # Root usually 'consulta_dnprc' for this endpoint
            root = data.get('consulta_dnprc')
            
            if not root:
                 # Try fallback to 'consulta_dnp' just in case
                 root = data.get('consulta_dnp')
            
            if not root:
                 print(f"Estructura XML desconocida para {ref_catastral}")
                 return None 

            # Check for errors reported by Catastro (lerr)
            if 'lerr' in root and root['lerr']:
                 err_info = root['lerr'].get('err')
                 if err_info:
                    print(f"Error Catastro para {ref_catastral}: {err_info}")
                    return None

            # Extract relevant info
            # Structure usually: root -> bico -> bi -> (dt, ldt, debi)
            # bico can be a list or dict
            bico = root.get('bico')
            if not bico:
                return None

            bi = bico.get('bi')
            if not bi:
                return None
                
            # If multiple results, take first
            if isinstance(bi, list):
                bi = bi[0]

            ldt = bi.get('ldt', "Dirección no disponible") # Dirección completa
            
            # Datos económicos/uso usually in 'debi' (Datos Económicos Bien Inmueble)
            # Fallback to 'de' just in case
            de = bi.get('debi') or bi.get('de', {})
            
            # Extract usage and surface
            usage = "Desconocido"
            surface = 0
            
            if isinstance(de, dict):
                    usage = de.get('luso', "Desconocido")
                    try:
                        surface = float(de.get('sfc', 0))
                    except:
                        surface = 0
            
            return {
                "reference": ref_catastral,
                "address": ldt,
                "usage": usage,
                "surface": surface,
                "info_link": "https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error de red consultando Catastro: {e}")
            return {"error": "Error de conexión con Catastro"}
        except Exception as e:
            print(f"Excepción consultando Catastro: {e}")
            return {"error": str(e)}

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