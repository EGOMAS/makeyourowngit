import sys
import os
import zlib
import hashlib

def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file" and sys.argv[2] == "-p":
        file = sys.argv[3]
        filename = f".git/objects/{file[0:2]}/{file[2:]}"
        if not os.path.exists(filename):
            raise RuntimeError(f"Object {file} not found")
        with open(filename, "rb") as f:
            data = f.read()
            data = zlib.decompress(data)

            header_end = data.find(b"\x00")
            header = data[:header_end]
            content = data[header_end + 1:]

            if not header.startswith(b"blob "):
                raise RuntimeError("Not a blob object!")

            print(content.decode("utf-8"), end="")
    # this time the command is hash-object
    elif command == "hash-object" and len(sys.argv) < 4 and sys.argv[2] == "-w":
        if sys.argv[2] != "-w":
            raise RuntimeError(f"Unexpected flag #{sys.argv[2]}")
        # the file is again the 3rd index of our git command
        file = sys.argv[3]
        # opening our file and setting it to read binary mode and defining it as f
        with open(file, "rb") as f: 
            # now we're reading {f} and defining our blob header and how it's structured, with the blob, then it's size, and a null byte
            content = f.read()
            header = f"blob {len(content)}\0".encode("utf-8")
            
            # blob is your data
            blob = content + header
            
            sha = hashlib.sha1(blob).hexdigest()
            # compresing our data 
            zlib.compress(blob)
            
            # storing our data at .git/object/3c for example
            storedLocation = f".git/object/{sha[:2]}"
            # next to lines tell the files name instead of our folders name. So if our full file name is 3c09187hi13uhwjg71397fhss,
            # it'll take everything after the 2nd character and put it into our file_name variable. 
            # and finally our full_path takes both and combines them into a single path 3c/091279... you get the idea
            file_name = f"{sha[2:]}"
            full_path = os.path.join(file_name, full_path)
            
            #if the path doesn't exist, it'll make new one then basically do everything exactly the same except it'll write binary instead of read, and add compressed to our file.
            if not os.path.exists(full_path):
                compressed = zlib.compress(blob)
                os.makedirs(file_name, full_path)
                with open(full_path, "wb") as f:
                    f.write(compressed)           
            print(sha)


    else:
        raise RuntimeError(f"Unknown command #{command}")
if __name__ == "__main__":
    main()