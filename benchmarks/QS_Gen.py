""" QSAM-Bench is a quantum-software bencmark suite """
import argparse
import os.path
import sys
import re
import time
import json
import glob
import operator
import re

import qiskit

from qiskit import qasm, unroll, QISKitError
from qiskit.unroll._backenderror import BackendError
from qiskit.unroll._unrollerbackend import UnrollerBackend
from qiskit.qasm import Qasm

if sys.version_info < (3, 0):
    raise Exception("Please use Python version 3 or greater.")

class PrintQsharp(UnrollerBackend):
    """Backend for the unroller that prints Q# code.
    """

    def __init__(self, namespace, operation, file, basis=None):
        super().__init__(basis)
        self.prec = 15
        self.creg = None
        self.cval = None
        self.gates = {}
        self.comments = False
        if basis:
            self.basis = basis
        else:
            self.basis = []
        self.listen = True
        self.in_gate = ""
        self.printed_gates = []
        self.namespace = namespace
        self.operation = operation
        self.file = file
        self.level = 0
        
        self.qreg_name = ""
        self.qreg_size = 0
        self.creg_name = ""
        self.creg_size = 0
        
        self.print_header = False
        
    def _printCode(self, line, end="\n", withIndent=True):
        space = ""
        if withIndent:
            for i in range(self.level):
                space += "    "
        self.file.write(space + line + end)
        print (space + line, end=end)
    
    def set_comments(self, comments):
        pass

    def set_basis(self, basis):
        """Declare the set of user-defined gates to emit.

        basis is a list of operation name strings.
        """
        self.basis = basis
    
    def _printHeaderIfNecessary(self):
        if (not self.print_header and self.qreg_size != 0 and self.creg_size != 0):
            self._printCode("mutable %s = new Result[%d];" % (self.creg_name, self.creg_size))
            self._printCode("using (%s = Qubit[%d]) {" % (self.qreg_name, self.qreg_size))
            self.level += 1
            self.print_header = True

    def version(self, version):
        """Print the version string.

        v is a version number.
        """
        self._printCode("namespace QasmBench." + self.namespace + " {")
        self.level += 1
        
        self._printCode("open Microsoft.Quantum.Primitive;");
        self._printCode("open Microsoft.Quantum.Canon;");
        self._printCode("open Microsoft.Quantum.Extensions.Math;");
        
        self._printCode("operation " + self.operation + "() : Result[] {")
        self.level += 1
        
        self._printCode("body {")
        self.level += 1

    def new_qreg(self, name, size):
        if self.qreg_size != 0:
            raise Exception("support only one quantum register array")
        
        self.qreg_name = name;
        self.qreg_size = size;
        self._printHeaderIfNecessary()

    def new_creg(self, name, size):
        if self.creg_size != 0:
            raise Exception("support only one classical register array")
        self.creg_name = name;
        self.creg_size = size;
        self._printHeaderIfNecessary()
    
    def printFooter(self):
        self.level -= 1
        self._printCode("}")
        self._printCode("return %s;" % self.creg_name)
        self.level -= 1
        self._printCode("}")
        self.level -= 1
        self._printCode("}")
        self.level -= 1
        self._printCode("}")

    def define_gate(self, name, gatedata):
        """Define a new quantum gate.
 
        name is a string.
        gatedata is the AST node for the gate.
        """
        atomics = ["U", "CX", "measure", "reset", "barrier"]
        self.gates[name] = gatedata
        # Print out the gate definition if it is in self.basis
        if name in self.basis and name not in atomics:
            raise Exception("support only U, CX, MEASURE, RESET, and BARRIER: unsupport=" + name)
        pass
    
    def _resolve(self, line):
        return line.replace("pi", "PI()")
    
    def _printStartIf(self):
        for i in range(self.creg_size):
            if (i == 0):
                self._printCode("if (", end="")
            else:
                self._printCode(" && ", end="", withIndent=False)
            if (1 << i & self.cval == 0):
                self._printCode("(%s[%d]==Zero)" % (self.creg_name, i), end="", withIndent=False)
            else:
                self._printCode("(%s[%d]==One)" % (self.creg_name, i), end="", withIndent=False)
        self._printCode(") {", withIndent=False)
        self.level += 1
        
    def _printEndIf(self):
        self.level -= 1
        self._printCode("}")

    def u(self, arg, qubit, nested_scope=None):
        if self.listen:
            if "U" not in self.basis:
                self.basis.append("U")
                
            if self.creg is not None:
                self._printStartIf()
                
            self._printCode("//U(%s,%s,%s) %s[%d];" % (arg[0].sym(nested_scope),
                                           arg[1].sym(nested_scope),
                                           arg[2].sym(nested_scope),
                                           qubit[0],
                                           qubit[1]))
            if (arg[0].sym(nested_scope) != 0):
                self._printCode("Rz(%s, %s[%d]);" % (self._resolve(str(arg[0].sym(nested_scope))), qubit[0], qubit[1]))
            if (arg[1].sym(nested_scope) != 0):
                self._printCode("Ry(%s, %s[%d]);" % (self._resolve(str(arg[1].sym(nested_scope))), qubit[0], qubit[1]))
            if (arg[2].sym(nested_scope) != 0):
                self._printCode("Rz(%s, %s[%d]);" % (self._resolve(str(arg[2].sym(nested_scope))), qubit[0], qubit[1]))
            
            if self.creg is not None:
                self._printEndIf()

    def cx(self, qubit0, qubit1):
        """Fundamental two qubit gate.

        qubit0 is (regname,idx) tuple for the control qubit.
        qubit1 is (regname,idx) tuple for the target qubit.
        """
        if self.listen:
            if "CX" not in self.basis:
                self.basis.append("CX")
                
            if self.creg is not None:
                self._printStartIf()
            
            self._printCode("//CX %s[%d],%s[%d];" % (qubit0[0], qubit0[1], qubit1[0], qubit1[1]))
            self._printCode("CNOT (%s[%d], %s[%d]);"  % (qubit0[0], qubit0[1], qubit1[0], qubit1[1]))
            
            if self.creg is not None:
                self._printEndIf()

    def measure(self, qubit, bit):
        """Measurement operation.

        qubit is (regname, idx) tuple for the input qubit.
        bit is (regname, idx) tuple for the output bit.
        """
        if "measure" not in self.basis:
            self.basis.append("measure")
        if self.creg is not None:
            self._printCode("//if(%s==%d) " % (self.creg, self.cval), end="")
            self._printStartIf()
            
        self._printCode("//measure %s[%d] -> %s[%d];" % (qubit[0], qubit[1], bit[0], bit[1]))
        self._printCode("set %s[%d] = M(%s[%d]);" % (bit[0], bit[1], qubit[0], qubit[1]));
        if self.creg is not None:
            self._printEndIf()

    def barrier(self, qubitlists):
        """Barrier instruction.

        qubitlists is a list of lists of (regname, idx) tuples.
        """
        if self.listen:
            if "barrier" not in self.basis:
                self.basis.append("barrier")
            names = []
            for qubitlist in qubitlists:
                if len(qubitlist) == 1:
                    names.append("%s[%d]" % (qubitlist[0][0], qubitlist[0][1]))
                else:
                    names.append("%s" % qubitlist[0][0])
            self._printCode("//barrier %s;" % ",".join(names))

    def reset(self, qubit):
        """Reset instruction.

        qubit is a (regname, idx) tuple.
        """
        if "reset" not in self.basis:
            self.basis.append("reset")
        if self.creg is not None:
            self._printCode("if(%s==%d) " % (self.creg, self.cval), end="")
        self._printCode("reset %s[%d];" % (qubit[0], qubit[1]))

    def set_condition(self, creg, cval):
        """Attach a current condition.

        creg is a name string.
        cval is the integer value for the test.
        """
        self.creg = creg
        self.cval = cval
        if self.comments:
            self._printCode("// set condition %s, %s" % (creg, cval))

    def drop_condition(self):
        """Drop the current condition."""
        self.creg = None
        self.cval = None
        if self.comments:
            self._printCode("// drop condition")

    def start_gate(self, name, args, qubits, nested_scope=None):
        """Begin a custom gate.

        name is name string.
        args is list of Node expression objects.
        qubits is list of (regname, idx) tuples.
        nested_scope is a list of dictionaries mapping expression variables
        to Node expression objects in order of increasing nesting depth.
        """
        if self.listen and self.comments:
            self._printCode("// start %s, %s, %s" % (name,
                                           list(map(lambda x:
                                                    str(x.sym(nested_scope)),
                                                    args)),
                                           qubits))
        if self.listen and name not in self.basis \
           and self.gates[name]["opaque"]:
            raise BackendError("opaque gate %s not in basis" % name)
        if self.listen and name in self.basis:
            raise Exception("custom gate is not supported.")
#             self.in_gate = name
#             self.listen = False
#             squbits = ["%s[%d]" % (x[0], x[1]) for x in qubits]
#             if self.creg is not None:
#                 self._printCode("if(%s==%d) " % (self.creg, self.cval), end="")
#             print(name, end="")
#             if args:
#                 self._printCode("(%s)" % ",".join(map(lambda x:
#                                             str(x.sym(nested_scope)),
#                                             args)), end="")
#             self._printCode(" %s;" % ",".join(squbits))

    def end_gate(self, name, args, qubits, nested_scope=None):
        """End a custom gate.

        name is name string.
        args is list of Node expression objects.
        qubits is list of (regname, idx) tuples.
        nested_scope is a list of dictionaries mapping expression variables
        to Node expression objects in order of increasing nesting depth.
        """
        if name == self.in_gate:
            self.in_gate = ""
            self.listen = True
        if self.listen and self.comments:
            self._printCode("// end %s, %s, %s" % (name,
                                         list(map(lambda x:
                                                  str(x.sym(nested_scope)),
                                                  args)),
                                         qubits))

    def get_output(self):
        """This backend will return nothing, as the output has been directly
        written to screen"""
        pass


def _main():
    #ast = Qasm(filename="qft/qft_n20.qasm").parse()
    ast = Qasm(filename="cc/cc_n19.qasm").parse()
    
    qs = open("test.qs", 'w')
    
    qubit = 10
    name = "QFT"
    operation = name + str(qubit)

    printQS = PrintQsharp(name, operation, qs)
    u = unroll.Unroller(ast, printQS)
    u.execute()
    printQS.printFooter()

    qs.close()

def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("Error")
        sys.exit(1)


if __name__ == "__main__":
    main()

