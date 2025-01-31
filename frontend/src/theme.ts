import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: 'gray.50',
        color: 'gray.800',
      },
    },
  },
  components: {
    Container: {
      baseStyle: {
        maxW: 'container.xl',
        px: [4, 6],
        py: [6, 8],
      },
    },
    Button: {
      defaultProps: {
        colorScheme: 'blue',
      },
    },
  },
});

export default theme; 