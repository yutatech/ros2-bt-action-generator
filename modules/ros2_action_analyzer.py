import os, re
from typing import Any


def ros2_action_analyzer(ros2_package_abs_path: str) -> list[Any]:
    """ ros2 action の内容を解析する

    Args:
        ros2_package_abs_path (str): 解析対象のros2 pkgの絶対パス

    Returns:
        list[Any]: 解析結果
    """
    pkg_directory = os.path.expanduser(ros2_package_abs_path)
    action_files = pick_action_rel_path(pkg_directory)

    result = []
    for action_file in action_files:
        action = analize_action(pkg_directory, action_file)
        result.append(action)
    return result


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
            {"ros2_action_name": str}: アクション名
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
        raise ValueError(
            '[ros2_action_analyzer] Invalid .action file format: ' +
            action_file_path)

    # action nameを抽出
    result = {'ros2_action_name': os.path.splitext(os.path.basename(action_rel_path))[0]}

    # goal, result, feedbackのメンバ変数を解析
    keys = ['goal', 'result', 'feedback']
    for i in range(3):
        result[keys[i]] = []
        for j in range(len(splited_lines[i])):
            result[keys[i]].append(analize_action_member(splited_lines[i][j]))
        result[keys[i]] = [item for item in result[keys[i]] if item]
    # print(result)
    return result


def analize_action_member(action_member_line: str) -> dict[str, str]:
    """actionのメンバ変数を解析する

    Args:
        action_member_line (str): .actionファイルのメンバ変数の行

    Returns:
        dict[str, str]: 解析結果
            {"var_name": str} : メンバ変数名
            {"var_c_type": str} : メンバ変数のC言語の型
            {"unit": str} : メンバ変数の単位
        None : 解析失敗時
    """
    
    # ros_typeをc_typeに変換
    ros_type_to_c_type = {
        'uint8': 'uint8_t',
        'int8': 'int8_t',
        'uint16': 'uint16_t',
        'int16': 'int16_t',
        'uint32': 'uint32_t',
        'int32': 'int32_t',
        'uint64': 'uint64_t',
        'int64': 'int64_t',
        'byte': 'uint8_t',
        'char': 'char',
        'wstring': 'std::u16string',
        'float32': 'float',
        'float64': 'double',
        'string': 'std::string',
        'bool': 'bool'
    }
    
    if re.fullmatch(r'[A-Z0-9_]+', action_member_line.strip().split(' ')[1]):
        # 定数の行は無視
        return None
    elif not action_member_line.strip().split(' ')[0] in ros_type_to_c_type.keys():
        # ros_typeが不明な場合は無視
        return None

    # 面部変数の行を最初の#で分割
    splited_line = action_member_line.split('#', 1)
    if len(splited_line) != 1 and len(splited_line) != 2:
        raise ValueError(
            '[ros2_action_analyzer] Invalid .action file format: ' +
            action_member_line)

    # 変数定義部分をtypeとnameに分割
    vars_str = splited_line[0].split(' ')
    vars_str = [var_str for var_str in vars_str if var_str]
    if len(vars_str) != 2:
        raise ValueError(
            '[ros2_action_analyzer] Invalid .action declare format: ' +
            action_member_line)
    [ros_type, var_name] = vars_str

    c_type = ros_type_to_c_type[ros_type]

    # コメントから単位を抽出
    unit = None
    if len(splited_line) == 2:
        if splited_line[1].count('[') > 1 or splited_line[1].count(']') > 1:
            raise ValueError(
                '[ros2_action_analyzer] Invalid .action comment format: ' +
                splited_line[1])
        unit_origin = re.findall(r'\[([^\]]*)\]', splited_line[1])
        if len(unit_origin) > 1:
            raise ValueError(
                '[ros2_action_analyzer] Invalid .action comment format: ' +
                splited_line[1])
        elif len(unit_origin) == 1:
            unit_origin = unit_origin[0].strip()
            # スペースを '_' に変換
            unit_origin = unit_origin.replace(' ', '_')
            # スラッシュを '_per_' に変換
            unit_origin = unit_origin.replace('/', '_per_')
            unit = unit_origin
    return {'var_name': var_name, 'var_c_type': c_type, 'unit': unit}


def split_list(input_list: list[Any], delimiter: Any) -> list[list[Any]]:
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
    ros2_package_abs_path = 'hoge'
    actions = ros2_action_analyzer(ros2_package_abs_path)
    print(actions)
