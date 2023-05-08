import argparse
import os
from protomod.modifier import ProtoModifier


def parse_input_argument():
    parser = argparse.ArgumentParser(
        description='Proto Modifier can modify the proto file, keeping rpcs with specific options.')

    parser.add_argument('-s', '--source-dir', required=True, action='append',
                        help="Source directory of protobuf files.")
    parser.add_argument('-d', '--dest-dir', required=True,
                        help='Destination directory of generated protobuf files.')
    parser.add_argument('-n', '--option-name', action='append',
                        help='Name of the options and the rpcs containing them to keep.')

    args = parser.parse_args()
    return args


def process_files(source_dirs, func):
    for source_dir in source_dirs:
        for root, _, files in os.walk(source_dir):
            relative_path = os.path.relpath(root, source_dir)
            for file in files:
                if file.endswith(".proto"):
                    func(os.path.join(root, file), relative_path, file)


def main():
    args = parse_input_argument()
    modifier = ProtoModifier(args.option_name)

    def create_usage_graph(file_path, relative_path, file):
        tree = modifier.parse_file(file_path)
        modifier.create_usage_graph(tree)

    def output_processor(dry_run: bool):
        def regenerate_files(file_path, relative_path, file):
            try:
                tree = modifier.parse_file(file_path)
                output, should_render = modifier.regenerate_file(tree)
                if should_render and not dry_run:
                    if not os.path.exists(os.path.join(args.dest_dir, relative_path)):
                        os.makedirs(os.path.join(args.dest_dir, relative_path))
                    with open(os.path.join(args.dest_dir, relative_path, file), 'w') as f:
                        f.write(output)
                    if "Not Implemented" in output:
                        print("Could not generate completely: " + os.path.join(args.dest_dir, relative_path, file))
                elif should_render and dry_run:
                    modifier.rendered_files.append(os.path.join(relative_path, file))
            except Exception as e:
                print(os.path.join(args.dest_dir, relative_path, file))
                print(e)
        return regenerate_files

    process_files(args.source_dir, create_usage_graph)
    modifier.update_should_render_state()
    process_files(args.source_dir, output_processor(True))
    process_files(args.source_dir, output_processor(False))
