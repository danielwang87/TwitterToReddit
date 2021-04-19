import tweepy
import time
import praw
import requests
import bs4 as bs
from naiveBayes import *

def deletePrevPosts(reddit, playerName):
    for submission in reddit.redditor("").submissions.new():
        if (submission.title.find(playerName) != -1 and submission.score < 20):
            submission.delete()
        
def getTopPlayers(): #returns a list of top 100 fantasy players
    players = []
    url = "https://dknation.draftkings.com/2020/12/1/21723927/fantasy-basketball-rankings-2020-2021-list-players-espn-top-100-luka-doncic-lebron-james-giannis"
    source = requests.get(url, headers = {'user-agent': 'agentx'})
    sourceText = bs.BeautifulSoup(source.text, 'lxml')
    for tag in sourceText.find_all('td'):
        tag = tag.string #get the contents within the tag
        if (tag == None):
            continue
        if (tag.find(',') != -1 ):
            tag = tag[:tag.find(',')]
            if (tag not in players):
                players.append(tag)
    return players

def preprocessFlabs(currentTweet):
    playerInfo = []
    exists = currentTweet.find("http")
    if (exists != -1):
        currentTweet = currentTweet[:exists] 
    if (currentTweet.find("Lineup note") != -1 or currentTweet.find("Key news") != -1):
        return -1

    players = getTopPlayers()
    for player in players:
        if (currentTweet.find(player) != - 1):
            playerInfo.append(player)
            playerInfo.append(currentTweet)
            return playerInfo
    return -1

def main():
    #twitter API authentication
    consumer_key = ""
    consumer_secret = ""
    access_token = ""
    access_token_secret = ""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    twitter = tweepy.API(auth, wait_on_rate_limit = True)

    #reddit API authentication/create reddit instance
    reddit = praw.Reddit(client_id = "", client_secret = "", 
                        password = "", user_agent = "", 
                        username = "")
    
    #for template in reddit.subreddit("fantasybball").flair.link_templates:
        #print(template["richtext"][0]["t"] + ": " + template["id"])

    output = train()

    previousTweetFlabs = ""
    previousTweetWoj = ""
    while(True):
        #fantasy labs
        flabsTweets = twitter.user_timeline(screen_name = "@FantasyLabsNBA", count = 1, include_rts = False, tweet_mode = "extended")
        #print(flabsTweets[0])
        currentTweet = flabsTweets[0].full_text
        if (previousTweetFlabs != currentTweet):
            previousTweetFlabs = currentTweet
            currentTweet = preprocessFlabs(currentTweet) #currentTweet now a pair of playerName and repsective tweet
            if (currentTweet != -1):
                deletePrevPosts(reddit, currentTweet[0])
                print(currentTweet[1])
                reddit.subreddit("fantasybball").submit(currentTweet[1], 
                    "Source: https://twitter.com/FantasyLabsNBA/status/" + flabsTweets[0].id_str, flair_id = "2198a034-1f76-11e9-95a1-0eef45e7287a")
        
        #woj
        wojTweets = twitter.user_timeline(screen_name = "@wojespn", count = 1, include_rts = False, tweet_mode = "extended")
        currentTweet = wojTweets[0].full_text
        if (previousTweetWoj != currentTweet):
            previousTweetWoj = currentTweet
            relevancy = testNaiveBayes(currentTweet, output[0], output[1], output[2], output[3], output[4])
            if (relevancy == "R"):
                print(currentTweet)
                reddit.subreddit("NBAUpdatestesting").submit(currentTweet, 
                    "Source: https://twitter.com/wojespn/status/" + wojTweets[0].id_str)
        time.sleep(10)

if __name__ == "__main__":
    main()