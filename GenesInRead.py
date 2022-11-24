#! /usr/bin/env python
import sys
import gzip

def argument_parser(argv,kmer_length, gene_file, read_file):
    """
    Sets up a argument parser from the argv vector. 
    In addition takes in default values for variables, if not given 
    arguments in argv
    """
    last_arg = ""
    # Go throug argv. If the last argument was a "-" argument (eg -k), save the argument in correct variable
    for arg in argv:
        # Exit if missing an argument
        if last_arg.startswith("-") and arg.startswith("-"):
            sys.exit(f"Missing argument in {last_arg}")
        elif arg.startswith("-") and argv[-1] == arg:
            sys.exit(f"Missing argument in {arg}")

        elif last_arg == "-k":
            try:
                kmer_length = int(arg)
            except ValueError as e:
                sys.exit(f"The kmer needs to be an integer, error:\n{e}")

        elif last_arg == "-g":
            gene_file = arg

        elif last_arg == "-r":
            read_file = arg

        last_arg = arg

    return (kmer_length, gene_file, read_file)

def read_fasta(filename):
    '''Reading in several fasta files
       yield each pair of header and dna seperate
    '''
    # Try to open the file, error if file does not exsist
    try: file = open(filename, "r")
    except FileNotFoundError as errormessage:
        sys.exit(f"The file '{filename}' could not be found, error: {errormessage}")

    # Extract the dna, and the headers.
    oldheader = "firstheader"
    for line in file:
        line = line.strip()
        #if line is header yield dna and header except first header
        if line.startswith(">"):    
            newheader = line
            if oldheader != "firstheader":
                yield dna, oldheader
            dna = ""
            oldheader = newheader
        else:
            dna += line
    # Yield the last header and dna
    yield dna, oldheader
    file.close()
    
def read_qfasta(filename):
    '''Extract dna from a gzipped fastaQ file '''
    # Try to open the file, error if file does not exsist
    try: sample_file = gzip.open(filename, "r")
    except FileNotFoundError as errormessage:
        sys.exit(f"The file '{filename}' could not be found, error: {errormessage}")

    last_line = ""
    try:
        for line in sample_file:
            line = line.decode("utf-8")

            # Extracting the dna
            if last_line.startswith("@"):
                dna = line.strip()
                yield dna

            last_line = line
    
    # Error message if the gzipped file does not work
    except gzip.BadGzipFile as errormessage:
        sys.exit(f"The file '{filename}' could not be gzipped, error: {errormessage}")

    sample_file.close()

def find_all_kmers(dna, kmer_len):
    '''Find Kmers from a dna string and return list with them
       in additon to list with their positions
       '''

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
        range_list.append(i)

    return kmer_list, range_list

def read_is_valid(gene, read):
    '''
    return True if the read is covering enough of the gene,
    else returns False
    Running time: O(len(gene))
    '''
    # Various parameters
    max_space = 1   # The maximum space in the read covering the gene
    side_bonus = int(0.70 * len(read))   # How much of the read can be outside the gene
    threshold_score = int(0.95 *len(read))   #The percent of the read which needs to cover the gene

    # Various init
    maxcount = 0
    count = 0
    exitcount = 0
    in_kmer = False
    len_dna = len(gene)

    # Score the reads coverage of the gene
    for pos,value in enumerate(gene):

        # Start counting the coverage at first [1] in gene
        if value == 1: in_kmer = True
        if in_kmer:
            if value == 0:
                exitcount += 1
            else:
                count += 1
                # If at either side position, add a bonus to the score
                if pos in [0, len_dna-1]:
                    count += side_bonus

            # If a better fitting coverage of the read to the gene is found, use it
            if count > maxcount:
                maxcount = count
            
            # Stop counting the coverage if there is too much spacing
            if exitcount >= max_space:
                count = 0
                exitcount = 0
                in_kmer = False

    return maxcount >= threshold_score

def coverage_stats(dna):
    '''from depht array return coverage, avg depht and min_depht
        Running time: O(len(dna))
    '''

    # Init
    count = 0
    total_depht = 0
    min_depth = 99999

    # Find total_depht, coverage and avg_depht
    for base in dna:
        total_depht += base
        if base != 0:
            count += 1
        if base < min_depth:
            min_depth = base
    coverage = count / len(dna)
    avg_depht = total_depht / len(dna)
    return coverage, avg_depht, min_depth


# Setting up the argument parser
(kmer_length,gene_filename,read_filename) = argument_parser(sys.argv,19,"resistance_genes.fsa","Unknown3_raw_reads_1.txt.gz")


### Read in the file with the antibiotic resistence genes and save it in the datastructure kmer2gene2kmerpos
kmer2gene2kmerpos = dict()
trans = str.maketrans("ACTG","TGAC")
for non_complement_dna, header in read_fasta(gene_filename):

    # MÅSKE OGSÅ SKAL VÆRE DEN ANDEN VEJ?
    complement_dna= non_complement_dna.translate(trans)
    for dna in [non_complement_dna, complement_dna,non_complement_dna[::-1], complement_dna[::-1]]:
        (kmer_list, kmer_positions) = find_all_kmers(dna, kmer_length)
        # Make gene_data datastructure which consists of: {Kmer: {"gene_name":(kmer_position_in_gene,length_gene)}}
        for kmer, kmer_pos_in_gene in zip(kmer_list, kmer_positions):
            if kmer in kmer2gene2kmerpos:
                kmer2gene2kmerpos[kmer][header] = (kmer_pos_in_gene, len(dna))
            else:
                kmer2gene2kmerpos[kmer] = {header : (kmer_pos_in_gene, len(dna))}

### Reading in the fastaq file, for each read evaluate if read is valid.
### If valid, add it to total depht for each gene
TOTALgene2depht_count = dict()
for dna_read in read_qfasta(read_filename):

    (kmer_list, _) = find_all_kmers(dna_read, kmer_length)

    READgene2depht_count = dict()
    for kmer in kmer_list:
        # If the kmer is equal to a kmer in the genes
        if kmer in kmer2gene2kmerpos:
            # Go through each gene which has the kmer and add depht to it.
            for genename in kmer2gene2kmerpos[kmer]:
                len_gene = kmer2gene2kmerpos[kmer][genename][1]
                kmer_pos = kmer2gene2kmerpos[kmer][genename][0]

                if genename not in READgene2depht_count:
                    # Make vector of [0] to represent depht of each nt corresponding to length of gene
                    READgene2depht_count[genename] = [0] * len_gene

                # Add depht to it, corresponding the kmer found
                for i in range(kmer_pos, kmer_pos + kmer_length):
                    READgene2depht_count[genename][i] = 1
    
    # If the read is valid, Add the gene to the final depht_count for each gene (FINALgene2depht_count)
    for genename, depht_count in READgene2depht_count.items():
        if read_is_valid(depht_count, dna_read):
            if genename in TOTALgene2depht_count:
                # elementwise addition
                for i in range(len(TOTALgene2depht_count[genename])):
                    TOTALgene2depht_count[genename][i] += depht_count[i]    

            else :
                TOTALgene2depht_count[genename] = depht_count

### Picking genes with enough coverage and printing them out
# Add genes with coverage and avg_depht above threshold values to gene2coverage_depht
gene2coverage_depht = dict()
for genename, dna in TOTALgene2depht_count.items():
    (coverage, avg_depht, min_depht) = coverage_stats(dna)
    if coverage > 0.95 and min_depht > 10:
        gene2coverage_depht[genename] = (coverage, avg_depht)

# sort the genes based on coverage then depht
sorted_gene_coverage_depht = sorted(
            gene2coverage_depht, 
            key= gene2coverage_depht.get, 
            reverse = True)

# output and format sorted_gene_coverage_depht to .tsv
print("gene\tresistence\tcoverage\tavg_depht")
for genename in sorted_gene_coverage_depht:
    coverage = round(gene2coverage_depht[genename][0],2)
    avg_depht = round(gene2coverage_depht[genename][1],2)
    (gene,resistence) = genename.split(maxsplit = 1)
    gene = gene[1:]
    print(f"{gene}\t{resistence}\t{coverage}\t{avg_depht}")
