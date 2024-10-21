import re

def case_formatter(input_string: str, case_type: str) -> str:
    """文字列のcaseを整える

    Args:
        input_string (str): 整える文字列
        case_type (str): 整えるcaseの種類
            - 'lower_snake_case'
            - 'UPPER_SNAKE_CASE'
            - 'UpperCamelCase'
            - 'lowerCamelCase'
            - 'kebab-case'

    Raises:
        ValueError

    Returns:
        str: _description_
    """

    if bool(re.search(r'[^a-zA-Z0-9-_]', input_string)):
        raise ValueError('[case_formatter] Invalid input_string: \"' + input_string + '\" The string must not contain anything other than alphanumeric characters, -, and _.')
    
    # 大文字の前に空白を挿入（先頭以外の場合）
    s = re.sub(r'(?<!^)(?=[A-Z])', ' ', input_string)
    # 非アルファベット文字を空白に置き換え
    s = re.sub(r'[^a-zA-Z0-9 ]', ' ', s)
    # 単語を分割し、各単語の最初の文字を大文字に変換
    string_word_list = s.lower().split()
    print(string_word_list)
    if case_type == 'lower_snake_case':
        for i in range(1, len(string_word_list)):
            string_word_list[i] = '_' + string_word_list[i]
        output_string = ''.join(string_word_list)
    if case_type == 'UPPER_SNAKE_CASE':
        for i in range(1, len(string_word_list)):
            string_word_list[i] = '_' + string_word_list[i]
        output_string = ''.join(string_word_list).upper()
    elif case_type == 'UpperCamelCase':
        output_string = ''.join(word.capitalize() for word in string_word_list)
    elif case_type == 'lowerCamelCase':
        output_string = ''.join(word.capitalize() for word in string_word_list)
        output_string = output_string[0].lower() + output_string[1:]
    elif case_type == 'kebab-case':
        for i in range(1, len(string_word_list)):
            string_word_list[i] = '-' + string_word_list[i]
        output_string = ''.join(string_word_list)
    else:
        raise ValueError('[case_formatter] Invalid case_type argument: ' + case_type)
    
    return output_string

if __name__ == '__main__':
    input_string = 'case-is-Not-onnnaji_denai-yabame1Dana'
    output_string = case_formatter(input_string, 'UPPER_SNAKE_CASE')
    print(output_string)