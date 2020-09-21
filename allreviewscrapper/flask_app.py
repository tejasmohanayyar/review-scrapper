#!/usr/bin/env python
# coding: utf-8

# In[1]:


# !pip install beautifulsoup4 requests --quiet
# !pip install pandas --quiet
# !pip install matplotlib


# In[2]:

from flask import Flask, render_template, request,jsonify,Response,send_file
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pandas as pd
import time
import pymongo

app = Flask(__name__)

# In[3]:
@app.route('/csv')
def return_file():
    return send_file('scrappedreviews.csv',as_attachment=True)


@app.route('/',methods=['POST','GET'])
def index():
    # In[4]:
    if request.method == 'POST':
        search = request.form['content'].replace(" ","-")
        numberofpages = int(request.form['numberpages'].replace(" ",""))
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            db = dbConn['allreviewsdb']
            reviews = db[search].find({})
            if reviews.count()>(numberofpages*10):
                reviews = list(db[search].find({}))[:((numberofpages*10)+1)]
                df = pd.DataFrame(reviews)
                df.drop_duplicates("Comments",inplace = True)
                df.to_csv('scrappedreviews.csv')
                return render_template('results.html',reviews=reviews)

            else:
                def scrapper_tool(reviews_link, tag, classparam, removefirst4=False, bsop=False):
                    reviewslink = uReq(reviews_link)
                    reviewspage = reviewslink.read()
                    reviewslink.close()
                    if bsop == True:
                        reviewspage = requests.get(reviews_link)
                        reviews_html = bs(reviewspage.text, "html.parser")
                        commentbox = reviews_html.findAll(tag, {'class': classparam})
                    if (removefirst4 == True):
                        del commentbox[0:4]
                    return commentbox

                url = "https://www.flipkart.com/search?q=" + search
                # In[5]:
                big_boxes = scrapper_tool(url, tag='div', classparam="bhgxx2 col-12-12", bsop=True)
                del big_boxes[0:3]
                box = big_boxes[0]
                product_link = "https://www.flipkart.com" + box.div.div.div.a['href']


                # In[7]:


                commentbox = scrapper_tool(product_link, tag='div', classparam="col _39LH-M", bsop=True)
                reviews_page = commentbox[0].findAll('a')[-1]['href']
                reviews_link = "https://www.flipkart.com" + reviews_page

                # In[8]:


                if len(reviews_page) > 120:
                    commentbox = scrapper_tool(reviews_link, 'div', "_3gijNv col-12-12", removefirst4=True, bsop=True)
                    nonextpage = 0
                else:
                    commentbox = scrapper_tool(reviews_link, 'div', "_3nrCtb", removefirst4=False, bsop=True)
                    nonextpage = 1

                # In[9]:


                reviews = []
                nextpagenumber = 2


                table = db[search]

                # In[10]:


                for i in range(numberofpages):

                    for commentboxes in commentbox:
                        # Name
                        try:
                            name = commentboxes.div.div.find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text
                        except:
                            pass


                        # rating
                        try:
                            rating = commentboxes.div.div.div.div.text[0]
                        except:
                            pass
                        # comment head
                        try:
                            commenthead = commentboxes.div.div.div.p.text
                        except:
                            pass
                        # comment
                        try:
                            comment = commentboxes.div.div.findAll('div', {'class': ''})[0].text
                            comment = comment[:-9]
                        except:
                            pass
                        mydict = {'Product': search,'Name': name, 'Comment Title': commenthead, 'Rating': rating, 'Comments': comment}
                        x = table.insert_one(mydict)
                        reviews.append(mydict)

                    if nonextpage == 1:
                        break
                    else:
                        nextpage = scrapper_tool(reviews_link, 'a', "_3fVaIS", removefirst4=False, bsop=True)[0]['href']
                        l = "https://www.flipkart.com" + nextpage
                        nextpagelink = l[:-1] + str(nextpagenumber)
                        commentbox = scrapper_tool(nextpagelink, 'div', "_3gijNv col-12-12", removefirst4=True, bsop=True)
                        nextpagenumber += 1
                        time.sleep(2)



                df = pd.DataFrame(reviews)
                df.drop_duplicates("Comments",inplace = True)
                df.to_csv('scrappedreviews.csv')
                return render_template('results.html', reviews=reviews)
                

        except:
            return 'Something is wrong'


    else:
        return render_template('index.html')
if __name__ == "__main__":
    app.run(port=8000,debug = True)
                # In[11]:

                # df = pd.DataFrame(reviews)


# for i in range(len(df)):
#     if df['name'][i] == "No Name":
#         df.drop(i, inplace=True)
#     else:
#         pass
#
# df.to_csv(r'reviews.csv')
