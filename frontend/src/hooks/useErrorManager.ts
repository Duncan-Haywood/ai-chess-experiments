import { useState, useCallback } from 'react';
import { ErrorItem } from '../components/ErrorDisplay';

interface UseErrorManagerResult {
  errors: ErrorItem[];
  addError: (message: string, severity?: ErrorItem['severity']) => void;
  dismissError: (id: string) => void;
  dismissAll: () => void;
}

export const useErrorManager = (maxErrors: number = 50): UseErrorManagerResult => {
  const [errors, setErrors] = useState<ErrorItem[]>([]);

  const addError = useCallback((
    message: string,
    severity: ErrorItem['severity'] = 'error'
  ) => {
    const newError: ErrorItem = {
      id: `${Date.now()}-${Math.random()}`,
      message,
      severity,
      timestamp: new Date(),
    };

    setErrors(currentErrors => {
      // Check if we have a similar recent error
      const similarError = currentErrors.find(err => 
        err.message === message &&
        err.severity === severity &&
        (Date.now() - err.timestamp.getTime()) < 5000 // Within last 5 seconds
      );

      if (similarError) {
        // Update the timestamp of the existing error instead of adding a new one
        return currentErrors.map(err =>
          err.id === similarError.id
            ? { ...err, timestamp: new Date() }
            : err
        );
      }

      // Add new error and limit total number
      const newErrors = [newError, ...currentErrors].slice(0, maxErrors);
      
      // Sort by severity and timestamp
      return newErrors.sort((a, b) => {
        const severityOrder = {
          critical: 0,
          error: 1,
          warning: 2,
          info: 3
        };
        
        const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
        if (severityDiff !== 0) return severityDiff;
        
        return b.timestamp.getTime() - a.timestamp.getTime();
      });
    });
  }, [maxErrors]);

  const dismissError = useCallback((id: string) => {
    setErrors(currentErrors => currentErrors.filter(err => err.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setErrors([]);
  }, []);

  return {
    errors,
    addError,
    dismissError,
    dismissAll
  };
}; 