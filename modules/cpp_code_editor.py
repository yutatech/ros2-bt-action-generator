import re

def modify_block_after_keyword(code, keyword, new_content):
    # 1. 指定された文字列の位置を探す
    keyword_index = code.find(keyword)

    if keyword_index == -1:
        # キーワードが見つからなければ何も変更せずに返す
        return code

    # 2. キーワードの後にある最初の '{' を探す
    start_brace_index = code.find("{", keyword_index)

    if start_brace_index == -1:
        # '{' が見つからなければ何も変更せずに返す
        return code

    # 3. '{' と '}' のバランスを取る
    open_braces = 1
    current_index = start_brace_index + 1

    while open_braces > 0 and current_index < len(code):
        if code[current_index] == "{":
            open_braces += 1
        elif code[current_index] == "}":
            open_braces -= 1
        current_index += 1

    # 4. 対応する '}' が見つかった場合、{}の中身を削除し、新しい内容を追加
    if open_braces == 0:
        # current_index は '}' の次の位置を指しているので、中身を削除して新しい内容を追加
        new_code = (
            code[: start_brace_index + 1]  # '{' まで保持
            + new_content  # 新しい内容を追加
            + code[current_index - 1 :]
        )  # '}' 以降を保持
        return new_code
    else:
        # 対応する '}' が見つからない場合は何も変更せずに返す
        return code


def modify_initializer_list(
    code: str, constructor_name: str, new_initialization: list[str]
):
    # 1. コンストラクタの正規表現パターンを作成（イニシャライザリストの先頭 ':' を探す）
    pattern = rf"{constructor_name}\s*\([^)]*\)\s*:\s*([^{{]*)"

    # 2. イニシャライザリストのマッチを取得
    match = re.search(pattern, code)

    if not match:
        # コンストラクタまたはイニシャライザリストが見つからなければ、そのまま返す
        return code

    # 3. イニシャライザリストの内容を取得
    initializer_list = match.group(1)

    # 4. カンマ区切りの初期化リストを分割
    initializers = [item.strip() for item in split_ignoring_brackets(initializer_list)]

    if len(initializers) <= 1:
        # 初期化が1つしかない場合は何も変更しない
        return code

    # 5. 2番目以降の初期化を削除し、1番目だけを保持
    modified_initializers = initializers[:1]

    # 6. 新しい初期化を追加
    modified_initializers += new_initialization

    # 7. 修正したイニシャライザリストを再構築
    modified_initializer_list = ", ".join(modified_initializers)

    # 8. 修正後のコードを生成
    new_code = (
        code[: match.start(1)]  # イニシャライザリストの前の部分
        + modified_initializer_list  # 修正後のイニシャライザリスト
        + code[match.end(1) :]
    )  # イニシャライザリストの後の部分

    return new_code


def split_ignoring_brackets(s):
    # 各種括弧の対応を定義
    open_brackets = "([{<"
    close_brackets = ")]}>"

    # 括弧の深さを記録するためのカウンタ
    bracket_depth = [0] * len(open_brackets)

    # 現在のトークンを保持するためのリスト
    result = []
    current_token = []

    # 文字列を1文字ずつ処理
    for char in s:
        # 括弧の開きを検出して深さを増やす
        if char in open_brackets:
            bracket_depth[open_brackets.index(char)] += 1
        # 括弧の閉じを検出して深さを減らす
        elif char in close_brackets:
            bracket_depth[close_brackets.index(char)] -= 1

        # カンマで分割するが、すべての括弧の深さが0の時のみ分割
        if char == "," and all(depth == 0 for depth in bracket_depth):
            # トークンを追加
            result.append("".join(current_token).strip())
            current_token = []
        else:
            # カンマ以外の文字、または括弧内のカンマはトークンに追加
            current_token.append(char)

    # 最後のトークンを追加
    if current_token:
        result.append("".join(current_token).strip())

    return result

def modify_function_arguments(code, function_name, new_arguments):
    # 関数の引数リストをキャプチャする正規表現
    # function_name(<引数リスト>) の形式を探す
    pattern = rf"({function_name}\s*\([^)]*\))"

    # 関数定義部分を検索
    match = re.search(pattern, code)
    if match:
        # 引数リスト全体を取得
        full_match = match.group(1)

        # 引数リストの部分のみを取り出す
        # 最初の(と最後の)の間の部分
        arg_list_start = full_match.index("(") + 1
        arg_list_end = full_match.index(")")
        argument_list = full_match[arg_list_start:arg_list_end].strip()

        # 引数をカンマで分割する
        arguments = [arg.strip() for arg in argument_list.split(",")]

        # 最初の3つの引数を残し、それ以降を削除
        if len(arguments) > 3:
            arguments = arguments[:3]

        # 新しい引数を追加
        arguments.extend(new_arguments)

        # 新しい引数リストを作成
        modified_arg_list = ", ".join(arguments)

        # 元のコードの引数部分を置換
        modified_code = code.replace(argument_list, modified_arg_list)

        return modified_code
    else:
        return code  # マッチしなければそのまま返す


def replace_private_members(code, class_name, members_to_remove, new_members):
    # クラス定義の開始を検出
    class_pattern = rf"class\s+{class_name}"
    class_match = re.search(class_pattern, code)

    if not class_match:
        print(f"Class {class_name} not found.")
        return code

    # クラスの終わりまでを取得
    class_start = class_match.start()
    class_body = code[class_start:]

    # privateセクションの検出
    private_pattern = r"(private\s*:(\s*\n)?)((\s*.+?)*?)\s*(public|protected|}\s*;)"
    private_match = re.search(private_pattern, class_body, re.DOTALL)

    if private_match:
        private_section = private_match.group(3)  # privateセクションの中身
        modified_private_section = private_section

        # ;で分割してメンバの定義のリストを作成
        member_list = re.findall(r"([^;]*?;)", modified_private_section)
        # メンバの定義のリストのうち削除するメンバのパターンと一致するものを削除
        for member_pattern in members_to_remove:
            for member in member_list:
                if re.match(rf".*{member_pattern}.*", member, re.DOTALL):
                    modified_private_section = modified_private_section.replace(
                        member, ""
                    )

        # 新しいメンバリストをprivateセクションの先頭に追加
        new_member_code = ""

        for new_member in new_members:
            if not new_member in modified_private_section:
                new_member_code += new_member + "\n"

        modified_private_section = new_member_code + modified_private_section

        # 元のコードで private セクションを置換
        modified_code = code.replace(private_section, modified_private_section)
        return modified_code
    else:
        print(f"No private section found in class {class_name}.")
        return code