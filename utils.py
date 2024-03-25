import os.path



#-----FUNCTIONS-------------

###read file with names to exclude
def getExcludeList(listOfExcludedNames, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    excludeList = []
    if os.path.isfile(listOfExcludedNames):
        with open(listOfExcludedNames, encoding="utf8") as file_in:    
            for line in file_in:
                excludeList.append(line)
    else:
        print("The file " + listOfExcludedNames + " doesn't exist. Nothing will be excluded.")
    return (excludeList)

def getUser(fileName, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    user = ''
    if(verboseOn): print("fileName:" + fileName)
    if os.path.isfile(fileName):
        if(verboseOn): print("file found")
        with open(fileName, encoding="utf8") as file_in:
            counter = 0
            for line in file_in:
                if counter==0:
                    user = line
                counter += 1
            if(verboseOn): print("user:" + user)
    else:
        print("The file " + fileName + " doesn't exist. Can't read.")
    return (user)

def getPwd(fileName, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    pwd = ''
    if(verboseOn): print("fileName:" + fileName)
    if os.path.isfile(fileName):
        if(verboseOn): print("file found")
        with open(fileName, encoding="utf8") as file_in:
            counter = 0
            for line in file_in:
                if counter==1:
                    pwd = line
                counter += 1
            if(verboseOn): print("pwd:" + pwd)
    else:
        print("The file " + fileName + " doesn't exist. Can't read.")
    return (pwd)

def printAd(adPrinted):
    if (not adPrinted):
        print("#########################################################################")
        print("   Created by IT Coach - Uldis Karlovs-Karlovskis")
        print("   Check out my website at https://www.uldiskarlovskarlovskis.com/")
        print("#########################################################################")
    return 1
    