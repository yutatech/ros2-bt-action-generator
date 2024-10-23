from modules import case_formatter


def generate_bt_plugin_file_name(
    ros2_pkg_name: str,
    ros2_action_name: str,
    bt_plugin_file_name_exclude_words: list[str] = [],
) -> str:
    """bt plugin のファイル名を生成する

    Args:
        ros2_pkg_name (str): ros2 pkg 名
        ros2_action_name (str): ros2 action 名
        bt_plugin_file_name_exclude_words (list[str], optional): bt pluginのファイル名で除外する単語. デフォルト値は[].

    Returns:
        str: bt plugin のファイル名
    """
    plugin_file_name = ros2_pkg_name + "_" + ros2_action_name
    for exclude_word in bt_plugin_file_name_exclude_words:
        plugin_file_name = plugin_file_name.replace(exclude_word, "")
    plugin_file_name = case_formatter.case_formatter(
        plugin_file_name, "lower_snake_case"
    )
    plugin_file_name = plugin_file_name + ".h"
    return plugin_file_name


def generate_bt_action_name(
    ros2_pkg_name: str, ros2_action_name: str, bt_action_name_exclude_words: list[str] = []
) -> str:
    """bt action の名前を生成する

    Args:
        ros2_pkg_name (str): ros2 pkg 名
        action_name (str): ros2 action 名
        bt_action_name_exclude_words (list[str], optional): bt actionの名前で除外する単語. デフォルト値は[].

    Returns:
        str: bt action の名前
    """
    bt_action_name = ros2_pkg_name + "_" + ros2_action_name
    for exclude_word in bt_action_name_exclude_words:
        bt_action_name = bt_action_name.replace(exclude_word, "")
    bt_action_name = case_formatter.case_formatter(bt_action_name, "UpperCamelCase")
    return bt_action_name
