import sys
import re
import gzip

def FindKmer(dna, kmer_len):
    '''Find Kmers from dna string and return list with them'''

    # Return None if there is no possible kmer's
    if kmer_len > len(dna):
        return

    kmer_list = []
    range_list = []
    from_range = 0
    to_range = len(dna) - kmer_len + 1   #+1 to also add last kmer
    for i in range(from_range, to_range):

        kmer = dna[i: i + kmer_len]
        kmer_list.append(kmer)
        range_list.append([i, len(dna)])

    return kmer_list, range_list

def CountEachKmer(kmer_list, Data_Structure, nKmer_per_AR):
    '''Counts the amount of each kmer in the dict: kmer_count'''

    # Goes through each found kmer
    for kmer in kmer_list:
        # If the kmer is equal to an AR gene
        if kmer in Data_Structure:
            AR_to_range = Data_Structure[kmer]
    
            # Go through each AR_gene for which the kmer was found and add the count to it
            for AR_gene in AR_to_range:
                
                if AR_gene in nKmer_per_AR:
                    from_to_len = AR_to_range[AR_gene]
                    AddDepth(from_to_len, nKmer_per_AR, AR_gene)
                
                else:
                    # Extract [from, to, len(dna)]
                    from_to_len = AR_to_range[AR_gene]
                    # Make vector of [0] to represent depht of each nt
                    length_of_gene = from_to_len[1]
                    nKmer_per_AR[AR_gene] = [0] * length_of_gene

                    # Add the count for the kmer to the specific place
                    AddDepth(from_to_len, nKmer_per_AR, AR_gene)
            

def AddDepth(from_to_len, nKmer_per_AR, AR_gene):
    """Add the count for the kmer to the specific place"""
    from_range = from_to_len[0]
    to_range = from_range + kmer_length
    add = 1
    for i in range(from_range, to_range):
        nKmer_per_AR[AR_gene][i] += 1


def AddToDatastructure(Data_Structure, kmer_list, header, range_list):
    """Adds the kmer_list and header to the Data_structure """
    for i in range(len(kmer_list)):
        kmer = kmer_list[i]
        kmer_range = range_list[i]

        # If the kmer is allready assigned to an AR gene, add the additional
        if kmer in Data_Structure:
            Data_Structure[kmer][header] = (kmer_range)
        # Else add the kmer to the datastructure
        else:
            Data_Structure[kmer] = {header:kmer_range}
                

# Set the kmer lenght to look for
kmer_length = 3

# Stores {Kmer: {"AR":kmer_range}}, The Kmer as key. 
#then there is a inner dict with the AR gene as key and the kmer_ range as values
Data_Structure = dict()
Could_be_kmers = dict()
nKmer_per_AR = dict()


## Reading in the Antibiotic Resistence (AR) File 

#AR_file = open('resistance_genes.fsa.txt', 'r')
#filename = "Unknown3_raw_reads_1.txt.gz"
AR_file = open('ARsmall.txt', 'r')
#filename = "smallfastaseq.txt.gz"

line = 'void'
while line != '' and line[0] != '>':
    line = AR_file.readline()

while line != '':
    line = line.strip()
    header = line
    dna = ''
    line = AR_file.readline()
    while line != "" and line[0] != '>':

        # Quit the program if the found DNA is not DNA
        # TODO Failer hvis DNA string starter med unkown eg. "N"
        line = re.sub("\s", "", line).upper()
        if re.search("[^ATGC]", line) is not None:
            print("Invalid sequence line: " + line)
            sys.exit(1)

        dna += line
        line = AR_file.readline()
    
    # Finding all the posible kmers and its positions
    (kmer_list, range_list) = FindKmer(dna, kmer_length)

    # Adding the kmer_list and header to the Data_structure 
    AddToDatastructure(Data_Structure, kmer_list, header, range_list)


read = "ATCGT"

read_length = len(read)
readcount = [0] * read_length

(kmerlist, range_list) = FindKmer(read, kmer_length)


threshhold = 2

start_of_gene = kmerlist[0: threshhold]
for i in range(len(start_of_gene)):
    kmer = start_of_gene[i]

    if kmer in Data_Structure:
       for gene_name in Data_Structure[kmer]:
            start_of_codon = range_list[i][0]
            readcount[start_of_codon: start_of_codon + kmer_length] = [gene_name] * kmer_length
    else:
        pass

print(readcount)