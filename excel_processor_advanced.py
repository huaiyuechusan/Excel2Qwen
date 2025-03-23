import os
import pandas as pd

def process_excel_files(directory_path):
    """
    处理指定目录下的所有Excel文件，提取每个文件所有sheet的B列数据
    
    参数:
        directory_path (str): Excel文件所在的目录路径
        
    返回:
        dict: 包含所有Excel文件的所有sheet的B列数据
              结构为 {文件名: {sheet名: [B列数据]}}
    """
    # 初始化一个嵌套字典，用于存储所有文件的所有sheet的B列数据
    all_data = {}
    
    # 获取目录中所有Excel文件
    excel_files = [f for f in os.listdir(directory_path) 
                  if f.endswith('.xlsx') or f.endswith('.xls')]
    
    # 遍历所有Excel文件
    for file_name in excel_files:
        file_path = os.path.join(directory_path, file_name)
        all_data[file_name] = {}  # 为每个文件创建一个子字典
        
        try:
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path)
            
            # 遍历所有sheet
            for sheet_name in excel_file.sheet_names:
                # 读取当前sheet的B列数据
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if 'B' in df.columns or 1 in df.columns:
                    col_data = df.iloc[:, 1].dropna().tolist()  # 获取B列（索引为1）的数据
                    all_data[file_name][sheet_name] = col_data
                
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {str(e)}")
    
    return all_data

# 使用示例
if __name__ == "__main__":
    directory = "your_excel_files_directory"  # 替换为实际的目录路径
    all_data = process_excel_files(directory)
    
    # 打印每个文件的每个sheet的B列数据
    for file_name, sheets_data in all_data.items():
        print(f"\n文件: {file_name}")
        for sheet_name, data_list in sheets_data.items():
            print(f"  {sheet_name} 工作表的B列数据:")
            print(f"  {data_list}") 