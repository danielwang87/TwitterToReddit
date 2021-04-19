import tweepy
import requests
import bs4 as bs
import sys
import math

def preprocessWoj(contents):
    #remove links
    linkIndex = contents.find("http")
    tempIndex = linkIndex
    length = 0
    if (linkIndex != -1):
        while (contents[tempIndex] != " " or contents[tempIndex] != "\n"):
            length += 1
            tempIndex += 1
            if (tempIndex == len(contents)):
                break
        contents = contents[:linkIndex] + contents[linkIndex + length - 1:]
    
    contents = contents.split(" ")
    i = 0
    for i in range(len(contents)):
        contents[i] = contents[i].strip(",")
        contents[i] = contents[i].strip(".")
        contents[i] = contents[i].strip(":")
        contents[i] = contents[i].strip(";")

    fileOpen = open('stopwords')
    stopwords = fileOpen.read()
    stopwords = stopwords.replace('\n', ' ')
    stopwords = stopwords.split(' ')
    for word in stopwords: #loop through all stopwords
        for word2 in contents: #loop through file
            if (word2 == "I"):
                continue
            if (word2.lower() == word.lower()): #if a stopword is found in the file, remove that word
                contents.remove(word2)
    fileOpen.close()
    return contents

def collectTweets():
    consumer_key = ""
    consumer_secret = ""
    access_token = ""
    access_token_secret = ""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    twitter = tweepy.API(auth, wait_on_rate_limit = True)

    outputFile = open("wojTweets.txt", "w")
    wojTweets = twitter.user_timeline(screen_name = "@wojespn", count = 200, include_rts = False, tweet_mode = "extended")
    for tweet in wojTweets:
        print(tweet.full_text + "\n", file = outputFile)
    outputFile.close()

def train():
    numRelevantWords = 0
    numIrrelevantWords = 0
    numRelevantTweets = 0
    numIrrelevantTweets = 0
    classProbs = {} #probability of each class
    wordProbs = {}
    vocabSize = 0
    output = []

    fileOpen = open(sys.argv[1])
    tweets = fileOpen.read()
    tweets = tweets.split("\n\n")
    for tweet in tweets:
        tweet = preprocessWoj(tweet)
        if (len(tweet) == 0):
            continue
        relevant = tweet[len(tweet) - 1] == "R"
        if (relevant): #find number of relevant and irrelevant tweets
            numRelevantTweets += 1
        else:
            numIrrelevantTweets += 1
        tweet = tweet[:len(tweet) - 1] #remove letter at the end

        for word in tweet: #calculate the number of occurences of each word in each class 
            if (word.lower() in wordProbs): #if already in dictionary, just add 1 to appropriate count
                if (relevant):
                    wordProbs[word.lower()]["R"] += 1
                else:
                    wordProbs[word.lower()]["I"] += 1
            else: #if not in dictionary, create an instance of it and add 1 to appropriate count
                wordProbs[word.lower()] = {}
                wordProbs[word.lower()]["R"] = 0
                wordProbs[word.lower()]["I"] = 0
                if (relevant):
                    wordProbs[word.lower()]["R"] += 1
                else:
                    wordProbs[word.lower()]["I"] += 1
        
    vocabSize = len(wordProbs)
    for word in wordProbs: #calculate total number of words in all true files and in all lie files
        numRelevantWords += wordProbs[word]["R"]
        numIrrelevantWords += wordProbs[word]["I"]

    classProbs["R"] = math.log10(numRelevantTweets / len(tweets)) #calculate class probabilities
    classProbs["I"] = math.log10(numIrrelevantTweets / len(tweets))
    
    for word in wordProbs: #replace number of occurences with conditional probabilities of each word
        wordProbs[word]["R"] = math.log10((wordProbs[word]["R"] + 1) / (numRelevantWords + vocabSize)) #smoothing
        wordProbs[word]["I"] = math.log10((wordProbs[word]["I"] + 1) / (numIrrelevantWords + vocabSize))

    output.append(classProbs)
    output.append(wordProbs)
    output.append(vocabSize)
    output.append(numRelevantWords)
    output.append(numIrrelevantWords)
    
    return output

def testNaiveBayes(contents, classProbs, wordProbs, vocabSize, numRelevantWords, numIrrelevantWords):
    contents = preprocessWoj(contents)
    if (contents == ""):
        return "I"
    relProb = 0
    irrelProb = 0
    for word in contents: #calculate probabilities for each class
        word = word.lower()
        if (word in wordProbs):
            relProb += wordProbs[word]["R"]
            irrelProb += wordProbs[word]["I"]
        else: #if word doesn't exist in training data dictionary, use smoothing numbers
            relProb += math.log10(1 / (vocabSize + numRelevantWords))
            irrelProb += math.log10(1 / (vocabSize + numIrrelevantWords))

    relProb += classProbs["R"]
    irrelProb += classProbs["I"]

    if (relProb > irrelProb): #pick higher one
        return "R"
    else:
        return "I"
