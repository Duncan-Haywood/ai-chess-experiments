import { test, expect } from '@playwright/test';
import { DebugHelper } from './debug-helper';

test.describe('Docker Environment', () => {
    test('services are running', async () => {
        expect(await DebugHelper.isServiceRunning('frontend')).toBe(true);
        expect(await DebugHelper.isServiceRunning('backend')).toBe(true);
    });

    test('environment variables are set correctly', async () => {
        const frontendEnv = await DebugHelper.getEnvVars('frontend');
        expect(frontendEnv.NODE_ENV).toBe('production');
        expect(frontendEnv.VITE_API_URL).toBeDefined();

        const backendEnv = await DebugHelper.getEnvVars('backend');
        expect(backendEnv.PYTHONPATH).toBeDefined();
        expect(backendEnv.STOCKFISH_PATH).toBeDefined();
    });

    test('logs are clean', async () => {
        const frontendLogs = await DebugHelper.getLogs('frontend');
        const backendLogs = await DebugHelper.getLogs('backend');

        expect(frontendLogs).not.toContain('ERROR');
        expect(backendLogs).not.toContain('ERROR');
    });

    test('memory usage is within limits', async () => {
        const frontendMemory = await DebugHelper.getMemoryUsage('frontend');
        const backendMemory = await DebugHelper.getMemoryUsage('backend');

        expect(frontendMemory).toBeLessThan(512 * 1024 * 1024); // 512MB
        expect(backendMemory).toBeLessThan(512 * 1024 * 1024); // 512MB
    });
});

test.describe('Debug Environment', () => {
    test('debug ports are accessible', async () => {
        expect(await DebugHelper.isDebuggerAttached('frontend')).toBe(true);
        expect(await DebugHelper.isDebuggerAttached('backend')).toBe(true);
    });

    test('source maps are available', async () => {
        const sourceMap = await DebugHelper.getSourceMap('main');
        expect(sourceMap.version).toBeDefined();
        expect(sourceMap.sources).toContain('src/main.tsx');
    });

    test('development tools are installed', async () => {
        expect(await DebugHelper.checkDevTools('frontend')).toBe(true);
        expect(await DebugHelper.checkDevTools('backend')).toBe(true);
    });

    test('hot reload is functioning', async () => {
        expect(await DebugHelper.checkHotReload()).toBe(true);
    });
});

test.describe('Error Handling', () => {
    test('recovers from network issues', async () => {
        // Track service status before disconnect
        const initialStatus = await DebugHelper.isServiceRunning('frontend');
        
        // Simulate network issue
        await DebugHelper.simulateNetworkIssue();
        
        // Check recovery
        const finalStatus = await DebugHelper.isServiceRunning('frontend');
        expect(finalStatus).toBe(initialStatus);
        
        // Check logs for reconnection attempts
        const logs = await DebugHelper.getLogs('frontend');
        expect(logs).toContain('Attempting to reconnect');
    });

    test('handles memory pressure', async () => {
        // Record initial memory usage
        const initialMemory = await DebugHelper.getMemoryUsage('frontend');
        
        // Create memory pressure
        await DebugHelper.createMemoryPressure('frontend');
        
        // Check memory usage after pressure
        const peakMemory = await DebugHelper.getMemoryUsage('frontend');
        expect(peakMemory).toBeGreaterThan(initialMemory);
        
        // Verify service recovers
        expect(await DebugHelper.isServiceRunning('frontend')).toBe(true);
    });

    test('maintains data integrity during restarts', async () => {
        // Stop services
        await DebugHelper.simulateNetworkIssue(0); // Disconnect immediately
        
        // Wait for automatic recovery
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Verify services are running and state is preserved
        expect(await DebugHelper.isServiceRunning('frontend')).toBe(true);
        expect(await DebugHelper.isServiceRunning('backend')).toBe(true);
        
        // Check logs for successful state recovery
        const logs = await DebugHelper.getLogs('frontend');
        expect(logs).toContain('State recovered');
    });
});

test.describe('Performance', () => {
    test('container startup time', async () => {
        const startTime = Date.now();
        
        // Stop and start services
        await DebugHelper.simulateNetworkIssue(0);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Wait for services to be ready
        while (!(await DebugHelper.isServiceRunning('frontend'))) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (Date.now() - startTime > 10000) throw new Error('Startup timeout');
        }
        
        const startupTime = Date.now() - startTime;
        expect(startupTime).toBeLessThan(5000); // Should start within 5 seconds
    });

    test('resource usage under load', async () => {
        const initialMemory = await DebugHelper.getMemoryUsage('frontend');
        
        // Create load
        for (let i = 0; i < 5; i++) {
            await DebugHelper.createMemoryPressure('frontend');
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        const finalMemory = await DebugHelper.getMemoryUsage('frontend');
        expect(finalMemory - initialMemory).toBeLessThan(100 * 1024 * 1024); // Max 100MB increase
    });
}); 