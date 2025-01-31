import { exec } from 'child_process';
import { promisify } from 'util';
import * as net from 'net';

const execAsync = promisify(exec);

export class DebugHelper {
    private static readonly FRONTEND_DEBUG_PORT = 9229;
    private static readonly BACKEND_DEBUG_PORT = 5678;

    /**
     * Check if a debug port is open
     */
    static async isPortOpen(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            const socket = new net.Socket();
            
            socket.on('connect', () => {
                socket.destroy();
                resolve(true);
            });
            
            socket.on('error', () => {
                socket.destroy();
                resolve(false);
            });
            
            socket.connect(port, 'localhost');
        });
    }

    /**
     * Get container logs
     */
    static async getLogs(service: string, lines: number = 100): Promise<string> {
        const { stdout } = await execAsync(`docker compose logs ${service} --tail=${lines}`);
        return stdout;
    }

    /**
     * Check if a service is running
     */
    static async isServiceRunning(service: string): Promise<boolean> {
        try {
            const { stdout } = await execAsync('docker compose ps --format json');
            const services = JSON.parse(stdout);
            const targetService = services.find(s => s.Service === service);
            return targetService?.State === 'running';
        } catch {
            return false;
        }
    }

    /**
     * Get container memory usage
     */
    static async getMemoryUsage(service: string): Promise<number> {
        const { stdout } = await execAsync('docker stats --no-stream --format json');
        const stats = JSON.parse(stdout);
        const serviceStats = stats.find(s => s.Name.includes(service));
        return parseInt(serviceStats?.MemUsage || '0');
    }

    /**
     * Check if debugger is attached
     */
    static async isDebuggerAttached(service: 'frontend' | 'backend'): Promise<boolean> {
        const port = service === 'frontend' ? 
            this.FRONTEND_DEBUG_PORT : 
            this.BACKEND_DEBUG_PORT;
            
        return this.isPortOpen(port);
    }

    /**
     * Get source maps for a file
     */
    static async getSourceMap(file: string): Promise<any> {
        const { stdout } = await execAsync(`docker compose exec frontend cat /app/dist/${file}.map`);
        return JSON.parse(stdout);
    }

    /**
     * Check if hot reload is working
     */
    static async checkHotReload(): Promise<boolean> {
        try {
            // Make a change to trigger rebuild
            await execAsync('echo "// Test" >> src/App.tsx');
            
            // Wait for rebuild
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check logs for rebuild message
            const logs = await this.getLogs('frontend', 10);
            return logs.includes('rebuilding');
        } catch {
            return false;
        }
    }

    /**
     * Get environment variables
     */
    static async getEnvVars(service: string): Promise<Record<string, string>> {
        const { stdout } = await execAsync(`docker compose exec ${service} env`);
        const vars = {};
        stdout.split('\n').forEach(line => {
            const [key, value] = line.split('=');
            if (key && value) {
                vars[key] = value;
            }
        });
        return vars;
    }

    /**
     * Check if development tools are installed
     */
    static async checkDevTools(service: string): Promise<boolean> {
        try {
            if (service === 'frontend') {
                const { stdout } = await execAsync('docker compose exec frontend npm list --dev');
                return stdout.includes('vitest') && stdout.includes('@types/react');
            } else {
                const { stdout } = await execAsync('docker compose exec backend pip list');
                return stdout.includes('pytest') && stdout.includes('debugpy');
            }
        } catch {
            return false;
        }
    }

    /**
     * Simulate network issues
     */
    static async simulateNetworkIssue(duration: number = 5000): Promise<void> {
        await execAsync('docker network disconnect chess-bot_default chess-bot-frontend-1');
        await new Promise(resolve => setTimeout(resolve, duration));
        await execAsync('docker network connect chess-bot_default chess-bot-frontend-1');
    }

    /**
     * Create memory pressure
     */
    static async createMemoryPressure(service: string): Promise<void> {
        if (service === 'frontend') {
            await execAsync('docker compose exec frontend node -e "const a = new Array(1e8).fill(0)"');
        } else {
            await execAsync('docker compose exec backend python3 -c "a = [0] * 100000000"');
        }
    }
} 