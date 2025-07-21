#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Redis Search 模块测试脚本
验证 Redis Search 功能是否正常工作
"""

import redis
import json
from typing import Dict, List, Any

def test_redis_connection():
    """测试 Redis 基本连接"""
    print("🔍 测试 Redis 基本连接...")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Redis 连接成功")
        return r
    except redis.ConnectionError:
        print("❌ Redis 连接失败 - 请确保 Redis 服务正在运行")
        print("💡 启动 Redis: redis-server")
        return None
    except Exception as e:
        print(f"❌ Redis 连接错误: {e}")
        return None

def test_redis_search_module(r: redis.Redis):
    """测试 Redis Search 模块功能"""
    print("\n🔍 测试 Redis Search 模块...")
    
    try:
        # 检查 Redis 版本
        info = r.info()
        redis_version = info.get('redis_version', 'unknown')
        print(f"📊 Redis 版本: {redis_version}")
        
        # 检查是否有 RediSearch 模块
        modules = r.execute_command('MODULE', 'LIST')
        print(f"📋 已加载的模块: {modules}")
        
        # 检查是否有 search 模块
        has_search = any('search' in str(module).lower() for module in modules)
        if has_search:
            print("✅ RediSearch 模块已加载")
            return True
        else:
            print("⚠️ RediSearch 模块未加载")
            print("💡 这可能意味着您需要安装 Redis Stack 或 RediSearch 模块")
            return False
            
    except redis.ResponseError as e:
        if "unknown command" in str(e).lower():
            print("⚠️ Redis 不支持 MODULE 命令 (可能是旧版本)")
            return False
        else:
            print(f"❌ Redis Search 测试失败: {e}")
            return False
    except Exception as e:
        print(f"❌ Redis Search 测试错误: {e}")
        return False

def test_redis_om():
    """测试 Redis OM (Object Mapping) 功能"""
    print("\n🔍 测试 Redis OM 功能...")
    
    try:
        from redis_om import get_redis_connection, JsonModel, Field
        
        # 测试连接
        redis_conn = get_redis_connection(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # 定义一个简单的模型
        class Person(JsonModel):
            name: str = Field(index=True)
            age: int = Field(index=True)
            email: str = Field(index=True)
            
            class Meta:
                database = redis_conn
        
        print("✅ Redis OM 导入成功")
        print("✅ 模型定义成功")
        
        # 测试基本操作
        person = Person(name="张三", age=30, email="zhangsan@example.com")
        person.save()
        print("✅ 数据保存成功")
        
        # 清理测试数据
        person.delete(person.pk)
        print("✅ 数据清理成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ Redis OM 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Redis OM 测试失败: {e}")
        return False

def test_redisvl():
    """测试 RedisVL (Vector Library) 功能"""
    print("\n🔍 测试 RedisVL 功能...")
    
    try:
        import redisvl
        from redisvl.redis.connection import get_redis_connection
        
        print(f"✅ RedisVL 版本: {redisvl.__version__}")
        
        # 测试连接
        redis_conn = get_redis_connection(
            host="localhost",
            port=6379,
            db=0
        )
        
        redis_conn.ping()
        print("✅ RedisVL 连接成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ RedisVL 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ RedisVL 测试失败: {e}")
        return False

def test_basic_search_operations(r: redis.Redis):
    """测试基本的搜索操作"""
    print("\n🔍 测试基本搜索操作...")
    
    try:
        # 使用 Redis 的基本搜索功能
        test_data = {
            "user:1": {"name": "张三", "age": "30", "city": "北京"},
            "user:2": {"name": "李四", "age": "25", "city": "上海"},
            "user:3": {"name": "王五", "age": "35", "city": "广州"}
        }
        
        # 存储测试数据
        for key, data in test_data.items():
            r.hset(key, mapping=data)
        
        print("✅ 测试数据存储成功")
        
        # 使用 SCAN 进行基本搜索
        keys = []
        for key in r.scan_iter(match="user:*"):
            keys.append(key)
        
        print(f"✅ 找到 {len(keys)} 个用户记录")
        
        # 清理测试数据
        for key in keys:
            r.delete(key)
        
        print("✅ 测试数据清理成功")
        return True
        
    except Exception as e:
        print(f"❌ 基本搜索操作失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Redis Search 模块测试")
    print("=" * 50)
    
    # 测试 Redis 连接
    r = test_redis_connection()
    if not r:
        return
    
    # 测试 Redis Search 模块
    has_search_module = test_redis_search_module(r)
    
    # 测试 Redis OM
    redis_om_works = test_redis_om()
    
    # 测试 RedisVL
    redisvl_works = test_redisvl()
    
    # 测试基本搜索操作
    basic_search_works = test_basic_search_operations(r)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   Redis 连接: ✅")
    print(f"   RediSearch 模块: {'✅' if has_search_module else '⚠️'}")
    print(f"   Redis OM: {'✅' if redis_om_works else '❌'}")
    print(f"   RedisVL: {'✅' if redisvl_works else '❌'}")
    print(f"   基本搜索: {'✅' if basic_search_works else '❌'}")
    
    if not has_search_module:
        print("\n💡 建议:")
        print("   如果需要完整的 Redis Search 功能，请考虑:")
        print("   1. 安装 Redis Stack: https://redis.io/docs/stack/")
        print("   2. 或使用 Docker: docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest")
        print("   3. 当前的 Redis OM 和 RedisVL 可以提供基本的搜索和向量功能")

if __name__ == "__main__":
    main()
