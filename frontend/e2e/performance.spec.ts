import { test, expect } from '@playwright/test';

// Custom type for Chrome Performance API
interface PerformanceMemory {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
}

declare global {
    interface Performance {
        memory?: PerformanceMemory;
    }
}

// Common test actions
const startGame = async (page) => {
    await page.getByRole('button', { name: 'New Game' }).click();
    await page.getByText('Play Against Bot').click();
};

const makeMove = async (page, from: string, to: string) => {
    await page.locator(`[data-square="${from}"]`).click();
    await page.locator(`[data-square="${to}"]`).click();
};

test.describe('Performance', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('initial page load performance', async ({ page }) => {
        const startTime = performance.now();
        await page.goto('/', { waitUntil: 'networkidle' });
        const loadTime = performance.now() - startTime;
        
        expect(loadTime).toBeLessThan(3000);
        
        const [fcpEntry] = await page.evaluate(() => 
            performance.getEntriesByName('first-contentful-paint')
        );
        expect(fcpEntry?.startTime).toBeLessThan(1500);
    });

    test('move response time', async ({ page }) => {
        await startGame(page);
        
        const startTime = performance.now();
        await makeMove(page, 'e2', 'e4');
        
        await page.waitForSelector('[data-testid="last-move"]');
        const moveTime = performance.now() - startTime;
        
        expect(moveTime).toBeLessThan(1000);
    });

    test('memory usage during gameplay', async ({ page, browserName }) => {
        test.skip(browserName !== 'chromium', 'Memory API only available in Chrome');
        
        await startGame(page);
        
        // Play for a short while
        await makeMove(page, 'e2', 'e4');
        await page.waitForTimeout(2000);
        
        const memoryUsage = await page.evaluate(() => {
            return performance.memory?.usedJSHeapSize || 0;
        });
        
        // Only assert if we got a valid measurement
        if (memoryUsage > 0) {
            expect(memoryUsage).toBeLessThan(50 * 1024 * 1024); // 50MB
        }
    });

    test('UI responsiveness during processing', async ({ page }) => {
        await startGame(page);
        await makeMove(page, 'e2', 'e4');
        
        // Measure time to toggle theme
        const responseTime = await page.evaluate(async () => {
            const start = performance.now();
            const button = document.querySelector('[aria-label*="toggle"]');
            (button as HTMLButtonElement)?.click();
            return performance.now() - start;
        });
        
        expect(responseTime).toBeLessThan(100);
    });

    test('request batching', async ({ page }) => {
        await startGame(page);
        
        const requests = new Set<string>();
        page.on('request', request => {
            if (request.url().includes('/api')) {
                requests.add(request.url());
            }
        });
        
        // Make multiple rapid moves
        for (let i = 0; i < 3; i++) {
            await makeMove(page, 'e2', 'e4');
            await page.waitForTimeout(100);
        }
        
        // Should batch or debounce requests
        expect(requests.size).toBeLessThan(6); // Allow for initial state + moves
    });
}); 