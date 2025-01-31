import React from 'react';
import {
  Box,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
  VStack,
  Button,
  Collapse,
  useDisclosure,
  Text,
  Badge,
} from '@chakra-ui/react';

export interface ErrorItem {
  id: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  timestamp: Date;
  count?: number;  // For grouped errors
}

interface ErrorDisplayProps {
  errors: ErrorItem[];
  onDismiss: (id: string) => void;
  onDismissAll: () => void;
  maxVisible?: number;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  errors,
  onDismiss,
  onDismissAll,
  maxVisible = 4  // Show max 4 errors at once
}) => {
  const { isOpen, onToggle } = useDisclosure({ defaultIsOpen: true });
  
  // Group similar errors
  const groupedErrors = errors.reduce((acc, error) => {
    const key = `${error.severity}-${error.message}`;
    if (!acc[key]) {
      acc[key] = { ...error, count: 1 };
    } else {
      acc[key].count = (acc[key].count || 1) + 1;
      acc[key].timestamp = error.timestamp; // Use most recent
    }
    return acc;
  }, {} as Record<string, ErrorItem>);

  const sortedErrors = Object.values(groupedErrors)
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, maxVisible);

  const hiddenCount = Math.max(0, errors.length - maxVisible);

  const getSeverityColor = (severity: ErrorItem['severity']) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'error': return 'orange';
      case 'warning': return 'yellow';
      default: return 'blue';
    }
  };

  if (errors.length === 0) return null;

  return (
    <Box position="fixed" top={4} right={4} maxW="400px" zIndex={1000}>
      <VStack spacing={2} align="stretch">
        <Box display="flex" justifyContent="space-between" mb={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={onToggle}
          >
            {isOpen ? 'Hide' : 'Show'} Errors ({errors.length})
          </Button>
          {errors.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              colorScheme="red"
              onClick={onDismissAll}
            >
              Dismiss All
            </Button>
          )}
        </Box>

        <Collapse in={isOpen}>
          <VStack spacing={2} align="stretch">
            {sortedErrors.map((error) => (
              <Alert
                key={error.id}
                status={error.severity === 'critical' ? 'error' : error.severity}
                variant="left-accent"
                borderRadius="md"
              >
                <AlertIcon />
                <Box flex="1">
                  <AlertTitle display="flex" alignItems="center" gap={2}>
                    {error.severity.toUpperCase()}
                    {error.count && error.count > 1 && (
                      <Badge colorScheme={getSeverityColor(error.severity)}>
                        ×{error.count}
                      </Badge>
                    )}
                  </AlertTitle>
                  <AlertDescription display="block">
                    {error.message}
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      {error.timestamp.toLocaleTimeString()}
                    </Text>
                  </AlertDescription>
                </Box>
                <CloseButton
                  onClick={() => onDismiss(error.id)}
                  position="absolute"
                  right={1}
                  top={1}
                />
              </Alert>
            ))}
            
            {hiddenCount > 0 && (
              <Alert status="info" variant="subtle">
                <AlertIcon />
                <AlertDescription>
                  +{hiddenCount} more error{hiddenCount > 1 ? 's' : ''}
                </AlertDescription>
              </Alert>
            )}
          </VStack>
        </Collapse>
      </VStack>
    </Box>
  );
}; 