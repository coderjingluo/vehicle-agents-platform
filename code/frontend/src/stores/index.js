import { createPinia } from 'pinia';
import { useUserStore } from './user';
import { useAgentStore } from './agent';

export {
  useUserStore,
  useAgentStore
};

// Initialize and setup the stores
export const setupStore = () => {
  const userStore = useUserStore();
  const agentStore = useAgentStore();
  
  // Initialize user data from localStorage if available
  if (localStorage.getItem('user')) {
    try {
      const userData = JSON.parse(localStorage.getItem('user'));
      userStore.setUser(userData);
    } catch (e) {
      console.error('Error parsing user data from localStorage', e);
    }
  }
  
  // Set default user avatar if not set
  if (!userStore.userAvatar) {
    userStore.userAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
  }
  
  // Set default credits
  if (!userStore.credits) {
    userStore.credits = '1500';
  }
  
  // Initialize agent data
  agentStore.initializeAgentData();
}; 