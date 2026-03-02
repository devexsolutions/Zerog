'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, FolderOpen, FileText, User, AlertTriangle, CheckCircle, Clock, Search, LogOut } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import Logo from '@/components/Logo';

interface Case {
  id: number;
  user_id: string;
  status: string;
  deadline: string | null;
  created_at: string;
  date_of_death: string | null;
}

export default function Home() {
  const [cases, setCases] = useState<Case[]>([]);
  const [filteredCases, setFilteredCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const [newCaseUserId, setNewCaseUserId] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL'); // ALL, OPEN, CLOSED, RISK
  const [searchTerm, setSearchTerm] = useState('');
  
  const { token, logout, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Debug info
    console.log('Current API URL:', process.env.NEXT_PUBLIC_API_URL);
    
    setIsMounted(true);
    if (!token && !localStorage.getItem('token')) {
        router.push('/login');
    } else if (token) {
        fetchCases();
    }
  }, [token]);

  useEffect(() => {
    if (cases.length > 0) {
        filterCases();
    }
  }, [cases, filterStatus, searchTerm]);

  const fetchCases = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/cases/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
      });
      if (res.status === 401) {
        logout();
        return;
      }
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setCases(data);
      setFilteredCases(data); // Init filtered
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateDeadlineInfo = (dateOfDeath: string | null) => {
    if (!dateOfDeath) return { daysRemaining: null, status: 'unknown', progress: 0 };
    
    const deathDate = new Date(dateOfDeath);
    const deadlineDate = new Date(deathDate);
    deadlineDate.setMonth(deadlineDate.getMonth() + 6);
    
    const now = new Date();
    const totalDuration = deadlineDate.getTime() - deathDate.getTime();
    const elapsed = now.getTime() - deathDate.getTime();
    const remaining = deadlineDate.getTime() - now.getTime();
    
    const daysRemaining = Math.ceil(remaining / (1000 * 60 * 60 * 24));
    const progress = Math.min(100, Math.max(0, (elapsed / totalDuration) * 100));
    
    let status = 'normal';
    if (daysRemaining < 30) status = 'critical';
    else if (daysRemaining < 90) status = 'warning';
    
    return { daysRemaining, status, progress, deadlineDate };
  };

  const filterCases = () => {
    let result = cases;

    // Filter by Status Tab
    if (filterStatus === 'OPEN') {
      result = result.filter(c => c.status !== 'CERRADO');
    } else if (filterStatus === 'CLOSED') {
      result = result.filter(c => c.status === 'CERRADO');
    } else if (filterStatus === 'RISK') {
      result = result.filter(c => {
        const { status } = calculateDeadlineInfo(c.date_of_death);
        return status === 'critical' || status === 'warning';
      });
    }

    // Filter by Search
    if (searchTerm) {
      result = result.filter(c => 
        c.user_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
        c.id.toString().includes(searchTerm)
      );
    }

    setFilteredCases(result);
  };

  const createCase = async () => {
    if (!newCaseUserId) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/cases/`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ user_id: newCaseUserId, status: 'ABIERTO' }),
      });
      if (res.ok) {
        setNewCaseUserId('');
        fetchCases();
        (document.getElementById('new-case-modal') as HTMLDialogElement)?.close();
      }
    } catch (error) {
      console.error(error);
    }
  };

  if (!isMounted) return null;

  // KPIs Calculation
  const totalActive = cases.filter(c => c.status !== 'CERRADO').length;
  const casesAtRisk = cases.filter(c => {
    const { status } = calculateDeadlineInfo(c.date_of_death);
    return (status === 'critical' || status === 'warning') && c.status !== 'CERRADO';
  }).length;
  const pendingValidation = cases.filter(c => c.status === 'PENDIENTE').length;

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans" suppressHydrationWarning>
      <header className="mb-8 flex justify-between items-center" suppressHydrationWarning>
        <div className="flex items-center gap-4">
          <Logo className="w-10 h-10" showText={false} />
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Panel Profesional</h1>
            <p className="text-gray-500 mt-1">Gestión centralizada de expedientes de herencia.</p>
          </div>
        </div>
        <div className="flex gap-2">
            <button
            onClick={() => (document.getElementById('new-case-modal') as HTMLDialogElement)?.showModal()}
            className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition shadow-sm font-medium"
            >
            <Plus size={20} /> Nuevo Expediente
            </button>
            <button
            onClick={logout}
            className="flex items-center gap-2 bg-white text-gray-700 px-5 py-2.5 rounded-lg hover:bg-gray-50 transition shadow-sm border border-gray-200"
            >
            <LogOut size={20} /> Salir
            </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500">Expedientes Activos</h3>
            <FolderOpen className="text-blue-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{totalActive}</p>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500">En Riesgo (Plazo)</h3>
            <AlertTriangle className="text-red-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-red-600">{casesAtRisk}</p>
          <p className="text-xs text-red-400 mt-1">Vencen en &lt; 3 meses</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500">Pendientes Validación</h3>
            <Clock className="text-yellow-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-yellow-600">{pendingValidation}</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500">Total Histórico</h3>
            <FileText className="text-gray-400" size={20} />
          </div>
          <p className="text-3xl font-bold text-gray-700">{cases.length}</p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Filters & Search */}
        <div className="px-6 py-4 border-b border-gray-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex gap-2">
            <button 
              onClick={() => setFilterStatus('ALL')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filterStatus === 'ALL' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:bg-gray-50'}`}
            >
              Todos
            </button>
            <button 
              onClick={() => setFilterStatus('OPEN')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filterStatus === 'OPEN' ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:bg-gray-50'}`}
            >
              Activos
            </button>
            <button 
              onClick={() => setFilterStatus('RISK')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filterStatus === 'RISK' ? 'bg-red-50 text-red-700' : 'text-gray-500 hover:bg-gray-50'}`}
            >
              En Riesgo
            </button>
            <button 
              onClick={() => setFilterStatus('CLOSED')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filterStatus === 'CLOSED' ? 'bg-green-50 text-green-700' : 'text-gray-500 hover:bg-gray-50'}`}
            >
              Cerrados
            </button>
          </div>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Buscar por cliente o ID..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-64"
            />
          </div>
        </div>
        
        {/* Table */}
        {loading ? (
          <div className="p-12 text-center text-gray-500">Cargando expedientes...</div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-gray-500">No se encontraron expedientes con los filtros actuales.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expediente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">Plazo Impuesto (6 meses)</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCases.map((c) => {
                  const { daysRemaining, status, progress, deadlineDate } = calculateDeadlineInfo(c.date_of_death);
                  
                  return (
                    <tr key={c.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{c.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <div className="bg-gray-100 p-1.5 rounded-full">
                            <User size={14} className="text-gray-500" />
                          </div>
                          {c.user_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-0.5 inline-flex text-xs font-medium rounded-full 
                          ${c.status === 'PENDIENTE' ? 'bg-yellow-100 text-yellow-800' : 
                            c.status === 'ABIERTO' ? 'bg-blue-100 text-blue-800' : 
                            c.status === 'CERRADO' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap align-middle">
                        {c.date_of_death ? (
                          <div className="w-full">
                            <div className="flex justify-between text-xs mb-1">
                              <span className={
                                status === 'critical' ? 'text-red-600 font-bold' : 
                                status === 'warning' ? 'text-orange-600 font-medium' : 
                                'text-gray-600'
                              }>
                                {daysRemaining && daysRemaining > 0 ? `${daysRemaining} días restantes` : 'Plazo vencido'}
                              </span>
                              <span className="text-gray-400">{deadlineDate?.toLocaleDateString()}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full transition-all duration-500 ${
                                  status === 'critical' ? 'bg-red-500' : 
                                  status === 'warning' ? 'bg-orange-500' : 
                                  'bg-green-500'
                                }`} 
                                style={{ width: `${progress}%` }}
                              ></div>
                            </div>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400 italic">Fecha defunción pendiente</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link href={`/cases/${c.id}`} className="text-blue-600 hover:text-blue-800 font-semibold">
                          Gestionar
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Nueva Creación */}
      <dialog id="new-case-modal" className="modal p-0 rounded-xl shadow-2xl backdrop:bg-black/60">
        <div className="bg-white p-8 w-[480px] rounded-xl">
            <h3 className="text-xl font-bold mb-6 text-gray-900">Crear Nuevo Expediente</h3>
            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">ID Cliente / Referencia</label>
                <input 
                    type="text" 
                    value={newCaseUserId}
                    onChange={(e) => setNewCaseUserId(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                    placeholder="Ej. Familia García - REF001"
                    autoFocus
                />
                <p className="text-xs text-gray-500 mt-2">Este ID servirá para identificar el expediente en el sistema.</p>
            </div>
            <div className="flex justify-end gap-3">
                <button 
                    onClick={() => (document.getElementById('new-case-modal') as HTMLDialogElement)?.close()}
                    className="px-5 py-2.5 text-gray-700 hover:bg-gray-100 rounded-lg font-medium transition"
                >
                    Cancelar
                </button>
                <button 
                    onClick={() => {
                        createCase();
                        (document.getElementById('new-case-modal') as HTMLDialogElement)?.close();
                    }}
                    className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm transition"
                >
                    Crear Expediente
                </button>
            </div>
        </div>
      </dialog>
    </div>
  );
}
