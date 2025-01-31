import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

// Color mode config
const config: ThemeConfig = {
  initialColorMode: 'system',
  useSystemColorMode: true,
};

// Custom colors
const colors = {
  brand: {
    50: '#E6F6FF',
    100: '#BAE3FF',
    200: '#7CC4FA',
    300: '#47A3F3',
    400: '#2186EB',
    500: '#0967D2',
    600: '#0552B5',
    700: '#03449E',
    800: '#01337D',
    900: '#002159',
  },
};

// Extend the theme
const theme = extendTheme({ 
  config,
  colors,
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
        color: props.colorMode === 'dark' ? 'white' : 'gray.900',
      },
    }),
  },
  components: {
    Container: {
      baseStyle: {
        maxW: 'container.xl',
        px: [4, 6],
        py: [6, 8],
      },
    },
    Modal: {
      baseStyle: (props: any) => ({
        dialog: {
          bg: props.colorMode === 'dark' ? 'gray.800' : 'white',
          boxShadow: 'xl',
        },
        overlay: {
          bg: props.colorMode === 'dark' ? 'blackAlpha.600' : 'blackAlpha.400',
        },
        header: {
          color: props.colorMode === 'dark' ? 'white' : 'gray.800',
        },
        body: {
          color: props.colorMode === 'dark' ? 'gray.100' : 'gray.800',
        },
      }),
    },
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
      variants: {
        ghost: (props: any) => ({
          _hover: {
            bg: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'blackAlpha.100',
          },
        }),
      },
    },
    Tooltip: {
      baseStyle: (props: any) => ({
        bg: props.colorMode === 'dark' ? 'gray.700' : 'gray.800',
        color: 'white',
        padding: '8px 16px',
        borderRadius: 'md',
        fontWeight: 'medium',
      }),
    },
    IconButton: {
      defaultProps: {
        variant: 'ghost',
      },
      variants: {
        ghost: (props: any) => ({
          _hover: {
            bg: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'blackAlpha.100',
          },
        }),
      },
    },
    Select: {
      baseStyle: (props: any) => ({
        field: {
          bg: props.colorMode === 'dark' ? 'gray.800' : 'white',
          borderColor: props.colorMode === 'dark' ? 'gray.600' : 'gray.200',
          _hover: {
            borderColor: props.colorMode === 'dark' ? 'gray.500' : 'gray.300',
          },
        },
      }),
    },
    Slider: {
      baseStyle: (props: any) => ({
        track: {
          bg: props.colorMode === 'dark' ? 'gray.600' : 'gray.200',
        },
        filledTrack: {
          bg: props.colorMode === 'dark' ? 'brand.400' : 'brand.500',
        },
        thumb: {
          bg: 'white',
          borderColor: props.colorMode === 'dark' ? 'brand.400' : 'brand.500',
        },
      }),
    },
    Chessboard: {
      baseStyle: (props: any) => ({
        lightSquareColor: props.colorMode === 'dark' ? '#4a5568' : '#f0d9b5',
        darkSquareColor: props.colorMode === 'dark' ? '#2d3748' : '#b58863',
        borderColor: props.colorMode === 'dark' ? 'gray.600' : 'gray.300',
      }),
    },
  },
  toast: {
    defaultOptions: {
      position: 'top-right',
      duration: 5000,
      isClosable: true,
    },
    maxToasts: 4,
  },
});

export default theme; 