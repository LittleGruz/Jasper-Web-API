from datetime import date,timedelta
import http.client
import json
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

dateToday = date.today()
sessionLimit = 5
dateReplace = dateToday.strftime("%m/%d/%Y")
dateReplacePrior = (dateToday - timedelta(days=29)).strftime("%m/%d/%Y")


ccidList = """CCIDS"""
jsSessionCookie = ""
username = "USERNAME"
password = "PASSWORD"

#Login request
conn = http.client.HTTPSConnection("telstra.jasper.com")
payload = 'j_username='+username+'&j_password='+password
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded'
}

urlCall = """/provision/j_acegi_security_check"""
conn.request("POST", urlCall, payload, headers)
res = conn.getresponse()
data = res.read()
if res.status >= 400:
    print("Login failed")
else:
    headers = res.getheader("Set-Cookie").split(",")
    for head in headers:
        #Get the login session cookie
        if "jsSessionCookie" in head:
            values = head.split(";")
            for val in values:
                if "jsSessionCookie" in val and "==" in val:
                    startPos = val.find("\"")
                    jsSessionCookie = val[startPos:]
                    print("Login biscuit: "+val[startPos:])
    
    ccids = ccidList.replace(",","\n").replace("\r","").split("\n")
        
    try:
        resultString = ""
        
        conn = http.client.HTTPSConnection("telstra.jasper.com")
        for ccid in ccids:
            payload = ''
            headers = {
                'Accept': '*/*',
                'Cookie': 'jsSessionCookie='+jsSessionCookie
            }

            #Get the Jasper simId from the CCID, this the reference ID used by the website for all requests
            urlCall = """/provision/api/v1/sims?_dc=1678372522628&page=1&limit=1&sort=dateAdded&dir=DESC&search=[{"property":"oneBox","type":"CONTAINS","value":"REPLACE","id":"oneBox"}]""".replace("REPLACE",ccid)
            conn.request("GET", urlCall, payload, headers)
            res = conn.getresponse()
            data = res.read()
            responseSim = json.loads(data.decode("utf-8"))
            simId = ""
            if res.status >= 300:
                print("Not fine")
                #print(responseSim)
                if "Full authentication" in responseSim["errorMessage"]:
                    raise RuntimeError("Session timed out")
            else:
                if len(responseSim["data"]) > 0:
                    simId = responseSim["data"][0]["simId"]
                else:
                    resultString += ccid + "\tNot found in Jasper\n"
                    continue
            
            payload = ''
            headers = {
                'Accept': '*/*',
                'Cookie': 'jsSessionCookie='+jsSessionCookie
            }

            #Get session details from the current month
            urlCall = """/provision/api/v1/dataTrafficDetails?_dc=1678366298870&page=1&limit=REPLACE_LIMIT&sort=recordOpenTime&dir=DESC&search=[{"property":"simId","type":"LONG_EQUALS","value":REPLACE,"id":"simId"},{"property":"billingCycle.cycleStartDate","type":"BILLDATE_EQUALS","value":"REPLACE_DATE","id":"cycleStartDate"}]""".replace("REPLACE_LIMIT",str(sessionLimit)).replace("REPLACE_DATE",str(dateReplace)).replace("REPLACE",str(simId))
            conn.request("GET", urlCall, payload, headers)
            res = conn.getresponse()
            data = res.read()
            response = json.loads(data.decode("utf-8"))
            sesh1 = ""
            sesh2 = ""
            apn1 = ""
            apn2 = ""
            duration1 = 0
            duration2 = 0
            usage1 = 0
            usage2 = 0
            sessions = 0
            if res.status >= 300:
                print("Not fine")
                print(response)
                if "Full authentication" in response["errorMessage"]:
                    raise RuntimeError("Session timed out")
            else:
                sessions = response["totalCount"]
                localLimit = sessionLimit
                if localLimit > response["totalCount"]:
                    localLimit = response["totalCount"]
                for i in range(localLimit):
                    #session = json.loads(response["data"][i])
                    if i == 0:
                        apn1 = response["data"][i]["apn"]
                        duration1 = response["data"][i]["duration"]
                        usage1 = response["data"][i]["roundedUsageKB"]
                    elif i == 1:
                        apn2 = response["data"][i]["apn"]
                        duration2 = response["data"][i]["duration"]
                        usage2 = response["data"][i]["roundedUsageKB"]
                        
                    print("Duration: "+str(response["data"][i]["duration"])+" APN: "+response["data"][i]["apn"]+" Data: "+str(response["data"][i]["roundedUsageKB"]))
            
                #We want the 2 most recent sessions. Jasper only returns data on a month, by month basis, so if it is split over 2 months, it needs a separate month request
                if response["totalCount"] < 2:
                    payload = ''
                    headers = {
                        'Accept': '*/*',
                        'Cookie': 'jsSessionCookie='+jsSessionCookie
                    }

                    #Get session details from the previous month
                    urlCall = """/provision/api/v1/dataTrafficDetails?_dc=1678366298870&page=1&limit=REPLACE_LIMIT&sort=recordOpenTime&dir=DESC&search=[{"property":"simId","type":"LONG_EQUALS","value":REPLACE,"id":"simId"},{"property":"billingCycle.cycleStartDate","type":"BILLDATE_EQUALS","value":"REPLACE_DATE","id":"cycleStartDate"}]""".replace("REPLACE_LIMIT",str(sessionLimit)).replace("REPLACE_DATE",str(dateReplacePrior)).replace("REPLACE",str(simId))
                    conn.request("GET", urlCall, payload, headers)
                    res = conn.getresponse()
                    data = res.read()
                    response = json.loads(data.decode("utf-8"))
                    if res.status >= 300:
                        print("Not fine")
                        print(response)
                    else:
                        sessions += response["totalCount"]
                        localLimit = sessionLimit
                        if localLimit > response["totalCount"]:
                            localLimit = response["totalCount"]
                        for i in range(localLimit):
                            #session = json.loads(response["data"][i])
                            print("Duration: "+str(response["data"][i]["duration"])+" APN: "+response["data"][i]["apn"]+" Data: "+str(response["data"][i]["roundedUsageKB"]))
                            if i == 0:
                                if apn1 == "":
                                    apn1 = response["data"][i]["apn"]
                                    duration1 = response["data"][i]["duration"]
                                    usage1 = response["data"][i]["roundedUsageKB"]
                                else:
                                    apn2 = response["data"][i]["apn"]
                                    duration2 = response["data"][i]["duration"]
                                    usage2 = response["data"][i]["roundedUsageKB"]
                            elif i == 1 and apn2 == "":
                                apn2 = response["data"][i]["apn"]
                                duration2 = response["data"][i]["duration"]
                                usage2 = response["data"][i]["roundedUsageKB"]
            
            #Determine if the last 2 sessions have been good
            mostRecentGood = False
            secondRecentGood = False
            oneGoodDuration = False
            if apn1 != "":
                if duration1 > 0:
                    oneGoodDuration = True
                if duration1 > 0 and usage1 > 0.0:
                    mostRecentGood = True
                    sesh1 = str(duration1)+"s/"+str(usage1)+"KB"
            if apn2 != "":
                if duration2 > 0 and usage2 > 0.0:
                    secondRecentGood = True
                    seshDeets = " ("+str(duration1)+"s/"+str(usage1)+"KB & "+str(duration2)+"s/"+str(usage2)+"KB)"
            
            resultString += ccid + "\t"
            if mostRecentGood and secondRecentGood:
                resultString += "Successfully sessions "+seshDeets+"\n"
            elif mostRecentGood:
                resultString += "One successful session ("+sesh1+")""\n"
            elif sessions == 0:
                resultString += "No sessions found in the last 2 billing cycles\n"
            else:
                resultString += "Unsuccessful\n"
        
        print("Finished. "+resultString)
    except http.client.RemoteDisconnected:
        print("Jasper connection timed out. Please login again.")
    except RuntimeError:
        print("Jasper connection timed out. Please login again.")

