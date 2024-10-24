from modules import ros2_action_analyzer
from modules import bt_action_cpp_generator
from modules import name_generator
from modules import bt_node_generator
import os, argparse, json

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # default_config_pathを取得
    relative_path = "assets/config.json"  # 相対パスを指定
    default_config_path = os.path.join(script_dir, relative_path)

    # ArgumentParserを作成
    parser = argparse.ArgumentParser(description="Process some configurations.")
    parser = argparse.ArgumentParser(description="Process some configurations.")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=default_config_path,
        help="Path to the configuration file (default: assets/config.json)",
    )

    parser.add_argument(
        "-p",
        "--plugin",
        action="store_true",
        help="generate bt plugin files",
    )

    parser.add_argument(
        "-b",
        "--bt",
        action="store_true",
        help="generate bt source file and node tree models",
    )

    # 引数を解析
    args = parser.parse_args()

    # 設定ファイルのパスを取得
    config_file_path = args.config

    # 設定ファイルの読み込み
    with open(config_file_path, "r") as file:
        # JSONデータを読み込む
        config = json.load(file)

    if args.plugin:
        # ros2 action の解析
        actions = ros2_action_analyzer.ros2_action_analyzer(
            config["ros2_package_abs_path"]
        )

        # ros2 pkg name の取得
        ros2_pkg_name = os.path.basename(config["ros2_package_abs_path"])
        # パスの末尾がスラッシュで終わっている場合を考慮
        if ros2_pkg_name == "":
            ros2_pkg_name = os.path.basename(
                os.path.dirname(config["ros2_package_abs_path"])
            )

        for action in actions:
            action["bt_plugin_file_name"] = name_generator.generate_bt_plugin_file_name(
                ros2_pkg_name,
                action["ros2_action_name"],
                config["bt_plugin_file_name_exclude_words"],
            )
            action["bt_action_name"] = name_generator.generate_bt_action_name(
                ros2_pkg_name,
                action["ros2_action_name"],
                config["bt_action_name_exclude_words"],
            )

        bt_action_cpp_generator.bt_action_cpp_generator(
            config["bt_plugin_save_path"],
            config["bt_plugin_cpp_template"],
            config["bt_plugin_cpp_include_guard_prefix"],
            actions,
            ros2_pkg_name,
            config["bt_action_default_arguments"],
            config["bt_action_ignore_arguments"],
        )

    elif args.bt:
        bt_node_generator.bt_node_generator(
            config["bt_plugin_save_path"], config["ros2_bt_source_abs_path"], config["btproj_abs_path"]
        )
