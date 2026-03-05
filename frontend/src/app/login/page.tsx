'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Mail, Lock, Eye, EyeOff, Scale } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/token`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error('Credenciales inválidas');
      }

      const data = await res.json();
      
      // Obtener datos del usuario
      const userRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      
      const userData = await userRes.json();
      
      login(data.access_token, userData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex w-full">
      {/* Left Side - Hero Section */}
      <div className="hidden lg:flex w-1/2 bg-[#1e293b] text-white flex-col justify-between p-12 relative overflow-hidden">
        {/* Background Overlay/Image placeholder */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#1e293b] to-[#0f172a] z-0"></div>
        {/* You could add a background image here with opacity */}
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 text-2xl font-semibold">
            <div className="bg-white/10 p-2 rounded-lg backdrop-blur-sm">
               <Scale className="w-6 h-6 text-white" />
            </div>
            <span>Inheritance Platform</span>
          </div>
        </div>

        <div className="relative z-10 max-w-lg">
          <h1 className="text-5xl font-bold leading-tight mb-6">
            Protegiendo su legado para las próximas generaciones.
          </h1>
          <p className="text-gray-300 text-lg mb-8">
            Acceda a su panel de gestión de herencias con la seguridad y confianza que su patrimonio merece.
          </p>
          
          <div className="flex items-center gap-4">
            <div className="flex -space-x-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="w-10 h-10 rounded-full bg-gray-400 border-2 border-[#1e293b]"></div>
              ))}
            </div>
            <span className="text-sm text-gray-400">Más de 10,000 familias confían en nosotros.</span>
          </div>
        </div>

        <div className="relative z-10 text-sm text-gray-500">
            {/* Footer space placeholder */}
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 bg-white flex items-center justify-center p-8">
        <div className="max-w-md w-full">
          <div className="mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Bienvenido de nuevo</h2>
            <p className="text-gray-500">Ingrese sus credenciales para acceder a su cuenta segura.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Correo Electrónico</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900"
                  placeholder="ejemplo@correo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Contraseña</label>
                <a href="#" className="text-sm font-medium text-gray-900 hover:text-blue-600">
                  ¿Olvidó su contraseña?
                </a>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  className="block w-full pl-10 pr-10 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-600">
                Recordar mi sesión
              </label>
            </div>

            {error && (
              <div className="bg-red-50 text-red-500 text-sm p-3 rounded-lg text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-[#1e293b] hover:bg-[#0f172a] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </button>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">O continúe con</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button className="flex items-center justify-center px-4 py-2 border border-gray-200 rounded-full shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                <span className="mr-2 font-bold text-lg">G</span> Google
              </button>
              <button className="flex items-center justify-center px-4 py-2 border border-gray-200 rounded-full shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                <span className="mr-2 font-bold text-lg text-blue-600">f</span> Facebook
              </button>
            </div>
          </div>

          <p className="mt-8 text-center text-sm text-gray-600">
            ¿Aún no tiene una cuenta?{' '}
            <Link href="/register" className="font-semibold text-[#1e293b] hover:text-black">
              Regístrese aquí
            </Link>
          </p>
          
          <div className="mt-12 text-center text-xs text-gray-400">
            <p>© 2024 Inheritance Platform. Todos los derechos reservados.</p>
            <div className="mt-2 space-x-4">
              <a href="#" className="hover:text-gray-600">Privacidad</a>
              <a href="#" className="hover:text-gray-600">Términos</a>
              <a href="#" className="hover:text-gray-600">Soporte</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
