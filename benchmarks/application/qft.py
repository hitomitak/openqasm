""" QSAM-Bench is a quantum-software bencmark suite """
import math
from qiskit import QuantumProgram


class QFT:
    """
    QFT Generator
    """
    def __init__(self, seed):
        self.name = "qft"
        self.seed = seed

    @classmethod
    def cu1(cls, circ, l_value, a_value, b_value):
        """
        cu1 gate
        """
        circ.u1(l_value/2, a_value)
        circ.cx(a_value, b_value)
        circ.u1(-l_value/2, b_value)
        circ.cx(a_value, b_value)
        circ.u1(l_value/2, b_value)

    def qft(self, circ, qreg, num):
        """n-qubit QFT on q in circ."""
        for j in range(num):
            for k in range(j):
                self.cu1(circ, math.pi/float(2**(j-k)), qreg[j], qreg[k])
                circ.h(qreg[j])

    def build_model_circuits(self, num):
        """
        create model
        """
        q_p = QuantumProgram()
        qreg = q_p.create_quantum_register("q", num)
        creg = q_p.create_classical_register("c", num)

        qftcirc = q_p.create_circuit("meas", [qreg], [creg])

        self.qft(qftcirc, qreg, creg)
        qftcirc.barrier(qreg)

        for j in range(num):
            qftcirc.measure(qreg[j], creg[j])

        q_p.add_circuit("qft" + "_n" + str(num), qftcirc)
        return q_p

    def gen_application(self, app_arg):
        """
        generate application
        """
        qubits = app_arg["qubit"]
        q_p = self.build_model_circuits(qubits)
        qasm_data = q_p.get_qasm(name="qft"+"_n"+str(qubits))
        return qasm_data
