'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  FolderOpen, 
  Calendar, 
  FileText, 
  Settings, 
  LogOut, 
  Scale, 
  Search,
  Bell,
  User as UserIcon,
  X
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user, token } = useAuth();
  const toast = useToast();
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCaseUserId, setNewCaseUserId] = useState('');
  const [creatingCase, setCreatingCase] = useState(false);

  // If we are on login or register page, don't show the dashboard layout
  if (pathname === '/login' || pathname === '/register') {
    return <>{children}</>;
  }

  const menuItems = [
    { name: 'Inicio', icon: LayoutDashboard, href: '/' },
    { name: 'Expedientes', icon: FolderOpen, href: '/cases' },
    { name: 'Calendario', icon: Calendar, href: '/calendar' },
    { name: 'Documentos', icon: FileText, href: '/documents' },
  ];

  const handleCreateCase = async () => {
    if (!newCaseUserId) return;
    setCreatingCase(true);
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
        const newCase = await res.json();
        setNewCaseUserId('');
        setIsModalOpen(false);
        toast.success('Expediente creado correctamente');
        // Navigate to the new case detail page
        router.push(`/cases/${newCase.id}`);
      } else {
        toast.error('Error al crear el expediente');
      }
    } catch (error) {
      console.error(error);
      toast.error('Error de conexión');
    } finally {
      setCreatingCase(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full z-10">
        <div className="p-6 flex items-center gap-3 border-b border-gray-100">
          <div className="bg-[#1e293b] p-2 rounded-lg">
            <Scale className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 leading-none">Gestión Herencias</h1>
            <span className="text-xs text-gray-500">Panel Profesional</span>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1">
          {menuItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-gray-100 text-[#1e293b]'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <item.icon className={`w-5 h-5 mr-3 ${isActive ? 'text-[#1e293b]' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <Link
            href="/settings"
            className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors mb-1 ${
              pathname === '/settings'
                ? 'bg-gray-100 text-[#1e293b]'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Settings className="w-5 h-5 mr-3 text-gray-400" />
            Configuración
          </Link>
          <button
            onClick={logout}
            className="flex w-full items-center px-4 py-3 text-sm font-medium text-red-600 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main Content Wrapper */}
      <div className="flex-1 ml-64 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex-1 max-w-2xl">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg leading-5 bg-gray-50 placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
                placeholder="Buscar expediente, DNI o cliente..."
              />
            </div>
          </div>

          <div className="flex items-center gap-6 ml-4">
            <button 
              onClick={() => setIsModalOpen(true)}
              className="text-white bg-[#1e293b] hover:bg-[#0f172a] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <span className="text-lg leading-none">+</span> Nuevo Expediente
            </button>
            
            <div className="h-8 w-px bg-gray-200"></div>

            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user?.email || 'Usuario'}</p>
                <p className="text-xs text-gray-500">Abogado Senior</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-gray-200 overflow-hidden border border-gray-200 flex items-center justify-center text-gray-400">
                  <UserIcon className="w-6 h-6" />
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-8">
          {children}
        </main>
      </div>

      {/* Global New Case Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900">Nuevo Expediente</h3>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
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
                  autoFocus
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg font-medium transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreateCase}
                  disabled={!newCaseUserId || creatingCase}
                  className="px-4 py-2 bg-[#1e293b] text-white rounded-lg hover:bg-[#0f172a] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {creatingCase ? 'Creando...' : 'Crear Expediente'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
