import argparse
import glob
import json
import os

def combine_logs(input_dir, output_file):
    combined_data = []
    
    # 入力ディレクトリの存在確認
    if not os.path.isdir(input_dir):
        raise ValueError(f"入力ディレクトリが存在しません: {input_dir}")

    # ファイル検索パス
    search_path = os.path.join(input_dir, "logs*.json")
    
    # ファイル処理
    for filename in sorted(glob.glob(search_path)):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                combined_data.extend(data)
        except Exception as e:
            print(f"警告: {filename} の処理に失敗しました - {str(e)}")
            continue

    # 出力ディレクトリの作成（必要なら）
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 結果保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)

    return len(combined_data)

def combine_logs_for_subdirectories(parent_dir, output_dir):
    # 親ディレクトリ内のサブディレクトリを対象にcombine_logsを実行
    for subdir in os.listdir(parent_dir):
        subdir_path = os.path.join(parent_dir, subdir)
        if os.path.isdir(subdir_path):
            out_file = os.path.join(output_dir, f"{subdir}.json")
            count = combine_logs(subdir_path, out_file)
            print(f"{subdir_path} を結合し {out_file} に {count} 件保存")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='JSONログファイル結合ツール',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', type=str, default='.',
                        help='入力ディレクトリのパス')
    parser.add_argument('-o', '--output-dir', type=str, default='.',
                        help='出力先ディレクトリのパス')
    args = parser.parse_args()

    try:
        combine_logs_for_subdirectories(args.input, args.output_dir)
        print("成功")
    except Exception as e:
        print(f"エラー: {str(e)}")
        exit(1)