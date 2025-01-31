import { useToast as useChakraToast, UseToastOptions, ToastId } from '@chakra-ui/react';
import { useCallback, useRef } from 'react';

interface ToastState {
  [key: string]: {
    id: ToastId;
    timestamp: number;
  };
}

interface CustomToastOptions extends UseToastOptions {
  key?: string;
}

export const useToast = () => {
  const chakraToast = useChakraToast();
  const activeToasts = useRef<ToastState>({});
  const TOAST_COOLDOWN = 5000; // 5 seconds cooldown between same type of toast

  const showToast = useCallback(
    (options: CustomToastOptions) => {
      const toastKey = options.key || (options.title as string) || 'default';
      
      const now = Date.now();
      const existingToast = activeToasts.current[toastKey];

      // Check if the same type of toast was shown recently
      if (
        existingToast &&
        now - existingToast.timestamp < TOAST_COOLDOWN
      ) {
        return;
      }

      // Close previous toast of the same type if it exists
      if (existingToast) {
        chakraToast.close(existingToast.id);
      }

      // Show new toast and store its info
      const id = chakraToast({
        ...options,
        id: `${toastKey}-${now}`,
        onCloseComplete: () => {
          delete activeToasts.current[toastKey];
          options.onCloseComplete?.();
        },
      });

      activeToasts.current[toastKey] = {
        id,
        timestamp: now,
      };

      return id;
    },
    [chakraToast]
  );

  const closeAll = useCallback(() => {
    chakraToast.closeAll();
    activeToasts.current = {};
  }, [chakraToast]);

  return Object.assign(showToast, {
    close: chakraToast.close,
    closeAll,
    update: chakraToast.update,
    isActive: chakraToast.isActive,
  });
}; 