"""
结果聚合器
负责聚合和分析智能体执行的多个步骤结果
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from .llm_client import LLMClientManager


class ResultAggregator:
    """结果聚合器"""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.llm_manager = llm_manager
        self.aggregation_history: List[Dict[str, Any]] = []
    
    async def aggregate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合多个步骤的执行结果
        
        Args:
            results: 步骤执行结果列表
            
        Returns:
            Dict[str, Any]: 聚合后的结果
        """
        if not results:
            return {
                "aggregated_result": "无结果需要聚合",
                "summary": "没有执行任何步骤",
                "total_steps": 0,
                "success_count": 0,
                "failed_count": 0
            }
        
        # 基础统计信息
        total_steps = len(results)
        success_count = sum(1 for r in results if r.get("status") == "completed")
        failed_count = total_steps - success_count
        
        # 分类收集结果
        categorized_results = self._categorize_results(results)
        
        # 提取关键信息
        key_findings = self._extract_key_findings(results)
        
        # 生成智能摘要
        intelligent_summary = await self._generate_intelligent_summary(results, categorized_results)
        
        # 构建聚合结果
        aggregated_result = {
            "aggregation_id": f"agg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "aggregated_at": datetime.utcnow().isoformat(),
            "total_steps": total_steps,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / total_steps if total_steps > 0 else 0,
            "categorized_results": categorized_results,
            "key_findings": key_findings,
            "intelligent_summary": intelligent_summary,
            "raw_results": results,
            "quality_score": self._calculate_quality_score(results)
        }
        
        # 记录聚合历史
        self.aggregation_history.append({
            "aggregation_id": aggregated_result["aggregation_id"],
            "timestamp": aggregated_result["aggregated_at"],
            "total_steps": total_steps,
            "success_rate": aggregated_result["success_rate"]
        })
        
        return aggregated_result
    
    def _categorize_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将结果按类型分类"""
        categories = {
            "analysis_results": [],
            "generation_results": [],
            "tool_results": [],
            "failed_results": []
        }
        
        for result in results:
            if result.get("status") == "failed":
                categories["failed_results"].append(result)
                continue
            
            step_result = result.get("result", {})
            execution_type = step_result.get("execution_type", "unknown")
            
            if execution_type == "tool":
                categories["tool_results"].append(result)
            
            # 根据结果内容进一步分类
            if "analysis_result" in step_result:
                categories["analysis_results"].append(result)
            elif "generation_result" in step_result:
                categories["generation_results"].append(result)
        
        # 移除空分类
        return {k: v for k, v in categories.items() if v}
    
    def _extract_key_findings(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取关键发现"""
        key_findings = []
        
        for result in results:
            if result.get("status") != "completed":
                continue
            
            step_result = result.get("result", {})
            finding = {
                "step_id": result.get("step_id"),
                "type": "analysis",
                "content": step_result.get("message", "执行完成"),
                "importance": "medium"
            }
            key_findings.append(finding)
        
        return key_findings
    
    async def _generate_intelligent_summary(
        self,
        results: List[Dict[str, Any]],
        categorized_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """生成智能摘要"""
        try:
            # 构建结果描述
            result_description = self._build_result_description(results, categorized_results)
            
            system_prompt = """
请分析执行结果并生成摘要，包括执行概况、主要成果、发现的问题和改进建议。
请以JSON格式返回，包含overview、achievements、issues、recommendations字段。
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下执行结果：\n{result_description}"}
            ]
            
            # 调用LLM生成摘要
            response = await self.llm_manager.generate_response(messages)
            
            try:
                summary = json.loads(response.strip())
                return summary
            except json.JSONDecodeError:
                return self._generate_basic_summary(results, categorized_results)
        
        except Exception:
            return self._generate_basic_summary(results, categorized_results)
    
    def _build_result_description(
        self,
        results: List[Dict[str, Any]],
        categorized_results: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """构建结果描述"""
        total_steps = len(results)
        success_count = sum(1 for r in results if r.get("status") == "completed")
        return f"总共执行了 {total_steps} 个步骤，其中 {success_count} 个成功。"
    
    def _generate_basic_summary(
        self,
        results: List[Dict[str, Any]],
        categorized_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """生成基础摘要（不使用LLM）"""
        total_steps = len(results)
        success_count = sum(1 for r in results if r.get("status") == "completed")
        
        return {
            "overview": f"执行了 {total_steps} 个步骤，成功率为 {success_count/total_steps*100:.1f}%",
            "achievements": [f"成功完成了 {success_count} 个步骤"],
            "issues": [],
            "recommendations": ["继续下一阶段任务"],
            "confidence": 0.7
        }
    
    def _calculate_quality_score(self, results: List[Dict[str, Any]]) -> float:
        """计算结果质量分数"""
        if not results:
            return 0.0
        
        success_count = sum(1 for r in results if r.get("status") == "completed")
        return success_count / len(results)
    
    def get_aggregation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取聚合历史
        
        Args:
            limit: 限制返回的记录数
            
        Returns:
            List[Dict[str, Any]]: 聚合历史
        """
        history = sorted(
            self.aggregation_history,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        if limit:
            history = history[:limit]
        
        return history
    
    def clear_history(self) -> None:
        """清除聚合历史"""
        self.aggregation_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取聚合统计信息"""
        if not self.aggregation_history:
            return {
                "total_aggregations": 0,
                "average_success_rate": 0,
                "best_success_rate": 0,
                "worst_success_rate": 0
            }
        
        success_rates = [h["success_rate"] for h in self.aggregation_history]
        
        return {
            "total_aggregations": len(self.aggregation_history),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "best_success_rate": max(success_rates),
            "worst_success_rate": min(success_rates)
        } 