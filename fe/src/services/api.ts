import axios from 'axios';
import { HistoryData } from '../types/water';

const API_URL = (import.meta as any).env.VITE_API_URL as string;

const api = axios.create({
	baseURL: API_URL,
	timeout: 5000,
});

// Interceptor để tự động đính kèm Token vào Header cho mỗi request
api.interceptors.request.use((config) => {
	const token = document.cookie
		.split('; ')
		.find(row => row.startsWith('access_token='))
		?.split('=')[1];

	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	return config;
});

export default api;

/**
 * User Management Services (Dành cho Admin)
 */
export const userService = {
	/**
	 * Lấy danh sách toàn bộ người dùng
	 * Endpoint tương ứng: GET /auth/users (Bạn cần tạo route này ở backend)
	 */
	getAllUsers: async () => {
		const res = await api.get('/auth/users');
		return res.data;
	},

	/**
	 * Lấy thông tin chi tiết một người dùng theo ID
	 */
	getUserById: async (id: string) => {
		const res = await api.get(`/auth/users/${id}`);
		return res.data;
	},

	/**
	 * Cập nhật thông tin người dùng (fullName, phoneNumber, urlAvatar, role, status)
	 * Backend sẽ sử dụng các trường từ User Domain
	 */
	updateUser: async (id: string, userData: {
		fullName?: string;
		phoneNumber?: string;
		urlAvatar?: string;
		role?: 'ADMIN' | 'MANAGER' | 'USER'; // Khớp với normalize_role
		status?: 'ACTIVE' | 'INACTIVE';      // Khớp với DEFAULT_USER_STATUS
	}) => {
		const res = await api.patch(`/auth/users/${id}`, userData);
		return res.data;
	},

	/**
	 * Xóa người dùng
	 */
	deleteUser: async (id: string) => {
		const res = await api.delete(`/auth/users/${id}`);
		return res.data;
	},

	/**
	 * Lấy thông tin người dùng hiện tại (Profile)
	 */
	getCurrentUser: async () => {
		const res = await api.get('/auth/me'); // Thường gọi đến AuthenticateUserUseCase
		return res.data;
	}
};


/**
 * AI Prediction Services
 */
// Lấy lịch sử 50 bản ghi dự đoán gần nhất
export const getHistory = async (): Promise<HistoryData[]> => {
	const res = await api.get('/prediction/history');
	return res.data;
};

// Gửi dữ liệu cảm biến để dự đoán chất lượng nước và rủi ro
export const predictWater = async (data: any) => {
	const res = await api.post('/prediction/predict', data);
	return res.data;
};

// Huấn luyện lại mô hình (từ file upload hoặc từ dữ liệu DB có sẵn)
export const trainAIModel = async (file?: File) => {
  if (file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/prediction/train', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } else {
    // Nếu không có file, back-end sẽ tự gọi ai_service.train_model_from_db()
    const res = await api.post('/prediction/train');
    return res.data;
  }
};

// Kiểm tra kết nối Database từ phía AI service
export const testAIDatabase = async () => {
  const res = await api.get('/prediction/test-db');
  return res.data;
};

/**
 * Sensor & Station Services
 */
export const sensorService = {
	// Lấy danh sách trạm (có phân trang)
	getStations: async (page = 1, limit = 10) => {
		const res = await api.get('/api/sensors', { params: { page, limit } });
		return res.data;
	},

	// Lấy chi tiết một trạm
	getStationById: async (id: string) => {
		const res = await api.get(`/api/sensors/${id}`);
		return res.data;
	},

	// Tạo trạm mới
	createStation: async (data: any) => {
		const res = await api.post('/api/sensors', data);
		return res.data;
	},

	// Cập nhật trạm
	updateStation: async (id: string, data: any) => {
		const res = await api.patch(`/api/sensors/${id}`, data);
		return res.data;
	},

	// Xóa trạm
	deleteStation: async (id: string) => {
		const res = await api.delete(`/api/sensors/${id}`);
		return res.data;
	},

	// Lấy dữ liệu cảm biến mới nhất
	getLatestData: async (sensorId?: string) => {
		const res = await api.get('/api/v1/sensors/latest', { params: { sensor_id: sensorId } });
		return res.data;
	},

	// Lấy kết quả phân loại từ AI
	getAIClassification: async (sensorId?: string) => {
		const res = await api.get('/api/v1/sensors/classification', { params: { sensor_id: sensorId } });
		return res.data;
	}
};

/**
 * Alert Services
 */
export const alertService = {
	// Lấy danh sách cảnh báo (mặc định là chưa đọc)
	getAlerts: async (status: 'unread' | 'read' | 'all' = 'unread') => {
		const res = await api.get('/api/v1/alerts', { params: { status } });
		return res.data;
	},

	// Đánh dấu cảnh báo là đã đọc
	markAsRead: async (alertId: string) => {
		const res = await api.put(`/api/v1/alerts/${alertId}/read`);
		return res.data;
	}
};