"""
模型管理API端点

提供模型配置管理相关的API接口，包括创建、获取和测试模型配置
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.model import ModelConfig

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="创建模型配置"
)
async def create_model_config(
    model_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的模型配置
    """
    # 验证当前用户是否为管理员
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        # 检查模型名称是否已存在
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.name == model_data["name"])
        )
        existing_model = result.scalars().first()
        
        if existing_model:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="模型配置名称已存在"
            )
        
        # 创建新模型配置
        new_model = ModelConfig(
            name=model_data["name"],
            provider=model_data["provider"],
            api_base=model_data.get("api_base"),
            api_key=model_data["api_key"],
            model_id=model_data.get("model_name", "default"),
            default_parameters=model_data.get("parameters", {}),
            description=model_data.get("description", ""),
            is_active=model_data.get("is_active", True),
            created_by=current_user.id
        )
        
        db.add(new_model)
        await db.commit()
        await db.refresh(new_model)
        
        # 隐藏API密钥
        response_data = {
            "id": new_model.id,
            "name": new_model.name,
            "provider": new_model.provider,
            "api_base": new_model.api_base,
            "model_id": new_model.model_id,
            "default_parameters": new_model.default_parameters,
            "is_active": new_model.is_active
        }
        
        return {
            "success": True,
            "data": response_data,
            "message": "模型配置创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模型配置失败: {str(e)}"
        )


@router.get(
    "/",
    summary="获取模型配置列表"
)
async def get_model_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有模型配置的列表
    """
    try:
        # 查询所有模型配置
        result = await db.execute(select(ModelConfig))
        models = result.scalars().all()
        
        # 构建响应，隐藏API密钥
        model_list = []
        for model in models:
            model_list.append({
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "api_base": model.api_base,
                "model_id": model.model_id,
                "is_active": model.is_active
            })
        
        return {
            "success": True,
            "data": {
                "models": model_list
            },
            "message": "获取模型配置列表成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型配置列表失败: {str(e)}"
        )


@router.get(
    "/{model_id}",
    summary="获取模型配置详情"
)
async def get_model_config(
    model_id: str = Path(..., description="模型配置ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定模型配置的详细信息
    """
    try:
        # 查询模型配置
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == model_id)
        )
        model = result.scalars().first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型配置不存在"
            )
        
        # 构建响应，隐藏API密钥
        response_data = {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "api_base": model.api_base,
            "model_id": model.model_id,
            "default_parameters": model.default_parameters,
            "is_active": model.is_active,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        
        # 管理员可以看到API密钥的部分内容
        if current_user.is_admin:
            api_key = model.api_key
            if api_key and len(api_key) > 8:
                response_data["api_key_preview"] = f"{api_key[:4]}...{api_key[-4:]}"
            elif api_key:
                response_data["api_key_preview"] = "****"
        
        return {
            "success": True,
            "data": response_data,
            "message": "获取模型配置详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型配置详情失败: {str(e)}"
        )


@router.put(
    "/{model_id}",
    summary="更新模型配置"
)
async def update_model_config(
    model_data: Dict[str, Any] = Body(...),
    model_id: str = Path(..., description="模型配置ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新指定的模型配置
    """
    # 验证当前用户是否为管理员
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        # 查询模型配置
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == model_id)
        )
        model = result.scalars().first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型配置不存在"
            )
        
        # 检查模型名称是否已被其他模型使用
        if "name" in model_data and model_data["name"] != model.name:
            name_result = await db.execute(
                select(ModelConfig).where(
                    ModelConfig.name == model_data["name"],
                    ModelConfig.id != model_id
                )
            )
            if name_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="模型配置名称已被使用"
                )
            model.name = model_data["name"]
        
        # 更新其他字段
        if "provider" in model_data:
            model.provider = model_data["provider"]
        if "api_base" in model_data:
            model.api_base = model_data["api_base"]
        if "api_key" in model_data:
            model.api_key = model_data["api_key"]
        if "model_id" in model_data:
            model.model_id = model_data["model_id"]
        if "default_parameters" in model_data:
            model.default_parameters = model_data["default_parameters"]
        if "is_active" in model_data:
            model.is_active = model_data["is_active"]
        
        await db.commit()
        await db.refresh(model)
        
        # 构建响应，隐藏API密钥
        response_data = {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "api_base": model.api_base,
            "model_id": model.model_id,
            "default_parameters": model.default_parameters,
            "is_active": model.is_active,
            "updated_at": model.updated_at
        }
        
        return {
            "success": True,
            "data": response_data,
            "message": "模型配置更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模型配置失败: {str(e)}"
        )


@router.delete(
    "/{model_id}",
    summary="删除模型配置"
)
async def delete_model_config(
    model_id: str = Path(..., description="模型配置ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定的模型配置
    """
    # 验证当前用户是否为管理员
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        # 查询模型配置
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == model_id)
        )
        model = result.scalars().first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型配置不存在"
            )
        
        # 删除模型配置
        await db.delete(model)
        await db.commit()
        
        return {
            "success": True,
            "data": None,
            "message": "模型配置删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模型配置失败: {str(e)}"
        )


@router.post(
    "/{model_id}/test",
    summary="测试模型连接"
)
async def test_model_connection(
    model_id: str = Path(..., description="模型配置ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    测试指定模型的连接
    """
    try:
        # 查询模型配置
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == model_id)
        )
        model = result.scalars().first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型配置不存在"
            )
        
        # 实际测试模型连接
        from app.core.logging import logger
        import asyncio
        import time
        import httpx
        
        start_time = time.time()
        connection_result = {
            "status": "error",
            "message": "未知错误",
            "latency": 0,
            "details": {}
        }
        
        # 根据不同的提供商实现不同的测试方法
        try:
            if model.provider.lower() == "openai":
                connection_result = await test_openai_connection(model)
            elif model.provider.lower() == "anthropic":
                connection_result = await test_anthropic_connection(model)
            elif model.provider.lower() == "azure":
                connection_result = await test_azure_openai_connection(model)
            elif model.provider.lower() == "huggingface":
                connection_result = await test_huggingface_connection(model)
            elif model.provider.lower() == "google":
                connection_result = await test_google_connection(model)
            else:
                # 对于其他提供商，尝试通用的API测试
                connection_result = await test_generic_api_connection(model)
                logger.info(f"通用API连接测试结果: {connection_result}")
        except Exception as e:
            logger.error(f"模型连接测试失败: {str(e)}")
            connection_result = {
                "status": "failed",
                "message": f"连接失败: {str(e)}",
                "latency": int((time.time() - start_time) * 1000),
                "details": {"error": str(e)}
            }
        
        # 更新模型最后测试时间
        model.last_tested = datetime.now()
        model.connection_status = connection_result["status"]
        await db.commit()
        
        return {
            "success": connection_result["status"] == "connected",
            "data": connection_result,
            "message": connection_result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模型连接测试异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试模型连接失败: {str(e)}"
        )


async def test_openai_connection(model):
    """测试OpenAI API连接"""
    import time
    import openai
    
    start_time = time.time()
    client = openai.AsyncOpenAI(
        api_key=model.api_key,
        base_url=model.api_base or "https://api.openai.com/v1"
    )
    
    try:
        # 测试模型列表接口
        response = await client.models.list()
        models_list = [m.id for m in response.data]
        
        # 验证配置的模型是否可用
        model_available = model.model_id in models_list
        
        # 可选：发送一个简单的请求来测试完整功能
        if model_available:
            completion = await client.chat.completions.create(
                model=model.model_id,
                messages=[{"role": "user", "content": "Say 'Connection test successful'"}],
                max_tokens=20
            )
            content = completion.choices[0].message.content
        else:
            # 模型不可用但API连接成功
            content = "API连接成功，但请求的模型不可用"
            
        latency = int((time.time() - start_time) * 1000)
        
        return {
            "status": "connected" if model_available else "warning",
            "message": "连接成功" if model_available else "API连接成功，但请求的模型不可用",
            "latency": latency,
            "details": {
                "available_models": models_list[:10],  # 只返回前10个模型以节省响应大小
                "model_available": model_available,
                "response": content
            }
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "message": f"连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }


async def test_anthropic_connection(model):
    """测试Anthropic API连接"""
    import time
    import httpx
    
    start_time = time.time()
    headers = {
        "x-api-key": model.api_key,
        "content-type": "application/json"
    }
    api_base = model.api_base or "https://api.anthropic.com"
    
    try:
        # 发送一个简单的请求来测试API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base}/v1/messages",
                json={
                    "model": model.model_id,
                    "messages": [{"role": "user", "content": "Say 'Connection test successful'"}],
                    "max_tokens": 20
                },
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            data = response.json()
            content = data.get("content", [{}])[0].get("text", "No response")
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "status": "connected",
                "message": "连接成功",
                "latency": latency,
                "details": {
                    "model": model.model_id,
                    "response": content
                }
            }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "message": f"连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }


async def test_azure_openai_connection(model):
    """测试Azure OpenAI API连接"""
    import time
    import openai
    
    start_time = time.time()
    
    # 解析Azure API配置
    if not model.api_base:
        return {"status": "failed", "message": "Azure OpenAI需要提供API Base URL", "latency": 0}
    
    # 检查参数中是否有资源名称和部署名称
    resource_name = model.default_parameters.get("resource_name", "")
    deployment_name = model.default_parameters.get("deployment_name", model.model_id)
    api_version = model.default_parameters.get("api_version", "2023-05-15")
    
    try:
        client = openai.AsyncAzureOpenAI(
            api_key=model.api_key,
            api_version=api_version,
            azure_endpoint=model.api_base
        )
        
        # 测试接口
        completion = await client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": "Say 'Azure connection test successful'"}],
            max_tokens=20
        )
        
        content = completion.choices[0].message.content
        latency = int((time.time() - start_time) * 1000)
        
        return {
            "status": "connected",
            "message": "Azure OpenAI连接成功",
            "latency": latency,
            "details": {
                "deployment": deployment_name,
                "response": content
            }
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "message": f"Azure OpenAI连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }


async def test_huggingface_connection(model):
    """测试HuggingFace API连接"""
    import time
    import httpx
    
    start_time = time.time()
    api_base = model.api_base or "https://api-inference.huggingface.co/models/"
    headers = {"Authorization": f"Bearer {model.api_key}"}
    
    try:
        # 发送一个简单的请求来测试API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base}/{model.model_id}",
                json={"inputs": "Say 'Connection test successful'"},
                headers=headers,
                timeout=15.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # HuggingFace的响应格式可能因模型类型而异
            content = data[0].get("generated_text", str(data))
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "status": "connected",
                "message": "HuggingFace连接成功",
                "latency": latency,
                "details": {
                    "model": model.model_id,
                    "response": content
                }
            }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "message": f"HuggingFace连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }


async def test_google_connection(model):
    """测试Google AI API连接"""
    import time
    import httpx
    
    start_time = time.time()
    api_base = model.api_base or "https://generativelanguage.googleapis.com/v1beta/models"
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # 调用Google AI API进行测试
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base}/{model.model_id}:generateContent?key={model.api_key}",
                json={
                    "contents": [{"parts": [{"text": "Say 'Connection test successful'"}]}]
                },
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 解析Google AI API的响应
            content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "status": "connected",
                "message": "Google AI连接成功",
                "latency": latency,
                "details": {
                    "model": model.model_id,
                    "response": content
                }
            }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed",
            "message": f"Google AI连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }


async def test_generic_api_connection(model):
    """通用API连接测试"""
    import time
    import httpx
    
    start_time = time.time()
    
    if not model.api_base:
        return {
            "status": "failed",
            "message": "需要提供API基础URL",
            "latency": 0,
            "details": {"error": "未提供API基础URL"}
        }
    
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # 尝试简单的GET请求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                model.api_base,
                headers=headers,
                timeout=10.0
            )
            
            latency = int((time.time() - start_time) * 1000)
            
            # 检查状态码
            if response.status_code < 400:
                return {
                    "status": "connected",
                    "message": "API连接成功",
                    "latency": latency,
                    "details": {
                        "status_code": response.status_code,
                        "response": "API连接成功，但未能验证模型可用性"
                    }
                }
            else:
                return {
                    "status": "warning",
                    "message": f"API连接返回状态码 {response.status_code}",
                    "latency": latency,
                    "details": {
                        "status_code": response.status_code,
                        "response": response.text[:200]  # 截取前200个字符
                    }
                }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "failed", 
            "message": f"连接失败: {str(e)}",
            "latency": latency,
            "details": {"error": str(e)}
        }