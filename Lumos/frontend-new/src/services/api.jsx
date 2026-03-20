import axios from 'axios';

const API_BASE_URL = '';

export const apiRequest = async (method, endpoint, data) => {
  try {
    const config = {
      method,
      url: `${API_BASE_URL}${endpoint}`,
      data,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    const response = await axios(config);
    return response.data;
  } catch (error) {
    console.error(`Error during API request to ${endpoint}:`, error);
    throw error;
  }
};

export const fetchArticles = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/news`);
    return response.data;
  } catch (error) {
    console.error('Error fetching articles:', error);
    return [];
  }
};

export const sendTestNotification = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/notify`, { message: 'Test notification' });
    return response.data;
  } catch (error) {
    console.error('Error sending notification:', error);
  }
};
