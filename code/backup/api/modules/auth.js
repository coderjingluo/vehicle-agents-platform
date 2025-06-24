import { apiClient as request } from '../index'

/**
 * @description 用户登录
 * @param {object} data { username, password }
 * @returns {Promise}
 */
export function login(data) {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new FormData();
  formData.append('username', data.username);
  formData.append('password', data.password);

  return request({
    url: '/auth/login',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * @description 获取当前用户信息
 * @returns {Promise}
 */
export function getMe() {
  return request({
    url: '/auth/me',
    method: 'get',
  });
} 
export default {
  login,
  getMe,
}