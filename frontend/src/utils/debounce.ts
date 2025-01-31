export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
    let timeout: NodeJS.Timeout;
    let lastCall: { args: Parameters<T>; resolve: (value: ReturnType<T>) => void; reject: (reason?: any) => void; } | null = null;

    return (...args: Parameters<T>) => {
        return new Promise<ReturnType<T>>((resolve, reject) => {
            if (timeout) {
                clearTimeout(timeout);
                if (lastCall) {
                    lastCall.reject(new Error('Cancelled by newer call'));
                }
            }

            lastCall = { args, resolve, reject };

            timeout = setTimeout(async () => {
                try {
                    const result = await func(...args);
                    if (lastCall) {
                        lastCall.resolve(result);
                        lastCall = null;
                    }
                } catch (error) {
                    if (lastCall) {
                        lastCall.reject(error);
                        lastCall = null;
                    }
                }
            }, wait);
        });
    };
} 