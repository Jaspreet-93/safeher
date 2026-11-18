import React, { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { AppHeader } from './components/layout/AppHeader';
import { EmergencyFooter } from './components/layout/EmergencyFooter';
import { HomePage } from './pages/HomePage';
import { AuthPage } from './pages/AuthPage';
import { ProfilePage } from './pages/ProfilePage';

export const MainContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'auth' | 'profile'>('home');

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <AppHeader
        environment="development"
        isMock={true}
        currentView={currentView}
        onNavigate={setCurrentView}
      />
      <div className="flex-1 flex flex-col">
        {currentView === 'home' && <HomePage />}
        {currentView === 'auth' && <AuthPage onSuccess={() => setCurrentView('home')} />}
        {currentView === 'profile' && <ProfilePage />}
      </div>
      <EmergencyFooter />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
};

export default App;
