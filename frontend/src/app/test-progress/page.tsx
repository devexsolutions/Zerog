// Componente de prueba para la barra de progreso
import React, { useState } from 'react';

const TestProgressBar = () => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');

  const simulateUpload = () => {
    setProgress(0);
    setStatus('Subiendo archivo...');
    
    // Simular progreso
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 10;
        if (newProgress >= 90) {
          clearInterval(interval);
          setProgress(100);
          setStatus('Procesando referencias catastrales...');
          
          setTimeout(() => {
            setStatus('Creando bienes en inventario...');
            
            setTimeout(() => {
              setStatus('✅ Procesamiento completado');
              
              setTimeout(() => {
                setProgress(0);
                setStatus('');
              }, 2000);
            }, 1500);
          }, 1000);
        }
        return newProgress;
      });
    }, 200);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-200 max-w-md mx-auto mt-8">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Prueba de Barra de Progreso</h3>
      
      {progress > 0 ? (
        <div className="space-y-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="text-xs text-gray-600 block text-center">
            {status}
          </span>
        </div>
      ) : (
        <button 
          onClick={simulateUpload}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          Simular Carga de Testamento
        </button>
      )}
    </div>
  );
};

export default TestProgressBar;