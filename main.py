import argparse
import os
from modifier import ProtoModifier


def parse_input_argument():
    parser = argparse.ArgumentParser(
        description='Proto Modifier can modify the proto file, keeping rpcs with specific options.')

    parser.add_argument('-s', '--source-dir', required=True,
                        help="Source directory of protobuf files.")
    parser.add_argument('-d', '--dest-dir', required=True,
                        help="Destination directory of generated protobuf files.")
    parser.add_argument('-n', '--option-name', action='append',
                        help="Name of the options and the rpcs containing them to keep.")

    args = parser.parse_args()
    return args



def main():
    args = parse_input_argument()
    modifier = ProtoModifier(args.option_name)
    for root, _, files in os.walk(args.source_dir):
        relative_path = os.path.relpath(root, args.source_dir)
        for file in files:
            if file.endswith(".proto"):
                try:
                    tree = modifier.parse_file(os.path.join(root, file))
                    output = modifier.regenerate_file(tree)
                    if not os.path.exists(os.path.join(args.dest_dir, relative_path)):
                        os.makedirs(os.path.join(args.dest_dir, relative_path))
                    with open(os.path.join(args.dest_dir, relative_path, file), 'w') as f:
                        f.write(output)
                    if "Not Implemented" in output:
                        print("Could not generate completely: " + os.path.join(args.dest_dir, relative_path, file))
                except Exception as e:
                    print(os.path.join(args.dest_dir, relative_path, file))
                    print(e)


if __name__ == '__main__':
    main()
