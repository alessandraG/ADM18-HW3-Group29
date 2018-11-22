
import pandas as pd
import numpy as np
import csv

# library for storing and loading objects
import pickle

# library for stemming work
import nltk
nltk.download('punkt')
nltk.download('stopwords')
import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# library used to make inverted index
from collections import defaultdict
from collections import Counter

# cosine distance
from scipy.spatial.distance import cosine

import math 

# heap_max library
import heapq
from heapq import heappush, heappop

from geopy.geocoders import Nominatim
from geopy import distance



# Stemming functions

def remove_step(doc):
    """
    takes as input the string of the document
    removes stopwords, punctuation and makes stemming 
    input:
    - string of document
    output:
    - list of term after stemming process
    
    """
    
    # check if it's a nan value 

    if isinstance(doc, float):
        return str(doc)
    
    sp = string.punctuation+'“”–’'
    
    doc=doc.replace("\\n", " ")
    # punctuations
    doc = [ c if c not in sp else " " for c in doc ]
    doc = ''.join(doc)
    # stopwords
    doc = [ word for word in doc.split() if word.lower() not in stopwords.words('english') ]
    doc = ' '.join(doc)
    
    # stemming
    ps = PorterStemmer()
    words = word_tokenize(doc)
    
    w_lst = []
    for w in words:
        w_lst.append(ps.stem(w))
    
    # something else
    
    return ' '.join(w_lst)


# pickle object functions

def save_obj(obj, name):
    """
    save the object int a pickle file
    """
    with open('data/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    """
    load the object from a pickle file
    """
    with open('data/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def preprocessing(data):
    """
    split rows dataframe into tsv files
    input:
    - data: dataframe taken from Airbnb_Texas_Rentals.csv file
    """
    n=len(data)

    for i in range(n):
        with open('data/docs/' + 'doc_'+ str(i) + '.tsv', 'w', encoding = "utf-8") as doc:
            a = csv.writer(doc, delimiter='\t')
            a.writerow([data.iloc[i]['average_rate_per_night'],data.iloc[i]['bedrooms_count'], data.iloc[i]['city'],
                        data.iloc[i]['date_of_listing'], data.iloc[i]['description'],
                        data.iloc[i]['latitude'],
                        data.iloc[i]['longitude'],
                        data.iloc[i]['title'],
                        data.iloc[i]['url']])

    return


# vocabulary function

def create_vocabulary_and_ii1 (data):
    n = len(data)
    vocabulary = {}
    ii1 = {}    
    cnt = 0
    
    for i in range(n):
        # creating a tokenized string with title and description
        tokenized_str = (remove_step(data.iloc[i]['title']) + ' ' 
                                     + remove_step(data.iloc[i]['description']))

        # creating the dictionary
        for term in tokenized_str.split(' '):
            if term in vocabulary.keys():
                term_id = vocabulary[term]
            else:
                vocabulary[term] = cnt
                term_id = cnt
                cnt+=1

            if term_id not in ii1.keys():
                ii1[term_id] = ['doc_'+str(i)]
            else:
                lista = ii1[term_id]
                document = 'doc_'+str(i)
                if document in lista:
                    continue
                else:        
                    ii1[term_id].append('doc_'+str(i))

    # store vocabulary in pickle format
    save_obj(vocabulary, 'vocabulary')
    save_obj(ii1, 'inverted_index_1')
    return


# Search engine 1

def search_engine_1(query): 
    
    query = remove_step(query)
    query = list(set(query.split(' ')))
    
    lst_of_lst=[]
    
    vocabulary = load_obj('vocabulary')
    ii1 = load_obj('inverted_index_1')
    
    for w in query:
        if w not in vocabulary:
            print('No results')
            return
        i = vocabulary[w]
        lst_of_lst.append(ii1[i])


    doc_list = set.intersection(*[set(sublist) for sublist in lst_of_lst])
    doc_list = list(doc_list)
    dl = len(doc_list)
    
    if dl ==0:
        print('No results')
        return

    list_for_df=[]
    for i in range(dl):
        with open ("data/docs/" + doc_list[i] + '.tsv') as doc:
            row = doc.read()
            lst = row.split('\t')
            lst = [lst[7],lst[4],lst[2],lst[8]]
            list_for_df.append(lst)
        
    df=pd.DataFrame(list_for_df, columns=['Title', 'Description', 'City', 'Url'])
    
    return df.head(5)   
        


# Q 3.2 functions:


# NOT USED (TO DELETE)
"""
def dict_with_tf(data):
    vocabulary = load_obj('vocabulary')
    n = len(data)
    
    ii2 = defaultdict(list)
    
    
    for i in range(n):
        tokenized_str = (remove_step(data.iloc[i]['title']) + ' ' 
                                     + remove_step(data.iloc[i]['description']))
    
        for term in tokenized_str.split(' '):
            doc_name = 'doc_%s'%i
            ii2[term].append((doc_name,1))
        
    return ii2
"""


def reduce_doc_list(doc_list):
    """
    function called by dict_TFIDF
    
    It reduces the list of documents into a list 
    of tuple with doc_id and its occurencies
    
    input:
    - list 
    output:
    - list 
    """
    tf_term_i = Counter(doc_list)
    doc_tf_lst = []
    doc_tf_lst = [tuple([key,value]) for key,value in tf_term_i.items()]
    return doc_tf_lst


def compute_ii2_TFIDF(ii2,n):
    """
    compute the ii2_TFIDF
    input:
    - inverted index matrix (with TF)
    - number of documents
    output:
    - ii2 
    """
    for key, value in ii2.items():
        N = len(value)
        new_list = []
        for item in value:
            new_list.append(tuple([item[0], round(float(item[1])* math.log(n/N),3)]))
            
        ii2[key] = new_list
    return ii2



def inverted_index_TFIDF(data):
    """
    creates the TFIDF inverted index as dict
    and store it into a pickle file
    input:
    - data
    """
    vocabulary = load_obj('vocabulary')
    n = len(data)
    
    ii2 = defaultdict(list)
    
    for i in range(n):
        tokenized_str = (remove_step(data.iloc[i]['title']) + ' ' 
                                     + remove_step(data.iloc[i]['description']))
    
        for term in tokenized_str.split(' '):
            doc_name = 'doc_%s'%i
            ii2[vocabulary[term]].append(doc_name)
            
    
    for key,value in ii2.items():
        ii2[key] = reduce_doc_list(value)
    
    ii2 = compute_ii2_TFIDF(ii2,n)
    save_obj(ii2,'inverted_index_TFIDF')
    return 


# Search engine 2 with TFIDF
def search_engine_2(query, k = 5):
    """
    search engine with TFIDF
    input:
    - query: the query (string)
    - k: number of output as doc (default = 5)
    output:
    - df: dataframe with k documents
    """

    # stemming the query with remove step method
    query = remove_step(query).split(' ')
    vocabulary = load_obj('vocabulary')
    
    # filtering the values not contained in vocabulary
    # dict and mapping each term to its term_ID value
    
    # for word in query:
        # if word is not in vocabulary.keys:
            # print('Zero documents with all char of the query')
            #return
    query = filter(lambda x: x in vocabulary.keys(),query)
    query = list(map(lambda x: vocabulary[x], query))
    
    # making query list and array at the same time 
    # with Counter() dict (to ensure the order of the 2 arrays)
    # (dictionaries are not ordered)
    query_array = []
    query_list = []
    for key, frequence in Counter(query).items():
        query_list.append(key)
        query_array.append(frequence)
    
    # creating query list and numpy array with frequencies
    query = query_list
    query_array = np.array([query_array])

    # list of documents obtained intersecating each list
    # from inverted index 1 (easier to compute)
    docs = []
    ii1 = load_obj('inverted_index_1')
    ii1 = {term_id:ii1[term_id] for term_id in query}
    docs = set.intersection(*[set(value) for value in ii1.values()])

    # filtering ii2 with only the query terms
    ii2 = load_obj('inverted_index_TFIDF')
    ii2 = {term_id:ii2[term_id] for term_id in query}
    
    # for each doc in the list docs it creates the ranking list
    rank_lst = []
    for doc_id in docs:
        # doc TFIDF array. It must have the same 'order' as
        # the query array. to ensure this we use the query list
        array = []
        for item in query:
            array += tuple(filter(lambda x:x[0]==doc_id, ii2[item]))

        array = np.array([x[1] for x in array])
        rank_lst.append(tuple([1-cosine(array,query_array),doc_id]))
    
    # print('%d documents'%len(rank_lst)) DEBUG
    
    df = first_k_documents(rank_lst, 5)
    
    return len(rank_lst)
    return df


def first_k_documents(heap_rank_lst, k = 5):
    """
    called in search_engine_2
    it returns the first k documents as a df
    loading them into an heap memory
    input:
    - heap_rank_lst: list to be heaped
    - k: first k documents
    output:
    - df: dataframe with k documents
    """
    list_for_df = []
    
    if k > len(heap_rank_lst):
        k = len(heap_rank_lst)
        
    heapq._heapify_max(heap_rank_lst)
    
    for i in range(k):
        current_doc = heapq._heappop_max(heap_rank_lst)
    
        with open ("data/docs/" + current_doc[1] + '.tsv') as doc:
            row = doc.read()
            lst = row.split('\t')
            lst = [lst[7],lst[4],lst[2],lst[8], round(current_doc[0],3)]
            list_for_df.append(lst)
    
    return pd.DataFrame(list_for_df, columns=['Title', 'Description', 'City', 'Url', 'Similarity'])




##### RANKING FUNCTIONS

# scoring distance rank between query and house of document
def distance_rank(center, house):
      
    R = distance.distance(center, house).km
    return round(1 - (R/(1+R)),3)


# scoring price rank between query and document
def price_rank(p_query, p_doc):
    
    value = abs(p_query-p_doc)
    
    if value >= 100: 
        return 0
    else:
        return round(1-value*1/100, 3)



def rooms_rank (rooms, nrooms, rooms_ranker):
    """
    ranks the room
    """
    
    # if rooms or nrooms is a string (eg: studio)
    # convert it into a string
    if isinstance(rooms, str):
        rooms = 1
    if isinstance(nrooms, str):
        nrooms = 1
    
    # taking the distance between the two rooms
    value = abs(rooms - nrooms)

    # if there's no a region of values give zero
    if value not in rooms_ranker:
        return 0
    else:
        # give the value signed in rooms_ranker
        return rooms_ranker[value]
    

##### Q4. Search engine 3
def search_engine_3(query): 
    
    rooms_ranker = { 0: 1, 1: 0.7, 2: 0.4, 3: 0.1}

    query = remove_step(query)
    query = list(set(query.split(' ')))
    
    heap = []#heap._heapify_max()
    lst_of_lst=[]
    
    vocabulary = load_obj('vocabulary')
    ii1 = load_obj('inverted_index_1')
    
    for w in query:
        if w not in vocabulary:
            print('No results')
            return
        i = vocabulary[w]
        lst_of_lst.append(ii1[i])


    doc_list = set.intersection(*[set(sublist) for sublist in lst_of_lst])
    doc_list = list(doc_list)
    d_len = len(doc_list)   
    
    if d_len == 0:
        print('No results')
        return
    
    # user's informations for the ranks
    print("target price:")
    target_price = int(input())
    print("n rooms:")
    rooms = int(input())
    print("location")
    location = input()
    
    # loading location's informations from geopy
    geolocator = Nominatim(user_agent="specify_your_app_name_here")
    location = geolocator.geocode(location)
    center = (location.latitude, location.longitude)   
    
    #if len(str(rmin)) == 0:
    #    rmin = 1
    for doc in doc_list:
        with open('data/docs/'+doc+'.tsv', encoding = 'utf-8') as f:
            row = f.read()
            row = row.split('\t')
            dp = int(row[0][1:])
            nrooms = row[1]
            
            if math.isnan(float(row[5])):
                continue
                
            target_location = (float(row[5]), float(row[6]))
            rank_dist = distance_rank(center, target_location)
             
            score_price = 0.3*price_rank(target_price,dp)
            ratio_rooms = 0.1*rooms_rank(rooms, nrooms, rooms_ranker)
            score_location = 0.6*rank_dist
            heap.append(tuple([score_price+ratio_rooms+score_location,doc]))   
            #heapq.heappush(heap,tuple([score_price+ratio_rooms,doc])) 
            
    list_for_df=[]
    k=5
    
    l = len(heap)
    for i in range(l):
        heapq._heapify_max(heap)
        
        tup = heappop(heap)
        #print(tup)
        with open ("data/docs/" + tup[1] + '.tsv', encoding = 'utf-8') as doc:
            row = doc.read()
            lst = row.split('\t')
            lst = [i, lst[7],lst[4],lst[2],lst[8]]
            list_for_df.append(lst)
        
    df=pd.DataFrame(list_for_df, columns=['Ranking','Title', 'Description', 'City', 'Url'])
    
    return df.head(k)
    