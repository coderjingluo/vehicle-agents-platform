import { defineStore } from 'pinia';
import { authAPI } from '@/api';
import { ElMessage } from 'element-plus';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: null,
    userAvatar: null, // Profile avatar URL
    credits: '1500',  // User credits/points
    isLoggedIn: false,
    notifications: []
  }),
  
  getters: {
    userName: (state) => state.user?.username || 'Guest',
    userEmail: (state) => state.user?.email || '',
    authHeader: (state) => state.token ? `Bearer ${state.token}` : '',
    hasNotifications: (state) => state.notifications.length > 0,
    notificationCount: (state) => state.notifications.length
  },
  
  actions: {
    async login(credentials) {
      try {
        const response = await authAPI.login(credentials);
        this.setAuth(response.token, response.user);
        return true;
      } catch (error) {
        console.error('Login failed:', error);
        ElMessage.error('登录失败: ' + (error.message || '请检查用户名和密码'));
        return false;
      }
    },
    
    async logout() {
      try {
        if (this.token) {
          await authAPI.logout();
        }
      } catch (error) {
        console.error('Logout error:', error);
      } finally {
        this.clearAuth();
      }
    },
    
    setAuth(token, userInfo) {
      this.token = token;
      this.user = userInfo;
      this.isLoggedIn = true;
      
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_info', JSON.stringify(userInfo));
    },
    
    clearAuth() {
      this.token = null;
      this.user = null;
      this.isLoggedIn = false;
      
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
    },
    
    async refreshUserInfo() {
      if (!this.isLoggedIn) return;
      
      try {
        const response = await authAPI.getUserInfo();
        this.user = response;
        localStorage.setItem('user_info', JSON.stringify(response));
      } catch (error) {
        console.error('Failed to refresh user info:', error);
      }
    },
    
    async updateCredit(amount) {
      if (!this.isLoggedIn) return;
      
      try {
        const newCredit = await authAPI.updateCredit({ amount });
        this.credits = newCredit.toString();
        localStorage.setItem('user_info', JSON.stringify(this.user));
        return newCredit;
      } catch (error) {
        console.error('Failed to update credits:', error);
        return parseInt(this.credits) || 0;
      }
    },
    
    setUser(userData) {
      this.user = userData;
      this.userAvatar = userData.avatar || this.userAvatar;
      this.isLoggedIn = true;
      localStorage.setItem('user', JSON.stringify(userData));
    },
    
    setToken(token) {
      this.token = token;
      localStorage.setItem('token', token);
    },
    
    setAvatar(avatarUrl) {
      this.userAvatar = avatarUrl;
      if (this.user) {
        this.user.avatar = avatarUrl;
        localStorage.setItem('user', JSON.stringify(this.user));
      }
    },
    
    addCredits(amount) {
      const currentCredits = parseInt(this.credits) || 0;
      this.credits = (currentCredits + parseInt(amount)).toString();
    },
    
    useCredits(amount) {
      const currentCredits = parseInt(this.credits) || 0;
      const newAmount = Math.max(0, currentCredits - parseInt(amount));
      this.credits = newAmount.toString();
      return newAmount >= amount;
    },
    
    addNotification(notification) {
      this.notifications.push({
        id: Date.now(),
        read: false,
        ...notification
      });
    },
    
    markNotificationAsRead(notificationId) {
      const notification = this.notifications.find(n => n.id === notificationId);
      if (notification) {
        notification.read = true;
      }
    },
    
    clearNotifications() {
      this.notifications = [];
    }
  }
}); 