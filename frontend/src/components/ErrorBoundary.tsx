import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Button, Text, VStack, useToast } from '@chakra-ui/react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null
        };
    }

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error
        };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <VStack spacing={4} p={4} align="stretch">
                    <Text fontSize="xl" fontWeight="bold" color="red.500">
                        Something went wrong
                    </Text>
                    <Box bg="red.50" p={4} borderRadius="md">
                        <Text color="red.900">
                            {this.state.error?.message || 'An unexpected error occurred'}
                        </Text>
                    </Box>
                    <Button
                        colorScheme="blue"
                        onClick={() => {
                            this.setState({ hasError: false, error: null });
                            window.location.reload();
                        }}
                    >
                        Try Again
                    </Button>
                </VStack>
            );
        }

        return this.props.children;
    }
}

// HOC to wrap components with error boundary
export const withErrorBoundary = <P extends object>(
    WrappedComponent: React.ComponentType<P>,
    fallback?: ReactNode
) => {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <WrappedComponent {...props} />
            </ErrorBoundary>
        );
    };
}; 