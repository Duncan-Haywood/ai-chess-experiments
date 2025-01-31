import React from 'react';
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Switch,
  HStack,
  Text,
  Select,
  VStack,
  Divider,
} from '@chakra-ui/react';
import { FiSettings } from 'react-icons/fi';
import { useSettings } from '../contexts/SettingsContext';

export const SettingsMenu: React.FC = () => {
  const { settings, updateSettings } = useSettings();

  const handleSoundToggle = () => {
    updateSettings({ soundEnabled: !settings.soundEnabled });
  };

  const handleColorModeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    updateSettings({ colorMode: event.target.value as 'light' | 'dark' | 'system' });
  };

  return (
    <Menu>
      <MenuButton
        as={IconButton}
        aria-label="Settings"
        icon={<FiSettings />}
        variant="ghost"
      />
      <MenuList p={2}>
        <VStack spacing={3} align="stretch">
          <MenuItem closeOnSelect={false}>
            <HStack justify="space-between" width="100%">
              <Text>Sound Effects</Text>
              <Switch
                isChecked={settings.soundEnabled}
                onChange={handleSoundToggle}
              />
            </HStack>
          </MenuItem>
          
          <Divider />
          
          <MenuItem closeOnSelect={false}>
            <VStack align="stretch" width="100%" spacing={2}>
              <Text>Color Theme</Text>
              <Select
                value={settings.colorMode}
                onChange={handleColorModeChange}
                size="sm"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </Select>
            </VStack>
          </MenuItem>
        </VStack>
      </MenuList>
    </Menu>
  );
}; 