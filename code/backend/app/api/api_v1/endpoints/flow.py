"""
KunlunSec AI Platform - 执行流 API

提供执行流的管理和执行API接口。
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.logging import logger
from app.flow.flow_manager import FlowManager
from app.services.flow_service import get_flow_manager


router = APIRouter()


class CreateFlowRequest(BaseModel):
    """创建流程请求"""
    flow_type: str = Field(..., description="流程类型，例如'tara', 'testcase', 'automation', 'report', 'dynamic'")
    name: Optional[str] = Field(None, description="流程名称")
    description: Optional[str] = Field(None, description="流程描述")
    use_langgraph: bool = Field(True, description="是否使用LangGraph实现")
    config: Dict[str, Any] = Field(default_factory=dict, description="流程配置")


class FlowResponse(BaseModel):
    """流程响应"""
    id: str = Field(..., description="流程ID")
    name: str = Field(..., description="流程名称")
    description: str = Field(..., description="流程描述")
    type: str = Field(..., description="流程类型")
    status: str = Field(..., description="流程状态")
    is_graph_based: bool = Field(..., description="是否基于图的流程")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class FlowStatusResponse(BaseModel):
    """流程状态响应"""
    id: str = Field(..., description="流程ID")
    status: str = Field(..., description="流程状态")
    name: str = Field(..., description="流程名称")
    type: str = Field(..., description="流程类型")
    error: Optional[str] = Field(None, description="错误信息")


class ExecuteFlowRequest(BaseModel):
    """执行流程请求"""
    input_data: Dict[str, Any] = Field(..., description="输入数据")


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: CreateFlowRequest,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    创建执行流
    """
    try:
        # 确保环境变量中有API密钥
        import os
        if not os.environ.get("OPENAI_API_KEY") and request.use_langgraph:
            # 设置一个默认的测试密钥（这里用占位符，实际应用中应从配置中获取）
            os.environ["OPENAI_API_KEY"] = "sk-placeholder-for-testing-only"
            from app.core.logging import logger
            logger.warning("未设置OPENAI_API_KEY环境变量，使用占位符密钥。请在生产环境中正确配置API密钥。")
        
        flow_id = await flow_manager.create_flow(
            flow_type=request.flow_type,
            name=request.name,
            description=request.description,
            use_langgraph=request.use_langgraph,
            **request.config
        )
        
        # 获取创建的流程状态
        flow_status = flow_manager.get_flow_status(flow_id)
        
        # 返回标准格式的响应
        return {
            "success": True,
            "data": {
                "id": flow_id,
                "name": flow_status.get("name", request.name or f"Flow {flow_id[:8]}"),
                "type": request.flow_type,
                "status": flow_status.get("status", "created")
            },
            "message": "执行流创建成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[FlowResponse])
def list_flows(
    flow_type: Optional[str] = None,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    列出所有执行流
    """
    try:
        flows = flow_manager.list_flows(flow_type)
        return flows
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{flow_id}/execute", response_model=Dict[str, Any])
async def execute_flow(
    flow_id: str,
    request: ExecuteFlowRequest,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    执行指定的执行流
    """
    try:
        # 获取流程信息
        flow_info = flow_manager.get_flow_status(flow_id)
        flow_type = flow_info.get("type")
        
        # 准备输入数据
        input_data = request.input_data
        
        # 对于动态流程，确保有task参数
        if flow_type == "dynamic" and "task" not in input_data:
            # 如果没有提供task参数，尝试从input_data中构建任务描述
            if input_data:
                task_description = "执行以下任务:\n"
                for key, value in input_data.items():
                    if isinstance(value, str):
                        task_description += f"- {key}: {value}\n"
                    else:
                        task_description += f"- {key}: {str(value)[:100]}...\n"
                input_data["task"] = task_description
            else:
                raise ValueError("动态流程需要提供task参数")
        
        # 执行流程
        result = await flow_manager.execute_flow(flow_id, **input_data)
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{flow_id}/result", response_model=Dict[str, Any])
def get_flow_result(
    flow_id: str,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    获取指定执行流的结果
    """
    try:
        result = flow_manager.get_flow_result(flow_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{flow_id}/visualization", response_model=Dict[str, str])
def get_flow_visualization(
    flow_id: str,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    获取指定执行流的可视化表示
    """
    try:
        visualization = flow_manager.get_flow_visualization(flow_id)
        return {"visualization": visualization}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{flow_id}", response_model=Dict[str, bool])
def delete_flow(
    flow_id: str,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    删除指定的执行流
    """
    try:
        success = flow_manager.delete_flow(flow_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 
    
@router.get("/{flow_id}", response_model=Dict[str, Any])
def get_flow_status(
    flow_id: str,
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    获取指定执行流的状态
    """
    try:
        status = flow_manager.get_flow_status(flow_id)
        logger.info(f"获取执行流状态: {status}")
        return status
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))