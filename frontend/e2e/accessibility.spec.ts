import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('main page passes accessibility scan', async ({ page }) => {
        const results = await new AxeBuilder({ page }).analyze();
        expect(results.violations).toEqual([]);
    });

    test('game board is keyboard navigable', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Navigate to board using keyboard
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        
        // Verify focus is on the board
        const focused = await page.evaluate(() => document.activeElement?.getAttribute('role'));
        expect(focused).toBe('application');
        
        // Test square selection with keyboard
        await page.keyboard.press('Enter');
        const selectedSquare = await page.evaluate(() => 
            document.querySelector('[data-square].selected')?.getAttribute('data-square')
        );
        expect(selectedSquare).toBeTruthy();
    });

    test('color contrast meets WCAG standards', async ({ page }) => {
        const results = await new AxeBuilder({ page })
            .withRules(['color-contrast'])
            .analyze();
        
        expect(results.violations).toEqual([]);
    });

    test('game status is announced to screen readers', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Check for aria-live region
        const liveRegion = await page.locator('[aria-live]');
        expect(await liveRegion.count()).toBeGreaterThan(0);
        
        // Make a move and check announcement
        await page.locator('[data-square="e2"]').click();
        await page.locator('[data-square="e4"]').click();
        
        const announcement = await page.locator('[aria-live="polite"]').textContent();
        expect(announcement).toContain('moved');
    });

    test('modal dialog follows ARIA practices', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        
        const dialog = page.getByRole('dialog');
        await expect(dialog).toHaveAttribute('aria-modal', 'true');
        await expect(dialog).toHaveAttribute('aria-labelledby', expect.any(String));
        
        // Check focus trap
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-focus-guard'));
        expect(focusedElement).toBeTruthy();
    });

    test('error messages are announced', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Trigger an invalid move
        await page.locator('[data-square="e2"]').click();
        await page.locator('[data-square="e6"]').click();
        
        const errorMessage = await page.locator('[role="alert"]');
        await expect(errorMessage).toBeVisible();
        await expect(errorMessage).toHaveAttribute('aria-live', 'assertive');
    });

    test('theme toggle is accessible', async ({ page }) => {
        const themeToggle = page.getByRole('button', { name: /toggle/i });
        await expect(themeToggle).toHaveAttribute('aria-label');
        
        await themeToggle.click();
        await expect(themeToggle).toHaveAttribute('aria-pressed', 'true');
    });

    test('game controls have proper labels', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        
        const controls = await page.locator('[role="button"], [role="slider"], select');
        const elements = await controls.all();
        
        for (const element of elements) {
            const label = await element.getAttribute('aria-label');
            expect(label).toBeTruthy();
        }
    });
}); 