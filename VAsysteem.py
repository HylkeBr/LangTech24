import requests
import time
import spacy

nlp = spacy.load("nl_core_news_lg")

'''Function to find answers to a given query'''
def getAnswer(query): 
    url = 'https://query.wikidata.org/sparql'
    resultsx = requests.get(url, params={'query': query, 'format': 'json'})
    
    # To prevent a 429 request code (too many requests), wait 5 seconds when this occurs and try again.
    if resultsx.status_code == 429:
        time.sleep(5)
        resultsx = requests.get(url, params={'query': query, 'format': 'json'})

    results = resultsx.json()

    # Check for yes/no answer
    if 'boolean' in results.keys():
        return results['boolean'] 
    else:
        answers = []
        varNames = results['head']['vars']
        answerItems = results['results']['bindings']
        
        # Loop through multiple answers (if given)
        for item in answerItems: 
            for varName in varNames:
                answers.append(item[varName]['value'])
    
        return answers

'''Function to find the IDs of a search query'''
def getIDs(query, p=False):
    # Create parameters
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities',               
              'language':'nl',
              'uselang':'nl',
              'format':'json',
              'search': query}
    if p: # If looking for property id
        params['type'] = 'property'
    json = requests.get(url,params).json()
    # Get IDs from different answers
    IDs = []
    for search in json['search']:
        IDs.append(search['id'])

    return IDs

'''To filter on animals. Returns boolean'''
def animalID(ID):
    query1 = 'SELECT ?ansLabel WHERE { wd:' + ID + ' wdt:P1417 ?ans. SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
    result1 = getAnswer(query1)
    isAnimal = False
    if result1 != []:
        # If dictionary code starts with animal
        if result1[0][:6] == 'animal':
            isAnimal = True

    query2 = 'SELECT ?ansLabel WHERE { wd:' + ID + ' schema:description ?ans. SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } FILTER (langMatches(lang(?ans),"nl")) }'
    result2 = getAnswer(query2)
    if result2 != []:
        # If dier is in description, it probably is an animal.
        if 'dier' in result2[0]:
            isAnimal = True
    return isAnimal

'''Removes articles 'de', 'het' and 'een' from the input'''
def removeArticles(line):
    lineSplit = line.lower().split()
    articles = ['de', 'het', 'een']
    for article in articles:
        while article in lineSplit:
            lineSplit.remove(article)
    newLine = ' '.join(lineSplit)

    return newLine

'''Function to retreive the keywords to 'wat'-questions, based on the question given'''
def getKeywords(question):
    sentence = nlp(question)
    keywords = {
        'subject': '',
        'property': ''
    }
    
    # First find the property by looking at the subject of the sentence
    for chunk in sentence.noun_chunks:
        if chunk.root.dep_ == 'nsubj':
            keywords['property'] = removeArticles(chunk.text)
            subject_root = chunk.root.text
        
    # Then find the right subject, by comparing the root of the property to the head chunk x
    for chunk in sentence.noun_chunks:
        if chunk.root.head.text == subject_root:
            keywords['subject'] = removeArticles(chunk.text)

    return keywords

'''Function to remove (select) punctuation'''
def rm_punct(sent):
    clean_sent = ''
    for char in sent:
        if char not in ['.', ',', '?', '!']:
            clean_sent += char
    return clean_sent

'''Returns POS of a given word within a sentence'''
def find_pos(parse_sent, qword):
    for word in parse_sent:
        if word.text == qword:
            funct = word.pos_

    return funct

'''Returns dependency of a given word within a sentence'''
def find_dep(parse_sent, qword):
    for word in parse_sent:
        if word.text == qword:
            funct = word.dep_

    return funct

'''Returns root, based on sentence and head word'''
def find_root(sent, head):
    parse = nlp(sent)
    root = []
    for word in parse:
        if word.head.text == head:
            root.append(word.text)
    return root

'''Returns head, based on sentence and root word'''
def find_head(sent, root):
    parse = nlp(sent)
    head = []
    for word in parse:
        if word.text == root:
            head.append(word.head.text)
    return head

'''Returns a dependency analysis of a sentence'''
def analyse(s):
    anal_d = {}
    for word in s:
        anal_d[word.text] = word.dep_
    return anal_d

'''[HARDCODE] Returns synonyms/category of select words,
if nothing in dict, it returns the input word'''
def categoryOf(word):
    cat_dict = {
        'kleur': [
            'wit', 'zwart', 'rood', 'oranje', 
            'paars', 'blauw', 'groen', 'geel',
            'roze', 'kleur'
        ],
        'draagtijd': [
            'draagtijd', 'zwanger', 'zwangerschap',
            'dracht'
        ],
        'hoogte': [
            'hoogte', 'lengte', 'grootte', 'lang',
            'hoog', 'groot'
        ],
        'massa': [
             'massa', 'gewicht', 'zwaarte'
        ]
    }

    found = False
    for k,v in cat_dict.items():
        for val in v:
            if word in val or word == val:
                cat = k
                found = True
    if not found:
        cat = word

    return cat

'''Returns Q and P properties, based on a sentence'''
def find_QP(sent):
    sent_cl = rm_punct(sent)
    query_dict = {}
    parse = nlp(sent)

    # questions starting with 'welk(e)'
    if parse[0].lemma_.lower() == 'welk':
        for word in sent_cl.split():
            if word == find_head(sent_cl, word)[0]:
                sent_ROOT = word
        keys = find_root(sent_cl, sent_ROOT)
        keys.remove(sent_ROOT)
        for word in keys:
            for root in find_root(sent_cl, word):
                if root == parse[0].text: # parse[0] => .lemma.lower() == 'welk'
                    query_dict['P'] = categoryOf(word)
                else:
                    query_dict['Q'] = [categoryOf(word)]
    # questions starting with 'hoe'
    elif parse[0].lemma_.lower() == 'hoe':
        for word in sent_cl.split():
            if word == find_head(sent_cl, word)[0]:
                sent_ROOT = word
                query_dict['P'] = categoryOf(sent_ROOT)
            elif find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
    # Binary questions starting with verb (aux)
    elif find_pos(parse, parse[0].text) == 'AUX':
        for word in sent_cl.split():
            if find_dep(parse, word) == 'ROOT':
                Q1 = word
            elif word == find_head(sent_cl, word)[0]:
                Q2 = word
                P1 = categoryOf(word)
        query_dict['Q'] = [Q1, Q2]
        query_dict['P'] = P1

    # questions starting with 'wat' / the rest
    else: 
        d = getKeywords(sent)
        query_dict['Q'] = [d['subject']]
        query_dict['P'] = d['property']

    return query_dict

'''Create query, based on given IDs'''
def createQueries(qIDs, pIDs):
    qs = []
    if len(qIDs) == 1:
        qIDs = qIDs[0]
        ID1s = []
        # Preventive check for animal IDs
        for ID in qIDs:
            if animalID(ID):
                ID1s.append(ID)
        # Generate queries based on differend ID combinations
        for ID1 in ID1s:
            for ID2 in pIDs:
                query = 'SELECT ?ansLabel WHERE { wd:' + ID1 + ' wdt:' + ID2 + ' ?ans. SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
                qs.append(query)
    else: # Boolean question
        qID1s = qIDs[0]
        qID2s = qIDs[1]

        for qID1 in qID1s:
            if animalID(qID1):
                for qID2 in qID2s:
                    for pID in pIDs:
                        query = 'ASK { wd:' + qID1 + ' wdt:' + pID + ' wd:' + qID2 + ' . }'
                        qs.append(query)

    return qs

'''Answers questions'''
def answerQuestion(question):
    keys = find_QP(question)
    q_ids = []
    for qkey in keys['Q']:
        q_ids.append(getIDs(qkey))
    p_ids = getIDs(keys['P'], p=True)

    queries = createQueries(q_ids, p_ids)

    answers = []
    for query in queries:
        answer = getAnswer(query)
        if answer != []:
            answers.append(answer)

    if len(answers) == 0:
        print(' - Excuses. Ik heb op deze vraag geen antwoord kunnen vinden.')
    else:
        answer_given = False
        for ans in answers:
            if type(ans) == bool:
                if not answer_given:
                    if True in answers:
                        print(' - Ja')
                        answer_given = True
                    else:
                        print(' - Nee')
                        answer_given = True
            else:
                for ansLabel in ans:
                    print(' -', ansLabel)


def main():
    q1 = 'Hoe groot is een olifant?'
    q2 = 'Welke kleur heeft een ijsbeer?'
    q3 = 'Welke commonscategorie past bij de olifant?'
    q4 = 'Hoe lang is een giraffe?'
    q5 = 'Wat is de belangrijkste voedselbron van een tijger?'
    q6 = 'Welke IUCN-status heeft de leeuw?'
    q7 = 'Is een ijsbeer wit?'
    questions = [q1, q2, q3, q4, q5, q6, q7]
    for q in questions:
        print(q)
        answerQuestion(q)
        print()


if __name__ == '__main__':
    main()