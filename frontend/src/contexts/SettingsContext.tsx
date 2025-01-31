import React, { createContext, useContext, useState, useEffect } from 'react';
import { useColorMode } from '@chakra-ui/react';

interface Settings {
  soundEnabled: boolean;
  colorMode: 'light' | 'dark' | 'system';
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (newSettings: Partial<Settings>) => void;
}

const defaultSettings: Settings = {
  soundEnabled: true,
  colorMode: 'system',
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<Settings>(() => {
    // Load settings from localStorage if available
    const savedSettings = localStorage.getItem('chessSettings');
    return savedSettings ? JSON.parse(savedSettings) : defaultSettings;
  });
  
  const { setColorMode } = useColorMode();

  // Effect to handle system color mode changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleColorSchemeChange = (e: MediaQueryListEvent) => {
      if (settings.colorMode === 'system') {
        setColorMode(e.matches ? 'dark' : 'light');
      }
    };

    // Initial setup
    if (settings.colorMode === 'system') {
      setColorMode(mediaQuery.matches ? 'dark' : 'light');
    } else {
      setColorMode(settings.colorMode);
    }

    mediaQuery.addEventListener('change', handleColorSchemeChange);
    return () => mediaQuery.removeEventListener('change', handleColorSchemeChange);
  }, [settings.colorMode, setColorMode]);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chessSettings', JSON.stringify(settings));
  }, [settings]);

  const updateSettings = (newSettings: Partial<Settings>) => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      // If color mode is being updated, apply it
      if (newSettings.colorMode) {
        if (newSettings.colorMode === 'system') {
          const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          setColorMode(isDark ? 'dark' : 'light');
        } else {
          setColorMode(newSettings.colorMode);
        }
      }
      return updated;
    });
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}; 