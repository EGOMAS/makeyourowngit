import sys
import os
import zlib
import hashlib

def init_git():
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def hash_object(data: bytes, obj_type: str = "blob", write: bool = True) -> str:
    header = f"{obj_type} {len(data)}".encode("utf-8") + b"\x00"
    full_data = header + data
    sha = hashlib.sha1(full_data).hexdigest()

    if write:
        dir_path = f".git/objects/{sha[:2]}"
        file_path = f"{dir_path}/{sha[2:]}"
        os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(zlib.compress(full_data))
    return sha

def cat_file(sha: str):
    file_path = f".git/objects/{sha[:2]}/{sha[2:]}"
    if not os.path.exists(file_path):
        raise RuntimeError(f"Object {sha} not found")

    with open(file_path, "rb") as f:
        compressed = f.read()
        data = zlib.decompress(compressed)

    header_end = data.find(b"\x00")
    header = data[:header_end]
    content = data[header_end + 1:]

    if not header.startswith(b"blob"):
        raise RuntimeError("Not a blob object!")

    print(content.decode("utf-8"), end="")

def write_tree():  
    files = [filename for filename in os.listdir() if os.path.isfile(filename) and filename != ".git"]
    entries = []
    for filename in files:
        with open(filename, "rb") as f:
            content = f.read()
            sha = hash_object(content, "blob")
            entry = f"100644 {filename}".encode() + b"\x00" + bytes.fromhex(sha)
            entries.append(entry)
            
    tree_data = b"".join(entries)
    header = f"tree {len(tree_data)}\0".encode()
    full_tree = header + tree_data
    full_sha = hashlib.sha1(full_tree).hexdigest()
    
    dir_path = f".git/objects/{full_sha[:2]}"
    file_path = f"{dir_path}/{full_sha[2:]}"
    os.makedirs(dir_path, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(zlib.compress(full_tree))
    
    print(f"Added {filename} with blob SHA {sha}")

    return full_sha   

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
    else:
        raise RuntimeError(f"Unknown command: {command}")

if __name__ == "__main__":
    main()