from datetime import datetime


class FileNode:
    def __init__(self, name, is_directory=False):
        self.name = name
        self.creation_date = datetime.now()
        self.modification_date = datetime.now()
        self.size = 0
        self.is_directory = is_directory
        self.children = [] if is_directory else None
        self.parent = None

    def add_child(self, child_node):
        if not self.is_directory:
            raise ValueError("Cannot add a child to a non-directory node.")
        self.children.append(child_node)
        child_node.parent = self

    def get_properties(self):
        return {
            "name": self.name,
            "creation_date": self.creation_date,
            "modification_date": self.modification_date,
            "size": self.size,
            "is_directory": self.is_directory,
        }

    def __repr__(self):
        return f"FileNode(name={self.name}, is_directory={self.is_directory})"
