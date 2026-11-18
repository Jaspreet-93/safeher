import React from 'react';
import { AppHeader } from './components/layout/AppHeader';
import { EmergencyFooter } from './components/layout/EmergencyFooter';
import { HomePage } from './pages/HomePage';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <AppHeader environment="development" isMock={true} />
      <HomePage />
      <EmergencyFooter />
    </div>
  );
};

export default App;
