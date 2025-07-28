import sys
import os
import zlib
import hashlib
import time 


def init_git():
    # Initialize a new git repository structure
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def hash_object(data: bytes, obj_type: str = "blob", write: bool = True) -> str:
    # Create a SHA-1 hash of the object
    header = f"{obj_type} {len(data)}".encode("utf-8") + b"\x00"
    full_data = header + data
    sha = hashlib.sha1(full_data).hexdigest()
    # If write is True, save the object to the .git/objects directory
    if write:
        dir_path = f".git/objects/{sha[:2]}"
        file_path = f"{dir_path}/{sha[2:]}"
        os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(zlib.compress(full_data))
    return sha
# This function retrieves and prints the content of a blob object given its SHA-1 hash.
def cat_file(sha: str):
    # Check if the object exists in the .git/objects directory
    file_path = f".git/objects/{sha[:2]}/{sha[2:]}"
    if not os.path.exists(file_path):
        raise RuntimeError(f"Object {sha} not found")
    # Read and decompress the object
    with open(file_path, "rb") as f:
        compressed = f.read()
        data = zlib.decompress(compressed)
    # Extract the header and content from the decompressed data
    header_end = data.find(b"\x00")
    header = data[:header_end]
    content = data[header_end + 1:]
    # Check if the header is valid for a blob object
    if not header.startswith(b"blob"):
        raise RuntimeError("Not a blob object!")

    print(content.decode("utf-8"), end="")

# This function writes a tree object based on the current directory's files.
def write_tree():  
    # Collect all files in the current directory, excluding .git
    files = [filename for filename in os.listdir() if os.path.isfile(filename) and filename != ".git"]
    entries = []
    for filename in files:
        with open(filename, "rb") as f:
            content = f.read()
            sha = hash_object(content, "blob")
            entry = f"100644 {filename}".encode() + b"\x00" + bytes.fromhex(sha)
            entries.append(entry)
    # Create the tree object         
    tree_data = b"".join(entries)
    header = f"tree {len(tree_data)}\0".encode()
    full_tree = header + tree_data
    full_sha = hashlib.sha1(full_tree).hexdigest()
    
    # Write the tree object to the .git/objects directory
    dir_path = f".git/objects/{full_sha[:2]}"
    file_path = f"{dir_path}/{full_sha[2:]}"
    os.makedirs(dir_path, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(zlib.compress(full_tree))

    print(f"Added {filename} with blob SHA {sha}")

    return full_sha   

# This function gets the users info and returns it in the Git format.
def get_user_info(role: str) -> str:
    name, email = input(f"{role} (format: Name Email) ").split()
    t = int(time.time())
    timezone = "+0000"
    return f"{role.lower()} {name} <{email}> {t} {timezone}"

# This builds the whole commit lines and content using all the information like the SHA code, author and commiter's lines.
def build_commit_content(tree_sha, parent_sha, author_line, committer_line, message):
    lines = [f"tree {tree_sha}"]
    if parent_sha:
        lines.append(f"parent {parent_sha}")
    lines += [author_line, committer_line, "", message]
    return("\n".join(lines) +"\n")

# This combines the previous two functions to write out the commit and hash it, compress it, and store it in the .git/HEAD folder.
def commit_tree(message: str, parent=None):
    tree_sha = write_tree()
    parent_sha = parent or get_head_commit()
    
    author_line = get_user_info("Author")
    committer_line = get_user_info("Committer")
    
    content = build_commit_content(tree_sha, parent_sha, author_line, committer_line, message)
    commit_bytes = content.encode()
    header = f"commit {len(commit_bytes)}\x00".encode()
    store = header + commit_bytes
    
    sha = hashlib.sha1(store).hexdigest()
    write_object(sha, store)
    
    with open(".git/HEAD", "w") as f:
        f.write(sha)

def write_object(sha, data):
    dir_path = f".git/objects/{sha[:2]}"
    file_path = f"{dir_path}/{sha[2:]}"
    os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(zlib.compress(data))

def get_head_commit():
    try:
        with open(".git/HEAD", "r") as f:
            ref = f.read().strip()
        if ref.startswith("ref: "):
            ref_path = ref[5:]
            full_path = os.path.join(".git", ref_path)
            if os.path.exists(full_path):
                with open(full_path, "r") as rf:
                    return rf.read().strip()
    except FileNotFoundError:
        pass
    return None
# Main function to handle command line arguments and execute git-like commands
def main():
    command = sys.argv[1]

    if command == "init":
        init_git()

    elif command == "cat-file" and sys.argv[2] == "-p":
        sha = sys.argv[3]
        cat_file(sha)

    elif command == "hash-object" and sys.argv[2] == "-w":
        file = sys.argv[3]
        with open(file, "rb") as f:
            data = f.read()
        sha = hash_object(data, "blob", write=True)
        print(sha)
    elif command == "write-tree":
        sha = write_tree()
        print(sha)
    
    elif command == "commit-tree":
        message = input("Commit message: ")
        commit_tree(message)
  
    
    else:
        raise RuntimeError(f"Unknown command: {command}")


if __name__ == "__main__":
    main()