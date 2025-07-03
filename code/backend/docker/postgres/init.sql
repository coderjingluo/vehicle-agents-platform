-- PostgreSQL初始化脚本

-- 创建必要的数据库扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 创建只读用户
CREATE ROLE readonly WITH LOGIN PASSWORD 'readonly123' NOSUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;

-- 注释
COMMENT ON ROLE readonly IS '只读用户，用于监控和报表查询';

-- 设置模式搜索路径
ALTER ROLE admin SET search_path TO public;
ALTER ROLE readonly SET search_path TO public;

-- 授予只读用户权限
GRANT CONNECT ON DATABASE automotive_security TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;

-- 创建额外的初始化表（如果需要）
CREATE TABLE IF NOT EXISTS system_info (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 插入系统初始化数据
INSERT INTO system_info (key, value, description) 
VALUES 
('db_version', '1.0.0', '数据库版本'),
('init_date', CURRENT_TIMESTAMP::TEXT, '数据库初始化日期'),
('app_name', '车联网安全测试生命周期管理平台', '应用名称')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value, 
    updated_at = CURRENT_TIMESTAMP;

-- 创建触发器函数来自动更新updated_at
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为system_info表添加触发器
DROP TRIGGER IF EXISTS set_timestamp ON system_info;
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON system_info
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp(); 