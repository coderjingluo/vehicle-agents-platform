"""
知识库智能体 - 项目知识自动归档和持续学习优化

该智能体具备以下核心能力：
1. 项目知识自动归档和分类
2. 智能知识检索和推荐
3. 持续学习和知识库优化
4. 最佳实践提取和分享
5. 专家经验知识化管理
"""

from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentStep, AgentPlan
from app.models.task import AgentType


class KnowledgeAgent(BaseAgent):
    """知识库智能体"""
    
    def __init__(self):
        agent_id = str(uuid.uuid4())
        super().__init__(
            agent_id=agent_id,
            name="知识库智能体",
            description="项目知识自动归档和持续学习优化"
        )
        self.agent_type = AgentType.KNOWLEDGE_BASE
        self.knowledge_categories = {
            "threats": "威胁情报和攻击模式",
            "vulnerabilities": "漏洞库和利用方式",
            "countermeasures": "缓解措施和安全控制",
            "test_cases": "测试用例库和测试方法",
            "compliance": "合规要求和标准解读",
            "best_practices": "最佳实践和经验分享",
            "tools": "工具使用和配置指南",
            "lessons_learned": "经验教训和改进建议"
        }
        
    def get_agent_type(self) -> str:
        return "knowledge_base"
    
    async def execute(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行知识库管理流程"""
        try:
            self.logger.info(f"开始执行知识库管理: {user_request}")
            
            # 生成计划
            plan = await self.generate_plan(user_request, context)
            
            results = {}
            all_steps_results = []
            
            # 逐步执行计划
            for step in plan.steps:
                step.status = "running"
                step.started_at = datetime.utcnow()
                
                # 执行步骤
                context_dict = context or {}
                context_dict.update({
                    "previous_results": results,
                    "plan": plan.to_dict()
                })
                step_result = await self.execute_step(step, context_dict)
                
                # 更新步骤状态
                step.status = "completed" if step_result.get("success", False) else "failed"
                step.completed_at = datetime.utcnow()
                step.result = step_result
                
                # 保存步骤结果
                if step.status == "completed":
                    results[step.name] = step_result.get("result", {})
                    all_steps_results.append(step_result)
                
                # 更新计划进度
                plan.update_progress()
            
            # 聚合结果
            final_result = await self.aggregate_results(all_steps_results, context or {})
            
            return {
                "success": True,
                "plan": plan.to_dict(),
                "result": final_result,
                "agent_type": self.get_agent_type(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"知识库管理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.get_agent_type(),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def aggregate_results(self, step_results: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """聚合所有步骤的结果"""
        knowledge_items = []
        knowledge_categories = {}
        knowledge_relations = []
        
        # 提取知识项目
        for result in step_results:
            if "result" in result and isinstance(result["result"], dict):
                if "knowledge_items" in result["result"]:
                    knowledge_items.extend(result["result"]["knowledge_items"])
                if "categories" in result["result"]:
                    knowledge_categories.update(result["result"]["categories"])
                if "relations" in result["result"]:
                    knowledge_relations.extend(result["result"]["relations"])
        
        return {
            "knowledge_items": knowledge_items,
            "knowledge_categories": knowledge_categories,
            "knowledge_relations": knowledge_relations,
            "total_items": len(knowledge_items),
            "total_categories": len(knowledge_categories),
            "total_relations": len(knowledge_relations),
            "generation_time": datetime.utcnow().isoformat()
        }
    
    async def _generate_plan(self, user_request: str, context: Dict[str, Any] = None) -> AgentPlan:
        """生成知识库管理计划"""
        default_steps = [
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="知识提取",
                description="从项目执行过程中提取有价值的知识和经验",
                tool_name="knowledge_extractor",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="知识分类",
                description="对提取的知识进行分类和标签化管理",
                tool_name="knowledge_classifier",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="知识关联",
                description="建立知识条目之间的关联关系",
                tool_name="knowledge_linker",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="知识优化",
                description="优化知识库结构和内容质量",
                tool_name="knowledge_optimizer",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="知识推荐",
                description="基于用户需求推荐相关知识",
                tool_name="knowledge_recommender",
                parameters={},
                dependencies=[]
            )
        ]
        
        return AgentPlan(
            plan_id=str(uuid.uuid4()),
            description="知识库管理和优化流程",
            steps=default_steps
        )
    
    async def execute_step(self, step: AgentStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行知识库管理步骤"""
        try:
            self.logger.info(f"执行知识库管理步骤: {step.name}")
            
            if "提取" in step.name:
                return await self._extract_knowledge(step, context)
            elif "分类" in step.name:
                return await self._classify_knowledge(step, context)
            elif "关联" in step.name:
                return await self._link_knowledge(step, context)
            elif "优化" in step.name:
                return await self._optimize_knowledge(step, context)
            elif "推荐" in step.name:
                return await self._recommend_knowledge(step, context)
            else:
                return await self._execute_general_step(step, context)
                
        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.step_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _extract_knowledge(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取项目知识"""
        prompt = f"""
作为知识管理专家，从项目执行过程中提取有价值的知识和经验。

项目数据:
{json.dumps(context, ensure_ascii=False, indent=2)}

请提取以下类型的知识：

1. **威胁情报知识**
   - 新发现的威胁模式
   - 攻击技术和方法
   - 威胁行为者特征
   - 威胁趋势分析

2. **漏洞知识**
   - 发现的漏洞类型
   - 漏洞利用方式
   - 漏洞修复方法
   - 漏洞影响评估

3. **测试方法知识**
   - 有效的测试策略
   - 创新的测试技术
   - 工具使用技巧
   - 测试覆盖方法

4. **缓解措施知识**
   - 成功的防护措施
   - 有效的安全控制
   - 应急响应经验
   - 风险缓解策略

5. **合规性知识**
   - 标准解读和应用
   - 认证准备经验
   - 合规检查方法
   - 法规更新趋势

6. **最佳实践**
   - 项目管理经验
   - 团队协作方法
   - 质量保证措施
   - 效率提升技巧

7. **经验教训**
   - 失败案例分析
   - 成功要素总结
   - 风险预警信号
   - 改进建议

对每个知识条目，请提供：
- 知识标题和描述
- 知识类型和分类
- 适用场景和条件
- 置信度和来源
- 关键标签

以JSON格式返回提取的知识条目。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        knowledge_extraction = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": knowledge_extraction,
            "step_id": step.id,
            "extracted_count": len(knowledge_extraction.get("knowledge_items", [])),
            "extraction_type": "comprehensive_knowledge",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _classify_knowledge(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """分类知识条目"""
        prompt = f"""
作为知识分类专家，对提取的知识进行结构化分类和标签管理。

提取的知识:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请建立完整的知识分类体系：

1. **一级分类 (主要领域)**
   - 威胁情报 (Threat Intelligence)
   - 漏洞管理 (Vulnerability Management)
   - 安全测试 (Security Testing)
   - 风险管理 (Risk Management)
   - 合规性 (Compliance)
   - 最佳实践 (Best Practices)

2. **二级分类 (具体类型)**
   - 威胁情报 → 攻击模式、威胁行为者、漏洞利用
   - 安全测试 → 测试方法、工具使用、用例设计
   - 风险管理 → 风险评估、缓解措施、应急响应

3. **标签体系**
   - 技术标签: API安全、Web安全、移动安全、IoT安全
   - 行业标签: 汽车、金融、医疗、能源
   - 标准标签: ISO21434、SAEJ3061、NIST、GDPR
   - 难度标签: 初级、中级、高级、专家

4. **知识属性**
   - 重要性等级 (Critical/High/Medium/Low)
   - 时效性 (永久/长期/中期/短期)
   - 可信度 (验证/可靠/一般/待验证)
   - 应用范围 (通用/行业/项目/团队)

5. **关系映射**
   - 前置知识依赖
   - 相关知识推荐
   - 后续深入学习
   - 实践应用指导

6. **检索优化**
   - 关键词索引
   - 全文搜索支持
   - 语义搜索标记
   - 相似度计算

以JSON格式返回完整的知识分类结构。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        knowledge_classification = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": knowledge_classification,
            "step_id": step.id,
            "classification_type": "hierarchical_taxonomy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _link_knowledge(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """建立知识关联"""
        prompt = f"""
作为知识图谱专家，建立知识条目之间的关联关系。

分类后的知识:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请建立知识关联图谱：

1. **关联类型定义**
   - 因果关系: A导致B (威胁 → 漏洞 → 风险)
   - 包含关系: A包含B (标准 → 要求 → 控制措施)
   - 相似关系: A类似B (相似威胁、相似解决方案)
   - 依赖关系: A依赖B (技术依赖、流程依赖)
   - 对立关系: A对抗B (攻击 vs 防护)

2. **知识链构建**
   - 威胁识别 → 风险评估 → 测试设计 → 缓解措施
   - 标准要求 → 测试方法 → 验证过程 → 合规证明
   - 问题发现 → 根因分析 → 解决方案 → 最佳实践

3. **关联强度评估**
   - 强关联 (0.8-1.0): 直接相关，必须了解
   - 中关联 (0.5-0.7): 间接相关，建议了解
   - 弱关联 (0.2-0.4): 背景相关，参考了解

4. **知识路径设计**
   - 新手学习路径: 基础 → 进阶 → 高级
   - 专题深化路径: 特定领域的深度学习
   - 问题解决路径: 从问题到解决方案
   - 项目应用路径: 理论到实践的应用

5. **动态关联更新**
   - 基于使用频率调整关联强度
   - 根据反馈优化推荐关系
   - 随时间演进更新关联关系

6. **可视化图谱**
   - 节点属性 (知识类型、重要性、时效性)
   - 边属性 (关联类型、强度、方向)
   - 布局算法 (层次布局、力导向布局)

以JSON格式返回知识关联图谱结构。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        knowledge_linking = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": knowledge_linking,
            "step_id": step.id,
            "linking_type": "knowledge_graph",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _optimize_knowledge(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化知识库"""
        prompt = f"""
作为知识库优化专家，对知识库进行质量优化和结构改进。

知识关联图谱:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请进行全面的知识库优化：

1. **内容质量优化**
   - 重复内容去重
   - 过时内容更新
   - 错误内容修正
   - 缺失内容补充
   - 模糊内容澄清

2. **结构优化**
   - 分类体系精简
   - 层级结构调整
   - 标签系统优化
   - 关联关系简化

3. **检索优化**
   - 关键词权重调整
   - 搜索索引优化
   - 相似度算法改进
   - 推荐算法优化

4. **用户体验优化**
   - 导航结构改进
   - 内容展示优化
   - 交互流程简化
   - 响应速度提升

5. **维护自动化**
   - 内容质量监控
   - 使用统计分析
   - 反馈收集处理
   - 定期更新提醒

6. **性能优化**
   - 数据存储优化
   - 查询性能优化
   - 缓存策略设计
   - 负载分布优化

7. **智能化增强**
   - 自动摘要生成
   - 智能问答支持
   - 个性化推荐
   - 学习路径规划

以JSON格式返回知识库优化方案。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        knowledge_optimization = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": knowledge_optimization,
            "step_id": step.id,
            "optimization_type": "comprehensive_improvement",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _recommend_knowledge(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """推荐相关知识"""
        prompt = f"""
作为智能推荐专家，基于用户需求和当前任务推荐相关知识。

优化后的知识库:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

用户当前任务: {context.get('user_task', '未指定')}

请提供智能知识推荐：

1. **任务相关推荐**
   - 直接相关的知识条目
   - 支撑性知识内容
   - 参考案例和经验
   - 相关工具和方法

2. **学习路径推荐**
   - 当前水平评估
   - 学习目标设定
   - 渐进式学习路径
   - 实践应用建议

3. **问题解决推荐**
   - 常见问题FAQ
   - 故障排除指南
   - 最佳实践案例
   - 专家经验分享

4. **技能提升推荐**
   - 技能差距分析
   - 培训资源推荐
   - 认证路径建议
   - 实战项目推荐

5. **趋势关注推荐**
   - 新技术发展
   - 标准更新动态
   - 威胁情报更新
   - 行业最佳实践

6. **协作推荐**
   - 相关团队经验
   - 专家咨询建议
   - 外部资源推荐
   - 社区交流平台

7. **个性化调整**
   - 基于使用历史的推荐
   - 兴趣偏好考虑
   - 学习风格适配
   - 时间安排优化

以JSON格式返回个性化知识推荐。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        knowledge_recommendation = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": knowledge_recommendation,
            "step_id": step.id,
            "recommendation_type": "personalized_intelligent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_general_step(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用步骤"""
        prompt = f"""
作为知识库管理专家，执行以下任务：

任务描述: {step.description}
预期输出: {step.expected_output}
成功标准: {step.success_criteria}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

以JSON格式返回结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "knowledge_base"}
        )
        
        result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": result,
            "step_id": step.id,
            "execution_type": "general",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "raw_response": response,
                "parsed": False,
                "error": "Failed to parse JSON response"
            } 