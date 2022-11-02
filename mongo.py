import pymongo
import json
import time
import random
import math
import requests
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def data_preprocess():
    list1 = [i*1000 for i in range(2)]
    list2 = [j*1000+999 for j in range(2)]

    for i in range(len(list1)):
        file = '/Users/imchengliang/Downloads/DataMining/Project/test/' + 'mpd.slice.' + str(list1[i]) + '-' + str(list2[i]) + '.json'
        with open(file) as info:
            dict1 =  json.load(info)
            del dict1['info']
            for i in range(len(dict1['playlists'])):
                del dict1['playlists'][i]["name"]
                del dict1['playlists'][i]["collaborative"]
                del dict1['playlists'][i]["modified_at"]
                del dict1['playlists'][i]["num_albums"]
                del dict1['playlists'][i]["num_tracks"]
                del dict1['playlists'][i]["num_followers"]
                del dict1['playlists'][i]["num_edits"]
                del dict1['playlists'][i]["duration_ms"]
                del dict1['playlists'][i]["num_artists"]
                tracks, artists = [], []
                for j in range(len(dict1['playlists'][i]["tracks"])):
                    u = dict1['playlists'][i]["tracks"][j]["track_uri"].split(':')
                    tracks.append(u[-1])
                    a = dict1['playlists'][i]["tracks"][j]["artist_uri"].split(':')
                    artists.append(a[-1])
                    del dict1['playlists'][i]["tracks"][j]["track_uri"]
                    del dict1['playlists'][i]["tracks"][j]["artist_name"]
                    del dict1['playlists'][i]["tracks"][j]["pos"]
                    del dict1['playlists'][i]["tracks"][j]["track_name"]
                    del dict1['playlists'][i]["tracks"][j]["album_uri"]
                    del dict1['playlists'][i]["tracks"][j]["duration_ms"]
                    del dict1['playlists'][i]["tracks"][j]["album_name"]
                dict1['playlists'][i]["tracks"] = tracks
                dict1['playlists'][i]["artists"] = artists
            for i in list(dict1['playlists']):
                print(i, '\n')
                mycol1.insert_one(i)

def jaccard(p1, p2):
    set1 = set(p1["tracks"])
    set2 = set(p2["tracks"])
    M11 = len(set1.intersection(set2))
    if M11 == 0:
        return 0
    else:
        M10 = len(p1["tracks"]) - M11
        M01 = len(p2["tracks"]) - M11           
        sim = M11/(M11+M10+M01) 
        return sim

def pearson(p1, p2):
    set1 = set(p1["tracks"])
    set2 = set(p2["tracks"])
    l1, l2 = [], []
    same = set1.intersection(set2)
    if len(same) <= 1:
        return 0
    else:
        print(same)
        for i in same:
            x = math.log(len(p1["tracks"])-p1["tracks"].index(i)+1)
            y = math.log(len(p2["tracks"])-p2["tracks"].index(i)+1)
            l1.append(x)
            l2.append(y)
        l1, l2 = np.array(l1), np.array(l2)
        print(l1, l2, '\n')
        print(l1-np.mean(l1), l2-np.mean(l2), '\n')
        r = np.sum((l1-np.mean(l1)) * (l2-np.mean(l2))) / np.sqrt(np.sum([a**2 for a in l1-np.mean(l1)]) * np.sum([a**2 for a in l2-np.mean(l2)]))
        print(r, '\n')
        return r

def cal_similarity():
    for i in range(100):
        p1 = mycol1.find_one({"pid":i})
        for j in range (i+1, 100):
            p2 = mycol1.find_one({"pid":j})
            jac = jaccard(p1, p2)
            mycol2.insert_one({'playlist1':i, 'playlist2':j, 'similarity':jac})
            mycol2.insert_one({'playlist1':j, 'playlist2':i, 'similarity':jac})
            #pea = pearson(p1, p2)
            #mycol3.insert_one({'playlist1':i, 'playlist2':j, 'similarity':pea})
            #mycol3.insert_one({'playlist1':j, 'playlist2':i, 'similarity':pea})
        print(i)

def nearest_user(user, near_num):
    sim = list(mycol2.find({"playlist1":user}))
    sim.sort(key=lambda x:(x["similarity"]), reverse=True)
    #sim.sort(key=lambda x:(x["pearson"]), reverse=True)
    return sim[:near_num]

def recommend(user, rec_num, near_num):
    l = nearest_user(user, near_num)
    total_rec = []
    total_sim = []
    for i in l:
        p1 = mycol1.find_one({"pid":i['playlist1']})
        p2 = mycol1.find_one({"pid":i['playlist2']})
        sim = i['similarity']
        total_sim.append(sim)
        set1 = set(p1["tracks"])
        set2 = set(p2["tracks"])
        same = set1.intersection(set2)
        rec = list(set2.symmetric_difference(same))
        total_rec.append(rec)
    merge = np.array(sum(total_rec, []))
    merge = np.unique(merge)

    scores = np.zeros(len(merge))
    idx = 0
    for i in merge:
        for j in range(len(l)):
            if i in total_rec[j]:
                scores[idx] += 1*total_sim[j]
            else:
                scores[idx] += 0*total_sim[j]
        idx += 1
    
    dict_rec = dict(zip(merge, scores))
    tup_rec = list(zip(dict_rec.values(), dict_rec.keys()))
    sort_rec = sorted(tup_rec, reverse=True)
    final_rec = []
    for i in range(rec_num):
        final_rec.append(sort_rec[i][1])
    print(final_rec)

    rec_artists, rec_genres = [], []
    for i in l:
        p2 = mycol1.find_one({"pid":i['playlist2']})
        s1 = list(p2["tracks"]) 
        s2 = list(p2["artists"])
        for j in final_rec:
            if j in s1:
                idx = p2["tracks"].index(j)
                a_id = s2[idx]
                rec_artists.append(a_id)
    rec_artists = np.unique(rec_artists)
    print(rec_artists, '\n')
    
    rec_g = []
    for a in rec_artists:
        url = "https://api.spotify.com/v1/artists/" + a
        response = requests.get(url, headers={"Content-Type":"application/json", 
                                "Authorization":"Bearer BQBdPGCW18qzde4kb8OkvIGsQXv5UvHmia4cXEtquKIWXAcvruwUusP00XR5HlHLZ_xXs1Z-961RHb8hIfIt3xf8q9B7OuvEskbDidXwx67KROcjtcxiwKX93Hfuw83fRdy7xhayENjoDlgO8CIdszOY28qcwPfoZdhMk8Scp-6IC6fwdme47_7_GgPWYU91VjI"})

        for i in response.json()['genres']:
            rec_g.append(i)

    print('\n', rec_g, '\n')
    return rec_g    

def get_genre(user):
    genres = []
    p1 = mycol1.find_one({"pid":user})
    set1 = set(p1["artists"])
    for j in set1:
        url = "https://api.spotify.com/v1/artists/" + j
        response = requests.get(url, headers={"Content-Type":"application/json", 
                                "Authorization":"Bearer BQBdPGCW18qzde4kb8OkvIGsQXv5UvHmia4cXEtquKIWXAcvruwUusP00XR5HlHLZ_xXs1Z-961RHb8hIfIt3xf8q9B7OuvEskbDidXwx67KROcjtcxiwKX93Hfuw83fRdy7xhayENjoDlgO8CIdszOY28qcwPfoZdhMk8Scp-6IC6fwdme47_7_GgPWYU91VjI"})

        for i in response.json()['genres']:
            genres.append(i)
            
    result = {}
    for i in set(genres):
        result[i] = genres.count(i)

    new_result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    print(new_result, '\n')
    return genres, new_result

def recall_precision(user, rec_num, near_num):
    l_p, d_p = get_genre(user)
    r = recommend(user, rec_num, near_num)
    #s1 = set(l_p)
    #s2 = set(r)
    r_same = []
    for i in r:
        if i in l_p:
            r_same.append(i)

    #same = s1.intersection(s2)
    recall = len(r_same) / len(l_p)
    precision = len(r_same) / len(r)
    #re.append(recall)
    #pre.append(precision)
    print('user: ', user, 'recall: ', recall, 'precision: ', precision, '\n')

def plot_genre(user, rec_num, near_num):
    l_p, d_p = get_genre(user)
    r = recommend(user, rec_num, near_num)
    '''
    result = {}
    for i in set(r):
        result[i] = r.count(i)

    new_result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    
    print(dict(d_p))
    names = list(dict(d_p).keys())
    values = list(dict(d_p).values())
    for i in range(len(d_p)):
        plt.bar(i, values[i],tick_label=names[i])
    plt.xticks(range(0, len(d_p)),names)
    #plt.savefig('fruit.png')
    plt.show()
    '''
    str = ''
    for i in l_p:
        str += i
        str += ' '
    wc = WordCloud(width=800, height=600, mode="RGBA", background_color=None).generate(str)
    plt.imshow(wc, interpolation='bilinear')   
    plt.axis("off")  
    plt.show()

    str = ''
    for i in r:
        str += i
        str += ' '
    wc = WordCloud(width=500, height=300, mode="RGBA", background_color=None).generate(str)
    plt.imshow(wc, interpolation='bilinear')   
    plt.axis("off")  
    plt.show()

def plot_recall_precision(re, pre, re_n):
    x = range(len(re_n))
    plt.plot(re_n, re,label=u'Recall')
    plt.plot(re_n, pre, label=u'Precision')
    plt.ylim(0, 1)
    plt.legend()
    plt.margins(0)
    plt.subplots_adjust(bottom=0.15)
    plt.xlabel(u"Number of Neighbors")
    plt.show()

if __name__ == '__main__':
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    dblist = myclient.list_database_names()
    mydb = myclient["spotify"]
    mycol1 = mydb["playlists"]
    mycol2 = mydb["jaccard"]
    mycol3 = mydb["pearson"]
    '''
    file = 'similarity.json'
    with open(file) as info:
        dict1 =  json.load(info)
        for i in range(len(dict1)):
                del dict1[i]['_id']
        for i in list(dict1):
                mycol2.insert_one(i)
    print("done")
    '''
    #mycol1.drop()
    #mycol2.drop()
    #mycol3.drop()
    #data_preprocess()
    #cal_similarity()
    pre, re, n = [], [], [1, 5, 10, 20, 50, 100, 150]
    for i in [18]:
        for j in [100]:
            nearest_user(user=i, near_num=j)
            recommend(user=i, rec_num=5, near_num=j)
            get_genre(user=i)
            recall_precision(user=i, rec_num=5, near_num=j)
            #plot_genre(user=i, rec_num=5, near_num=j)
    print(re, pre)
    #plot_recall_precision(re, pre, n)