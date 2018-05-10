#!/usr/bin/python
import sys
import getopt
import pickle
import math
from sets import Set
from nltk.stem.porter import PorterStemmer

# NOT > AND = AND NOT > OR
# ANOT = AND NOT
operators = Set(["NOT", "AND", "OR", "ANOT"])
operator_precedence = {"NOT":2,"AND":1,"ANOT":1,"OR": 0}

def top_operator_precedence(stack):
    if len(stack) == 0:
        return 0
    else:
        return operator_precedence[stack[len(stack) - 1]]
def shunting_yard(query):
    tokens = query.split(" ")
    query_tokens = []
    for t in tokens:
        current = t
        while(current[0] == "("):
            query_tokens.append("(")
            current = current[1:]
        end_parenthese_cnt = 0
        while(current[-1] == ")"):
            end_parenthese_cnt += 1
            current = current[:-1]
        query_tokens.append(current)
        for _ in range(end_parenthese_cnt):
            query_tokens.append(")")
    output_queue = []
    operator_stack = []
    while query_tokens:
        current = query_tokens.pop(0)
        # Handling AND NOT case
        if query_tokens and current == "AND" and query_tokens[0] == "NOT":
            current = "ANOT"
            query_tokens.pop(0)
        # Actual shunting yard algorithm here
        if current not in operators and current != "(" and current != ")":
            output_queue.append(current)
        if current in operators:
            while len(operator_stack) != 0 and operator_stack[len(operator_stack)-1] != "(" and ((top_operator_precedence(operator_stack) > operator_precedence[current]) or (top_operator_precedence(operator_stack) == operator_precedence[current] and current != "NOT")):
                output_queue.append(operator_stack.pop())
            operator_stack.append(current)
        if current == "(":
            operator_stack.append(current)
        if current == ")":
            while operator_stack[len(operator_stack) -1] != "(":
                output_queue.append(operator_stack.pop())
            operator_stack.pop()
    while operator_stack:
        output_queue.append(operator_stack.pop())
    return output_queue

def or_query(operand_a, operand_b, index, postings_file):
    result = []
    if operand_a.has_results and len(operand_a.evaluated_results) == 0:
        result = operand_b.get_results()
    elif operand_b.has_results and len(operand_b.evaluated_results) == 0:
        result = operand_a.get_results()
    else:
        a = operand_a.next()
        b = operand_b.next()
        while a != "" and b != "":
            if int(a) == int(b):
                result.append(a)
                a = operand_a.next()
                b = operand_b.next()
            elif int(a) < int(b):
                result.append(a)
                a = operand_a.next()
            else:
                result.append(b)
                b = operand_b.next()
        while a != "":
            result.append(a)
            a = operand_a.next()
        while b != "":
            result.append(b)
            b = operand_b.next()
    return Operand(index, postings_file, result=result)

def and_query(operand_a, operand_b, index, postings_file):
    if operand_a.get_frequency() > operand_b.get_frequency():
        return and_query(operand_b, operand_a, index, postings_file)
    else:
        result = []
        a = operand_a.next()
        b = operand_b.next()
        while a != "" and b != "":
            if int(a) == int(b):
                result.append(a)
                a = operand_a.next()
                b = operand_b.next()
            elif int(a) < int(b):
                (a_skip, a_skip_interval) = operand_a.skip_pointer()
                if a_skip != "" and int(a_skip) <= int(b):
                    operand_a.next_skip(a_skip_interval)
                    a = a_skip
                else:
                    a = operand_a.next()
            else:
                (b_skip, b_skip_interval) = operand_b.skip_pointer()
                if b_skip != "" and int(b_skip) <= int(a):
                    operand_b.next_skip(b_skip_interval)
                    b = b_skip
                else:
                    b = operand_b.next()
        return Operand(index, postings_file, result=result)

def and_not_query(operand_b, operand_a, index, postings_file):
    a = operand_a.next()
    b = operand_b.next()
    result = []
    while a != "" and b != "":
        if int(a) == int(b):
            a = operand_a.next()
            b = operand_b.next()
        elif int(a) < int(b):
            result.append(a)
            a = operand_a.next()
        else:
            b = operand_b.next()
    while a != "":
        result.append(a)
        a = operand_a.next()
    return Operand(index, postings_file, result=result)


def not_query(operand, index, all_ids, postings_file):
    all_operand = Operand(all_ids, postings_file, is_all=True)
    a = operand.next()
    b = all_operand.next()
    result = []
    while a != "" and b != "":
        if int(a) == int(b):
            a = operand.next()
            b = all_operand.next()
        elif int(a) < int(b):
            result.append(a)
            a = operand.next()
        else:
            result.append(b)
            b = all_operand.next()
    while b != "":
        result.append(b)
        b = all_operand.next()
    return Operand(index, postings_file, result=result)

def process_rpn(rpn_query, index, postings_file):
    rpn_stack = []
    for rpn_token in rpn_query:
        if rpn_token not in operators:
            rpn_stack.append(Operand(index[0], postings_file, token=rpn_token))
        elif rpn_token == "OR":
            rpn_stack.append(or_query(rpn_stack.pop(), rpn_stack.pop(), index[0], postings_file))
        elif rpn_token == "AND":
            rpn_stack.append(and_query(rpn_stack.pop(), rpn_stack.pop(), index[0], postings_file))
        elif rpn_token == "NOT":
            rpn_stack.append(not_query(rpn_stack.pop(), index[0], index[1], postings_file))
        elif rpn_token == "ANOT":
            rpn_stack.append(and_not_query(rpn_stack.pop(), rpn_stack.pop(), index[0], postings_file))
    return " ".join(rpn_stack.pop().get_results())
    
class Operand:
    def __init__(self, index, postings_file, token="", result=[], is_all=False):
        self.has_results = False
        """
        Token related variables
        """
        self.token = ""
        self.starting_fp = 0
        self.frequency = 0
        self.length = 0
        self.postings_file = postings_file
        self.next_fp = 0
        """
        Result related variables
        """
        self.evaluated_results = []
        self.next_idx = 0
        if is_all:
            self.starting_fp = index[0]
            self.frequency = index[1]
            self.length = index[2]
            self.next_fp = self.starting_fp
        elif token != "":
            stemmer = PorterStemmer()
            self.token = stemmer.stem(token).lower()
            if self.token not in index:
                self.has_results = True
            else:
                self.starting_fp = index[self.token][0]
                self.next_fp = self.starting_fp
                self.frequency = index[self.token][1]
                self.length = index[self.token][2]
        else:
            self.has_results = True
            self.evaluated_results = result

    def get_frequency(self):
        if self.has_results:
            return len(self.evaluated_results)
        else:
            return self.frequency

    def get_results(self):
        if not self.has_results:
            self.__token_get_doc_id_from_posting()
        return self.evaluated_results

    def skip_pointer(self):
        value = ("",0)
        if self.has_results:
            skip_interval = math.sqrt(len(self.evaluated_results))
            if self.next_idx % skip_interval == 0 and self.next_idx + skip_interval < len(self.evaluated_results):
                value = (self.evaluated_results[self.next_idx + skip_interval], skip_interval)
        else:
            fp = open(self.postings_file, "r")
            fp.seek(self.next_fp)
            fp.seek(1,1) # The first one is a space
            current = fp.read(1)
            skipped_bytes = 0
            skip = ""
            skipped_value = ""
            if current == "^":
                skipped_bytes += 2
                current = fp.read(1)
                skipped_bytes += 1
                while current != " ":
                    skip += current
                    current = fp.read(1)
                    skipped_bytes += 1
                fp.seek(int(skip)-1,1)
                skipped_bytes += int(skip)-1
                current = fp.read(1)
                skipped_bytes += 1
                while current != " ":
                    skipped_value += current
                    current = fp.read(1)
                    skipped_bytes += 1
                skipped_bytes -= 1 # We rewind one byte so that it will always start on space
            fp.close()
            value = (skipped_value,skipped_bytes)
        return value

    def next_skip(self, interval):
        if self.has_results:
            self.next_idx += interval
        else:
            self.next_fp += interval

    def next(self):
        value = ""
        if self.has_results:
            if self.next_idx < len(self.evaluated_results):
                value = self.evaluated_results[self.next_idx]
                self.next_idx += 1
        elif self.next_fp < self.starting_fp + self.length:
            accumulated = ""
            fp = open(self.postings_file, "r")
            fp.seek(self.next_fp)
            while value == "":
                fp.seek(1,1) # The first one is a space
                current = fp.read(1)
                is_end = current == "" # We have reached EOF
                is_skip = current == "^" # This is a skip pointer, we have to omit this
                if is_end:
                    return value
                while current != " " and current != "":
                    if not is_skip:
                        value += current
                    current = fp.read(1)
                fp.seek(-1,1)
            self.next_fp = fp.tell()
            fp.close()
        return value

    def __token_get_doc_id_from_posting(self):
        for _ in range(self.frequency):
            self.evaluated_results.append(self.next())
        self.has_results = True

def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictionary_file = postings_file = file_of_queries = output_file_of_results = None
	
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

index = pickle.load(open(dictionary_file, "rb"))
query_fp = open(file_of_queries, "r")
output_fp = open(file_of_output, "w")

for line in query_fp:
    rpn_query = shunting_yard(line.strip())
    result = process_rpn(rpn_query, index, postings_file)
    output_fp.write(result + "\n")
query_fp.close()
output_fp.close()