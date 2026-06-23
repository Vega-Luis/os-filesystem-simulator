from file_system import FileSystem


def main():
    file_system = FileSystem()
    file_system.list()
    file_system.create_file("file1.txt")
    file_system.create_directory("dir1")
    file_system.list()
    file_system.change_directory("dir1")
    file_system.create_file("file2.txt")
    file_system.list()
    file_system.change_directory("..")
    file_system.list()
    print(file_system.get_properties("dir1"))
    file_system.delete("file1.txt")
    file_system.list()
    file_system.delete("dir1")
    file_system.list()
    file_system.create_file("file3.txt")
    file_system.create_directory("dir2")
    file_system.list()
    print(file_system.get_directory_tree())
    file_system.change_directory("dir2")
    file_system.create_file("file4.txt")
    file_system.create_directory("dir3")
    file_system.change_directory("dir3")
    file_system.create_file("file4.txt")
    print(file_system.get_directory_tree())
    print(file_system.find("file4.txt"))


if __name__ == "__main__":
    main()
