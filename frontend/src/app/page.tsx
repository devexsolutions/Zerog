'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, FolderOpen, FileText, User, AlertTriangle, CheckCircle, Clock, Search, LogOut, MoreVertical, ArrowRight } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import DashboardLayout from '@/components/DashboardLayout';

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
  
  const { token, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
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
      setFilteredCases(data);
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
  const completed = cases.filter(c => c.status === 'CERRADO').length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Expedientes Activos</h3>
              <div className="bg-blue-50 p-2 rounded-lg">
                <FolderOpen className="text-blue-600 w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-gray-900">{totalActive}</p>
              <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">+12%</span>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">En Trámite</h3>
              <div className="bg-yellow-50 p-2 rounded-lg">
                <Clock className="text-yellow-600 w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-gray-900">{pendingValidation}</p>
              <span className="text-xs font-medium text-gray-500">Igual que ayer</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Finalizados</h3>
              <div className="bg-green-50 p-2 rounded-lg">
                <CheckCircle className="text-green-600 w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-gray-900">{completed}</p>
              <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">+4%</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Riesgo de Plazo</h3>
              <div className="bg-red-50 p-2 rounded-lg">
                <AlertTriangle className="text-red-600 w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-gray-900">{casesAtRisk}</p>
              <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">Atención</span>
            </div>
          </div>
        </div>

        {/* Recent Cases Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
                <button 
                    onClick={() => setFilterStatus('ALL')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterStatus === 'ALL' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}
                >
                    Todos
                </button>
                <button 
                    onClick={() => setFilterStatus('OPEN')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterStatus === 'OPEN' ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}
                >
                    Abiertos
                </button>
                <button 
                    onClick={() => setFilterStatus('RISK')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterStatus === 'RISK' ? 'bg-red-50 text-red-700' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}
                >
                    En Riesgo
                </button>
                <button 
                    onClick={() => setFilterStatus('CLOSED')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterStatus === 'CLOSED' ? 'bg-green-50 text-green-700' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}
                >
                    Cerrados
                </button>
            </div>
            
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                    type="text" 
                    placeholder="Buscar por DNI o ID..." 
                    className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full md:w-64"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID Expediente</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Cliente / Causante</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Fecha Fallecimiento</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Progreso</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredCases.length === 0 ? (
                    <tr>
                        <td colSpan={6} className="p-8 text-center text-gray-500">
                            No se encontraron expedientes.
                        </td>
                    </tr>
                ) : (
                  filteredCases.map((caseItem) => {
                    const { daysRemaining, status, progress } = calculateDeadlineInfo(caseItem.date_of_death);
                    
                    return (
                      <tr key={caseItem.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="bg-blue-50 p-2 rounded-lg">
                              <FileText className="w-4 h-4 text-blue-600" />
                            </div>
                            <span className="font-medium text-gray-900">#{caseItem.id}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-900">{caseItem.user_id}</span>
                            <span className="text-xs text-gray-500">DNI: {caseItem.user_id}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {caseItem.date_of_death ? new Date(caseItem.date_of_death).toLocaleDateString() : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            caseItem.status === 'ABIERTO' ? 'bg-green-100 text-green-800' :
                            caseItem.status === 'CERRADO' ? 'bg-gray-100 text-gray-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {caseItem.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-full max-w-xs">
                            <div className="flex justify-between text-xs mb-1">
                              <span className={`font-medium ${
                                status === 'critical' ? 'text-red-600' :
                                status === 'warning' ? 'text-yellow-600' :
                                'text-blue-600'
                              }`}>{Math.round(progress)}%</span>
                              <span className="text-gray-400">{daysRemaining ? `${daysRemaining} días` : '-'}</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-1.5">
                              <div 
                                className={`h-1.5 rounded-full ${
                                  status === 'critical' ? 'bg-red-500' :
                                  status === 'warning' ? 'bg-yellow-500' :
                                  'bg-blue-500'
                                }`} 
                                style={{ width: `${progress}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link href={`/cases/${caseItem.id}`} className="text-gray-400 hover:text-gray-600">
                            <MoreVertical className="w-5 h-5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal for new case */}
        <dialog id="new-case-modal" className="modal p-0 rounded-xl shadow-xl backdrop:bg-black/50">
          <div className="bg-white rounded-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900">Nuevo Expediente</h3>
              <form method="dialog">
                <button className="text-gray-400 hover:text-gray-600">
                  <span className="sr-only">Close</span>
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </form>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">DNI del Cliente / Causante</label>
                <input
                  type="text"
                  placeholder="12345678A"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  value={newCaseUserId}
                  onChange={(e) => setNewCaseUserId(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <form method="dialog">
                  <button className="px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg font-medium transition-colors">Cancelar</button>
                </form>
                <button
                  onClick={createCase}
                  className="px-4 py-2 bg-[#1e293b] text-white rounded-lg hover:bg-[#0f172a] font-medium transition-colors"
                >
                  Crear Expediente
                </button>
              </div>
            </div>
          </div>
        </dialog>
      </div>
    </DashboardLayout>
  );
}
