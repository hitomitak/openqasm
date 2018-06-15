"""
To generate a Bernstein-Vazirani algorithm using 5 qubits, type the following.

python bv_gen.py -q 5 -o bv5
The resulting circuit is stored at bv5.qasm and its drawing at bv5.tex.

For more details, run the above command with -h or --help argument.

@author Raymond Harry Rudy rudyhar@jp.ibm.com
"""
import sys
import argparse
import random
from qiskit import QuantumProgram

if sys.version_info < (3, 5):
    raise Exception("Please use Python 3.5 or later")


def print_qasm(acircuit, comments=None, outname=None):
    """
        print qasm string with comments
    """
    if outname is None:
        for each in comments:
            print("//"+each)
        print(acircuit)
    else:
        if not outname.endswith(".qasm"):
            outfilename = outname + ".qasm"
        outfile = open(outfilename, "w")
        for each in comments:
            outfile.write("//"+each)
            outfile.write("\n")
        outfile.write(acircuit)
        outfile.close()


def generate_astring(nqubits, prob=1.0):
    """
        generate a random binary string as a hidden bit string
    """
    answer = []
    for _ in range(nqubits):
        if random.random() <= prob:
            answer.append("1")
        else:
            answer.append("0")

    return "".join(answer)


def bin2int(alist):
    """
        convert a binary string into integer
    """
    answer = 0
    temp = alist
    temp.reverse()
    for i in range(temp):
        answer += 2**int(temp[i])
    temp.reverse()
    return answer


def check_astring(astring, nqubits):
    """
        check the validity of string
    """
    if len(astring) > nqubits:
        raise Exception("The length of the hidden string is \
                         longer than the number of qubits")
    else:
        for i in astring:
            if i != "0" and i != "1":
                raise Exception("Found nonbinary string at "+astring)
    return True


def gen_bv_main(nqubits, hiddenstring):
    """
        generate a circuit of the Bernstein-Vazirani algorithm
    """
    q_program = QuantumProgram()
    # Creating registers
    # qubits for querying the oracle and finding the hidden integer
    q_r = q_program.create_quantum_register("qr", nqubits)
    # for recording the measurement on qr
    c_r = q_program.create_classical_register("cr", nqubits-1)

    circuitname = "BernsteinVazirani"
    bvcircuit = q_program.create_circuit(circuitname, [q_r], [c_r])

    # Apply Hadamard gates to the first
    # (nQubits - 1) before querying the oracle
    for i in range(nqubits-1):
        bvcircuit.h(q_r[i])

    # Apply 1 and Hadamard gate to the last qubit
    # for storing the oracle's answer
    bvcircuit.x(q_r[nqubits-1])
    bvcircuit.h(q_r[nqubits-1])

    # Apply barrier so that it is not optimized by the compiler
    bvcircuit.barrier()

    # Apply the inner-product oracle
    hiddenstring = hiddenstring[::-1]
    for index, element in enumerate(hiddenstring):
        if element == "1":
            bvcircuit.cx(q_r[index], q_r[nqubits-1])
    hiddenstring = hiddenstring[::-1]
    # Apply barrier
    bvcircuit.barrier()

    # Apply Hadamard gates after querying the oracle
    for i in range(nqubits-1):
        bvcircuit.h(q_r[i])

    # Measurement
    for i in range(nqubits-1):
        bvcircuit.measure(q_r[i], c_r[i])

    return q_program, [circuitname, ]


def main(nqubits, hiddenstring, prob, outname):
    """
    main function
    """
    if hiddenstring is None:
        hiddenstring = generate_astring(nqubits-1, prob)
    assert check_astring(hiddenstring, nqubits-1) is True, "Invalid hidden str"

    comments = ["Bernstein-Vazirani with " + str(nqubits) + " qubits.",
                "Hidden string is " + hiddenstring]
    q_p, names = gen_bv_main(nqubits, hiddenstring)

    if outname is None:
        outname = "bv_n" + str(nqubits)

    for each in names:
        print_qasm(q_p.get_qasm(each), comments, outname)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Generate qasm of \
                                                  the Bernstein-Vazirani \
                                                  algorithm.")
    PARSER.add_argument("-q", "--qubits", type=int, default=16,
                        help="number of qubits")
    PARSER.add_argument("-p", "--prob", type=float, default=1.0,
                        help="probability of 1 of the hidden bit")
    PARSER.add_argument("-a", "--astring", default=None,
                        help="the hidden bitstring")
    PARSER.add_argument("-s", "--seed", default=0,
                        help="the seed for random number generation")
    PARSER.add_argument("-o", "--output", default=None, type=str,
                        help="output filename")
    ARGS = PARSER.parse_args()
    # initialize seed
    random.seed(ARGS.seed)
    main(ARGS.qubits, ARGS.astring, ARGS.prob, ARGS.output)
