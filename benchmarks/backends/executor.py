"""
Executor Class
"""
from backends.qiskit_executor import QiskitExecutor
from backends.qsharp_executor import QsharpExecutor
from backends.projectq_executor import ProjectQExecutor


class Executor:
    """
    Backend Executor
    """
    def __init__(self, backend_name=None, name=None, seed=None):
        self.seed = seed
        self.name = name
        self.backend_name = backend_name
        self.backend_list = [QiskitExecutor(self), QsharpExecutor(self), ProjectQExecutor(self)]
        return

    def get_backend(self, name):
        """
        get backend class
        """
        for backend in self.backend_list:
            if "qiskit_" in name and "qiskit_" in backend.name:
                return backend
            if name == backend.name:
                return backend
        return None

    def get_backend_name_list(self):
        """
        get backend name list
        """
        name_list = []
        for backend in self.backend_list:
            name = backend.name
            name_list.append(name)
        return name_list
