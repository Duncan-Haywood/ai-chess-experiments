import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Grid,
  useColorModeValue,
  Heading,
} from '@chakra-ui/react';
import { Line } from 'react-chartjs-2';

interface EngineMetrics {
  nodesPerSecond: number;
  averageDepth: number;
  cacheHitRate: number;
  moveCalculationTime: number;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  activeGames: number;
  queuedMoves: number;
}

export const PerformanceMonitor: React.FC = () => {
  const [engineMetrics, setEngineMetrics] = useState<EngineMetrics>({
    nodesPerSecond: 0,
    averageDepth: 0,
    cacheHitRate: 0,
    moveCalculationTime: 0,
  });

  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    activeGames: 0,
    queuedMoves: 0,
  });

  const [historicalData, setHistoricalData] = useState({
    labels: [] as string[],
    nodesPerSecond: [] as number[],
    cpuUsage: [] as number[],
  });

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        setEngineMetrics(data.engine);
        setSystemMetrics(data.system);
        
        // Update historical data
        setHistoricalData(prev => ({
          labels: [...prev.labels, new Date().toLocaleTimeString()].slice(-20),
          nodesPerSecond: [...prev.nodesPerSecond, data.engine.nodesPerSecond].slice(-20),
          cpuUsage: [...prev.cpuUsage, data.system.cpuUsage].slice(-20),
        }));
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    const interval = setInterval(fetchMetrics, 1000);
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: historicalData.labels,
    datasets: [
      {
        label: 'Nodes/Second',
        data: historicalData.nodesPerSecond,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
      {
        label: 'CPU Usage %',
        data: historicalData.cpuUsage,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
      },
    ],
  };

  return (
    <VStack spacing={6} w="100%" p={4}>
      <Heading size="lg">System Performance</Heading>
      
      <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6} w="100%">
        <Box p={6} bg={bgColor} borderRadius="lg" borderWidth={1} borderColor={borderColor}>
          <Heading size="md" mb={4}>Engine Metrics</Heading>
          <VStack align="stretch" spacing={4}>
            <Stat>
              <StatLabel>Nodes/Second</StatLabel>
              <StatNumber>{engineMetrics.nodesPerSecond.toLocaleString()}</StatNumber>
              <StatHelpText>Search speed</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Average Depth</StatLabel>
              <StatNumber>{engineMetrics.averageDepth.toFixed(1)}</StatNumber>
              <StatHelpText>Search depth</StatHelpText>
            </Stat>
          </VStack>
        </Box>

        <Box p={6} bg={bgColor} borderRadius="lg" borderWidth={1} borderColor={borderColor}>
          <Heading size="md" mb={4}>System Metrics</Heading>
          <VStack align="stretch" spacing={4}>
            <Stat>
              <StatLabel>CPU Usage</StatLabel>
              <StatNumber>{systemMetrics.cpuUsage.toFixed(1)}%</StatNumber>
              <StatHelpText>Current load</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Memory Usage</StatLabel>
              <StatNumber>{systemMetrics.memoryUsage.toFixed(1)}%</StatNumber>
              <StatHelpText>RAM utilization</StatHelpText>
            </Stat>
          </VStack>
        </Box>

        <Box p={6} bg={bgColor} borderRadius="lg" borderWidth={1} borderColor={borderColor}>
          <Heading size="md" mb={4}>Game Stats</Heading>
          <VStack align="stretch" spacing={4}>
            <Stat>
              <StatLabel>Active Games</StatLabel>
              <StatNumber>{systemMetrics.activeGames}</StatNumber>
              <StatHelpText>Currently running</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Move Queue</StatLabel>
              <StatNumber>{systemMetrics.queuedMoves}</StatNumber>
              <StatHelpText>Pending calculations</StatHelpText>
            </Stat>
          </VStack>
        </Box>
      </Grid>

      <Box w="100%" h="400px" p={6} bg={bgColor} borderRadius="lg" borderWidth={1} borderColor={borderColor}>
        <Heading size="md" mb={4}>Performance History</Heading>
        <Line 
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
              },
            },
          }}
        />
      </Box>
    </VStack>
  );
}; 