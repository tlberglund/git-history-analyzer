import sys
import subprocess
import matplotlib.pyplot as plt
import squarify
import argparse
from datetime import datetime
from functools import reduce
from collections import defaultdict
import json 


def parse_git_log(log_output):
    state = "search";
    changed_files = {}
    log_entry = {}
    log = []

    for line in log_output.split('\n'):
        match state:
            case "search":
                if line.startswith("commit "):
                    log_entry = {}
                    log_entry['commit'] = line[7:]
                    state = "commit";

            case "commit":
                if(line.startswith("Author")):
                    author = line[8:].split()
                    log_entry['author_name'] = author[0]
                    log_entry['author_email'] = author[1][1:-1]

                if(line.startswith("Date")):
                    log_entry['timestamp'] = int(datetime.fromisoformat(line[8:]).timestamp())

                if len(line) == 0:
                    changed_files = {}
                    state = "comment";
            
            case "comment":
                if len(line) > 0 and not line.startswith(' '):
                    execute_stat_state(changed_files, line)
                    state = "stat";

            case "stat":
                if len(line) > 0:
                   execute_stat_state(changed_files, line)
                else:
                    log_entry['files'] = changed_files
                    log.append(log_entry)
                    log_entry = {}
                    state = "search"

            case default:
                state = "search"
    
    return log


def execute_stat_state(file_dict, line):
    entries = parse_stat_line(line);
    if(len(entries) == 3):
        path = entries[0]
        added = entries[1]
        removed = entries[2]
        if is_included_file(path):
            store_stat_line(file_dict, path, added, removed)
                       

def is_included_file(path):
    return path.endswith('.md')


def parse_stat_line(line):
    parts = line.split();
    if(len(parts) == 3):
        added = to_int_or_zero(parts[0])
        removed = to_int_or_zero(parts[1])
        path = parts[2]

        if not is_move(path):
            return [path, added, removed]
        else:
            return []
    else:
        return []


def to_int_or_zero(str):
    try:
        value = int(str)
    except ValueError:
        value = 0

    return value



def is_move(path):
    path.find('=>') >= 0


def store_stat_line(file_dict, path, added, removed):
    if path in file_dict:
        entry = file_dict[path]
        entry[0] += added
        entry[1] += removed
    else:
        # print(f"{path} ADDED {added} REMOVED {removed}")
        file_dict[path] = [added, removed]


def sortSecond(val):
    return val[1]


def parse_args():
    parser = argparse.ArgumentParser(prog="treemap", 
                                    description="Aggregates the change history of files in a Git repo")
    parser.add_argument('repo_path',
                        help='the location of the Git repo to analyze')
    parser.add_argument('-b', '--begin', 
                        help='when the log analysis begins (ISO8601 format)')
    parser.add_argument('-e', '--end', 
                        help='when the log analysis ends (ISO8601 format)')
    # parser.add_argument('-o', '--output', 
    #                     help="filename for output (defaults to stdout)")
    parser.add_argument('-s', '--summary', default=False, action='store_true',
                        help='Only emit a rollup of all changed files across the analyzed commits')
    parser.add_argument('-f', '--format', 
                        choices=['json','csv','treemap'], 
                        default='treemap', 
                        help='the desired output (json, csv, or treemap)')

    return parser.parse_args()


def build_git_command(args):
    git_cmd = f"git log --numstat --date=iso"

    if args.begin:
        git_cmd += f" --since={args.begin}"

    if args.end:
        git_cmd += f" --until={args.end}"

    return git_cmd


def reduce_log_to_file_changes(log):
    changed_files = defaultdict(int)
    for entry in log:
        files = entry['files']
        for path in files.keys():
            # stop me before I kill again
            changed_files[path] += reduce(lambda addend, augend : addend + augend, files[path])
    return changed_files


def escape_csv(s):
    if s.find(',') >= 0:
        return f"\"{s}\""
    else:
        return s


def list_to_csv(l):
    return ','.join(map(escape_csv, list(map(str, l))))


def minimum_unique_paths(paths):
    piece_count = defaultdict(int)
    unique_paths = []
    paths_by_pieces = []
    for path in paths:
        pieces = path.split('/')
        pieces.reverse()
        piece_collection = {}
        for index, piece in enumerate(pieces):
            piece_collection[index+1] = '/'.join(pieces[0:index+1])
        paths_by_pieces.append(piece_collection)
    # This function is not complete...

args = parse_args()
repo_dir = args.repo_path
git_cmd = build_git_command(args)

completed_process = subprocess.run(git_cmd.split(), cwd=repo_dir, capture_output=True, universal_newlines=True)
log = parse_git_log(completed_process.stdout)
changed_files = reduce_log_to_file_changes(log)

sorted_changes = []
for path in changed_files:
    sorted_changes.append([path, changed_files[path]])
sorted_changes.sort(key=sortSecond, reverse=True)

changes = []
paths = []
for change in sorted_changes:
    changes.append(change[1])
    paths.append(change[0])

just_files = list(map(lambda path: path.split('/')[-1], paths))

if args.format == 'treemap':
    squarify.plot(changes, label=paths)
    plt.axis("off")
    plt.show()
    exit()
elif args.format == 'json':
    if args.summary:
        print(json.dumps(list(map(lambda e : {e[0]:e[1]}, sorted_changes))))
    else:
        print(json.dumps(log))
    exit()
elif args.format == 'csv':
    print(log)
    if args.summary:
        print('path,changes')
        for change in sorted_changes:
            print(list_to_csv([change[0], change[1]]))
    else:
        print("path,additions,deletions,commit,authorName,authorEmail,timestamp")
        for entry in log:
            for file in entry['files']:
                fields = [file,entry['files'][file][0],entry['files'][file][1],entry['commit'],entry['author_name'],entry['author_email'],entry['timestamp']]
                print(list_to_csv(fields))
    exit()

