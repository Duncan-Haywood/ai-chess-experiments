import { IconButton, useColorMode, Tooltip } from '@chakra-ui/react';
import { SunIcon, MoonIcon } from '@chakra-ui/icons';

export const ThemeToggle = () => {
    const { colorMode, toggleColorMode } = useColorMode();

    return (
        <Tooltip 
            label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}
            placement="bottom"
        >
            <IconButton
                aria-label={`Toggle ${colorMode === 'light' ? 'dark' : 'light'} mode`}
                icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                onClick={toggleColorMode}
                variant="ghost"
                colorScheme={colorMode === 'light' ? 'gray' : 'yellow'}
                size="md"
            />
        </Tooltip>
    );
}; 