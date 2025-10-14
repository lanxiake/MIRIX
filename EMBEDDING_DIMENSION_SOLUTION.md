# Embedding维度一致性解决方案

## 问题诊断

### 根本原因
MIRIX系统在 `mirix/agent/agent_wrapper.py:116-118` 硬编码了默认embedding配置:
```python
self.client.set_default_embedding_config(
    EmbeddingConfig.default_config("text-embedding-004")  # Google AI 768维
)
```

这导致所有memory agent使用Google AI的text-embedding-004模型(768维),但如果数据库中存在使用其他模型创建的embeddings(如OpenAI的1536维),就会发生维度不匹配错误。

### 错误表现
```
shapes (4096,) and (768,) not aligned: 4096 (dim 0) != 768 (dim 0)
```

虽然向量都被填充到4096维,但实际有效维度不同,导致向量运算失败。

## 解决方案

### 方案1: 确保系统级一致性(推荐)

**优点**:
- 简单直接,不需要数据迁移
- 保证未来不会再出现维度不匹配

**步骤**:

1. **检查当前embedding配置**
   ```bash
   # 查看agent_wrapper.py中的配置
   grep -A 2 "set_default_embedding_config" mirix/agent/agent_wrapper.py
   ```

2. **确认所有agent使用相同配置**

   当前配置(lines 116-118):
   ```python
   self.client.set_default_embedding_config(
       EmbeddingConfig.default_config("text-embedding-004")  # 768维
   )
   ```

   这确保了所有新创建的agent都使用相同的embedding模型。

3. **可选:改为OpenAI模型(如果需要更高维度)**

   如果希望使用OpenAI的1536维模型:
   ```python
   self.client.set_default_embedding_config(
       EmbeddingConfig.default_config("text-embedding-3-small")  # 1536维
   )
   ```

   但这需要迁移现有数据(见方案2)。

### 方案2: 数据迁移(如果历史数据使用不同模型)

**适用场景**: 数据库中存在使用旧模型创建的embeddings

**步骤**:

1. **检查数据库中的embedding维度**
   ```python
   # 连接到PostgreSQL数据库
   import psycopg2
   import numpy as np

   conn = psycopg2.connect(
       host="localhost",
       database="mirix",
       user="mirix",
       password="mirix123"
   )
   cur = conn.cursor()

   # 检查各个记忆表的embedding维度
   tables = [
       'episodic_memory',
       'semantic_memory',
       'procedural_memory',
       'resource_memory'
   ]

   for table in tables:
       cur.execute(f"""
           SELECT id, array_length(details_embedding, 1) as dim
           FROM {table}
           WHERE details_embedding IS NOT NULL
           LIMIT 5
       """)

       rows = cur.fetchall()
       if rows:
           print(f"\n{table}:")
           for row in rows:
               # 计算非零维度(实际有效维度)
               cur.execute(f"SELECT details_embedding FROM {table} WHERE id = %s", (row[0],))
               embedding = np.array(cur.fetchone()[0])
               non_zero_dims = np.count_nonzero(embedding)
               print(f"  ID {row[0]}: 总维度={row[1]}, 非零维度={non_zero_dims}")

   cur.close()
   conn.close()
   ```

2. **如果发现不一致,重新生成embeddings**
   ```python
   # 示例:重新生成所有episodic memory的embeddings
   from mirix.embeddings import embedding_model
   from mirix.schemas.embedding_config import EmbeddingConfig

   # 使用当前的embedding配置
   embed_config = EmbeddingConfig.default_config("text-embedding-004")
   embed_model = embedding_model(embed_config)

   # 重新生成embeddings
   cur.execute("SELECT id, details FROM episodic_memory WHERE details IS NOT NULL")
   rows = cur.fetchall()

   for row_id, details_text in rows:
       new_embedding = embed_model.get_text_embedding(details_text)
       # 填充到4096维
       padded_embedding = np.pad(
           new_embedding,
           (0, 4096 - len(new_embedding)),
           mode='constant'
       ).tolist()

       cur.execute(
           "UPDATE episodic_memory SET details_embedding = %s WHERE id = %s",
           (padded_embedding, row_id)
       )

   conn.commit()
   ```

### 方案3: 配置化embedding模型(长期改进)

**目标**: 允许在配置文件中指定embedding模型,而不是硬编码

**实现步骤**:

1. **修改配置文件schema** (`mirix/configs/mirix_monitor.yaml`):
   ```yaml
   agent_name: mirix
   model_name: gemini-2.0-flash
   is_screen_monitor: true

   # 新增embedding配置
   embedding_config:
     model_name: text-embedding-004
     provider: google_ai
     dimension: 768
   ```

2. **修改AgentWrapper读取配置**:
   ```python
   # mirix/agent/agent_wrapper.py

   # 从配置文件读取embedding配置
   embedding_config_data = config.get('embedding_config', {})
   if embedding_config_data:
       embedding_model_name = embedding_config_data.get('model_name', 'text-embedding-004')
   else:
       embedding_model_name = 'text-embedding-004'  # 默认值

   self.client.set_default_embedding_config(
       EmbeddingConfig.default_config(embedding_model_name)
   )
   ```

3. **添加embedding配置验证**:
   ```python
   # 在系统启动时验证embedding配置一致性
   def validate_embedding_consistency(agent_states):
       configs = []
       for attr_name in ['episodic_memory_agent_state', 'semantic_memory_agent_state',
                         'procedural_memory_agent_state', 'resource_memory_agent_state']:
           agent_state = getattr(agent_states, attr_name, None)
           if agent_state:
               config = agent_state.embedding_config
               configs.append({
                   'agent': attr_name,
                   'model': config.embedding_model,
                   'dimension': config.embedding_dim,
                   'endpoint_type': config.embedding_endpoint_type
               })

       # 检查是否所有配置一致
       if configs:
           first_config = configs[0]
           for config in configs[1:]:
               if config['dimension'] != first_config['dimension']:
                   raise ValueError(
                       f"Embedding dimension mismatch: "
                       f"{config['agent']} uses {config['dimension']}D, "
                       f"but {first_config['agent']} uses {first_config['dimension']}D"
                   )

           logger.info(f"✅ Embedding配置验证通过: 所有agents使用 {first_config['model']} ({first_config['dimension']}维)")

       return configs
   ```

## 当前状态总结

根据代码分析:

1. **当前配置**: Google AI text-embedding-004 (768维)
   - 位置: `mirix/agent/agent_wrapper.py:116-118`
   - 所有新创建的memory agent都使用此配置

2. **向量填充**: 所有向量都被填充到4096维
   - 位置: `mirix/embeddings.py:189-196`
   - 使用`np.pad()`填充零值

3. **潜在风险**:
   - 如果数据库中存在旧的1536维embeddings(OpenAI模型生成)
   - 新的768维查询向量无法正确匹配旧数据
   - 即使都填充到4096维,有效信息位于不同的维度范围

## 推荐操作

### 立即行动:
1. **验证当前状态**: 运行方案2的第1步,检查数据库中实际的embedding维度
2. **确认一致性**: 如果所有embeddings都是768维(非零维度),则系统正常
3. **如果不一致**: 需要执行数据迁移(方案2的第2步)

### 长期改进:
1. 实施方案3,将embedding配置移到配置文件
2. 在系统启动时添加embedding配置验证
3. 在agent创建时记录embedding配置到日志

## 测试验证

创建一个测试脚本验证embedding一致性:

```python
# test_embedding_consistency.py

import asyncio
import sys
sys.path.insert(0, '/opt/MIRIX')

from mirix.agent.agent_wrapper import AgentWrapper

async def test_embedding_consistency():
    # 初始化agent
    agent = AgentWrapper('mirix/configs/mirix_monitor.yaml')

    # 获取所有memory agent的embedding配置
    agent_states = agent.agent_states

    configs = []
    for attr_name in ['episodic_memory_agent_state', 'semantic_memory_agent_state',
                      'procedural_memory_agent_state', 'resource_memory_agent_state',
                      'knowledge_vault_agent_state']:
        agent_state = getattr(agent_states, attr_name, None)
        if agent_state:
            config = agent_state.embedding_config
            configs.append({
                'agent': attr_name,
                'model': config.embedding_model,
                'dimension': config.embedding_dim,
                'endpoint_type': config.embedding_endpoint_type,
                'endpoint': config.embedding_endpoint
            })
            print(f"\n{attr_name}:")
            print(f"  模型: {config.embedding_model}")
            print(f"  维度: {config.embedding_dim}")
            print(f"  端点类型: {config.embedding_endpoint_type}")
            print(f"  端点: {config.embedding_endpoint}")

    # 检查一致性
    if configs:
        first_dim = configs[0]['dimension']
        all_same = all(c['dimension'] == first_dim for c in configs)

        if all_same:
            print(f"\n✅ 所有agents使用相同的embedding维度: {first_dim}")
        else:
            print(f"\n❌ 警告: agents使用不同的embedding维度!")
            for c in configs:
                print(f"  {c['agent']}: {c['dimension']}维")

if __name__ == "__main__":
    asyncio.run(test_embedding_consistency())
```

运行测试:
```bash
cd /opt/MIRIX
python test_embedding_consistency.py
```

## 参考文档

- Google AI Embedding API: https://ai.google.dev/tutorials/embeddings
- OpenAI Embedding API: https://platform.openai.com/docs/guides/embeddings
- PostgreSQL pgvector: https://github.com/pgvector/pgvector
- MIRIX Embedding配置: `mirix/schemas/embedding_config.py`
