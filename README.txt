This is the README file for A0126576X's submission

== Python Version ==

I'm (We're) using Python Version 2.7 for
this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general.  A few paragraphs 
are usually sufficient.

Indexing:
The indexing process starts by going through all the training files, and uses nltk to parses
all the words.
For the dictionary, we will need to know the starting position of its posting list from the
posting file, the frequency of the word and the length of the posting
The final output of the dictionary is:
({"word": (starting position, frequency, length of posting), ...}, 
 (starting position of all ids, frequeny of all ids, length of all ids)
)
The dictionary will stored using pickle
The posting list format is as follows:
[6,313,6412,9193,9521,10758] in posting format will be:
" 6 ^10 313 6412 9193 ^12 9521 10758"
"^" indicates a skip pointer, the number beside the skip pointer specifies the number of bytes to skip

Searching:
The query will first go through the shunting yard algorithm. To speed up the query, "AND NOT" is converted
to "ANOT" which has the same precedence with "AND", so that we reduce the time needed to process the query.

Then we process the RPN notation of the query. Each operand is encapsulated into the class Operand. Intermediate
results will be stored as an operand as well. For example: A AND (B or C), we can store the results as an operand.
When we do operations between two operands, we do not need to know whether we have to get the posting list from
posting file or in memory for a intermediate results. The Operand abstracts it out.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

index.py: This file indexes the documents and produces a dictionary file and a posting file
search.py: This file reads through the queries and writes the results to a file
dictionary.txt: This file contains the dictionary
posting.txt: This file contains the postings
README.txt: This file.

== Statement of individual work ==

Please initial one of the following statements.

[X] I, A0126576X, certify that I have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I
expressly vow that I have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

N/A

I suggest that I should be graded as follows:

N/A

== References ==

Shunting Yard Algorithm: https://en.wikipedia.org/wiki/Shunting-yard_algorithm
Reverse Polish Notation: https://en.wikipedia.org/wiki/Reverse_Polish_notation
