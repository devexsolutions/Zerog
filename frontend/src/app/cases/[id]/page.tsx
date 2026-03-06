'use client';

import { useState, useEffect, use } from 'react';
import { 
  ArrowLeft, Upload, CheckCircle, AlertCircle, Clock, FileText, 
  Calculator, Landmark, Download, Users, Search, Plus, MapPin, 
  Trash2, Calendar, CreditCard, ChevronRight, FileCheck, Euro
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import DashboardLayout from '@/components/DashboardLayout';
import Modal from '@/components/ui/Modal';

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

  useEffect(() => {
    if (!isEditing) {
      setDisplayValue(formatCurrency(value));
    }
  }, [value, isEditing]);

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
      className={`bg-transparent border-none focus:ring-0 p-0 w-full text-sm font-medium ${className} ${isEditing ? 'text-left' : 'text-right'}`}
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
  const [activeTab, setActiveTab] = useState<'overview' | 'assets' | 'documents' | 'distribution'>('overview');
  
  // Estados para el progreso de carga de testamentos
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [processingStatus, setProcessingStatus] = useState<{[key: string]: string}>({});
  
  const { token, logout } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // State for OCR Report Modal
  const [ocrReport, setOcrReport] = useState<{title: string, content: string} | null>(null);

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

    // Inicializar progreso para este tipo de documento
    setUploadProgress(prev => ({ ...prev, [docType]: 0 }));
    setProcessingStatus(prev => ({ ...prev, [docType]: 'Subiendo archivo...' }));

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', docType);

    try {
      // Simular progreso de subida
      const uploadInterval = setInterval(() => {
        setUploadProgress(prev => {
          const current = prev[docType] || 0;
          const newProgress = Math.min(current + 10, 90);
          return { ...prev, [docType]: newProgress };
        });
      }, 200);

      const res = await fetch(`${API_URL}/cases/${caseId}/upload-doc/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      clearInterval(uploadInterval);
      setUploadProgress(prev => ({ ...prev, [docType]: 100 }));

      if (res.ok) {
        const result = await res.json();
        
        // Mostrar mensaje de procesamiento si existe (para testamentos)
        if (result.message) {
          // Si es un testamento, mostrar progreso de procesamiento basado en la respuesta real
          if (docType === 'testamento') {
            setProcessingStatus(prev => ({ ...prev, [docType]: result.message }));
            
            // Construir mensaje detallado de resultados
            let detailMsg = "";
            let hasErrors = false;
            
            if (result.assets_created > 0) {
                detailMsg += `✅ Se han creado ${result.assets_created} bienes automáticamente.\n`;
            } else if (result.cadastral_references_found > 0) {
                detailMsg += `ℹ️ Se encontraron ${result.cadastral_references_found} referencias (ya existían o no se pudieron procesar).\n`;
            }
            
            if (result.failed_references_list && result.failed_references_list.length > 0) {
                hasErrors = true;
                detailMsg += `\n⚠️ Errores en consulta a Catastro (${result.failed_references_list.length}):\n`;
                result.failed_references_list.forEach((fail: any) => {
                    detailMsg += `- ${fail.reference}: ${fail.error}\n`;
                });
            }
            
            if (detailMsg) {
                // Usar Modal para el reporte detallado en lugar de alert
                setOcrReport({
                  title: `Resultado del Análisis (${docType})`,
                  content: detailMsg
                });
            }

            setProcessingStatus(prev => ({ 
                ...prev, 
                [docType]: hasErrors ? '⚠️ Procesado con errores' : (result.assets_created > 0 ? '✅ Bienes creados' : '✅ Procesado') 
            }));
            
            setTimeout(() => {
              setProcessingStatus(prev => ({ ...prev, [docType]: '' }));
              setUploadProgress(prev => ({ ...prev, [docType]: 0 }));
            }, 5000);
          }
        }
        
        // Recargar datos para actualizar estado y cálculos (si OCR funcionó)
        fetchData();
        toast.success("Documento subido correctamente");
      } else {
        setProcessingStatus(prev => ({ ...prev, [docType]: '❌ Error al subir documento' }));
        setUploadProgress(prev => ({ ...prev, [docType]: 0 }));
        toast.error("Error subiendo documento");
      }
    } catch (error) {
      console.error(error);
      setProcessingStatus(prev => ({ ...prev, [docType]: '❌ Error de conexión' }));
      setUploadProgress(prev => ({ ...prev, [docType]: 0 }));
      toast.error("Error de conexión");
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
            toast.success("Informe descargado correctamente");
        } else {
            toast.error("Error al descargar el informe");
        }
    } catch (e) {
        console.error(e);
        toast.error("Error de conexión");
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
            toast.success("Modelo 650 (Borrador) descargado correctamente");
        } else {
            toast.error("Error al descargar el borrador del Modelo 650");
        }
    } catch (e) {
        console.error(e);
        toast.error("Error de conexión");
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
            toast.success("Modelo 650 (XML) descargado correctamente");
        } else {
            toast.error("Error al descargar el XML del Modelo 650");
        }
    } catch (e) {
        console.error(e);
        toast.error("Error de conexión");
    }
  };

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
            toast.error(`Error: ${error.detail}`);
        }
    } catch (err) {
        console.error(err);
        toast.error("Error de conexión con el servicio de Catastro");
    } finally {
        setSearchingCatastro(false);
    }
  };

  const handleAddProperty = async () => {
      if (!catastroData) return;

      // Validación: al menos uno de los valores debe ser mayor que 0
      if (marketValue <= 0 && referenceValue <= 0) {
          toast.info("Por favor, introduce al menos un valor: Valor de Mercado o Valor de Referencia");
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
              toast.success("Inmueble añadido al inventario correctamente");
              setCatastroData(null);
              setCatastroRef('');
              setMarketValue(0);
              setReferenceValue(0);
              fetchData(); 
          } else {
              const error = await res.json();
              toast.error(`Error al añadir inmueble: ${error.detail || 'Error desconocido'}`);
          }
      } catch (e) {
          console.error(e);
          toast.error("Error de conexión al guardar el inmueble");
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
              toast.success("Bien eliminado del inventario correctamente");
              fetchData(); // Recargar la lista de assets
          } else {
              const error = await res.json();
              toast.error(`Error al eliminar bien: ${error.detail || 'Error desconocido'}`);
          }
      } catch (e) {
          console.error(e);
          toast.error("Error de conexión al eliminar el bien");
      }
  };

  const handleUpdateAsset = async (assetId: number, field: string, value: any) => {
      try {
          // Actualización optimista en UI
          setAssets(prev => prev.map(a => a.id === assetId ? { ...a, [field]: value } : a));

          const res = await fetch(`${API_URL}/cases/${caseId}/assets/${assetId}`, {
              method: 'PUT',
              headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ [field]: value })
          });

          if (!res.ok) {
              const error = await res.json();
              console.error("Error updating asset:", error);
              fetchData(); // Recargar para revertir/asegurar consistencia
          } else {
             // Si cambia el valor, recargar cálculos (breve delay para que el backend procese si fuera necesario, aunque aquí es directo)
             if (field === 'value' || field === 'reference_value') {
                 // Debounce o esperar un poco podría ser mejor, pero por ahora recargamos
                 fetchData();
             }
          }
      } catch (e) {
          console.error(e);
          fetchData();
          toast.error("Error de conexión al actualizar el bien");
      }
  };

  if (!isMounted) return null;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!caseData) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <AlertCircle size={48} className="mb-4 text-red-500" />
          <p className="text-xl font-medium">Expediente no encontrado</p>
          <Link href="/" className="mt-4 text-blue-600 hover:underline">Volver al inicio</Link>
        </div>
      </DashboardLayout>
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
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <Link href="/" className="hover:text-blue-600 transition-colors">Expedientes</Link>
              <ChevronRight size={14} />
              <span>#{caseData.id}</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900">{caseData.deceased_name || 'Sin nombre'}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                caseData.status === 'open' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {caseData.status === 'open' ? 'Abierto' : 'Cerrado'}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-6 mt-4 text-sm text-gray-500">
              <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm">
                <Calendar size={16} className="text-blue-600"/> 
                <span className="font-medium">Fallecimiento:</span> {caseData.date_of_death}
              </div>
              <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm">
                <CreditCard size={16} className="text-purple-600"/> 
                <span className="font-medium">DNI:</span> {caseData.deceased_dni}
              </div>
              {deadlineDate && (
                <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm">
                  <Clock size={16} className="text-orange-600"/> 
                  <span className="font-medium">Plazo:</span> {deadlineDate.toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <button 
              onClick={handleDownloadReport}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 text-sm font-medium transition-colors shadow-sm"
            >
              <FileText size={16} />
              Informe
            </button>
            <button 
              onClick={handleDownloadModel650}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 text-sm font-medium transition-colors shadow-sm"
            >
              <FileCheck size={16} />
              Modelo 650
            </button>
            <button 
              onClick={handleDownloadModel650XML}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors shadow-sm"
            >
              <Download size={16} />
              Exportar XML
            </button>
          </div>
        </div>

        {/* Content Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'assets', 'documents', 'distribution'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`
                  whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                {tab === 'overview' && 'Resumen General'}
                {tab === 'assets' && 'Inventario de Bienes'}
                {tab === 'documents' && 'Documentación'}
                {tab === 'distribution' && 'Reparto y Adjudicación'}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[500px]">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* KPIs */}
              <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-gray-500 text-sm font-medium">Caudal Relicto Neto</h3>
                    <div className="p-2 bg-green-50 rounded-lg">
                      <Euro size={20} className="text-green-600" />
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{formatCurrency(calculation?.net_estate || 0)}</p>
                  <div className="mt-2 text-sm text-green-600 flex items-center gap-1">
                    <ArrowLeft size={14} className="rotate-45" />
                    <span>Calculado automáticamente</span>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-gray-500 text-sm font-medium">Ajuar Doméstico (3%)</h3>
                    <div className="p-2 bg-blue-50 rounded-lg">
                      <Landmark size={20} className="text-blue-600" />
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{formatCurrency(calculation?.household_goods || 0)}</p>
                  <div className="mt-2 text-sm text-blue-600">
                    Calculado sobre activo total
                  </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-gray-500 text-sm font-medium">Base Imponible Total</h3>
                    <div className="p-2 bg-purple-50 rounded-lg">
                      <Calculator size={20} className="text-purple-600" />
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{formatCurrency(calculation?.taxable_base || 0)}</p>
                  <div className="mt-2 text-sm text-purple-600">
                    Suma total a repartir
                  </div>
                </div>
              </div>

              {/* Progress & Checklist */}
              <div className="lg:col-span-2 space-y-6">
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                    <h3 className="font-semibold text-gray-900">Estado del Trámite</h3>
                    <span className="text-sm text-gray-500">{Math.round(timeProgress)}% plazo consumido</span>
                  </div>
                  <div className="p-6">
                    <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6">
                      <div 
                        className={`h-2.5 rounded-full ${timeProgress > 80 ? 'bg-red-500' : 'bg-blue-600'}`} 
                        style={{ width: `${timeProgress}%` }}
                      ></div>
                    </div>
                    
                    <div className="space-y-4">
                      {checklist.map((item, index) => (
                        <div key={index} className="flex items-center p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors">
                          <div className={`mr-4 flex-shrink-0 ${item.status === 'completed' ? 'text-green-500' : 'text-gray-300'}`}>
                            {item.status === 'completed' ? <CheckCircle size={24} /> : <div className="w-6 h-6 rounded-full border-2 border-current"></div>}
                          </div>
                          <div className="flex-1">
                            <h4 className={`font-medium ${item.status === 'completed' ? 'text-gray-900' : 'text-gray-500'}`}>
                              {item.label}
                            </h4>
                          </div>
                          {item.file_url && (
                            <Link 
                              href={item.file_url} 
                              target="_blank"
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              Ver documento
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions / Recent Activity Placeholder */}
              <div className="space-y-6">
                <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
                  <h3 className="font-semibold text-blue-900 mb-2">Próximos pasos</h3>
                  <p className="text-sm text-blue-700 mb-4">
                    Recuerda verificar los valores de referencia de los inmuebles antes de generar el informe final.
                  </p>
                  <button 
                    onClick={() => setActiveTab('assets')}
                    className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Ir a Bienes
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ASSETS TAB */}
          {activeTab === 'assets' && (
            <div className="space-y-6">
              {/* Catastro Search */}
              <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Search size={20} className="text-gray-400" />
                  Añadir Inmueble desde Catastro
                </h3>
                <form onSubmit={handleSearchCatastro} className="flex gap-4">
                  <input
                    type="text"
                    value={catastroRef}
                    onChange={(e) => setCatastroRef(e.target.value)}
                    placeholder="Referencia Catastral (20 caracteres)"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  />
                  <button
                    type="submit"
                    disabled={searchingCatastro || !catastroRef}
                    className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                  >
                    {searchingCatastro ? 'Buscando...' : 'Buscar'}
                  </button>
                </form>

                {catastroData && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-in fade-in slide-in-from-top-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-semibold text-gray-900">{catastroData.address}</h4>
                        <p className="text-sm text-gray-500">{catastroData.usage} • {catastroData.surface} m²</p>
                      </div>
                      <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded font-medium">
                        {catastroData.reference}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Valor de Mercado (€)</label>
                        <input
                          type="number"
                          value={marketValue || ''}
                          onChange={(e) => setMarketValue(parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500"
                          placeholder="0.00"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Valor de Referencia (€)</label>
                        <input
                          type="number"
                          value={referenceValue || ''}
                          onChange={(e) => setReferenceValue(parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 bg-gray-100"
                        />
                        <p className="text-xs text-gray-400 mt-1">Obtenido automáticamente si disponible</p>
                      </div>
                    </div>
                    
                    <div className="flex justify-end gap-3">
                      <button
                        onClick={() => setCatastroData(null)}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium text-sm"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={handleAddProperty}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm flex items-center gap-2"
                      >
                        <Plus size={16} />
                        Añadir al Inventario
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Assets Table */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                  <h3 className="font-semibold text-gray-900">Inventario Actual</h3>
                  <span className="text-sm text-gray-500">{assets.length} bienes registrados</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3">Descripción</th>
                        <th className="px-6 py-3">Tipo</th>
                        <th className="px-6 py-3 text-right">Valor Mercado</th>
                        <th className="px-6 py-3 text-right">Valor Ref.</th>
                        <th className="px-6 py-3 text-center">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {assets.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                            No hay bienes registrados todavía.
                          </td>
                        </tr>
                      ) : (
                        assets.map((asset) => (
                          <tr key={asset.id} className="hover:bg-gray-50 transition-colors group">
                            <td className="px-6 py-4">
                              <div className="font-medium text-gray-900">{asset.description}</div>
                              {asset.cadastral_reference && (
                                <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                                  <MapPin size={10} /> {asset.cadastral_reference}
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <span className="capitalize px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
                                {asset.type}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="w-32 ml-auto p-1 rounded hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-200 transition-all cursor-text">
                                <CurrencyInput 
                                  value={asset.value} 
                                  onValueChange={(val) => handleUpdateAsset(asset.id, 'value', val)}
                                />
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="w-32 ml-auto p-1 rounded hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-200 transition-all cursor-text">
                                <CurrencyInput 
                                  value={asset.reference_value || 0} 
                                  onValueChange={(val) => handleUpdateAsset(asset.id, 'reference_value', val)}
                                  className="text-gray-500"
                                />
                              </div>
                            </td>
                            <td className="px-6 py-4 text-center">
                              <button
                                onClick={() => handleDeleteAsset(asset.id)}
                                className="text-gray-400 hover:text-red-600 transition-colors p-1 rounded-full hover:bg-red-50 opacity-0 group-hover:opacity-100"
                                title="Eliminar bien"
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* DOCUMENTS TAB */}
          {activeTab === 'documents' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { id: 'DNI', label: 'DNI / Cert. Defunción', icon: CreditCard, desc: 'Sube el DNI del fallecido o certificado.' },
                { id: 'testamento', label: 'Testamento / Últimas Voluntades', icon: FileText, desc: 'El sistema extraerá automáticamente los datos.' },
                { id: 'certificado_bancario', label: 'Certificados Bancarios', icon: Landmark, desc: 'Para acreditar saldos y posiciones.' },
                { id: 'escritura', label: 'Escrituras de Propiedad', icon: MapPin, desc: 'Títulos de propiedad de inmuebles.' }
              ].map((doc) => (
                <div key={doc.id} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-blue-50 rounded-xl text-blue-600">
                      <doc.icon size={24} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{doc.label}</h3>
                      <p className="text-sm text-gray-500 mb-4">{doc.desc}</p>
                      
                      <div className="mt-2">
                        <label className="relative inline-flex items-center justify-center w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-colors group">
                          <input 
                            type="file" 
                            className="hidden" 
                            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], doc.id)}
                          />
                          <div className="flex items-center gap-2 text-sm text-gray-600 group-hover:text-blue-600 font-medium">
                            <Upload size={16} />
                            <span>Seleccionar archivo</span>
                          </div>
                        </label>
                      </div>

                      {(uploadProgress[doc.id] > 0 || processingStatus[doc.id]) && (
                        <div className="mt-4 space-y-2">
                          {uploadProgress[doc.id] > 0 && uploadProgress[doc.id] < 100 && (
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div className="bg-blue-600 h-1.5 rounded-full transition-all duration-300" style={{ width: `${uploadProgress[doc.id]}%` }}></div>
                            </div>
                          )}
                          {processingStatus[doc.id] && (
                            <p className="text-xs font-medium text-blue-600 flex items-center gap-1 animate-pulse">
                              {processingStatus[doc.id]}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* DISTRIBUTION TAB */}
          {activeTab === 'distribution' && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="font-semibold text-gray-900">Cuadro de Reparto</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3">Heredero</th>
                      <th className="px-6 py-3">Parentesco</th>
                      <th className="px-6 py-3 text-right">Cuota (%)</th>
                      <th className="px-6 py-3 text-right">Base Imponible</th>
                      <th className="px-6 py-3 text-right">A Pagar</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {!distribution?.heirs_distribution?.length ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                          No hay datos de reparto disponibles. Asegúrate de añadir herederos y bienes.
                        </td>
                      </tr>
                    ) : (
                      distribution.heirs_distribution.map((heir) => (
                        <tr key={heir.heir_id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 font-medium text-gray-900">{heir.name}</td>
                          <td className="px-6 py-4 text-gray-500 capitalize">{heir.relationship}</td>
                          <td className="px-6 py-4 text-right font-medium">{heir.share_percentage}%</td>
                          <td className="px-6 py-4 text-right text-gray-900">{formatCurrency(heir.tax_base)}</td>
                          <td className="px-6 py-4 text-right font-bold text-blue-600">{formatCurrency(heir.total_to_pay)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                  {distribution && distribution.heirs_distribution && distribution.heirs_distribution.length > 0 && (
                    <tfoot className="bg-gray-50 font-semibold text-gray-900 border-t border-gray-200">
                      <tr>
                        <td colSpan={3} className="px-6 py-4 text-right">TOTALES</td>
                        <td className="px-6 py-4 text-right">
                          {formatCurrency(distribution.heirs_distribution.reduce((acc, h) => acc + h.tax_base, 0))}
                        </td>
                        <td className="px-6 py-4 text-right text-blue-700">
                          {formatCurrency(distribution.heirs_distribution.reduce((acc, h) => acc + h.total_to_pay, 0))}
                        </td>
                      </tr>
                    </tfoot>
                  )}
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* OCR Report Modal */}
      <Modal
        isOpen={!!ocrReport}
        onClose={() => setOcrReport(null)}
        title={ocrReport?.title || ''}
        footer={
          <button 
            onClick={() => setOcrReport(null)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Cerrar
          </button>
        }
      >
        <div className="whitespace-pre-wrap text-sm text-gray-700 font-mono bg-gray-50 p-4 rounded-lg border border-gray-100">
          {ocrReport?.content}
        </div>
      </Modal>

    </DashboardLayout>
  );
}
