"""
模型配置管理API路由

提供多模型配置、连接测试、使用统计等功能的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_async_session
from app.models.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelConfigList,
    ModelProvider,
    ModelType,
    ModelStatus,
    ModelTestRequest,
    ModelTestResponse,
    ModelUsageStats,
    ModelProviderInfo
)
from app.services.model_config_service import ModelConfigService
from loguru import logger

router = APIRouter(prefix="/models", tags=["model-config"])


@router.post("/", response_model=ModelConfigResponse)
async def create_model_config(
    config_data: ModelConfigCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """创建模型配置"""
    try:
        service = ModelConfigService()
        model_config = await service.create_model_config(config_data, db)
        return ModelConfigResponse.model_validate(model_config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建模型配置API错误: {e}")
        raise HTTPException(status_code=500, detail="创建模型配置失败")


@router.get("/", response_model=ModelConfigList)
async def list_model_configs(
    provider: Optional[ModelProvider] = Query(None, description="按提供商筛选"),
    model_type: Optional[ModelType] = Query(None, description="按模型类型筛选"),
    status: Optional[ModelStatus] = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_async_session)
):
    """获取模型配置列表"""
    try:
        service = ModelConfigService()
        model_list = await service.list_model_configs(
            db, 
            provider=provider,
            model_type=model_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return model_list
    except Exception as e:
        logger.error(f"获取模型配置列表API错误: {e}")
        raise HTTPException(status_code=500, detail="获取模型配置列表失败")


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """获取模型配置详情"""
    try:
        service = ModelConfigService()
        model_config = await service.get_model_config(config_id, db)
        
        if not model_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        return ModelConfigResponse.model_validate(model_config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型配置API错误: {e}")
        raise HTTPException(status_code=500, detail="获取模型配置失败")


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: str,
    update_data: ModelConfigUpdate,
    db: AsyncSession = Depends(get_async_session)
):
    """更新模型配置"""
    try:
        service = ModelConfigService()
        model_config = await service.update_model_config(config_id, update_data, db)
        
        if not model_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        return ModelConfigResponse.model_validate(model_config)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新模型配置API错误: {e}")
        raise HTTPException(status_code=500, detail="更新模型配置失败")


@router.delete("/{config_id}")
async def delete_model_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """删除模型配置"""
    try:
        service = ModelConfigService()
        success = await service.delete_model_config(config_id, db)
        
        if not success:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        return {"message": "模型配置删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模型配置API错误: {e}")
        raise HTTPException(status_code=500, detail="删除模型配置失败")


@router.post("/{config_id}/test", response_model=ModelTestResponse)
async def test_model_connection(
    config_id: str,
    test_request: ModelTestRequest = ModelTestRequest(),
    db: AsyncSession = Depends(get_async_session)
):
    """测试模型连接"""
    try:
        service = ModelConfigService()
        test_response = await service.test_model_connection(config_id, test_request, db)
        return test_response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"测试模型连接API错误: {e}")
        raise HTTPException(status_code=500, detail="测试模型连接失败")


@router.get("/{config_id}/stats", response_model=ModelUsageStats)
async def get_model_usage_stats(
    config_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_async_session)
):
    """获取模型使用统计"""
    try:
        service = ModelConfigService()
        stats = await service.get_model_usage_stats(config_id, db, days=days)
        
        if not stats:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型统计API错误: {e}")
        raise HTTPException(status_code=500, detail="获取模型统计失败")


@router.get("/providers/{provider}", response_model=ModelProviderInfo)
async def get_provider_info(provider: ModelProvider):
    """获取模型提供商信息"""
    try:
        service = ModelConfigService()
        provider_info = await service.get_provider_info(provider)
        
        if not provider_info:
            raise HTTPException(status_code=404, detail="不支持的模型提供商")
        
        return provider_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提供商信息API错误: {e}")
        raise HTTPException(status_code=500, detail="获取提供商信息失败")


@router.get("/defaults/{model_type}", response_model=ModelConfigResponse)
async def get_default_model(
    model_type: ModelType,
    db: AsyncSession = Depends(get_async_session)
):
    """获取指定类型的默认模型"""
    try:
        service = ModelConfigService()
        default_model = await service.get_default_model(model_type, db)
        
        if not default_model:
            raise HTTPException(
                status_code=404, 
                detail=f"没有配置 {model_type.value} 类型的默认模型"
            )
        
        return ModelConfigResponse.model_validate(default_model)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取默认模型API错误: {e}")
        raise HTTPException(status_code=500, detail="获取默认模型失败")


# 演示和快速配置API
@router.post("/demo/quick-setup")
async def quick_setup_models(
    db: AsyncSession = Depends(get_async_session)
):
    """快速设置演示模型配置"""
    try:
        service = ModelConfigService()
        
        # 创建演示模型配置
        demo_configs = [
            {
                "name": "openai-gpt4-demo",
                "display_name": "OpenAI GPT-4 (演示)",
                "description": "OpenAI GPT-4 演示配置",
                "provider": ModelProvider.OPENAI,
                "model_type": ModelType.CHAT,
                "model_name": "gpt-4-turbo",
                "api_key": "demo-key-replace-with-real",
                "is_default": True
            },
            {
                "name": "openai-embedding-demo",
                "display_name": "OpenAI Embedding (演示)",
                "description": "OpenAI 嵌入模型演示配置",
                "provider": ModelProvider.OPENAI,
                "model_type": ModelType.EMBEDDING,
                "model_name": "text-embedding-ada-002",
                "api_key": "demo-key-replace-with-real",
                "is_default": True
            },
            {
                "name": "deepseek-chat-demo",
                "display_name": "DeepSeek Chat (演示)",
                "description": "DeepSeek 对话模型演示配置",
                "provider": ModelProvider.DEEPSEEK,
                "model_type": ModelType.CHAT,
                "model_name": "deepseek-chat",
                "api_key": "demo-key-replace-with-real",
                "priority": 2
            }
        ]
        
        created_configs = []
        for config_data in demo_configs:
            try:
                # 检查是否已存在
                existing_configs, _ = await service.list_model_configs(db, limit=1000)
                existing_names = [config.name for config in existing_configs.models]
                
                if config_data["name"] not in existing_names:
                    from pydantic import SecretStr
                    create_data = ModelConfigCreate(
                        name=config_data["name"],
                        display_name=config_data["display_name"],
                        description=config_data["description"],
                        provider=config_data["provider"],
                        model_type=config_data["model_type"],
                        model_name=config_data["model_name"],
                        api_key=SecretStr(config_data["api_key"]),
                        is_default=config_data.get("is_default", False),
                        priority=config_data.get("priority", 0)
                    )
                    
                    model_config = await service.create_model_config(create_data, db)
                    created_configs.append(ModelConfigResponse.model_validate(model_config))
                else:
                    logger.info(f"模型配置已存在，跳过: {config_data['name']}")
                    
            except Exception as e:
                logger.warning(f"创建演示模型配置失败 {config_data['name']}: {e}")
                continue
        
        return {
            "message": f"成功创建 {len(created_configs)} 个演示模型配置",
            "created_configs": created_configs,
            "note": "请替换API密钥为真实值后进行测试"
        }
        
    except Exception as e:
        logger.error(f"快速设置演示模型API错误: {e}")
        raise HTTPException(status_code=500, detail=f"快速设置失败: {str(e)}")


@router.post("/{config_id}/demo/chat")
async def demo_chat_with_model(
    config_id: str,
    message: str = Query(..., description="聊天消息"),
    db: AsyncSession = Depends(get_async_session)
):
    """演示与模型对话"""
    try:
        # 首先测试模型连接
        service = ModelConfigService()
        test_request = ModelTestRequest(test_message=message)
        test_response = await service.test_model_connection(config_id, test_request, db)
        
        if test_response.success:
            return {
                "success": True,
                "message": message,
                "response": test_response.response,
                "model_id": test_response.model_id,
                "response_time": test_response.response_time,
                "token_count": test_response.token_count
            }
        else:
            return {
                "success": False,
                "message": message,
                "error": test_response.error,
                "model_id": test_response.model_id
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"演示对话API错误: {e}")
        raise HTTPException(status_code=500, detail="演示对话失败")


@router.get("/demo/providers")
async def list_supported_providers():
    """获取支持的模型提供商列表"""
    try:
        service = ModelConfigService()
        providers = []
        
        for provider in ModelProvider:
            provider_info = await service.get_provider_info(provider)
            if provider_info:
                providers.append(provider_info.model_dump())
        
        return {
            "supported_providers": providers,
            "total_count": len(providers)
        }
        
    except Exception as e:
        logger.error(f"获取支持的提供商API错误: {e}")
        raise HTTPException(status_code=500, detail="获取支持的提供商失败")


@router.post("/batch-test")
async def batch_test_models(
    model_ids: List[str],
    test_message: str = "Hello, this is a test message.",
    db: AsyncSession = Depends(get_async_session)
):
    """批量测试多个模型"""
    try:
        service = ModelConfigService()
        test_request = ModelTestRequest(test_message=test_message)
        
        results = []
        for config_id in model_ids:
            try:
                test_response = await service.test_model_connection(config_id, test_request, db)
                results.append({
                    "model_id": config_id,
                    "success": test_response.success,
                    "response": test_response.response,
                    "error": test_response.error,
                    "response_time": test_response.response_time
                })
            except Exception as e:
                results.append({
                    "model_id": config_id,
                    "success": False,
                    "error": str(e),
                    "response_time": 0.0
                })
        
        successful_tests = sum(1 for r in results if r["success"])
        
        return {
            "test_results": results,
            "total_tested": len(results),
            "successful": successful_tests,
            "failed": len(results) - successful_tests,
            "success_rate": successful_tests / len(results) if results else 0
        }
        
    except Exception as e:
        logger.error(f"批量测试模型API错误: {e}")
        raise HTTPException(status_code=500, detail="批量测试失败") 