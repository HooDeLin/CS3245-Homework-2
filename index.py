#!/usr/bin/python
import nltk
import sys
import getopt
import math
import pickle
from os import listdir
from os.path import isfile, join
from nltk.stem.porter import PorterStemmer
from sets import Set
import string
import sys

def build_index_and_posting(input_directory):
    stemmer = PorterStemmer()
    punc = list(string.punctuation)
    files = [f for f in listdir(input_directory) if isfile(join(input_directory, f))]
    index = {}
    posting = {}
    for f in files:    
        fp = open(join(input_directory, f), "r")
        tokens = []
        for line in fp:
            for sent_tokens in nltk.sent_tokenize(line):
                for word in nltk.word_tokenize(sent_tokens):
                    stemmed_word = stemmer.stem(word).lower()
                    if stemmed_word not in punc:
                        tokens.append(stemmed_word)
        for t in tokens:
            if t not in index:
                index[t] = (0,1,0)
                posting[t] = Set([int(f)])
            else:
                if int(f) not in posting[t]:
                    index[t] = (0, index[t][1] + 1, 0)
                posting[t].add(int(f))
    return (index, posting, sorted([int(f) for f in files]))

def get_posting_string(posting_list):
    """
    Accepts a sorted posting list and create a posting list with skip pointers in string format
    The output of the postings is as follows:
    Input: [1,2,3,4,5]
    Output: " 1 ^3 2 3 ^3 4 5"
    """
    skip_interval = int(math.sqrt(len(posting_list)))
    counter = 0
    post_string = ""
    while(counter < len(posting_list)):
        post_string += " " + str(posting_list[counter])
        if counter % skip_interval == 0 and skip_interval > 1:
            end = counter + skip_interval
            if end < len(posting_list):
                skipping = posting_list[counter + 1:end]
                skipping_string = " ".join(str(doc) for doc in skipping)
                # Calculate the bytes that needs to be skipped
                post_string += " " + "^" + str(len(skipping_string) + 2)
                post_string += " " + skipping_string
                counter += len(skipping) + 1
            else:
                counter += 1
        else:
            counter += 1
    return post_string

def save_index_and_posting(index, posting, all_ids, output_file_postings, output_file_dictionary):
    accumulate_fp = 0
    fp = open(output_file_postings, "w")
    for post in posting:
        post_string = get_posting_string(sorted(list(posting[post])))
        fp.write(post_string)
        index[post] = (accumulate_fp, index[post][1], len(post_string))
        accumulate_fp += len(post_string)
    all_ids_string = get_posting_string(all_ids)
    fp.write(all_ids_string)
    fp.close()
    pickle.dump([index,(accumulate_fp,len(all_ids),len(all_ids_string))], open(output_file_dictionary,"wb"))


def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
    
for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"
        
if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

(index, posting, all_ids) = build_index_and_posting(input_directory)
save_index_and_posting(index, posting, all_ids, output_file_postings, output_file_dictionary)