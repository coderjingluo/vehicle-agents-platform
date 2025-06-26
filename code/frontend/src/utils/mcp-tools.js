/**
 * Utility functions for MCP tools integration
 */

import { ElMessage } from 'element-plus';

// List of available MCP tools
export const mcpTools = {
  analyzer: {
    id: 'analyzer',
    name: '安全分析器',
    description: 'TARA威胁分析和风险评估工具',
    status: 'connected',
    icon: 'Shield'
  },
  knowledge_base: {
    id: 'knowledge_base',
    name: '知识库查询',
    description: '查询车联网安全相关知识和法规标准',
    status: 'connected',
    icon: 'Document'
  },
  network_scanner: {
    id: 'network_scanner',
    name: '网络扫描器',
    description: '车联网设备安全漏洞扫描工具',
    status: 'connected',
    icon: 'Search'
  },
  test_generator: {
    id: 'test_generator',
    name: '测试用例生成器',
    description: '根据威胁模型生成测试用例',
    status: 'connected',
    icon: 'Edit'
  },
  code_analyzer: {
    id: 'code_analyzer',
    name: '代码分析器',
    description: '车载软件安全漏洞静态分析工具',
    status: 'connected',
    icon: 'Files'
  },
  script_generator: {
    id: 'script_generator',
    name: '脚本生成器',
    description: '自动化测试脚本生成工具',
    status: 'connected',
    icon: 'Document'
  },
  test_executor: {
    id: 'test_executor',
    name: '测试执行器',
    description: '自动化测试执行和管理工具',
    status: 'connected',
    icon: 'VideoPlay'
  },
  report_collector: {
    id: 'report_collector',
    name: '报告收集器',
    description: '测试结果收集和整理工具',
    status: 'connected',
    icon: 'Collection'
  },
  report_generator: {
    id: 'report_generator',
    name: '报告生成器',
    description: '安全测试报告自动生成工具',
    status: 'connected',
    icon: 'Reading'
  },
  data_analyzer: {
    id: 'data_analyzer',
    name: '数据分析器',
    description: '测试数据分析和可视化工具',
    status: 'connected',
    icon: 'DataAnalysis'
  }
};

// Mock MCP tool execution function
export const executeMcpTool = async (toolId, params) => {
  // Check if tool exists
  if (!mcpTools[toolId]) {
    ElMessage.error(`工具 ${toolId} 不存在`);
    throw new Error(`Tool ${toolId} not found`);
  }
  
  // Mock API call delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Mock execution result based on tool ID
  let result = {
    status: 'success',
    timestamp: new Date().toISOString(),
    toolId,
    data: {}
  };
  
  switch (toolId) {
    case 'analyzer':
      result.data = {
        threatsIdentified: Math.floor(Math.random() * 10) + 1,
        riskLevel: ['低', '中', '高'][Math.floor(Math.random() * 3)],
        recommendations: [
          '完善ECU加密通信',
          '增加CAN总线安全监控',
          '实施OTA更新验证机制'
        ]
      };
      break;
      
    case 'knowledge_base':
      result.data = {
        relevantStandards: [
          'ISO 21434 - 道路车辆网络安全工程',
          'GB/T 38278 - 智能网联汽车网络安全技术要求',
          'UN R155 - 联合国车联网网络安全法规'
        ],
        relevantArticles: [
          '车联网安全风险评估方法综述',
          '基于ISO 21434的TARA分析实践',
          '车载网关安全设计指南'
        ]
      };
      break;
      
    case 'test_generator':
      result.data = {
        testCasesGenerated: Math.floor(Math.random() * 20) + 5,
        coverageRate: Math.floor(Math.random() * 30) + 70,
        categories: {
          'authentication': Math.floor(Math.random() * 5) + 1,
          'authorization': Math.floor(Math.random() * 5) + 1,
          'input_validation': Math.floor(Math.random() * 5) + 1,
          'encryption': Math.floor(Math.random() * 5) + 1
        }
      };
      break;
      
    default:
      result.data = {
        message: `执行工具 ${mcpTools[toolId].name} 成功`,
        randomValue: Math.floor(Math.random() * 100)
      };
  }
  
  return result;
};

// Format MCP tool output for display
export const formatMcpOutput = (output) => {
  if (typeof output === 'object') {
    return JSON.stringify(output, null, 2);
  }
  
  return String(output);
};

// Check if MCP tool is connected
export const checkToolConnection = async (toolId) => {
  // Mock API call delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Return mock connection status
  return {
    connected: mcpTools[toolId]?.status === 'connected',
    lastChecked: new Date().toISOString()
  };
};

// Connect to MCP tool
export const connectToMcpTool = async (toolId) => {
  // Mock API call delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Update the tool status
  if (mcpTools[toolId]) {
    mcpTools[toolId].status = 'connected';
    ElMessage.success(`已成功连接到 ${mcpTools[toolId].name}`);
    return true;
  }
  
  ElMessage.error(`工具 ${toolId} 不存在`);
  return false;
};

// Disconnect from MCP tool
export const disconnectFromMcpTool = async (toolId) => {
  // Mock API call delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Update the tool status
  if (mcpTools[toolId]) {
    mcpTools[toolId].status = 'disconnected';
    ElMessage.info(`已断开与 ${mcpTools[toolId].name} 的连接`);
    return true;
  }
  
  return false;
};

export default {
  mcpTools,
  executeMcpTool,
  formatMcpOutput,
  checkToolConnection,
  connectToMcpTool,
  disconnectFromMcpTool
}; 