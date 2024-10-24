import os, shutil, re
from typing import Any
from modules import case_formatter
from modules import cpp_code_editor


def bt_action_cpp_generator(
    bt_plugin_save_path: str,
    bt_plugin_cpp_template: str,
    bt_plugin_cpp_include_guard_prefix: str,
    actions: list[Any],
    ros2_pkg_name: str,
    bt_action_default_arguments: list[str] = [],
    bt_action_ignore_arguments: list[str] = [],
):
    # プラグインの保存先のディレクトリを作成
    os.makedirs(os.path.expanduser(bt_plugin_save_path), exist_ok=True)

    for action in actions:
        plugin_file_path = os.path.expanduser(
            os.path.join(bt_plugin_save_path, action["bt_plugin_file_name"])
        )
        if os.path.exists(plugin_file_path) == False:
            # ファイルをコピー
            shutil.copy(os.path.expanduser(bt_plugin_cpp_template), plugin_file_path)

        bt_action_cpp_editor(
            plugin_file_path,
            bt_plugin_cpp_include_guard_prefix,
            action,
            ros2_pkg_name,
            bt_action_default_arguments,
            bt_action_ignore_arguments,
        )


def bt_action_cpp_editor(
    plugin_file_path: str,
    bt_plugin_cpp_include_guard_prefix: str,
    action: Any,
    ros2_pkg_name: str,
    bt_action_default_arguments: list[str] = [],
    bt_action_ignore_arguments: list[str] = [],
):
    # action dictionary に["bt_arg_name"]を追加
    for input_port in action["goal"]:
        bt_arg_name = input_port["var_name"]
        if input_port["unit"] != None:
            bt_arg_name += f'__{input_port["unit"]}'
        input_port["bt_arg_name"] = bt_arg_name

    for output_port in action["result"]:
        bt_arg_name = output_port["var_name"]
        if output_port["unit"] != None:
            bt_arg_name += f'__{output_port["unit"]}'
        output_port["bt_arg_name"] = bt_arg_name

    # プラグインファイルの読み込み
    with open(plugin_file_path, "r") as f:
        plugin_file = f.read()

    # プラグインファイルの編集
    plugin_file = plugin_file.replace("PATHTOFILE", bt_plugin_cpp_include_guard_prefix)

    plugin_file = plugin_file.replace(
        "ACTIONCLASSNAME_H",
        case_formatter.case_formatter(
            action["bt_plugin_file_name"].replace(".", "_"), "UPPER_SNAKE_CASE"
        ),
    )

    plugin_file = plugin_file.replace("ActionClassName", action["bt_action_name"])

    plugin_file = plugin_file.replace("action_package_name", ros2_pkg_name)

    plugin_file = plugin_file.replace("ActionName", action["ros2_action_name"])

    plugin_file = plugin_file.replace(
        "action_name",
        case_formatter.case_formatter(action["ros2_action_name"], "lower_snake_case"),
    )

    # providedBasicPortsの編集
    provided_basic_ports_str = ""

    for input_port in action["goal"]:
        if input_port["var_name"] in bt_action_ignore_arguments:
            continue
        provided_basic_ports_str += f'BT::InputPort<{input_port["var_c_type"]}>("{input_port["bt_arg_name"]}"), '

    for output_port in action["result"]:
        if output_port["var_name"] in bt_action_ignore_arguments:
            continue
        provided_basic_ports_str += f'BT::OutputPort<{output_port["var_c_type"]}>("{output_port["bt_arg_name"]}"), '
    provided_basic_ports_str = provided_basic_ports_str[:-2]

    plugin_file = cpp_code_editor.modify_block_after_keyword(
        plugin_file, "providedBasicPorts", provided_basic_ports_str
    )

    # default値をとるとらないで、argを分離
    default_args = []
    non_default_args = []
    for input_port in action["goal"]:
        if input_port["var_name"] in bt_action_ignore_arguments:
            continue
        elif len([
            var_name
            for var_name in bt_action_default_arguments
            if re.match(var_name, input_port["var_name"])
        ]) == 0:
            non_default_args.append(input_port)
        else:
            default_args.append(input_port)

    # 初期化リストの編集
    initializers = []
    for default_arg in default_args:
        bt_arg_name = default_arg["var_name"]
        if input_port["unit"] != None:
            bt_arg_name += f'_{default_arg["unit"]}'
        initializers.append(f"{bt_arg_name}_({bt_arg_name})")

    plugin_file = cpp_code_editor.modify_initializer_list(
        plugin_file, action["bt_action_name"], initializers
    )

    # コンストラクタの引数リストの編集
    constructor_args = []
    for default_arg in default_args:
        constructor_args.append(
            f'std::optional<{input_port["var_c_type"]}> {default_arg["bt_arg_name"]} = std::nullopt'
        )

    plugin_file = cpp_code_editor.modify_function_arguments(
        plugin_file, action["bt_action_name"], constructor_args
    )

    # setGoalの編集 - 変数の定義
    set_goal_content = "\n"

    for default_arg in default_args:
        set_goal_content += (
            f'    {default_arg["var_c_type"]} {default_arg["bt_arg_name"]};\n'
        )

    for non_default_arg in non_default_args:
        set_goal_content += (
            f'    {non_default_arg["var_c_type"]} {non_default_arg["bt_arg_name"]};\n'
        )

    # setGoalの編集 - default 引数の処理
    set_goal_content += "\n"

    for default_arg in default_args:
        set_goal_content += f'    if ({default_arg["bt_arg_name"]}_.has_value()) {{\n'
        set_goal_content += f'      {default_arg["bt_arg_name"]} = {default_arg["bt_arg_name"]}_.value();\n'
        set_goal_content += f"    }} else {{\n"
        set_goal_content += f'      getInput<{default_arg["var_c_type"]}>("{default_arg["bt_arg_name"]}", {default_arg["bt_arg_name"]});\n'
        set_goal_content += f"    }}\n"
        
    # setGoalの編集 - 非 default 引数の処理
    set_goal_content += "\n"

    for non_default_arg in non_default_args:
        set_goal_content += f'    getInput<{non_default_arg["var_c_type"]}>("{non_default_arg["bt_arg_name"]}", {non_default_arg["bt_arg_name"]});\n'

    # setGoalの編集 - ros2 actionのメンバ変数への代入
    set_goal_content += "\n"

    for default_arg in default_args:
        set_goal_content += (
            f'    goal.{default_arg["var_name"]} = {default_arg["bt_arg_name"]};\n'
        )

    for non_default_arg in non_default_args:
        set_goal_content += f'    goal.{non_default_arg["var_name"]} = {non_default_arg["bt_arg_name"]};\n'

    # setGoalの編集 - 残りの処理
    set_goal_content += f"    return true;\n  "

    plugin_file = cpp_code_editor.modify_block_after_keyword(
        plugin_file, "setGoal", set_goal_content
    )

    default_arg_menbers = []

    for default_arg in default_args:
        default_arg_menbers.append(
            f'  std::optional<{default_arg["var_c_type"]}> {default_arg["bt_arg_name"]}_;'
        )

    # onResultReceivedの編集
    on_result_received_content = "\n"

    for output_port in action["result"]:
        if output_port["var_name"] in bt_action_ignore_arguments:
            continue
        on_result_received_content += f'    setOutput<{output_port["var_c_type"]}>("{output_port["bt_arg_name"]}", result.result->{output_port["var_name"]});\n'

    on_result_received_content += """
    if (result.code ==  rclcpp_action::ResultCode::SUCCEEDED) {
      return BT::NodeStatus::SUCCESS;
    } else {
      return BT::NodeStatus::FAILURE;
    }
  \
"""

    plugin_file = cpp_code_editor.modify_block_after_keyword(
        plugin_file, "onResultReceived", on_result_received_content
    )

    # praivate メンバの編集
    plugin_file = cpp_code_editor.replace_private_members(
        plugin_file, action["bt_action_name"], ["default_arg.*"], default_arg_menbers
    )

    # プラグインファイルの保存
    with open(plugin_file_path, "w") as f:
        f.write(plugin_file)
    return
