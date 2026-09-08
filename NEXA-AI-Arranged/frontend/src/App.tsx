import React from 'react';
import { MainDashboard } from './components/MainDashboard';

export const App: React.FC = () => {
  return (
    <div className="w-screen h-screen overflow-hidden bg-[#0A0E1A] text-gray-100 font-sans select-none">
      <MainDashboard />
    </div>
  );
};

export default App;
