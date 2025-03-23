import os
import pandas as pd

def process_excel_files(directory_path):
    """
    处理指定目录下的所有Excel文件，提取每个文件所有sheet的B列数据
    
    参数:
        directory_path (str): Excel文件所在的目录路径
        
    返回:
        dict: 包含所有sheet的B列数据，键为sheet名称
    """
    # 初始化一个字典，用于存储所有sheet的B列数据
    all_sheets_data = {}
    
    # 获取目录中所有Excel文件
    excel_files = [f for f in os.listdir(directory_path) 
                  if f.endswith('.xlsx') or f.endswith('.xls')]
    
    # 遍历所有Excel文件
    for file_name in excel_files:
        file_path = os.path.join(directory_path, file_name)
        
        try:
            # 根据文件扩展名选择适当的引擎
            if file_name.endswith('.xlsx'):
                engine = 'openpyxl'
            elif file_name.endswith('.xls'):
                engine = 'xlrd'
            else:
                print(f"不支持的文件格式: {file_name}")
                continue
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path, engine=engine)
            sheet_names = excel_file.sheet_names
            
            # 遍历所有sheet
            for sheet_name in sheet_names:
                # 如果字典中还没有这个sheet的键，则创建一个空列表
                if sheet_name not in all_sheets_data:
                    all_sheets_data[sheet_name] = []
                
                # 读取当前sheet的B列数据
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
                col_data = df.iloc[:, 1].dropna().tolist()  # 获取B列（索引为1）的数据
                all_sheets_data[sheet_name].extend(col_data)
                
        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {str(e)}")
            # 如果第一个引擎失败，尝试使用另一个引擎
            try:
                alternative_engine = 'xlrd' if engine == 'openpyxl' else 'openpyxl'
                print(f"尝试使用替代引擎 {alternative_engine} 读取文件 {file_name}")
                
                excel_file = pd.ExcelFile(file_path, engine=alternative_engine)
                sheet_names = excel_file.sheet_names
                
                for sheet_name in sheet_names:
                    if sheet_name not in all_sheets_data:
                        all_sheets_data[sheet_name] = []
                    
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine=alternative_engine)
                    if 'B' in df.columns or 1 in df.columns:
                        col_data = df.iloc[:, 1].dropna().tolist()
                        all_sheets_data[sheet_name].extend(col_data)
                
            except Exception as inner_e:
                print(f"使用替代引擎处理文件 {file_name} 也失败: {str(inner_e)}")
    
    return all_sheets_data

# 使用示例
if __name__ == "__main__":
    directory = "your_excel_files_directory"  # 替换为实际的目录路径
    all_sheets_data = process_excel_files(directory)
    
    # 打印每个sheet的B列数据
    for sheet_name, data_list in all_sheets_data.items():
        print(f"\n{sheet_name} 工作表的B列数据:")
        print(data_list) 