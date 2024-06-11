import requests
import time
import spacy
import json
import re
import langcodes

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
        ],
        'gekarakteriseerd door': [
            'herbivoor', 'carnivoor', 'omnivoor',
            'gender'
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
    extra_dict = {}
    lan_list = []
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
    # questions on name of animal in other language
    elif re.match("Hoe heet.*in het.*", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "triviale naam"
            if find_dep(parse, word) == 'nmod':
                result = langcodes.find(word)
                lan_list = [str(result)]
    # "hoe groot kan [een dier] worden?"
    elif re.match("Hoe groot kan.*worden?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'xcomp':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = categoryOf("groot")
    # "hoe lang is [een dier] zwanger?"
    elif re.match("Hoe lang is.*zwanger?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "draagtijd"
    # "hoe oud is de oudste [een dier] geworden?"
    elif re.match("Hoe oud is de oudste.*geworden?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj' or find_dep(parse, word) == 'xcomp':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "hoogst geobserveerde levensduur"
    # "hoe oud wordt een [dier]?"
    elif re.match("Hoe oud wordt.*?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "levensverwachting"
    # "Hoe zwaar is een [dier]"            
    elif re.match("Hoe zwaar is.*", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "massa"
            elif find_dep(parse, word) == 'amod':
                if word == "pasgeboren":
                    extra_dict['Q'] = getIDs("geboortegewicht")[0]
                    extra_dict['P'] = getIDs("van", p=True)[0]
                if word == "volwassen":
                    extra_dict['Q'] = getIDs("volwassen gewicht")[0]
                    extra_dict['P'] = getIDs("van", p=True)[0]
                if word == "mannelijke":
                    extra_dict['Q'] = getIDs("mannelijk organisme")[0]
                    extra_dict['P'] = getIDs("sekse of geslacht", p=True)[0]
                if word == "vrouwelijke":
                    extra_dict['Q'] = getIDs("vrouwelijke organisme")[0]
                    extra_dict['P'] = getIDs("sekse of geslacht", p=True)[0]
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
        Q2 = None
        P = False
        for word in sent_cl.split():
            if find_dep(parse, word) == 'ROOT':
                Q1 = word
            elif word == find_head(sent_cl, word)[0]:
                Q2 = word
                P1 = categoryOf(word)
                P = True
            else:
                if word != categoryOf(word):
                    P1 = categoryOf(word)
                    P = True
        if not P:
            P1 = word
        # For troubled cases
        if Q2 == None:
            for word in sent_cl.split():
                if word != Q1:
                    if word != P1:
                        if word.lower() not in ['de', 'het', 'een']:
                            if find_pos(parse, word) != 'AUX':
                                Q2 = word
        query_dict['Q'] = [Q1, Q2]
        query_dict['P'] = P1
    elif re.match("Waar is.*goed voor?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "gebruik"
    elif re.match("Waar komt.*voor?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "endemisch in"
    elif re.match("Hoeveel jongen krijgt.*?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'obj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "nestgrootte"
    # "(sinds/vanaf) wanneer is [een dier] uitgestorven?"
    elif re.match("(?:Sinds |Vanaf )?(W|w)anneer is.*uitgestorven?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "einddatum"
    # "(sinds/vanaf) wanneer bestaat [een dier]?"
    elif re.match("(?:Sinds |Vanaf )?(W|w)anneer bestaat.*?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "begindatum"
    # "behoort [eem dier] tot de [klasse]?"
    elif re.match("Behoort.*tot de.*?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                Q1 = [categoryOf(word)]
            elif find_dep(parse, word) == 'obl':
                Q2 = [categoryOf(word)]
                query_dict['P'] = getIDs("subklasse van", p=True)[0]
        query_dict['Q'] = [Q1, Q2]
    # "eet [een dier] [eten]?"
    elif re.match("Eet.*?", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'amod':
                Q1 = [categoryOf(word)]
            elif find_dep(parse, word) == 'obj':
                Q2 = [categoryOf(word)]
                query_dict['P'] = getIDs("belangrijkste voedselbron", p=True)[0]
    # "Hoeveel weegt [een dier]?"
    elif re.match("Hoeveel weegt.*", sent):
        for word in sent_cl.split():
            if find_dep(parse, word) == 'nsubj':
                query_dict['Q'] = [categoryOf(word)]
                query_dict['P'] = "massa"
            elif find_dep(parse, word) == 'amod':
                if word == "pasgeboren":
                    extra_dict['Q'] = getIDs("geboortegewicht")[0]
                    extra_dict['P'] = getIDs("van", p=True)[0]
                if word == "volwassen":
                    extra_dict['Q'] = getIDs("volwassen gewicht")[0]
                    extra_dict['P'] = getIDs("van", p=True)[0]
                if word == "mannelijke":
                    extra_dict['Q'] = getIDs("mannelijk organisme")[0]
                    extra_dict['P'] = getIDs("sekse of geslacht", p=True)[0]
                if word == "vrouwelijke":
                    extra_dict['Q'] = getIDs("vrouwelijke organisme")[0]
                    extra_dict['P'] = getIDs("sekse of geslacht", p=True)[0]

    # questions starting with 'wat' / the rest
    else: 
        d = getKeywords(sent)
        query_dict['Q'] = [d['subject']]
        query_dict['P'] = d['property']
    
    # Check whether or not there is need for a metric unit
    if query_dict['P'] in [
        'hoogte', 'lengte', 'breedte', 'massa',
        'levensverwachting', 'hoogst geobserveerde levensduur',
        'minimale frequentie van hoorbaar geluid', 
        'maximale frequentie van hoorbaar geluid',
        'hartslag', 'draagtijd', 'broedperiode'
    ]:
        extra_dict['metricUnit'] = True
    else:
        extra_dict['metricUnit'] = False

    return query_dict, extra_dict, lan_list

'''Create query, based on given IDs'''
def createQueries(qIDs, pIDs, extra, lan):
    qs = []
    if len(qIDs) == 1:
        qIDs = qIDs[0]
        ID1s = []
        # Preventive check for animal IDs
        for ID in qIDs:
            if animalID(ID):
                ID1s.append(ID)
        # Generate queries based on differend ID combinations
        if list(extra.keys()) == ['metricUnit'] and lan == []:
            for ID1 in ID1s:
                for ID2 in pIDs:
                    if extra['metricUnit']:
                        query = 'SELECT ?ansLabel ?unitLabel WHERE { wd:' + ID1 + ' p:' + ID2 + ' ?x. ?x psv:' + ID2 + ' ?node. ?node wikibase:quantityAmount ?ans. ?node wikibase:quantityUnit ?unit. SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
                    else: 
                        query = 'SELECT ?ansLabel WHERE { wd:' + ID1 + ' p:' + ID2 + ' ?ans. SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
                    qs.append(query)
        # Generate statement query
        elif lan != []:
            for ID1 in ID1s:
                for ID2 in pIDs:
                    query = 'SELECT ?label WHERE { SERVICE wikibase:label { bd:serviceParam wikibase:language "' + lan[0] + '". wd:' + ID1 + ' rdfs:label ?label. } }'
                    qs.append(query)
        else:
            for ID1 in ID1s:
                for ID2 in pIDs:
                    if extra['metricUnit']:
                        query = 'SELECT ?statement ?ansLabel ?unitLabel WHERE { wd:' + ID1 + ' p:' + ID2 + ' ?statement. ?statement psv:' + ID2 + '?node. ?node wikibase:quantityUnit ?unit. ?statement ps:' + ID2 + ' ?ans. ?statement pq:' + extra['P'] + ' wd:' + extra['Q'] + ' SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
                    else: 
                        query = 'SELECT ?statement ?ansLabel WHERE { wd:' + ID1 + ' p:' + ID2 + ' ?statement. ?statement ps:' + ID2 + ' ?ans. ?statement pq:' + extra['P'] + ' wd:' + extra['Q'] + ' SERVICE wikibase:label { bd:serviceParam wikibase:language "nl,en". } }'
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
    try:
        keys, extra, lan_list = find_QP(question)
        q_ids = []
        for qkey in keys['Q']:
            q_ids.append(getIDs(qkey))
        p_ids = getIDs(keys['P'], p=True)
        lan = lan_list
        queries = createQueries(q_ids, p_ids, extra, lan)
        answers = []
        for query in queries:
            answer = getAnswer(query)
            if answer != []:
                answers.append(answer)
        if len(answers) == 0:
            return 'null'
        else:
            answer_given = False
            for ans in answers:
                if type(ans) == bool:
                    if not answer_given:
                        if True in answers:
                            answer_given = True
                            return 'Ja'
                        else:
                            answer_given = True
                            return 'Nee'
                else:
                    ans_str = ''
                    if extra['metricUnit']:
                        if len(ans) == 3:
                            ans = ans[1:]
                        for n in range(len(ans)):
                            if n == 0 or n % 2 == 0:
                                ans_str += ans[n]
                                ans_str += ' '
                                ans_str += ans[n+1]
                            elif n != len(ans) - 1:
                                ans_str += ', '
                    else:
                        for ansLabel in ans:
                            ans_str += ansLabel
                            if ansLabel != ans[-1]:
                                ans_str += ', '
                    return ans_str
    except Exception as e:
        print(f"Er was een fout bij het beantwoorden van de vraag: {str(e)}")

def main():
#    with open('simulate_input.json', 'r', encoding='utf-8') as f:
#       questions = json.load(f)

    #for question_data in questions:
        #question = question_data['string']
        #print(f"Vraag: {question}")
        #answerQuestion(question)
        #print()

    #q1 = "Hoe heet een goudvis in het Italiaans?"
    #q2 = 'Welke kleur heeft een ijsbeer?'
    #q3 = 'Welke commonscategorie past bij de olifant?'
    #q4 = 'Hoe lang is een giraffe?'
    #q5 = 'Wat is de belangrijkste voedselbron van een tijger?'
    #q6 = 'Welke IUCN-status heeft de leeuw?'
    #q7 = 'Is een ijsbeer wit?'
    questions = [
        'Wat is het gewicht van een rode panda?',
        'Hoe oud wordt een hond?',
        'Welke kleuren heeft een duitse herder?',
        'Is een reuzepanda herbivoor?',
        'Is de reuzepanda een carnivoor?',
        'Hoe zwaar is een volwassen mannetjes leeuw?',
        'Wat is de wetenschappelijke naam van een hond?',
        'Wat is de belangrijkste voedselbron van een orang-oetan?',
        'Eet een ijsbeer vis?',
        'Tot welk ras behoort de boerenfox?',
        'Hoe lang is een kat zwanger?',
        'Wat is de Engelse naam van een schol?'
    ]
    for q in questions:
        print(q)
        print(answerQuestion(q))
        print()
#    q = 'Waar leven orang-oetangs?'
#    print(q)
#    print(answerQuestion(q))
#    print()
#    output = []
#    for question_data in questions:
#        question_id = question_data['id']
#        question_text = question_data['question']
#        answer = answerQuestion(question_text)
#        correct = 1 if answer else 0
#    	
#        output.append({
#            "id": question_id,
#            "question": question_text,
#            "answer": answer,
#            "correct": correct
#        })
#    
#    with open('answers.json', 'w', encoding='utf-8') as f:
#        json.dump(output, f, indent=4)

if __name__ == '__main__':
    main()
