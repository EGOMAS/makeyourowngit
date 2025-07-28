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

def commit_tree(message: str, parent=None):
    tree_sha = write_tree()
    lines = []
    timestamp = int(time.time())
    timezone = "+0000"
    name = input("Please Input your name for the commmit.\n")
    email = input("Please input your email for the commit.\n")
    lines.append(timestamp, timezone, name, email, tree_sha)
    commit_sha =f"tree <{tree_sha}>\n author <{name}> <{email}> <{timestamp}> <{timezone}>\n committer <{name}> <{email}> <{timestamp}> <{timezone}>\n <commit {message}>"

    return commit_sha

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
    
    elif command == "commit_tree"(sha, input("message"),):
        print(commit_tree)
    
    else:
        raise RuntimeError(f"Unknown command: {command}")


if __name__ == "__main__":
    main()