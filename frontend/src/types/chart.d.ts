declare module 'chart.js' {
    export const Chart: any;
    export const CategoryScale: any;
    export const LinearScale: any;
    export const PointElement: any;
    export const LineElement: any;
    export const Title: any;
    export const Tooltip: any;
    export const Legend: any;
}

declare module 'react-chartjs-2' {
    import { Chart } from 'chart.js';
    
    export interface LineProps {
        data: {
            labels: string[];
            datasets: Array<{
                label: string;
                data: number[];
                borderColor: string;
                tension: number;
            }>;
        };
        options?: any;
        ref?: React.RefObject<Chart>;
    }

    export const Line: React.FC<LineProps>;
} 