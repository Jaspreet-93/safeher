import React, { useState, useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { AppHeader } from './components/layout/AppHeader';
import { EmergencyFooter } from './components/layout/EmergencyFooter';
import { HomePage } from './pages/HomePage';
import { AuthPage } from './pages/AuthPage';
import { ProfilePage } from './pages/ProfilePage';
import { EmergencyAckPage } from './pages/EmergencyAckPage';
import { ContactVerifyPage } from './pages/ContactVerifyPage';
import { SafePlacesPage } from './features/places/SafePlacesPage';

export const MainContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'auth' | 'profile' | 'ack' | 'verify' | 'places'>('home');
  const [routeToken, setRouteToken] = useState<string>('');

  useEffect(() => {
    const path = window.location.pathname;
    if (path.startsWith('/emergency/ack/')) {
      const token = path.replace('/emergency/ack/', '');
      if (token) {
        setRouteToken(token);
        setCurrentView('ack');
      }
    } else if (path.startsWith('/contact/verify/')) {
      const token = path.replace('/contact/verify/', '');
      if (token) {
        setRouteToken(token);
        setCurrentView('verify');
      }
    }
  }, []);

  const handleNavigateHome = () => {
    window.history.pushState({}, '', '/');
    setCurrentView('home');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <AppHeader
        environment="development"
        isMock={true}
        currentView={currentView === 'ack' || currentView === 'verify' ? 'home' : currentView as 'home' | 'auth' | 'profile' | 'places'}
        onNavigate={(view) => {
          window.history.pushState({}, '', '/');
          setCurrentView(view);
        }}
      />
      <div className="flex-1 flex flex-col">
        {currentView === 'home' && <HomePage />}
        {currentView === 'auth' && <AuthPage onSuccess={() => setCurrentView('home')} />}
        {currentView === 'profile' && <ProfilePage />}
        {currentView === 'places' && <SafePlacesPage />}
        {currentView === 'ack' && (
          <EmergencyAckPage token={routeToken} onBack={handleNavigateHome} />
        )}
        {currentView === 'verify' && (
          <ContactVerifyPage token={routeToken} onBack={handleNavigateHome} />
        )}
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
