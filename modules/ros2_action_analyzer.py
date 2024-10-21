import os
from typing import Any

def ros2_action_analyzer(ros2_package_abs_path):
    pkg_directory = os.path.expanduser(ros2_package_abs_path)
    action_files = pick_action_rel_path(pkg_directory)
    
    print(action_files[0])
    action = analize_action(pkg_directory, action_files[0])
    return action

def pick_action_rel_path(pkg_directory: str) -> list[str]:
    """ ros2 pkgのディレクトリから.actionファイルのpkgのディレクトリからの相対パスを取得する

    Args:
        pkg_directory (str): 探索対象のros2 pkgのディレクトリ

    Returns:
        List[str]: .actionファイルのpkgのディレクトリからの相対パス
    """
    action_files = []
    for root, _, files in os.walk(pkg_directory):
        for file in files:
            if file.endswith('.action'):
                path = os.path.join(root, file)
                
                action_files.append(os.path.relpath(path, pkg_directory))
    return action_files

def analize_action(pkg_directory: str, action_rel_path: str) -> dict[str, Any]:
    """ .actionファイルの内容を解析する

    Args:
        pkg_directory (str): .actionファイルのあるros2 pkgのディレクトリ
        action_rel_path (str): .actionファイルのpkgのディレクトリからの相対パス

    Returns:
        dict[str, Any]: 解析結果
            {"action_name": str}: アクション名
            {"goal": [{"var_name": str, "var_c_type": str, "unit": str}]}: goalのメンバ変数
            {"result": [{"var_name": str, "var_c_type": str, "unit": str}]}: resultのメンバ変数
            {"feedback": [{"var_name": str, "var_c_type": str, "unit": str}]}: feedbackのメンバ変数
    """
    
    # actionファイルの各行の内容を取得
    action_file_path = os.path.join(pkg_directory, action_rel_path)
    with open(action_file_path, 'r') as f:
        lines = f.readlines()
        
    # 各行の先頭のスペースをと行末の改行を削除
    lines = [line.strip() for line in lines]
    
    # 各行の先頭が#で始まる行を削除
    lines = [line for line in lines if not line.startswith('#')]
    
    # 空行を削除
    lines = [line for line in lines if line]

    # 要素'---'でリストを分割
    splited_lines = split_list(lines, '---')

    if len(splited_lines) != 3:
        raise ValueError('[ros2_action_analyzer] Invalid .action file format: ' + action_file_path)
    
    result = {}
    keys = ['goal', 'result', 'feedback']
    for i in range(3):
        result[keys[i]] = []
        for j in range(len(splited_lines[i])):
            result[keys[i]].append(analize_action_member(splited_lines[i][j]))
    
    return splited_lines

def analize_action_member(action_member_line: str) -> dict[str, str]:
    """actionのメンバ変数を解析する

    Args:
        action_member_line (str): .actionファイルのメンバ変数の行

    Returns:
        dict[str, str]: 解析結果
            {"var_name": str} : メンバ変数名
            {"var_c_type": str} : メンバ変数のC言語の型
            {"unit": str} : メンバ変数の単位
    """
    
    # 面部変数の行を最初の#で分割
    splited_line = action_member_line.split('#', 1)
    print(splited_line)
    return 
    

def split_list(input_list: list[Any], delimiter:Any) -> list[list[Any]]:
    """リストを特定の要素で分割する

    Args:
        input_list (list[Any]): 分割対象のリスト
        delimiter (Any): 分割する要素

    Returns:
        list[list[Any]]: 分割結果
    """
    result = []
    current_chunk = []

    for item in input_list:
        if item == delimiter:
            result.append(current_chunk)
            current_chunk = []
        else:
            current_chunk.append(item)

    result.append(current_chunk)

    return result

if __name__ == '__main__':
    ros2_package_abs_path = '~/ni/Burger-cooker/embedded/NUC_SOFT/EM3/colcon_ws/src/niec_cvd_azd_can_client_interfaces'
    result = ros2_action_analyzer(ros2_package_abs_path)
    # print(result)