"""
Qiskit Executor
"""
import os
import time
import json
import qiskit


class QiskitExecutor(object):
    """
    Qiskit Executor
    """
    def __init__(self, executor):
        self.name = "qiskit_"
        self.seed = executor.seed
        self.application = executor.name
        self.backend_name = executor.backend_name
        self.result = None
        self.filename = None

    def run_simulation(self, filename=None, qasm_text=None):
        """
        Execute Simulator
        """
        q_prog = qiskit.QuantumProgram()
        self.backend_name = self.backend_name.replace("qiskit_", "")

        if self.backend_name.startswith("ibmqx"):
            import Qconfig
            q_prog.set_api(Qconfig.APItoken, Qconfig.config['url'])
        elif not self.backend_name.startswith("local"):
            raise Exception('only ibmqx or local simulators are supported')

        if filename is not None:
            self.filename = filename
            q_prog.load_qasm_file(filename, name=self.application)
        elif qasm_text:
            q_prog.load_qasm_text(qasm_text, name=self.application)
        else:
            raise Exception("no qasm data")

        start = time.time()
        ret = q_prog.execute([self.application], backend=self.backend_name, shots=1,
                             max_credits=5, hpc=None,
                             timeout=60*60*24, seed=self.seed)
        elapsed = time.time() - start

        if not ret.get_circuit_status(0) == "DONE":
            return -1.0

        if self.backend_name.startswith("ibmqx"):
            elapsed = ret.get_data(self.application)["time"]

        self.result = ret.get_counts(self.application)
        return elapsed

    def verify_result(self, depth=0, qubit=0):
        """
        Verify Simulation Result
        """
        if not self.filename:
            if depth > 0:
                self.filename = self.application + "_n" + qubit + "_d" + depth + ".qasm"
            else:
                self.filename = self.application + "_n" + qubit + ".qasm"

        if not os.path.exists("qasm/"+self.application + "/ref"):
            raise Exception("Verification not support for " + self.application)

        ref_file_name = "qasm/"+self.application + "/ref/" + \
                        os.path.basename(self.filename)+"."+self.backend_name+".ref"
        if not os.path.exists(ref_file_name):
            raise Exception("Reference file not exist: " + ref_file_name)

        ref_file = open(ref_file_name)
        ref_data = ref_file.read()
        ref_file.close()
        ref_data = json.loads(ref_data)
        sim_result_keys = self.result.keys()

        for key in sim_result_keys:
            if key not in ref_data:
                raise Exception(key + " not exist in " + ref_file_name)
            ref_count = ref_data[key]
            count = self.result[key]

            if ref_count != count:
                raise Exception(" Count is differ: " + str(count) +
                                " and " + str(ref_count))
