import os, re
from typing import Any
import fnmatch
import json, csv
from io import StringIO

def bt_node_generator(
    bt_plugin_save_path: str,
    ros2_bt_source_abs_path: str,
    btproj_abs_path: str):
    
    bt_plugin_dir = os.path.expanduser(bt_plugin_save_path)
    ros2_source_path = os.path.expanduser(ros2_bt_source_abs_path)
    btproj_path = os.path.expanduser(btproj_abs_path)
    
    extensions = ['*.h', '*.hpp']

    # ファイルの一覧を取得
    files = [os.path.join(bt_plugin_dir, f) for f in os.listdir(bt_plugin_dir) if any(fnmatch.fnmatch(f, ext) for ext in extensions)]

    plugins_info = []
    for file in files:
        plugin_info = get_plugin_from_cpp(file)
        plugins_info.append(plugin_info)
        
    edit_bt_source_action_area(ros2_source_path, plugins_info)
    
    # named_actionsは、bt actionのcpp classのコンストラクタに、デフォルト引数を渡したものを意味する
    named_actions_info = analyze_named_actions(ros2_source_path)
    
    named_actions_list_for_bt = edit_bt_source_named_action_area(ros2_source_path, named_actions_info, plugins_info)
    
    edit_bt_tree_models_action(btproj_path, plugins_info)
    
    edit_bt_tree_models_named_action(btproj_path, named_actions_list_for_bt)
    
def get_plugin_from_cpp(plugin_file_name: str) -> list[Any]:
    """ bt plugin ファイルから bt plugin 情報を取得する

    Args:
        plugin_file_name (str): plugin ファイル名

    Returns:
        list[Any]: ポート情報
            {"action_class_name" : str,
             "non_default_input_ports" : [{"name": str, "type" : str}],
             "default_input_ports" : [{"name" : str, "type" : str, "c_name" : str}],
             "output_ports" : [{"name" : str}]}
    """
    
    # プラグインファイルの読み込み
    with open(plugin_file_name, "r") as f:
        plugin_file = f.read()
    
    # class 名を取得する
    class_name = re.search(r'class\s+(\w+)\s*:', plugin_file).group(1)
    
    # コンストラクタの()の中身を取得する
    constructor_str = re.search(r'(\w+)\s*\((.+)\)', plugin_file).group(2)
    
    # コンストラクタのデフォルト引数の名前と型を取得する
    default_input_ports = []
    argument_list = constructor_str.split(',')
    for arg in argument_list:
        if '=' in arg:
            matches = re.search(r'[\w\s:]*\s*<(.*?)>\s*(\w+)\s*=\s*(\w+)', arg)
            default_input_ports.append({"c_name" : matches.group(2), "type" : matches.group(1)})
        
    # providedBasicPortsのあとのブロックを取得する
    provided_basic_ports = re.search(r'(providedBasicPorts[^{]*?{(.+)})', plugin_file).group(1)
    
    # provided_basic_portsの中からInputPortの型と名前を取得する
    input_ports_str = re.findall(r'InputPort<(.+?)>\s*\([^\w]*?(\w*?)[^\w]*?\)', provided_basic_ports)
    
    non_default_input_ports = []
    for input_port in input_ports_str:
        # input_port[1]が、default_input_portsの["c_name"]のうちどれかに文字列が含まれているかを調べる
        if any(input_port[1] in default_port["c_name"] for default_port in default_input_ports):
            for default_port in default_input_ports:
                if input_port[1] in default_port["c_name"]:
                    default_port["name"] = input_port[1]
        else:
            non_default_input_ports.append({"name" : input_port[1], "type" : input_port[0]})
    
    # providedBasicPortsのあとのブロックの中からOutputPortの名前を取得する
    output_ports_str = re.findall(r'OutputPort<(?:.+?)>\s*\([^\w]*?(\w*?)[^\w]*?\)', provided_basic_ports)
    output_ports = []
    for output_port in output_ports_str:
        output_ports.append({"name" : output_port})

    # print(class_name)
    # print(default_input_ports)
    # print(non_default_input_ports)
    # print(output_ports)
    
    return {"action_class_name" : class_name,
            "non_default_input_ports" : non_default_input_ports,
            "default_input_ports" : default_input_ports,
            "output_ports" : output_ports}
    
    
def edit_bt_source_action_area(ros2_source_path: str, plugins_info: list[Any]):
    """ bt plugin 情報を元に、ros2のbtソースを編集する

    Args:
        ros2_source_path (str): ros2のbtソースの絶対パス
        plugins_info (list[Any]): bt plugin 情報
    """

    # bt ソースコードの読み込み
    with open(ros2_source_path, "r") as f:
        bt_source_code = f.read()
        
    # 定義済みのインスタンスの取得
    factory_match = re.search(r'BT::BehaviorTreeFactory\s*(\w+)\s*;', bt_source_code)
    if factory_match == None:
        raise ValueError(f"BT::BehaviorTreeFactory instance does not declared in {ros2_source_path}.")
    factory_str = factory_match.group(1)
    
    node_param_match = re.search(r'BT::RosNodeParams\s*(\w+)\s*;', bt_source_code)
    if node_param_match == None:
        raise ValueError(f"BT::RosNodeParams instance does not declared in {ros2_source_path}.")
    node_param_str = node_param_match.group(1)
    
    # 編集領域の取得
    edit_area_match = re.search(r'// auto generate action area start(.+)// auto generate action area end', bt_source_code, re.DOTALL)
    edit_area = edit_area_match.group(0)
    edit_erea_content = edit_area_match.group(1)

    # 編集領域の編集
    modified_edit_erea_content = edit_erea_content
    for plugin_info in plugins_info:
        # プラグインファイルのクラス名を追加
        if not plugin_info["action_class_name"] in modified_edit_erea_content:
            modified_edit_erea_content += f'  {factory_str}.registerNodeType<{plugin_info["action_class_name"]}>("{plugin_info["action_class_name"]}", {node_param_str});\n'
        
    edit_area = edit_area.replace(edit_erea_content, modified_edit_erea_content)
    
    bt_source_code = bt_source_code.replace(edit_area_match.group(0), edit_area)

    
    # bt ソースコードの保存
    with open(ros2_source_path, "w") as f:
        f.write(bt_source_code)
    return

def analyze_named_actions(ros2_source_path):
    """ bt ソースからnamed actionの情報を取得する

    Args:
        ros2_source_path (str): ros2のbtソースの絶対パス
    
    Returns:
        list[Any]: named_actions_info
            {"action_class_names" : [str],
             "named_actions": [{
                 "instance_name" : str,
                 args : [{"name" : str, "value" : str}}]
                ]
            }
    """
    
    # bt ソースコードの読み込み
    with open(ros2_source_path, "r") as f:
        bt_source_code = f.read()
        
    named_actions_area_match = re.search(r'\/\* named action list(.+)\*\/', bt_source_code, re.DOTALL)
    named_actions_area = named_actions_area_match.group(0)
    named_actions_erea_content = named_actions_area_match.group(1)
    
    action_list_matches = re.findall(r'\[([\w,\s]+?)\](.*?)(?=\[|$)', named_actions_erea_content, re.DOTALL)
    
    named_actions_info = []
    for action_list_match in action_list_matches:
        action_class_names_str = action_list_match[0]
        
        # セクションの内容をCSVとして読み込み
        csv_file = StringIO(action_list_match[1].replace(' ', '').strip())

        headers = list(csv.reader(StringIO(action_list_match[1].replace(' ', '').strip())))[0]
        if not 'instance_name' in headers:
            raise ValueError(f"instance_name header is not found in named action list of {action_class_names_str} in {ros2_source_path}")

        action_class_names = [i.strip() for i in action_class_names_str.split(',')]
        named_actions_info.append({"action_class_names" : action_class_names, "named_actions" : []})
        named_actions = named_actions_info[-1]["named_actions"]
        
        reader = csv.DictReader(csv_file)
        # 各行を辞書として表示
        for row in reader:
            named_actions.append({"instance_name": row["instance_name"], "args": []})
            named_action = named_actions[-1]
            args = row.copy()
            args.pop('instance_name')
            for key, value in args.items():
                named_action["args"].append({"name": key, "value": value})
    
    return named_actions_info
    
    
def edit_bt_source_named_action_area(ros2_source_path: str, named_actions_info: list[Any], plugins_info: list[Any]):
    """ named_actions 情報を元に、ros2のbtソースを編集する

    Args:
        ros2_source_path (str): ros2のbtソースの絶対パス
        named_actions_info (list[Any]): named_actions 情報
        plugins_info (list[Any]): bt plugin 情報
    """

    # bt ソースコードの読み込み
    with open(ros2_source_path, "r") as f:
        bt_source_code = f.read()
        
    # 定義済みのインスタンスの取得
    factory_match = re.search(r'BT::BehaviorTreeFactory\s*(\w+)\s*;', bt_source_code)
    if factory_match == None:
        raise ValueError(f"BT::BehaviorTreeFactory instance does not declared in {ros2_source_path}.")
    factory_str = factory_match.group(1)
    
    node_param_match = re.search(r'BT::RosNodeParams\s*(\w+)\s*;', bt_source_code)
    if node_param_match == None:
        raise ValueError(f"BT::RosNodeParams instance does not declared in {ros2_source_path}.")
    node_param_str = node_param_match.group(1)
    
    # 編集領域の取得
    edit_area_match = re.search(r'// auto generate named action area start(.+)// auto generate named action area end', bt_source_code, re.DOTALL)
    edit_area = edit_area_match.group(0)
    edit_erea_content = edit_area_match.group(1)
    
    # bt 向けに名前ありのactionのリストを作成しておく
    named_actions_list_for_bt = []

    # 編集領域の編集
    modified_edit_erea_content = edit_erea_content
    for named_actions in named_actions_info:
        for named_action in named_actions["named_actions"]:
            action_name = named_action["instance_name"]
            for class_name in named_actions["action_class_names"]:
                named_actions_list_for_bt.append({"class_name" : class_name, "action_name" : action_name+class_name})
                if f'{action_name}{class_name}' in modified_edit_erea_content:
                    continue
                modified_edit_erea_content += f'  {factory_str}.registerNodeType<{action_name}{class_name}>("{class_name}", {node_param_str}'
                for arg in named_action["args"]:
                    modified_edit_erea_content += f', {arg["value"]}'
                modified_edit_erea_content += ');\n'
        # プラグインファイルのクラス名を追加
        
    edit_area = edit_area.replace(edit_erea_content, modified_edit_erea_content)
    
    bt_source_code = bt_source_code.replace(edit_area_match.group(0), edit_area)
    
    # bt ソースコードの保存
    with open(ros2_source_path, "w") as f:
        f.write(bt_source_code)

    return named_actions_list_for_bt

def edit_bt_tree_models_action(btproj_path, plugins_info):
    
    # bt btprojファイルの読み込み
    with open(btproj_path, "r") as f:
        btproj_file = f.read()
        
    # 編集領域の取得
    edit_area_match = re.search(r'( *<TreeNodesModel>.+</TreeNodesModel>)', btproj_file, re.DOTALL)
    edit_area = edit_area_match.group(0)
    print(edit_area)
    
    # bt btprojファイルの読み込み
    # with open(btproj_path, "w") as f:
    #     f.write(btproj_file)
    # return
    
def edit_bt_tree_models_named_action(btproj_path, named_actions_list_for_bt):
    pass