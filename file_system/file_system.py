from platform import node

from .file_node import FileNode


class FileSystem:
    def __init__(self):
        self.root = FileNode("root", is_directory=True)
        self.current_directory = self.root

    def create_file(self, filename):
        file_node = FileNode(filename, is_directory=False)
        self.current_directory.add_child(file_node)

    def create_directory(self, dirname):
        dir_node = FileNode(dirname, is_directory=True)
        self.current_directory.add_child(dir_node)

    def list(self):
        file_list = [child.name for child in self.current_directory.children]
        print(file_list)
        return file_list

    def change_directory(self, dirname):
        if dirname == "..":
            if self.current_directory.parent is not None:
                self.current_directory = self.current_directory.parent
            return
        for child in self.current_directory.children:
            if child.name == dirname and child.is_directory:
                self.current_directory = child
                return
        raise ValueError(f"Directory '{dirname}' not found.")

    def get_properties(self, name):
        for child in self.current_directory.children:
            if child.name == name:
                return child.get_properties()
        raise ValueError(f"File or directory '{name}' not found.")

    def delete(self, filename):
        for child in self.current_directory.children:
            if child.name == filename:
                self.current_directory.children.remove(child)
                return
        raise ValueError(f"File or directory '{filename}' not found.")

    def find(self, name, node=None, results=None):
        if node is None:
            node = self.root

        if results is None:
            results = []

        if node.name == name:
            results.append(node)

        if node.is_directory:
            for child in node.children:
                self.find(name, child, results)

        return results

    def get_directory_tree(self, node=None, prefix=""):
        if node is None:
            node = self.root
        tree_str = f"{prefix}{node.name}/\n" if node.is_directory else f"{prefix}{node.name}\n"
        if node.is_directory:
            for child in node.children:
                tree_str += self.get_directory_tree(child, prefix + "  ")
        return tree_str
