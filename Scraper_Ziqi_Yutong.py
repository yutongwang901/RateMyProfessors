from bs4 import BeautifulSoup
import requests
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import csv
import io

def GenerateSchoolurls(schoolID):
    '''
    input: School IDs obtained from RateMyProfessor, after sid= in the url
    return: a list of school urls to visit later
    '''
    print("Generating urls from given school IDs...")
    schoolLinks = []
    base_url = 'https://www.ratemyprofessors.com/campusRatings.jsp?sid='
    for i in schoolID:
        url = base_url + i
        schoolLinks.append(url)
    return schoolLinks

def GenerateProfLists(url):
    '''
    Use the school urls to get list of profs
    '''
    print("Generating professors lists...")
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',})
    #linklist = []
    base_url = 'https://www.ratemyprofessors.com'
    try:
        page = requests.get(url,headers = headers)
    except:
        print('Failed opening the url:', url, '... Retrying')
    soup = BeautifulSoup(page.content, 'html.parser')
    profLink = soup.find_all('div',{'class': "header"})[5].find_all('a', href=True)[0]
    txt = str(profLink)
    x = re.findall(r'href=[\'"]?([^\'" >]+)', txt)[0]
    output = base_url + x.replace('amp;', '')
    #linklist.append(output)
    return output

def EachProfPage(url):
    '''
    Each university page contains a list of professors' url, scrape all professor urls.
    '''
    #url = 'https://www.ratemyprofessors.com/search.jsp?queryBy=schoolId&schoolName=Harvard+University&schoolID=399&queryoption=TEACHER'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    browser = webdriver.Chrome("./chromedriver")
    browser.implicitly_wait(10)
    browser.get(url)
    browser.find_element_by_xpath('//*[@id="ccpa-footer"]/button[2]').click()
    #Simulate clicking 10 times, each time 20 more profs is loaded
    for j in range(3):     
        try: 
            print("Loading more...")
            target = browser.find_element_by_xpath('//*[@id="mainContent"]/div[1]/div/div[5]/div/div[1]')
            browser.execute_script('arguments[0].scrollIntoView(true);', target)
            target.click()
            time.sleep(1)
        except:
            print("Failed to load more...")
            continue

    profPage = []
    base_url = 'https://www.ratemyprofessors.com'
    page = browser.page_source
    soup = BeautifulSoup(page)
    div = soup.find_all('div', {'class': 'result-list'})[1].find_all("a", href=True)
    x = re.findall(r'href=[\'"]?([^\'" >]+)', str(div))   
    output = []
    for i in x:
        fullurl = base_url + i.replace('amp;', '')
        output.append(fullurl)
    return output


def StoreURLs(schoolids):
    l = len(schoolids)
    schoolurls = []
    for i in schoolids:
        ids = GenerateSchoolurls([i])
        schoolurls.append(ids)
    proflist = []
    for i in schoolurls:
        profpage = GenerateProfLists(i[0])
        proflist.append(profpage)
    all_Prof = []
    for i in proflist:
        zxc = EachProfPage(i)
        all_Prof.append(zxc)
    with io.open('url_community.txt', 'a') as file:
        for i in all_Prof:
            file.write('%s\n' % i)

def grabScore(url, soup):
    quality = soup.find_all('div', {'class': 'RatingValues__RatingContainer-sc-6dc747-1 DObVa'})
    scores = []
    for i in quality:
        pointer = i.find('div', {'class': 'RatingValues__RatingLabel-sc-6dc747-2 gLxTSP'})
        next_tag = pointer.findNext('div')
        qualityScore = re.findall('\>(.*?)\<', str(next_tag))
        scores.append(qualityScore)
    #print(scores)
    #scrape quality scores and difficulty scores
    qua = []
    diff = []
    for i in range(len(scores)):
        if i % 2 == 0:
            qua.append(scores[i])
        else:
            diff.append(scores[i])
    try:
        feature = soup.find_all('div', {'class': 'EmotionLabel__StyledEmotionLabel-sc-1u525uj-0 cJfJJi HelpfulRating__StyledHelpfulEmotionLabel-sc-4ngnti-3 jngUOr'})
    except:
        print("Failed to scrape FEATURECOMMENT from this url:", url)
    #if re.findall('\>(.*?)\<', str(feature)) is True: 
    try:
        course = [[re.findall('\>(.*?)\<', str(feature))[-1]]]
        qua.insert(0, ['NA'])
        diff.insert(0, ['NA'])
    except:
        print('This prof. has no featured rating...')
        course = []
    return qua, diff, course

def grabComment(url, soup):
    commentList = []
    try:
        comments = soup.find_all('div', {'class': 'Comments__StyledComments-dzzyvm-0 gRjWel'})
        for i in comments:
            text = re.findall('\>(.*?)\<', str(i))
            commentList.append(text)
    except:
        print("Failed to scrape COMMENT from this url:", url)
    return commentList

def grabfeature(url, soup):
    try:
        feature = soup.find_all('div', {'class': 'EmotionLabel__StyledEmotionLabel-sc-1u525uj-0 cJfJJi HelpfulRating__StyledHelpfulEmotionLabel-sc-4ngnti-3 jngUOr'})
    except:
        print("Failed to scrape FEATURECOMMENT from this url:", url)
    #if re.findall('\>(.*?)\<', str(feature)) is True: 
    try:
        course = [[re.findall('\>(.*?)\<', str(feature))[-1]]]
        qua.insert(0, ['NA'])
        diff.insert(0, ['NA'])
    except:
        print('This prof. has no featured rating...')
        course = []
    return course

def grabCourse(url, soup, course):
    #scrape normal course IDs
    try:
        otherCourse = soup.find_all('div', {'class': 'RatingHeader__StyledClass-sc-1dlkqw1-2 gxDIt'})
        for i in range(len(otherCourse)):
            if i % 2 == 0:
                c = re.findall('\-->(.*?)\<', str(otherCourse[i]))
                course.append(c)
            else:
                pass
    except:
        print("Failed to scrape COURSE from this url:", url)
    return course

def grabSchool(url, soup):
    try:
        schoolnamediv = soup.find('div', {'class': 'NameTitle__Title-dowf0z-1 iLYGwn'}).find('a')
        schoolname = re.findall('\>(.*?)\<', str(schoolnamediv))
    except:
        print("Failed to scrape SCHOOL NAME from this url:", url)
    return schoolname

def grabFirst(url, soup):
    #scrape prof name
    try:
        firstnamediv = soup.find('div', {'class': 'NameTitle__Name-dowf0z-0 cfjPUG'}).find('span')
        firstname = re.findall('\>(.*?)\<', str(firstnamediv))
    except:
        print("Failed to scrape FIRSTNAME from this url:", url)
    return firstname

def grabLast(url, soup):
    try:
        lastnamediv = soup.find('span', {'class': 'NameTitle__LastNameWrapper-dowf0z-2 glXOHH'})
        lastname = re.findall('\>(.*?)\<!--', str(lastnamediv))
    except:
        print("Failed to scrape LASTNAME from this url:", url)
    return lastname

def grabDep(url, soup):
    #scrape department
    try:
        departmentdiv = soup.find('div', {'class': 'NameTitle__Title-dowf0z-1 iLYGwn'}).find('span').find('b')
        department = re.findall('\>(.*?)\<!--', str(departmentdiv))
    except:
        print("Failed to scrape DEPARTMENT from this url:", url)
    return department

def grabID(url, soup):
    #scrape  Prof ID
    try:
        iddiv = soup.find('div', {'class': 'NameLink__StyledNameLink-sc-4u2ek-0 hiHJpP'})
        ID = re.findall(r'tid=(.*?)\"', str(iddiv))    
    except:
        print("Failed to scrpae ProfID from this url:", url)
    return ID

def grabAvgScore(url, soup):
    #scrape  Prof average score
    try:
        s = soup.find_all('div', {'class': 'RatingValue__Numerator-qw8sqy-2 liyUjw'})
        score = re.findall('\>(.*?)\<', str(s))  
    except:
        print("Failed to scrpae average Score from this url:", url)
    return score

def AvgScoreOnly(url):
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',})
    try:
        print("Scraping a new professor page...")
        page = requests.get(url, headers=headers)
    except:
        print('Failed opening the url:', url, '... Retrying')
    soup = BeautifulSoup(page.content, 'html.parser')
    ID = grabID(url, soup)
    score = grabAvgScore(url,soup)
    with io.open('com_score.csv', 'a', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(len(ID)):
            try:
                writer.writerow([ID[0],score[0]])
            except:
                print('Failed storing data...')

def startGrab(url):
    #url = 'https://www.ratemyprofessors.com/ShowRatings.jsp?tid=6088&showMyProfs=true'
    #ID = '6088'
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',})
    try:
        print("Scraping a new professor page...")
        page = requests.get(url, headers=headers)
    except:
        print('Failed opening the url:', url, '... Retrying')
    soup = BeautifulSoup(page.content, 'html.parser')
    
    qua, diff,course1 = grabScore(url, soup)
    course = grabCourse(url,soup, course1)
    schoolname = grabSchool(url, soup)
    firstname = grabFirst(url, soup)
    lastname = grabLast(url, soup)
    department = grabDep(url,soup)
    ID = grabID(url, soup)
    commentList = grabComment(url,soup)

    with io.open('data_community.csv', 'a', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

#         #write column names
#         column_names = ['ID', "first name", 'last name', 'school',\
#                         'department','courseID', 'quality', 'difficulty', 'text']
#         writer.writerow(column_names)

        #write rows
        for i in range(len(qua)):
            try:
                writer.writerow([ID[0],firstname[0], lastname[0],schoolname[0], department[0], course[i][0], qua[i][0], diff[i][0], commentList[i][0]])
            except:
                print('Failed storing data...')
    return 


if __name__ == '__main__':
    #schoolids = ['399', '278', '580', '1222', '953', '1085', '1275', '148', '464', '1350', '1339', '137', '4002', '799', '1147', '298', '1576', '1075', '340',\
    #            '1072', '355', '1258', '1381', '1075', '1072', '1258', '1277', '1232', '1077', '1100', '361', '1074', '1079', '1073', '5968', '1255', '1256', \
    #           '1101', '1112', '724', '783', '1237', '1270', '1247', '1530', '758', '825', '1091', '399', '278', '1222', '1275', '1339', '137', '298', '1112', \
    #          '440', '1115', '1270', '1258', '601', '1257', '1249', '724', '758', '783', '825', '1256']

    #ids = [45,237,599,850,999,1087,1261,1600,1262,301,540,807,1111,1385,452,668,826,973,1309,1320,207,240,1389,4250,347]
    #schoolids = [str(x) for x in ids]
    schoolids=['13706', '2264', '2184', '1355', '1557', '1308', '1544', '1704', '1278', '2004', '4394', '4405', '2639', '1304', '13734']
    #StoreURLs(schoolids)

    url = []
    with open('url_community.txt', 'r') as file:
        for i in file:
            url.append(i)
    for i in url:
        cleanurl = i.replace("'", "").split(',')
        cleanurl = [x.replace("[", '') for x in cleanurl]
        cleanurl = [x.replace("'", '') for x in cleanurl]
        cleanurl = [x.replace(' ', '') for x in cleanurl]
        #print(len(cleanurl))
        for j in cleanurl[40:]:
            AvgScoreOnly(j)
                
#    StoreURLs(schoolids)
#    for i in all_Prof:
#       for j in i:
#            startGrab(j)
