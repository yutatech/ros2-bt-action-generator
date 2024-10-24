# ros2-bt-action-generator

# behavior tree の ros2 action の C++ ヘッダーの出力
- `python3 ./ros2-bt-action-generator.py -p -c ./assets/config.json`
    - ros2 pkgから.actionファイルを探索し、ソースコードを自動生成

# behavior tree の .btprj の編集と、ros2 bt node の C++ ソースの編集
- `python3 ./ros2-bt-action-generator.py -b -c ./assets/config.json`
    - behavior tree の ros2 action の C++ ヘッダーを探索し、ros2 bt node の C++ ソースを自動編集
    - C++ ヘッダーのコメントをもとに btproj ファイルを編集

# `ros_bt_node.cc`の自動編集について
## 普通のactionの自動生成
以下の範囲が編集される。記述されていることが必須
```cpp
// auto generate action area start
...
// auto generate action area end
```

## default引数を代入済みのactionの自動生成
以下の範囲が編集される。記述されていることが必須
```cpp
// auto generate named action area start
...
// auto generate named action area end
```

## default引数を代入済みのactionに関する指示
以下の範囲を解釈してdefault引数を代入済みのactionが自動生成される。記述されていることが必須。内容は空白でもOK
```cpp
/* named action list
[ActionClassName]
instance_name, default_arg1
InstanceOne, 0
InstanceTwo, 2

[ActionClassName1, ActionClassName2]
instance_name, default_arg1, default_arg2
InstanceOne, 0, 1
InstanceTwo, 2, 2
*/
```