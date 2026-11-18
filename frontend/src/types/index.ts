export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  timestamp: string;
  version: string;
  integrations: Record<string, string>;
  emergency_fallback_number: string;
}

export interface User {
  id: string;
  email: string;
  phone_number?: string;
  role: 'user' | 'org_admin' | 'coordinator' | 'admin';
}
