# ros2-bt-action-generator

# behavior tree の ros2 action の C++ ヘッダーの出力
- `python3 ./ros2-bt-action-generator.py -p -c ./assets/config.json`
    - ros2 pkgから.actionファイルを探索し、ソーづコードを自動生成

# behavior tree の .btprj の編集と、ros2 bt node の C++ ソースの編集
- `python3 ./ros2-bt-action-generator.py -b -c ./assets/config.json`
    - behavior tree の ros2 action の C++ ヘッダーを探索し、ros2 bt node の C++ ソースを自動編集
    - C++ ヘッダーのコメントをもとに btproj ファイルを編集

