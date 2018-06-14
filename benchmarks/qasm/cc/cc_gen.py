"""
To generate a circuit for counterfeit-coin finding
algorithm using 15 coins and the false coin is the third coin,
type the following.

python cc_gen.py -c 15 -f 3

@author Raymond Harry Rudy rudyhar@jp.ibm.com
"""
import sys
import argparse
import random
from qiskit import QuantumProgram
from qiskit.tools.visualization import latex_drawer

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


def draw_circuit(acircuit, outfilename="bv.tex"):
    """
        draw the circuit
    """
    latex_drawer(acircuit, outfilename, basis="h,x,cx")


def generate_false(ncoins):
    """
        generate a random index of false coin (counting from zero)
    """
    return random.randint(0, ncoins-1)


def gen_cc_main(ncoins, index_of_false_coin):
    """
        generate a circuit of the counterfeit coin problem
    """
    q_program = QuantumProgram()
    # using the last qubit for storing the oracle's answer
    nqubits = ncoins + 1
    # Creating registers
    # qubits for querying coins and storing the balance result
    q_r = q_program.create_quantum_register("qr", nqubits)
    # for recording the measurement on qr
    c_r = q_program.create_classical_register("cr", nqubits)

    circuitname = "CounterfeitCoinProblem"
    cccircuit = q_program.create_circuit(circuitname, [q_r], [c_r])

    # Apply Hadamard gates to the first ncoins quantum register
    # create uniform superposition
    for i in range(ncoins):
        cccircuit.h(q_r[i])

    # check if there are even number of coins placed on the pan
    for i in range(ncoins):
        cccircuit.cx(q_r[i], q_r[ncoins])

    # perform intermediate measurement to check if the last qubit is zero
    cccircuit.measure(q_r[ncoins], c_r[ncoins])

    # proceed to query the quantum beam balance if cr is zero
    cccircuit.x(q_r[ncoins]).c_if(c_r, 0)
    cccircuit.h(q_r[ncoins]).c_if(c_r, 0)

    # we rewind the computation when cr[N] is not zero
    for i in range(ncoins):
        cccircuit.h(q_r[i]).c_if(c_r, 2**ncoins)

    # apply barrier for marking the beginning of the oracle
    cccircuit.barrier()

    cccircuit.cx(q_r[index_of_false_coin], q_r[ncoins]).c_if(c_r, 0)

    # apply barrier for marking the end of the oracle
    cccircuit.barrier()

    # apply Hadamard gates to the first ncoins qubits
    for i in range(ncoins):
        cccircuit.h(q_r[i]).c_if(c_r, 0)

    # measure qr and store the result to cr
    for i in range(ncoins):
        cccircuit.measure(q_r[i], c_r[i])

    return q_program, [circuitname, ]


def main(ncoins, falseindex, draw, outname):
    """
    main function
    """
    comments = ["Counterfeit coin finding with " + str(ncoins) + " coins.",
                "The false coin is " + str(falseindex)]
    if outname is None:
        outname = "cc_n" + str(ncoins + 1)
    q_p, names = gen_cc_main(ncoins, falseindex)
    for each in names:
        print_qasm(q_p.get_qasm(each), comments, outname)
        if draw:
            if outname is None:
                midfix = "_"+str(ncoins)+"_"+str(falseindex)
                draw_circuit(q_p.get_circuit(each),
                             outfilename=each+midfix+".tex")
            else:
                draw_circuit(q_p.get_circuit(each),
                             outfilename=outname+".tex")


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Generate qasm of \
                                                  the counterfeit-coin \
                                                  finding algorithm.")
    PARSER.add_argument("-c", "--coins", type=int, default=16,
                        help="number of coins")
    PARSER.add_argument("-f", "--false", type=int, default=None,
                        help="index of false coin")
    PARSER.add_argument("-s", "--seed", default=0,
                        help="the seed for random number generation")
    PARSER.add_argument("-d", "--draw", default=False, type=bool,
                        help="flag to draw the circuit")
    PARSER.add_argument("-o", "--output", default=None, type=str,
                        help="output filename")
    ARGS = PARSER.parse_args()
    # initialize seed
    random.seed(ARGS.seed)

    if ARGS.false is None:
        ARGS.false = generate_false(ARGS.coins)
    main(ARGS.coins, ARGS.false, ARGS.draw, ARGS.output)
