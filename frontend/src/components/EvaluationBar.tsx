import React from 'react';
import {
  Box,
  Text,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';

interface EvaluationBarProps {
  evaluation: number;  // Evaluation in pawns (positive for white advantage)
  height?: string;    // Optional height override
}

export const EvaluationBar: React.FC<EvaluationBarProps> = ({ 
  evaluation,
  height = '400px'  // Default height matches typical board size
}) => {
  const bgColor = useColorModeValue('gray.100', 'gray.700');
  const whiteColor = useColorModeValue('white', 'gray.100');
  const blackColor = useColorModeValue('gray.800', 'gray.900');
  
  // Convert evaluation to percentage for the bar
  // Use a sigmoid-like function to keep it in bounds
  const getPercentage = (eval_pawns: number): number => {
    // Handle mate scores
    if (eval_pawns >= 100) return 100;
    if (eval_pawns <= -100) return 0;
    
    // Convert pawn score to percentage
    // Use sigmoid-like function to compress the range
    const percentage = 50 + (Math.atan(eval_pawns) / Math.PI * 50);
    return Math.min(100, Math.max(0, percentage));
  };
  
  const percentage = getPercentage(evaluation);
  
  // Format the evaluation text
  const formatEvaluation = (eval_pawns: number): string => {
    if (eval_pawns >= 100) return 'Mate';
    if (eval_pawns <= -100) return '-Mate';
    
    const sign = eval_pawns > 0 ? '+' : '';
    return `${sign}${eval_pawns.toFixed(1)}`;
  };
  
  const tooltipLabel = `Evaluation: ${formatEvaluation(evaluation)}
White ${evaluation >= 0 ? 'winning' : 'losing'} by ${Math.abs(evaluation).toFixed(1)} pawns`;

  return (
    <Tooltip label={tooltipLabel} placement="right">
      <Box
        width="30px"
        height={height}
        bg={bgColor}
        borderRadius="md"
        overflow="hidden"
        position="relative"
        role="progressbar"
        aria-valuenow={evaluation}
        aria-valuemin={-100}
        aria-valuemax={100}
      >
        {/* Black's portion */}
        <Box
          bg={blackColor}
          height={`${100 - percentage}%`}
          transition="height 0.3s ease-in-out"
        />
        
        {/* White's portion */}
        <Box
          bg={whiteColor}
          height={`${percentage}%`}
          transition="height 0.3s ease-in-out"
        />
        
        {/* Evaluation text */}
        <Text
          position="absolute"
          top="50%"
          left="50%"
          transform="translate(-50%, -50%) rotate(-90deg)"
          fontSize="sm"
          fontWeight="bold"
          color={evaluation >= 0 ? blackColor : whiteColor}
          textShadow="0 0 2px rgba(0,0,0,0.3)"
        >
          {formatEvaluation(evaluation)}
        </Text>
      </Box>
    </Tooltip>
  );
}; 