import axios from 'axios';
import { HistoryData } from '../types/water';

const API_URL = 'http://localhost:5000';

const api = axios.create({
    baseURL: API_URL,
    timeout: 5000,
});

export const getHistory = async (): Promise<HistoryData[]> => {
    const res = await api.get('/prediction/history');
    return res.data;
};

export const predictWater = async (data: any) => {
    const res = await api.post('/prediction/predict', data);
    return res.data;
};
