'use client';

import { useState, useEffect, use } from 'react';
import { ArrowLeft, Upload, CheckCircle, AlertCircle, Clock, FileText, Calculator, Landmark, Download, Users, Search, Plus, MapPin, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

// Funciones auxiliares para formato de moneda española
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

const parseCurrency = (value: string): number => {
  // Eliminar símbolo de euro y espacios
  let cleanValue = value.replace(/[€\s]/g, '');
  
  // Si tiene punto como separador decimal (formato español)
  if (cleanValue.includes(',') && cleanValue.includes('.')) {
    // Eliminar puntos de miles y cambiar coma por punto decimal
    cleanValue = cleanValue.replace(/\./g, '').replace(',', '.');
  } else if (cleanValue.includes(',')) {
    // Solo tiene coma, es el separador decimal
    cleanValue = cleanValue.replace(',', '.');
  }
  
  return parseFloat(cleanValue) || 0;
};

const formatNumberInput = (value: string): string => {
  // Permitir solo números, puntos y comas
  const cleanValue = value.replace(/[^0-9.,]/g, '');
  
  // Si hay múltiples puntos o comas, mantener solo el último
  const parts = cleanValue.split(/[.,]/);
  if (parts.length > 2) {
    const decimalSeparator = cleanValue.includes(',') ? ',' : '.';
    return parts.slice(0, -1).join('') + decimalSeparator + parts[parts.length - 1];
  }
  
  return cleanValue;
};

// Componente de input de moneda española
const CurrencyInput = ({ 
  value, 
  onValueChange, 
  placeholder = "0,00 €",
  className = ""
}: { 
  value: number; 
  onValueChange: (value: number) => void; 
  placeholder?: string;
  className?: string;
}) => {
  const [displayValue, setDisplayValue] = useState(formatCurrency(value));
  const [isEditing, setIsEditing] = useState(false);
  const [tempValue, setTempValue] = useState("");

  const handleFocus = () => {
    setIsEditing(true);
    setTempValue(value === 0 ? "" : value.toString().replace(".", ","));
  };

  const handleBlur = () => {
    setIsEditing(false);
    const parsedValue = parseCurrency(tempValue);
    onValueChange(parsedValue);
    setDisplayValue(formatCurrency(parsedValue));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatNumberInput(e.target.value);
    setTempValue(formatted);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.currentTarget.blur();
    }
  };

  return (
    <input
      type="text"
      value={isEditing ? tempValue : displayValue}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      className={`${className} ${isEditing ? 'text-left' : 'text-right'}`}
      style={{ fontVariantNumeric: 'tabular-nums' }}
    />
  );
};

interface Case {
  id: number;
  user_id: string;
  status: string;
  deadline: string | null;
  date_of_death: string | null;
  deceased_name: string | null;
  deceased_dni: string | null;
  has_will: boolean;
}

interface ChecklistItem {
  type: string;
  label: string;
  status: string;
  file_url: string | null;
}

interface Calculation {
  total_assets: number;
  total_debts: number;
  net_estate: number;
  household_goods: number;
  taxable_base: number;
}

interface HeirDistribution {
  heir_id: number;
  name: string;
  relationship: string;
  share_percentage: number;
  quota_value: number;
  tax_base: number;
  reductions: number;
  tax_quota: number;
  total_to_pay: number;
}

interface Asset {
  id: number;
  type: string;
  value: number;
  is_ganancial: boolean;
  is_debt: boolean;
  is_funeral_expense: boolean;
  description?: string;
  cadastral_reference?: string;
  address?: string;
  surface?: number;
  usage?: string;
  reference_value?: number;
}

interface CatastroData {
  reference: string;
  address: string;
  surface: string;
  usage: string;
  construction_year?: number;
  urban?: boolean;
}

interface DistributionResult {
  estate_summary: Calculation;
  heirs_distribution: HeirDistribution[];
  total_distributed: number;
  remainder: number;
}

export default function CaseDetail({ params }: { params: Promise<{ id: string }> }) {
  // Desempaquetar params usando hook use() (Next.js 15 pattern)
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [calculation, setCalculation] = useState<Calculation | null>(null);
  const [distribution, setDistribution] = useState<DistributionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const [catastroRef, setCatastroRef] = useState('');
  const [catastroData, setCatastroData] = useState<CatastroData | null>(null);
  const [searchingCatastro, setSearchingCatastro] = useState(false);
  const [marketValue, setMarketValue] = useState(0);
  const [referenceValue, setReferenceValue] = useState(0);
  const [assets, setAssets] = useState<Asset[]>([]);
  
  const { token, logout } = useAuth();
  const router = useRouter();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    setIsMounted(true);
    if (!token && !localStorage.getItem('token')) {
        router.push('/login');
    } else if (token) {
        fetchData();
    }
  }, [caseId, token]);

  const fetchData = async () => {
    try {
      const headers = {
        'Authorization': `Bearer ${token}`
      };
      
      const [caseRes, checkRes, calcRes, distRes, assetsRes] = await Promise.all([
        fetch(`${API_URL}/cases/${caseId}`, { headers }),
        fetch(`${API_URL}/cases/${caseId}/checklist`, { headers }),
        fetch(`${API_URL}/cases/${caseId}/calculate`, { headers }),
        fetch(`${API_URL}/cases/${caseId}/distribution`, { headers }),
        fetch(`${API_URL}/cases/${caseId}/assets/`, { headers })
      ]);

      if (caseRes.status === 401 || checkRes.status === 401 || calcRes.status === 401 || assetsRes.status === 401) {
          logout();
          return;
      }

      if (caseRes.ok) setCaseData(await caseRes.json());
      if (checkRes.ok) setChecklist(await checkRes.json());
      if (calcRes.ok) setCalculation(await calcRes.json());
      if (distRes.ok) setDistribution(await distRes.json());
      if (assetsRes.ok) setAssets(await assetsRes.json());
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File, docType: string) => {
    // Si es DNI, forzar validación simulada
    if (docType === 'DNI') {
        // En un caso real, el backend valida. Aquí solo para demo visual inmediata.
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', docType);

    try {
      const res = await fetch(`${API_URL}/cases/${caseId}/upload-doc/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (res.ok) {
        const result = await res.json();
        
        // Mostrar mensaje de procesamiento si existe (para testamentos)
        if (result.message) {
          alert(result.message);
        }
        
        // Recargar datos para actualizar estado y cálculos (si OCR funcionó)
        fetchData();
      } else {
        alert("Error subiendo documento");
      }
    } catch (error) {
      console.error(error);
      alert("Error de conexión");
    }
  };

  const handleDownloadReport = async () => {
    try {
        const res = await fetch(`${API_URL}/cases/${caseId}/report`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Informe_Reparto_${caseId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            alert("Error al descargar el informe");
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
  };

  const handleDownloadModel650 = async () => {
    try {
        const res = await fetch(`${API_URL}/cases/${caseId}/model650`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Modelo650_Borrador_${caseId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            alert("Error al descargar el borrador del Modelo 650");
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
  };

  const handleDownloadModel650XML = async () => {
    try {
        const res = await fetch(`${API_URL}/cases/${caseId}/model650/xml`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Modelo650_Export_${caseId}.xml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            alert("Error al descargar el XML del Modelo 650");
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
  };

  if (!isMounted) return null;

  const handleSearchCatastro = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!catastroRef) return;
    
    setSearchingCatastro(true);
    setCatastroData(null);
    try {
        // Primero obtener los datos básicos del catastro
        const res = await fetch(`${API_URL}/integrations/catastro/${catastroRef}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            setCatastroData(data);
            
            // Intentar obtener el valor de referencia automáticamente
            try {
                const valueRes = await fetch(`${API_URL}/integrations/catastro/value/${catastroRef}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (valueRes.ok) {
                    const valueData = await valueRes.json();
                    // Si hay un valor disponible, establecerlo automáticamente
                    if (valueData.value && valueData.value > 0) {
                        setReferenceValue(valueData.value);
                    }
                }
            } catch (valueError) {
                console.warn("No se pudo obtener el valor automáticamente:", valueError);
                // No mostrar error al usuario, solo continuar sin valor automático
            }
        } else {
            const error = await res.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (err) {
        console.error(err);
        alert("Error de conexión con el servicio de Catastro");
    } finally {
        setSearchingCatastro(false);
    }
  };

  const handleAddProperty = async () => {
      if (!catastroData) return;

      // Validación: al menos uno de los valores debe ser mayor que 0
      if (marketValue <= 0 && referenceValue <= 0) {
          alert("Por favor, introduce al menos un valor: Valor de Mercado o Valor de Referencia");
          return;
      }

      try {
          const newAsset = {
              type: "inmueble", 
              value: marketValue > 0 ? marketValue : referenceValue, // Usar valor de mercado si existe, sino referencia
              description: `Inmueble Catastro: ${catastroData.address}`,
              cadastral_reference: catastroData.reference,
              address: catastroData.address,
              surface: parseFloat(catastroData.surface),
              usage: catastroData.usage,
              reference_value: referenceValue,
              is_ganancial: false, 
              is_debt: false,
              is_funeral_expense: false
          };

          const res = await fetch(`${API_URL}/cases/${caseId}/assets/`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify(newAsset)
          });

          if (res.ok) {
              alert("Inmueble añadido al inventario correctamente");
              setCatastroData(null);
              setCatastroRef('');
              setMarketValue(0);
              setReferenceValue(0);
              fetchData(); 
          } else {
              const error = await res.json();
              alert(`Error al añadir inmueble: ${error.detail || 'Error desconocido'}`);
          }
      } catch (e) {
          console.error(e);
          alert("Error de conexión al guardar el inmueble");
      }
  };

  const handleDeleteAsset = async (assetId: number) => {
      if (!confirm("¿Estás seguro de que quieres eliminar este bien del inventario?")) {
          return;
      }

      try {
          const res = await fetch(`${API_URL}/cases/${caseId}/assets/${assetId}`, {
              method: 'DELETE',
              headers: {
                  'Authorization': `Bearer ${token}`
              }
          });

          if (res.ok) {
              alert("Bien eliminado del inventario correctamente");
              fetchData(); // Recargar la lista de assets
          } else {
              const error = await res.json();
              alert(`Error al eliminar bien: ${error.detail || 'Error desconocido'}`);
          }
      } catch (e) {
          console.error(e);
          alert("Error de conexión al eliminar el bien");
      }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Cargando expediente...</p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-red-500">Expediente no encontrado.</p>
      </div>
    );
  }

  // Calcular progreso de tiempo (6 meses desde fallecimiento)
  const calculateTimeProgress = () => {
    if (!caseData.date_of_death) return 0;
    const deathDate = new Date(caseData.date_of_death);
    const deadline = new Date(deathDate);
    deadline.setMonth(deadline.getMonth() + 6);
    
    const now = new Date();
    const totalTime = deadline.getTime() - deathDate.getTime();
    const elapsedTime = now.getTime() - deathDate.getTime();
    
    // Clamp entre 0 y 100
    return Math.min(100, Math.max(0, (elapsedTime / totalTime) * 100));
  };
  
  const timeProgress = calculateTimeProgress();
  const deadlineDate = caseData.date_of_death ? new Date(new Date(caseData.date_of_death).setMonth(new Date(caseData.date_of_death).getMonth() + 6)) : null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Header */}
      <header className="mb-8">
        <Link href="/" className="inline-flex items-center text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft size={16} className="mr-1" /> Volver al listado
        </Link>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              Expediente #{caseData.id} 
              <span className="text-sm font-normal text-gray-500 bg-gray-200 px-2 py-1 rounded-full">{caseData.user_id}</span>
            </h1>
            <p className="text-gray-600 mt-1">
                {caseData.deceased_name && <span className="font-semibold block text-lg">{caseData.deceased_name} {caseData.deceased_dni && `(${caseData.deceased_dni})`}</span>}
                {caseData.has_will ? "Con Testamento" : "Intestada (Sin Testamento)"} • Fallecimiento: {caseData.date_of_death ? new Date(caseData.date_of_death).toLocaleDateString() : 'No registrada'}
            </p>
          </div>
          <div className="text-right flex flex-col items-end gap-2">
             <div className={`px-3 py-1 rounded-full text-sm font-semibold inline-block
                ${caseData.status === 'PENDIENTE' ? 'bg-yellow-100 text-yellow-800' : 
                  caseData.status === 'ABIERTO' ? 'bg-green-100 text-green-800' : 
                  'bg-gray-100 text-gray-800'}`}>
                {caseData.status}
             </div>
             {distribution && (
                 <>
                    <button 
                        onClick={handleDownloadReport}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition shadow-sm w-full justify-center"
                    >
                        <Download size={16} /> Informe Reparto
                    </button>
                    <button 
                        onClick={handleDownloadModel650}
                        className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition shadow-sm w-full justify-center"
                    >
                        <FileText size={16} /> Borrador 650
                    </button>
                    <button 
                        onClick={handleDownloadModel650XML}
                        className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 transition shadow-sm w-full justify-center"
                    >
                        <Download size={16} /> XML AEAT
                    </button>
                 </>
             )}
          </div>
        </div>
      </header>

      {/* Timeline de Plazos */}
      <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Clock size={20} className="text-blue-600" /> Plazo Impuesto Sucesiones (6 meses)
        </h3>
        {caseData.date_of_death ? (
            <div>
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Inicio: {new Date(caseData.date_of_death).toLocaleDateString()}</span>
                    <span className="font-bold text-red-600">Límite: {deadlineDate?.toLocaleDateString()}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                    <div 
                        className={`h-4 rounded-full transition-all duration-500 ${timeProgress > 80 ? 'bg-red-500' : 'bg-blue-500'}`} 
                        style={{ width: `${timeProgress}%` }}
                    ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-right">
                    {timeProgress >= 100 ? "Plazo vencido" : `Quedan ${Math.ceil((100 - timeProgress) * 1.8)} días aprox.`}
                </p>
            </div>
        ) : (
            <div className="text-yellow-600 bg-yellow-50 p-3 rounded-md text-sm">
                ⚠️ Registra la fecha de fallecimiento para activar el control de plazos.
            </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Columna Izquierda: Checklist Documental */}
        <div className="lg:col-span-2 space-y-8">
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <FileText size={20} className="text-indigo-600" /> Documentación Requerida
                    </h3>
                    <span className="text-sm text-gray-500">
                        {checklist.filter(c => c.status !== 'MISSING').length} / {checklist.length}
                    </span>
                </div>
                <div className="divide-y divide-gray-100">
                    {checklist.map((item, idx) => (
                        <div key={idx} className="p-4 flex items-center justify-between hover:bg-gray-50 transition">
                            <div className="flex items-center gap-3">
                                {item.status === 'VALIDATED' ? (
                                    <CheckCircle className="text-green-500" size={24} />
                                ) : item.status === 'UPLOADED' ? (
                                    <Clock className="text-yellow-500" size={24} />
                                ) : (
                                    <AlertCircle className="text-gray-300" size={24} />
                                )}
                                <div>
                                    <p className="font-medium text-gray-800">{item.label}</p>
                                    <p className="text-xs text-gray-500 uppercase">{item.type.replace('_', ' ')}</p>
                                </div>
                            </div>
                            <div>
                                {item.status === 'MISSING' || item.status === 'PENDING' || item.status === 'PENDIENTE' ? (
                                    <label className="flex items-center gap-1 text-sm text-blue-600 hover:bg-blue-50 px-3 py-1.5 rounded border border-blue-200 cursor-pointer">
                                        <Upload size={14} /> Subir
                                        <input 
                                            type="file" 
                                            className="hidden" 
                                            accept=".pdf,.jpg,.png"
                                            onChange={(e) => {
                                                if (e.target.files?.[0]) {
                                                    handleFileUpload(e.target.files[0], item.type);
                                                }
                                            }}
                                        />
                                    </label>
                                ) : (
                                    <span className={`text-xs font-semibold px-2 py-1 rounded 
                                        ${item.status === 'VALIDATED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                        {item.status}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Inventario de Bienes */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <Calculator size={20} className="text-gray-700" /> Inventario de Bienes
                    </h3>
                </div>
                <div className="p-6">
                    {assets.length === 0 ? (
                        <div className="text-center py-8">
                            <Calculator className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                            <h3 className="text-sm font-medium text-gray-900 mb-2">No hay bienes registrados</h3>
                            <p className="text-sm text-gray-500">Utiliza la sección de Catastro arriba para añadir inmuebles al inventario.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {assets.map((asset) => (
                                    <div key={asset.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:shadow-md transition-shadow">
                                        <div className="flex justify-between items-start mb-3">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                                                {asset.type}
                                            </span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-lg font-semibold text-gray-900">
                                                    {asset.value.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                                </span>
                                                <button
                                                    onClick={() => handleDeleteAsset(asset.id)}
                                                    className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                                                    title="Eliminar bien"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                        <h4 className="font-medium text-gray-900 mb-2">
                                            {asset.description || 'Sin descripción'}
                                        </h4>
                                        {asset.address && (
                                            <p className="text-sm text-gray-600 mb-2">
                                                <MapPin size={14} className="inline mr-1" />
                                                {asset.address}
                                            </p>
                                        )}
                                        <div className="space-y-1 text-sm">
                                            {asset.cadastral_reference && (
                                                <p className="text-gray-600">
                                                    <span className="font-medium">Referencia:</span> {asset.cadastral_reference}
                                                </p>
                                            )}
                                            {asset.surface && (
                                                <p className="text-gray-600">
                                                    <span className="font-medium">Superficie:</span> {asset.surface} m²
                                                </p>
                                            )}
                                            {asset.usage && (
                                                <p className="text-gray-600">
                                                    <span className="font-medium">Uso:</span> {asset.usage}
                                                </p>
                                            )}
                                            {asset.reference_value && asset.reference_value > 0 && (
                                                <p className="text-gray-600">
                                                    <span className="font-medium">Valor de referencia:</span> {asset.reference_value.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm font-medium text-blue-900">Total del Inventario:</span>
                                    <span className="text-lg font-bold text-blue-900">
                                        {assets.reduce((sum, asset) => sum + asset.value, 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </div>

        {/* Columna Derecha: Motor de Cálculo y Reparto */}
        <div className="space-y-8">
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-slate-50">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <Calculator size={20} className="text-emerald-600" /> Masa Hereditaria
                    </h3>
                </div>
                <div className="p-6 space-y-4">
                    {calculation && (
                        <>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-600">Activos Totales</span>
                                <span className="font-mono font-medium text-green-600">
                                    {calculation.total_assets.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-600">Deudas y Gastos</span>
                                <span className="font-mono font-medium text-red-600">
                                    - {calculation.total_debts.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                </span>
                            </div>
                            <div className="border-t border-gray-200 my-2"></div>
                            <div className="flex justify-between items-center font-bold">
                                <span className="text-gray-800">Caudal Relicto</span>
                                <span className="font-mono text-gray-900">
                                    {calculation.net_estate.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                </span>
                            </div>
                            <div className="flex justify-between items-center text-sm bg-blue-50 p-2 rounded mt-2">
                                <span className="text-blue-800 flex items-center gap-1">
                                    <Landmark size={14} /> Ajuar Doméstico (3%)
                                </span>
                                <span className="font-mono font-medium text-blue-800">
                                    + {calculation.household_goods.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                </span>
                            </div>
                            <div className="bg-gray-900 text-white p-4 rounded-lg mt-4">
                                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Base Imponible Total</div>
                                <div className="text-2xl font-mono font-bold">
                                    {calculation.taxable_base.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </section>
            
            {distribution && distribution.heirs_distribution.length > 0 && (
                <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 bg-emerald-50">
                        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                            <Users size={20} className="text-emerald-700" /> Reparto Herederos
                        </h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Heredero</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Parentesco</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">%</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">Cuota Hereditaria</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">Base Imponible</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">Impuesto (Est.)</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {distribution.heirs_distribution.map((heir) => (
                                    <tr key={heir.heir_id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{heir.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{heir.relationship}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{heir.share_percentage}%</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{heir.quota_value.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                                            {heir.tax_base.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600 text-right">
                                            {heir.total_to_pay.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}

            {/* Catastro Integration Section */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <MapPin size={20} className="text-blue-700" /> Añadir Inmueble (Catastro)
                    </h3>
                </div>
                <div className="p-6">
                    <form onSubmit={handleSearchCatastro} className="flex gap-4 items-end mb-6">
                        <div className="flex-1">
                            <label htmlFor="catastroRef" className="block text-sm font-medium text-gray-700 mb-1">
                                Referencia Catastral
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    id="catastroRef"
                                    value={catastroRef}
                                    onChange={(e) => setCatastroRef(e.target.value)}
                                    placeholder="Ej: 13077A01800039"
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={searchingCatastro || !catastroRef}
                            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {searchingCatastro ? 'Buscando...' : 'Buscar'}
                        </button>
                    </form>

                    {catastroData && (
                        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Dirección</span>
                                    <p className="text-gray-900 font-medium">{catastroData.address}</p>
                                </div>
                                <div>
                                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Uso Principal</span>
                                    <p className="text-gray-900">{catastroData.usage || 'Desconocido'}</p>
                                </div>
                                <div>
                                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Superficie</span>
                                    <p className="text-gray-900">{catastroData.surface} m²</p>
                                </div>
                                <div>
                                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Referencia</span>
                                    <p className="font-mono text-gray-800">{catastroData.reference}</p>
                                </div>
                            </div>

                            <div className="mb-4 border-t border-gray-200 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Valor de Referencia (Base Imponible)
                                    </label>
                                    <div className="flex gap-2 items-center">
                                        <CurrencyInput
                                            value={referenceValue}
                                            onValueChange={setReferenceValue}
                                            placeholder="0,00 €"
                                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                        />
                                        <a 
                                            href="https://www1.sedecatastro.gob.es/Accesos/SECAccvr.aspx" 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="p-2 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-md text-xs font-semibold whitespace-nowrap"
                                            title="Consultar en Sede Catastro"
                                        >
                                            Consultar
                                        </a>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Consultar en Sede Electrónica del Catastro
                                    </p>
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Valor de Mercado (Estimado)
                                    </label>
                                    <CurrencyInput
                                        value={marketValue}
                                        onValueChange={setMarketValue}
                                        placeholder="0,00 €"
                                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Si es mayor al de referencia, se usará este.
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <button
                                    onClick={handleAddProperty}
                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
                                >
                                    <Plus size={18} />
                                    Añadir al Inventario
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </div>
      </div>
    </div>
  );
}
