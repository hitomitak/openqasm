"""
Generate (or run) randomized circuits for Quantum Volume analysis.

Example run:
  python quantum_volume.py -n 5 -d 5
"""

import math
import argparse
from numpy import random
from scipy import linalg
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.mapper import two_qubit_kak
from qiskit.wrapper import register, execute


def random_su(num):
    """Return an n x n Haar distributed unitary matrix,
    using QR-decomposition on a random n x n.
    """
    x_value = (random.randn(num, num) + 1j * random.randn(num, num))
    q_value, _ = linalg.qr(x_value)           # Q is a unitary matrix
    q_value /= pow(linalg.det(q_value), 1/num)  # make Q a special unitary
    return q_value


def build_model_circuits(num, depth, num_circ=1):
    """Create a quantum program containing model circuits.
    The model circuits consist of layers of Haar random
    elements of SU(4) applied between corresponding pairs
    of qubits in a random bipartition.

    Args:
        n (int): number of qubits
        depth (int): ideal depth of each model circuit (over SU(4))
        num_circ (int): number of model circuits to construct

    Returns:
        list(QuantumCircuit): list of quantum volume circuits
    """
    # Create quantum/classical registers of size n
    q_r = QuantumRegister(num)
    c_r = ClassicalRegister(num)
    # For each sample number, build the model circuits
    circuits = []
    for _ in range(num_circ):
        # Initialize empty circuit
        circuit = QuantumCircuit(q_r, c_r)
        # For each layer
        for _ in range(depth):
            # Generate uniformly random permutation Pj of [0...n-1]
            perm = random.permutation(num)
            # For each consecutive pair in Pj, generate Haar random SU(4)
            # Decompose each SU(4) into CNOT + SU(2) and add to Ci
            for k in range(math.floor(num/2)):
                qubits = [int(perm[2*k]), int(perm[2*k+1])]
                for gate in two_qubit_kak(random_su(4)):
                    i_0 = qubits[gate["args"][0]]
                    if gate["name"] == "cx":
                        i_1 = qubits[gate["args"][1]]
                        circuit.cx(q_r[i_0], q_r[i_1])
                    elif gate["name"] == "u1":
                        circuit.u1(gate["params"][2], q_r[i_0])
                    elif gate["name"] == "u2":
                        circuit.u2(gate["params"][1], gate["params"][2], q_r[i_0])
                    elif gate["name"] == "u3":
                        circuit.u3(gate["params"][0], gate["params"][1],
                                   gate["params"][2], q_r[i_0])
                    elif gate["name"] == "id":
                        pass
        # Barrier before measurement to prevent reordering, then measure
        circuit.barrier(q_r)
        circuit.measure(q_r, c_r)
        # Save sample circuit
        circuits.append(circuit)
    return circuits


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser(
        description="Create randomized circuits for quantum volume analysis.")
    parser.add_argument('--name', default='quantum_volume',
                        help='circuit name')
    parser.add_argument('-n', '--qubits', default=5, type=int,
                        help='number of circuit qubits')
    parser.add_argument('-d', '--depth', default=5, type=int,
                        help='SU(4) circuit depth')
    parser.add_argument('-s', '--seed', default=17, type=int,
                        help='random seed')
    parser.add_argument('--num_circ', default=1, type=int,
                        help='how many circuits?')
    parser.add_argument('-r', '--run', action='store_true',
                        help='execute circuit(s)')
    parser.add_argument('-b', '--backend', default='local_qasm_simulator',
                        help='backend to execute on')

    args = parser.parse_args()

    random.seed(args.seed)

    circuits = build_model_circuits(num=args.qubits, depth=args.depth,
                                    num_circ=args.num_circ)

    # Run the circuits
    if args.run:
        backend_name = args.backend
        if backend_name.startswith("ibmq"):
            import Qconfig
            register(Qconfig.APItoken, Qconfig.config['url'])
        result = execute(circuits, backend_name=backend_name)
        print(result.get_counts(circuits[0]))
        return

    # Save QASM representation of circuits
    for i in range(args.num_circ):
        file_fd = open('quantum_volume_n%d_d%d_%d.qasm' % (args.qubits, args.depth, i), 'w')
        file_fd.write(circuits[i].qasm())
        file_fd.close()


if __name__ == "__main__":
    main()
