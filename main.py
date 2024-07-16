from rclone_python import rclone
import os
import re
import time
from rich import print
import argparse

# Argument --limit to specify the space limit in TB
parser = argparse.ArgumentParser(description="Copy data between rclone remotes")
parser.add_argument("--limit", type=int, default=10, help="Space limit in TB")

# Argument --free to indicate that all available space should be freed in the source remote by moving data to other remotes
parser.add_argument("--free", action="store_true", help="Free up space in the source remote")

# Argument --remotes to specify the remotes to use, it receives a comma-separated string and converts it to a list
parser.add_argument("--remotes", required=True, help="List of remotes separated by commas")

# Argument --config to specify the path to the rclone.conf file
parser.add_argument("--config", required=True, help="Path to the rclone.conf file")

args = parser.parse_args()

# Convert remotes to a list
remotes = args.remotes.split(',')

def get_folders(remote):
    """
    Gets the list of folders from a specific remote.
    """
    rclone_options = [
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--checkers=8',
        '-R',
        f'--config={args.config}'
    ]
    folders = rclone.ls(remote, dirs_only=True, args=rclone_options)
    return [folder['Path'] for folder in folders]

def create_folders(target_remote, folders):
    """
    Creates the specified folders in the target remote.
    """
    rclone_options = [
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--checkers=8',
        '--log-file=rclone.log',
        f'--config={args.config}'
    ]
    for folder in folders:
        rclone.mkdir(target_remote + folder, args=rclone_options)

def compare_folders(remote1, remote2):
    """
    Compares folders between two remotes and returns the folders that are in remote1 but not in remote2.
    """
    folders1 = get_folders(remote1)
    folders2 = get_folders(remote2)
    return [folder for folder in folders1 if folder not in folders2]

def save_folders():
    """
    Saves folders from one remote to another if they do not exist.
    """
    for remote in remotes:
        for target_remote in remotes:
            if target_remote != remote:
                print(f"Comparing folders in {remote} with {target_remote}")
                folders = compare_folders(remote, target_remote)
                print(f'[blue]A total of {len(folders)} folders will be created in {target_remote}[/blue]')
                create_folders(target_remote, folders)

def check_files(remote1, remote2, file_list):
    """
    Checks files between two remotes using a specific file list.
    """
    log_file = 'rclone.log'
    rclone_options = [
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--checkers=8',
        f'--log-file={log_file}',
        f'--config={args.config}'
    ]

    print("[blue]Checking files in the remotes, please wait[/blue]")
    rclone.check(remote1, remote2, one_way=True, match=file_list, args=rclone_options)
    try:
        os.remove(log_file)
    except Exception as e:
        print(f"[red]Error deleting log file: {e}[/red]")

def get_size(remote, file_list):
    """
    Gets the size and number of files from a remote based on a file list.
    """
    rclone_options = [
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--checkers=8',
        f'--files-from={file_list}',
        f'--config={args.config}'
    ]
    size = rclone.size(remote, args=rclone_options)
    return size['bytes'], size['count']

def get_remote_size(remote):
    """
    Gets the total size of the used space in a remote.
    """
    size = rclone.about(remote, args=[f'--config={args.config}'])
    return size['bytes']

def after_copy(destination, input_file, output_file):
    """
    Processes the log file after copying files and returns the size and number of copied files.
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            if 'INFO' in line and 'Copied' in line:
                match = re.search(r'INFO\s+:\s+(.*?): Copied', line)
                if match:
                    file.write(match.group(1) + '\n')
    try:
        os.remove(input_file)
    except Exception as e:
        print(f"[red]Error deleting input file: {e}[/red]")
    return get_size(destination, output_file)

def copy_files(source, destination, max_transfer_size):
    """
    Copies files from one remote to another while respecting the maximum transfer size.
    """
    log_file = 'copy.log'
    output_file = 'output.txt'
    rclone_options = [
        '--server-side-across-configs',
        '--transfers=4',
        '--checkers=8',
        f'--max-transfer={max_transfer_size}',
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--check-first',
        '--order-by=size,desc',
        '--size-only',
        '--no-check-dest',
        '--ignore-checksum',
        f'--log-file={log_file}',
        '--log-level', 'INFO',
        f'--config={args.config}'
    ]
    start_time = time.time()
    rclone.copy(source, destination, ignore_existing=True, show_progress=True, args=rclone_options)
    total_time = calculate_time(time.time() - start_time)
    size, files = after_copy(f'{destination}', log_file, output_file)
    size_human_readable = calculate_size(size)
    print(f'[green]Copy completed, total size: {size_human_readable}, total files: {files}, elapsed time: {total_time}[/green]')
    try:
        os.remove(output_file)
    except Exception as e:
        print(f"[red]Error deleting output file: {e}[/red]")
    return size

def delete_files(remote1, remote2, file_list):
    """
    Deletes files from a remote based on a file list.
    """
    rclone_options = [
        '--user-agent="ISV|rclone.org|rclone/v1.67.0"',
        '--tpslimit=8',
        '--onedrive-delta',
        '--fast-list',
        '--transfers=8',
        '--checkers=8',
        f'--log-file=rclone.log',
        '--files-from', file_list,
        '--onedrive-hard-delete',
        f'--config={args.config}'
    ]
    print(f'[red]Deleting files from {remote1}[/red]')
    start_time = time.time()
    rclone.delete(remote1, args=rclone_options)
    total_time = calculate_time(time.time() - start_time)
    try:
        os.remove('rclone.log')
    except Exception as e:
        print(f"[red]Error deleting log file: {e}[/red]")
    size, files = get_size(remote2, file_list)
    size = calculate_size(size)
    print(f'[green]Delete completed, total size: {size}, total files: {files}, elapsed time: {total_time}[/green]')
    try:
        os.remove(file_list)
    except Exception as e:
        print(f"[red]Error deleting file list: {e}[/red]")

def calculate_time(seconds):
    """
    Converts time in seconds to a string in hh:mm:ss format.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def calculate_size(size):
    """
    Converts a size in bytes to a human-readable string (KB, MB, GB, TB).
    """
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 ** 2:
        return f"{round(size / 1024, 2)} KB"
    elif size < 1024 ** 3:
        return f"{round(size / 1024 ** 2, 2)} MB"
    elif size < 1024 ** 4:
        return f"{round(size / 1024 ** 3, 2)} GB"
    else:
        return f"{round(size / 1024 ** 4, 2)} TB"

def rclone_calculate_size(size):
    """
    Converts a size in bytes to a rclone-readable string (K, M, G, T).
    """
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 ** 2:
        return f"{round(size / 1024, 2)}K"
    elif size < 1024 ** 3:
        return f"{round(size / 1024 ** 2, 2)}M"
    elif size < 1024 ** 4:
        return f"{round(size / 1024 ** 3, 2)}G"
    else:
        return f"{round(size / 1024 ** 4, 2)}T"

def main():
    """
    Main function to manage data transfer between remotes.
    """
    space_limit_tb = args.limit * 1024 ** 4

    if args.free:
        source_remote = args.free
        
        print(f"[yellow]Freeing up space in the source remotes[/yellow]")
        
        source_size = get_remote_size(source_remote)
        # Moves all data from the remote specified in --free to other remotes to free up space, respecting the limit of each remote specified in --limit, source remote must be completely empty
        if source_size > 0:
            print(f'[yellow]{source_remote} exceeds the space limit: {calculate_size(source_size)}[/yellow]')

            excess_size = source_size
            while excess_size > 0:
                for i, destination_remote in enumerate(remotes):
                    if destination_remote != source_remote:
                        destination_size = get_remote_size(destination_remote)
                        available_space = space_limit_tb - destination_size
                        if available_space > 0:
                            if available_space < 0.5 * 1024 ** 4:
                                print(f'[yellow]Skipping {destination_remote} due to insufficient space. Available space: {calculate_size(available_space)}[/yellow]')
                                continue

                            transfer_size = min(excess_size, available_space)
                            max_transfer_size = rclone_calculate_size(transfer_size)

                            print(f"Copying {max_transfer_size} from {source_remote} to {destination_remote}")
                            copied_size = copy_files(source_remote, destination_remote, max_transfer_size)

                            # Check for duplicates and delete them
                            check_files(source_remote, destination_remote, 'duplicate_files.txt')
                            delete_files(source_remote, destination_remote, 'duplicate_files.txt')

                            excess_size -= copied_size

                        if excess_size <= 0:
                            break
        
    else:
        print(f"[yellow]Copying data between remotes[/yellow]")

        for i, source_remote in enumerate(remotes):
            source_size = get_remote_size(source_remote)
            if source_size > space_limit_tb:
                print(f'[yellow]{source_remote} exceeds the space limit: {calculate_size(source_size)}[/yellow]')
                excess_size = source_size - space_limit_tb
                while excess_size > 0:
                    for j, destination_remote in enumerate(remotes):
                        if i != j:
                            destination_size = get_remote_size(destination_remote)
                            available_space = space_limit_tb - destination_size
                            if available_space > 0:
                                if available_space < 0.5 * 1024 ** 4:
                                    print(f'[yellow]Skipping {destination_remote} due to insufficient space. Available space: {calculate_size(available_space)}[/yellow]')
                                    continue

                                transfer_size = min(excess_size, available_space)
                                max_transfer_size = rclone_calculate_size(transfer_size)

                                print(f"Copying {max_transfer_size} from {source_remote} to {destination_remote}")
                                copied_size = copy_files(source_remote, destination_remote, max_transfer_size)

                                # Check for duplicates and delete them
                                check_files(source_remote, destination_remote, 'duplicate_files.txt')
                                delete_files(source_remote, destination_remote, 'duplicate_files.txt')

                                excess_size -= copied_size

                            if excess_size <= 0:
                                break

            else:
                print(f'[green]{source_remote} is within the space limit: {calculate_size(source_size)}[/green]')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[red]Operation cancelled by user[/red]")
        exit(0)
