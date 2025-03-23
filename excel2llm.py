from excel_processor import process_excel_files
from chat_qwen import call_qwen_api
import os
import pandas as pd
import glob
import json
import re

# 添加正则表达式匹配函数
def extract_json_with_regex(text):
    """
    使用正则表达式从文本中提取JSON对象
    
    Args:
        text (str): 可能包含JSON对象的文本
        
    Returns:
        dict: 提取并解析的JSON对象，如果未找到有效JSON则返回默认值
    """
    # 尝试匹配标准JSON对象
    json_pattern = r'(\{[\s\S]*?"contains_keywords"[\s\S]*?"reasoning"[\s\S]*?"matched_keywords"[\s\S]*?\})'
    matches = re.search(json_pattern, text)
    
    if matches:
        json_str = matches.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"提取的JSON字符串格式不正确: {json_str}")
    
    # 如果无法提取完整JSON，尝试分别提取各个字段
    contains_pattern = r'"contains_keywords"\s*:\s*(true|false)'
    reasoning_pattern = r'"reasoning"\s*:\s*"([^"]*)"'
    keywords_pattern = r'"matched_keywords"\s*:\s*\[(.*?)\]'
    
    contains_match = re.search(contains_pattern, text, re.IGNORECASE)
    reasoning_match = re.search(reasoning_pattern, text)
    keywords_match = re.search(keywords_pattern, text)
    
    result = {}
    if contains_match:
        result["contains_keywords"] = contains_match.group(1).lower() == "true"
    else:
        result["contains_keywords"] = False
        
    if reasoning_match:
        result["reasoning"] = reasoning_match.group(1)
    else:
        result["reasoning"] = "未能提取到解释信息"
        
    if keywords_match:
        # 处理关键词列表
        keywords_str = keywords_match.group(1)
        if keywords_str.strip():
            # 分割并清理关键词列表
            keywords = [k.strip(' "\'') for k in keywords_str.split(',')]
            result["matched_keywords"] = keywords
        else:
            result["matched_keywords"] = []
    else:
        result["matched_keywords"] = []
    
    return result
def process_input_excel_column(directory):
    """
    获取指定目录下所有Excel文件的A列数据，并保留行索引信息
    
    Args:
        directory (str): Excel文件所在目录的路径
        
    Returns:
        dict: 包含所有Excel文件A列数据的字典，格式为：
             {excel文件名: {工作表名: DataFrame}}
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"目录不存在: {directory}")
    
    # 获取目录下所有Excel文件路径
    excel_files = glob.glob(os.path.join(directory, "*.xlsx")) + \
                 glob.glob(os.path.join(directory, "*.xls"))
    
    all_excel_data = {}
    
    for excel_file in excel_files:
        file_name = os.path.basename(excel_file)
        try:
            # 读取Excel文件的所有工作表
            excel = pd.ExcelFile(excel_file)
            sheets_data = {}
            
            for sheet_name in excel.sheet_names:
                # 读取工作表
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 确保A列存在
                if df.shape[1] > 0:
                    # 保存整个DataFrame以便后续更新
                    sheets_data[sheet_name] = df
            
            all_excel_data[file_name] = sheets_data
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {str(e)}")
    
    return all_excel_data

def process_excel(input_directory, data_directory):
    """
    处理Excel文件并调用API，将结果写回Excel文件
    
    Args:
        input_directory (str): 输入Excel文件所在目录的路径
        data_directory (str): 数据清单Excel文件所在目录的路径
    """
    # 获取所有inputs下的Excel数据
    input_data = process_input_excel_column(input_directory)
    
    # 获取data清单B列数据
    data = process_excel_files(data_directory)
    
    # 处理数据并调用API
    for sheet_name, tech_keywords in data.items():
        print(f"\n{sheet_name} 技术关键词清单:")
        print(tech_keywords)
        
        # 遍历每个输入Excel文件
        for input_file, sheets in input_data.items():
            print(f"处理文件: {input_file}")
            
            # 遍历每个工作表
            for sheet_name, df in sheets.items():
                print(f"处理工作表: {sheet_name}")
                
                # 遍历每一行
                for index, row in df.iterrows():
                    # 获取A列的值作为prompt
                    prompt = str(row.iloc[0])
                    if pd.isna(prompt) or prompt.strip() == "":
                        continue
                    
                    # 调用API
                    api_result = call_qwen_api(prompt, tech_keywords)
                    
                    try:
                        # 解析JSON结果
                        # result_json = json.loads(api_result)
                        result_json = extract_json_with_regex(api_result)
                        contains_keywords = result_json.get("contains_keywords", False)
                        reasoning = result_json.get("reasoning", "未提供解释")
                        matched_keywords = result_json.get("matched_keywords", [])
                        
                        # 拼接结果
                        if contains_keywords:
                            result_text = f"包含关键词: {', '.join(matched_keywords)}。{reasoning}"
                        else:
                            result_text = f"不包含关键词。{reasoning}"
                        
                        # 写入B列
                        if df.shape[1] > 1:
                            df.iloc[index, 1] = result_text
                        else:
                            # 如果B列不存在，则添加B列
                            df.insert(1, "API结果", "")
                            df.iloc[index, 1] = result_text
                    
                    except json.JSONDecodeError:
                        print(f"解析JSON失败: {api_result}")
                        df.iloc[index, 1] = "API返回结果解析错误"
                    
                    except Exception as e:
                        print(f"处理行 {index} 时出错: {str(e)}")
                        df.iloc[index, 1] = f"处理错误: {str(e)}"
                
                # 将更新后的DataFrame写回Excel文件
                excel_path = os.path.join(input_directory, input_file)
                with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"工作表 {sheet_name} 处理完成")


# 示例使用
if __name__ == "__main__":
    input_directory = "input"  # 替换为实际的目录路径
    data_directory = "data"  # 替换为实际的目录路径
    process_excel(input_directory, data_directory)