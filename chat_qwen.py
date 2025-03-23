import os
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

def build_keyword_check_prompt(tech_keywords, user_input):
    return f"""
                你是一个严格的关键词检测器，按以下规则处理输入：

                任务
                1. 分析输入文本，识别是否匹配以下列表的词汇：{tech_keywords}
                2. 当文本明确提及列表中的关键词时，判定存在
                3. 若是输入文本中存在相近的关键词表达，则需要根据上下文判断是否存在
                4. 返回包含以下字段的严格JSON格式：
                - "contains_keywords": 布尔值
                - "reasoning": 说明判定依据及位置，如果是明确提及，示例："文本第2段明确提及'AI'"。
                               若是相近的表达，判断输入文本是和哪个关键词相近，示例："文本第2段明确提及'AI'，与'人工智能'相近"
                - "matched_keywords": 数组，仅包含列表中的匹配词

                强制规则
                - 禁止输出列表外的技术词
                - 必须标注具体位置（段落/句子）

                输入文本
                {user_input}

                必须返回严格JSON格式
                ```json
                {{ 
                "contains_keywords": <布尔值>,
                "reasoning": "<判定理由>", 
                "matched_keywords": [<严格匹配的词>]
                }}
                ```
                """

def call_thinking_qwen_api(prompt: str, 
                           tech_keywords: list[str],
                           model: str = "qwq-32b", 
                           temperature: float = 0.7,
                           max_tokens: int = 8096,
                           api_key: Optional[str] = None
                           ) -> str:
    """
    调用千问大模型API获取文本生成结果
    
    参数:
        prompt: 输入的提示文本
        model: 使用的模型，默认为"qwq-32b"
        temperature: 温度参数，控制生成的随机性，默认0.7
        max_tokens: 最大生成的token数量，默认8096
        api_key: API密钥，如果为None则从.env文件中获取
        
    返回:
        生成的文本响应
        
    异常:
        可能抛出请求异常或API错误
    """

    # 加载环境变量
    load_dotenv()
    # 获取API密钥
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 验证API密钥是否存在
    if not dashscope_api_key:
        raise ValueError("API密钥未设置。请通过参数提供api_key或在.env文件中设置DASHSCOPE_API_KEY")

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=dashscope_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复

    input_prompt = build_keyword_check_prompt(tech_keywords, prompt)
    # 创建聊天完成请求
    completion = client.chat.completions.create(
        model=model,  # 此处以 qwq-32b 为例，可按需更换模型名称
        messages=[
            {   "role": "user", "content": input_prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        # QwQ 模型仅支持流式输出方式调用
        stream=True,
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )

    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")

    for chunk in completion:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content != None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if delta.content != "" and is_answering is False:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                print(delta.content, end='', flush=True)
                answer_content += delta.content
                return answer_content   

def call_qwen_api(prompt: str, 
                  tech_keywords: list[str],
                  model: str = "qwen-max", 
                  temperature: float = 0.5,
                  max_tokens: int = 8096,
                  api_key: Optional[str] = None,
                  ) -> str:
    """
    调用千问大模型API获取文本生成结果
    
    参数:
        prompt: 输入的提示文本
        model: 使用的模型，默认为"qwen-max"
        temperature: 温度参数，控制生成的随机性，默认0.5
        max_tokens: 最大生成的token数量，默认8096
        api_key: API密钥，如果为None则从.env文件中获取
        env_path: 可选的.env文件路径
        
    返回:
        生成的文本响应
        
    异常:
        可能抛出请求异常或API错误
    """
    # 加载环境变量
    load_dotenv()
    # 获取API密钥
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 验证API密钥是否存在
    if not dashscope_api_key:
        raise ValueError("API密钥未设置。请通过参数提供api_key或在.env文件中设置DASHSCOPE_API_KEY")

    client = OpenAI(
        api_key=dashscope_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    input_prompt = build_keyword_check_prompt(tech_keywords, prompt)

    completion = client.chat.completions.create(
        model=model, # 此处以qwen-max为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[
            {'role': 'user', 'content': input_prompt}],
        temperature=temperature,
        max_tokens=max_tokens
        )
        
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content


if __name__ == "__main__":
    # 测试调用
    prompt = "你好，世界！"
    tech_keywords = ["AI", "机器学习", "深度学习"]
    
    try:
        # 从.env文件加载API密钥
        result = call_qwen_api(prompt, tech_keywords)
        print(result)
    except ValueError as e:
        print(f"错误: {e}")
        print("请确保已在.env文件中设置DASHSCOPE_API_KEY或通过参数提供api_key")