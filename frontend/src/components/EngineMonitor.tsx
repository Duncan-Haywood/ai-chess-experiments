import React, { useEffect, useRef } from 'react';
import { Box, VStack, Text, Progress, useColorModeValue, HStack } from '@chakra-ui/react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { EngineMetrics } from '../types/game';

// Register ChartJS components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface EngineMonitorProps {
    engineName: string;
    metrics: EngineMetrics[];
    isThinking: boolean;
}

export const EngineMonitor: React.FC<EngineMonitorProps> = ({
    engineName,
    metrics,
    isThinking
}) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const textColor = useColorModeValue('gray.800', 'white');
    const chartRef = useRef<typeof ChartJS>(null);

    // Calculate derived metrics
    const lastMetric = metrics[metrics.length - 1];
    const nodesPerSecond = lastMetric ? 
        Math.round(lastMetric.nodes_searched / lastMetric.time_taken) : 0;

    // Chart data - only show last 20 data points for performance
    const recentMetrics = metrics.slice(-20);
    const chartData = {
        labels: recentMetrics.map((_, i) => i.toString()),
        datasets: [
            {
                label: 'Depth',
                data: recentMetrics.map(m => m.depth_reached),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            {
                label: 'CPU Usage (%)',
                data: recentMetrics.map(m => m.cpu_percent),
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        animation: {
            duration: 0 // Disable animations for better performance
        },
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: `${engineName} Performance`,
            },
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    // Update chart on theme change
    useEffect(() => {
        if (chartRef.current) {
            chartRef.current.update();
        }
    }, [bgColor]);

    return (
        <VStack 
            spacing={4} 
            p={4} 
            bg={bgColor} 
            borderRadius="lg" 
            shadow="md"
            align="stretch"
        >
            <HStack justify="space-between">
                <Text fontSize="lg" fontWeight="bold" color={textColor}>
                    {engineName}
                </Text>
                {isThinking && (
                    <Box>
                        <Text fontSize="sm" color="blue.500">Thinking...</Text>
                        <Progress size="xs" isIndeterminate w="100px" />
                    </Box>
                )}
            </HStack>

            <VStack align="stretch" spacing={2}>
                <HStack justify="space-between">
                    <Text fontSize="sm">Depth:</Text>
                    <Text fontSize="sm" fontWeight="bold">
                        {lastMetric?.depth_reached || 0}
                    </Text>
                </HStack>
                <HStack justify="space-between">
                    <Text fontSize="sm">Nodes/second:</Text>
                    <Text fontSize="sm" fontWeight="bold">
                        {nodesPerSecond.toLocaleString()}
                    </Text>
                </HStack>
                <HStack justify="space-between">
                    <Text fontSize="sm">Memory:</Text>
                    <Text fontSize="sm" fontWeight="bold">
                        {((lastMetric?.memory_used || 0) / (1024 * 1024)).toFixed(1)} MB
                    </Text>
                </HStack>
                <HStack justify="space-between">
                    <Text fontSize="sm">CPU:</Text>
                    <Text fontSize="sm" fontWeight="bold">
                        {(lastMetric?.cpu_percent || 0).toFixed(1)}%
                    </Text>
                </HStack>
            </VStack>

            <Box h="200px">
                <Line
                    ref={chartRef}
                    data={chartData}
                    options={chartOptions}
                />
            </Box>
        </VStack>
    );
}; 