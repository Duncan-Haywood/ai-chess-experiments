import React from 'react';
import {
    Box,
    VStack,
    Text,
    Badge,
    List,
    ListItem,
    ListIcon,
    Popover,
    PopoverTrigger,
    PopoverContent,
    PopoverHeader,
    PopoverBody,
    PopoverArrow,
    PopoverCloseButton,
    Button,
    useColorModeValue
} from '@chakra-ui/react';
import { InfoIcon, CheckIcon } from '@chakra-ui/icons';
import { BotAlgorithm } from '../types/bots';

interface BotInfoProps {
    bot: BotAlgorithm;
    isSelected?: boolean;
    onSelect?: () => void;
}

export const BotInfo: React.FC<BotInfoProps> = ({ bot, isSelected, onSelect }) => {
    const bgColor = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const selectedBorderColor = useColorModeValue('blue.500', 'blue.300');

    const getDifficultyColor = (difficulty: string) => {
        switch (difficulty) {
            case 'Beginner':
                return 'green';
            case 'Intermediate':
                return 'yellow';
            case 'Advanced':
                return 'red';
            default:
                return 'gray';
        }
    };

    return (
        <Box
            p={4}
            borderWidth="1px"
            borderRadius="lg"
            borderColor={isSelected ? selectedBorderColor : borderColor}
            bg={bgColor}
            cursor={onSelect ? 'pointer' : 'default'}
            onClick={onSelect}
            position="relative"
            transition="all 0.2s"
            _hover={{
                transform: onSelect ? 'translateY(-2px)' : 'none',
                boxShadow: onSelect ? 'md' : 'none'
            }}
        >
            <VStack align="start" spacing={3}>
                <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                    <Text fontSize="lg" fontWeight="bold">
                        {bot.name}
                    </Text>
                    <Badge colorScheme={getDifficultyColor(bot.difficultyLevel)}>
                        {bot.difficultyLevel}
                    </Badge>
                </Box>

                <Text fontSize="sm" color="gray.500">
                    {bot.description}
                </Text>

                <Popover placement="right">
                    <PopoverTrigger>
                        <Button size="sm" leftIcon={<InfoIcon />} variant="ghost">
                            View Features
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent>
                        <PopoverArrow />
                        <PopoverCloseButton />
                        <PopoverHeader fontWeight="bold">Bot Characteristics</PopoverHeader>
                        <PopoverBody>
                            <List spacing={2}>
                                {bot.characteristics.map((char, index) => (
                                    <ListItem key={index} display="flex" alignItems="center">
                                        <ListIcon as={CheckIcon} color="green.500" />
                                        {char}
                                    </ListItem>
                                ))}
                            </List>
                        </PopoverBody>
                    </PopoverContent>
                </Popover>

                <Box>
                    <Text fontSize="sm" color="gray.500">
                        Recommended Depth: {bot.recommendedDepth.min}-{bot.recommendedDepth.max}
                    </Text>
                </Box>
            </VStack>
        </Box>
    );
}; 