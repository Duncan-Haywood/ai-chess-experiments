import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ErrorBoundary, withErrorBoundary } from '../components/ErrorBoundary';

// Test component that throws an error
const BuggyComponent = ({ shouldThrow = false }) => {
    if (shouldThrow) {
        throw new Error('Test error');
    }
    return <div>Working component</div>;
};

// Store original console.error
const originalError = console.error;

describe('ErrorBoundary', () => {
    beforeEach(() => {
        console.error = vi.fn();
    });
    
    afterEach(() => {
        console.error = originalError;
    });

    it('renders children when no error occurs', () => {
        render(
            <ChakraProvider>
                <ErrorBoundary>
                    <BuggyComponent shouldThrow={false} />
                </ErrorBoundary>
            </ChakraProvider>
        );

        expect(screen.getByText('Working component')).toBeInTheDocument();
    });

    it('renders error UI when error occurs', () => {
        render(
            <ChakraProvider>
                <ErrorBoundary>
                    <BuggyComponent shouldThrow={true} />
                </ErrorBoundary>
            </ChakraProvider>
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('Test error')).toBeInTheDocument();
    });

    it('renders custom fallback when provided', () => {
        const fallback = <div>Custom error message</div>;
        render(
            <ChakraProvider>
                <ErrorBoundary fallback={fallback}>
                    <BuggyComponent shouldThrow={true} />
                </ErrorBoundary>
            </ChakraProvider>
        );

        expect(screen.getByText('Custom error message')).toBeInTheDocument();
    });

    it('resets error state when try again is clicked', () => {
        const { container } = render(
            <ChakraProvider>
                <ErrorBoundary>
                    <BuggyComponent shouldThrow={true} />
                </ErrorBoundary>
            </ChakraProvider>
        );

        // Mock window.location.reload
        const reloadMock = vi.fn();
        Object.defineProperty(window, 'location', {
            value: { reload: reloadMock },
            writable: true
        });

        const tryAgainButton = screen.getByText('Try Again');
        fireEvent.click(tryAgainButton);

        expect(reloadMock).toHaveBeenCalled();
    });
});

describe('withErrorBoundary HOC', () => {
    beforeEach(() => {
        console.error = vi.fn();
    });
    
    afterEach(() => {
        console.error = originalError;
    });

    it('wraps component with error boundary', () => {
        const WrappedComponent = withErrorBoundary(BuggyComponent);
        
        render(
            <ChakraProvider>
                <WrappedComponent shouldThrow={false} />
            </ChakraProvider>
        );

        expect(screen.getByText('Working component')).toBeInTheDocument();
    });

    it('handles errors in wrapped component', () => {
        const WrappedComponent = withErrorBoundary(BuggyComponent);
        
        render(
            <ChakraProvider>
                <WrappedComponent shouldThrow={true} />
            </ChakraProvider>
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('uses custom fallback in HOC', () => {
        const fallback = <div>Custom HOC error</div>;
        const WrappedComponent = withErrorBoundary(BuggyComponent, fallback);
        
        render(
            <ChakraProvider>
                <WrappedComponent shouldThrow={true} />
            </ChakraProvider>
        );

        expect(screen.getByText('Custom HOC error')).toBeInTheDocument();
    });
}); 